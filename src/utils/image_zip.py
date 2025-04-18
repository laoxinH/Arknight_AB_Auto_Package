import os
import shutil
import zlib
from struct import unpack_from
from typing import Union, BinaryIO
from pathlib import Path
from PIL import Image
# 导入日志
import logging
logger = logging.getLogger(__name__)

class ImageZip:
    """图种工具类，用于将图片附加到ZIP文件尾部"""
    """初始化图种工具类"""
    @staticmethod
    def create_image_zip(zip_path: Union[str, Path], image_path: Union[str, Path]) -> bool:
        idat_body = b""
        # 截取图片文件houzhui
        PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
        image_suffix = os.path.splitext(image_path)[1]
        zip_name = os.path.splitext(zip_path)[0]
        content_in = open(zip_path, "rb")
        png_in = read_png(image_path, os.path.getsize(zip_path) * 1.5)
        png_out = open(f"{zip_name}{image_suffix}", "wb")
        png_header = png_in.read(len(PNG_MAGIC))
        assert(png_header == PNG_MAGIC)
        png_out.write(png_header)

        # iterate through the chunks of the PNG file
        while True:
            # parse a chunk
            chunk_len = int.from_bytes(png_in.read(4), "big")
            chunk_type = png_in.read(4)
            chunk_body = png_in.read(chunk_len)
            chunk_csum = int.from_bytes(png_in.read(4), "big")

            # if it's a non-essential chunk, skip over it
            if chunk_type not in [b"IHDR", b"PLTE", b"IDAT", b"IEND"]:
                # print("Warning: dropping non-essential or unknown chunk:", chunk_type.decode())
                logger.warning(f"警告: 丢弃非必要或未知块: {chunk_type.decode()}")
                continue

            # take note of the image width and height, for future calculations
            if chunk_type == b"IHDR":
                width, height = unpack_from(">II", chunk_body)
                # print(f"Image size: {width}x{height}px")
                logger.info(f"图片大小: {width}x{height}px")


            # There might be multiple IDAT chunks, we will concatenate their contents
            # and write them into a single chunk later
            if chunk_type == b"IDAT":
                idat_body += chunk_body
                continue

            # the IEND chunk should be at the end, now is the time to write our IDAT
            # chunk, before we actually write the IEND chunk
            if chunk_type == b"IEND":
                start_offset = png_out.tell()+8+len(idat_body)
                # print("Embedded file starts at offset", hex(start_offset))
                logger.info(f"嵌入文件开始于偏移量: {hex(start_offset)}")

                # concatenate our content that we want to embed
                idat_body += content_in.read()

                if len(idat_body) > width * height:
                    logger.error("错误: 输入文件过大，无法容纳在封面图像分辨率内。")
                    raise ValueError("输入文件过大，无法容纳在封面图像分辨率内。")

                # if its a zip file, fix the offsets
                if os.path.splitext(zip_path)[1].lower().replace(".","") in ["zip", "jar"]:
                    logger.info("修复zip偏移量...")
                    idat_body = bytearray(idat_body)
                    fixup_zip(idat_body, start_offset)

                # write the IDAT chunk
                png_out.write(len(idat_body).to_bytes(4, "big"))
                png_out.write(b"IDAT")
                png_out.write(idat_body)
                png_out.write(zlib.crc32(b"IDAT" + idat_body).to_bytes(4, "big"))

            # if we reached here, we're writing the IHDR, PLTE or IEND chunk
            png_out.write(chunk_len.to_bytes(4, "big"))
            png_out.write(chunk_type)
            png_out.write(chunk_body)
            png_out.write(chunk_csum.to_bytes(4, "big"))

            if chunk_type == b"IEND":
                # we're done!
                break

        # close our file handles
        png_in.close()
        content_in.close()
        png_out.close()
        return True

# this function is gross
def fixup_zip(data, start_offset):

    # find the "end of central directory" marker
    end_central_dir_offset = data.rindex(b"PK\x05\x06")

    # adjust comment length so that any trailing data (i.e. PNG IEND)
    # is part of the comment
    comment_length = (len(data)-end_central_dir_offset) - 22 + 0x10
    cl_range = slice(end_central_dir_offset+20, end_central_dir_offset+20+2)
    data[cl_range] = comment_length.to_bytes(2, "little")

    # find the number of central directory entries
    cdent_count = unpack_from("<H", data, end_central_dir_offset+10)[0]

    # find the offset of the central directory entries, and fix it
    cd_range = slice(end_central_dir_offset+16, end_central_dir_offset+16+4)
    central_dir_start_offset = int.from_bytes(data[cd_range], "little")
    data[cd_range] = (central_dir_start_offset + start_offset).to_bytes(4, "little")

    # iterate over the central directory entries
    for _ in range(cdent_count):
        central_dir_start_offset = data.index(b"PK\x01\x02", central_dir_start_offset)

        # fix the offset that points to the local file header
        off_range = slice(central_dir_start_offset+42, central_dir_start_offset+42+4)
        off = int.from_bytes(data[off_range], "little")
        data[off_range] = (off + start_offset).to_bytes(4, "little")

        central_dir_start_offset += 1

def read_png(png_path, file_size):
    """
    Resize an image to the specified resolution, stretching or compressing as needed.

    Args:
        input_path (str): Path to the input image.
        output_path (str): Path to save the resized image.
        width (int): Target width.
        height (int): Target height.
    """
    # 判断文件大小是否超过限制是否超过图片长宽乘积
    # 计算图片的长宽乘积
    width, height = Image.open(png_path).size
    image_size = width * height
    # 如果file_size超过限制image_size，则进行放大
    logger.info(f"文件大小: {file_size}，图片大小: {image_size}")
    if file_size > image_size:
        logger.info("文件大小超过限制，进行缩放")
        # 计算缩放比例
        scale = (file_size / image_size) ** 0.5
        # 计算新的宽高
        width = int(width * scale)
        height = int(height * scale)
        with Image.open(png_path) as img:
    # Resize the image to the specified resolution
            resized_img = img.resize((width, height), Image.Resampling.LANCZOS)
            resized_img.save(png_path)
    # 修改完成返回textIOwrapper
    # Save the resized image to the output path

    return open(png_path,"rb")

# Example usage
