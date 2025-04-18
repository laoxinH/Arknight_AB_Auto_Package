"""
ZIP压缩工具模块
"""
import os
import zipfile
from typing import Optional
import logging
from typing import Union, BinaryIO
from pathlib import Path
import shutil
import py7zr
import pyminizip
import pyzipper

logger = logging.getLogger(__name__)

def compress_to_zip(source_dir: str, output_path: str, compression_format: str = "ZIP", password: str = None) -> bool:
    """
    将目录压缩为ZIP或7Z文件
    
    Args:
        source_dir: 源目录路径
        output_path: 输出文件路径
        compression_format: 压缩格式，可选"ZIP"或"7Z"
        password: 压缩密码，可选
        
    Returns:
        bool: 是否压缩成功
    """
    if password == "" or password is None:
        password = None
    try:
        # 确保源目录存在
        if not os.path.exists(source_dir):
            logging.error(f"源目录不存在: {source_dir}")
            return False
            
        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        if compression_format == "ZIP":
            try:
                # 使用pyzipper创建ZIP文件，支持AES加密
                with pyzipper.AESZipFile(
                    output_path,
                    'w',
                    compression=pyzipper.ZIP_DEFLATED,
                    encryption=pyzipper.WZ_AES if password else None
                ) as zipf:
                    # 如果设置了密码，使用AES加密
                    if password:
                        zipf.setpassword(password.encode('utf-8'))
                    
                    # 遍历目录并添加文件
                    for root, dirs, files in os.walk(source_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            # 计算相对路径，确保使用UTF-8编码
                            arcname = os.path.relpath(file_path, source_dir)
                            zipf.write(file_path, arcname)
                return True
            except ImportError:
                logging.error("未安装pyzipper库，无法创建加密ZIP文件")
                return False
            except Exception as e:
                logging.error(f"创建ZIP文件时出错: {str(e)}")
                return False
        elif compression_format == "7Z":
            try:
                # 使用py7zr创建带密码的7Z文件
                with py7zr.SevenZipFile(output_path, 'w', password=password) as archive:
                    archive.writeall(source_dir, os.path.basename(source_dir))
                return True
            except ImportError:
                logging.error("未安装py7zr库，无法创建7Z文件")
                return False
        else:
            logging.error(f"不支持的压缩格式: {compression_format}")
            return False
            
    except Exception as e:
        logging.error(f"压缩文件时出错: {str(e)}")
        return False

def compress_files_to_zip(file_paths: list[str], output_path: str) -> bool:
    """
    将多个文件压缩为ZIP文件
    
    Args:
        file_paths: 需要压缩的文件路径列表
        output_path: 输出ZIP文件的完整路径（包含文件名）
        
    Returns:
        bool: 压缩是否成功
    """
    try:
        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # 创建ZIP文件
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in file_paths:
                if os.path.exists(file_path):
                    # 只添加文件名，不包含路径
                    zipf.write(file_path, os.path.basename(file_path))
                    
        logger.info(f"成功压缩多个文件到: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"压缩多个文件时出错: {str(e)}")
        return False 
    
@staticmethod
def create_image_zip(zip_path: Union[str, Path], image_path: Union[str, Path], output_path: Union[str, Path]) -> bool:
    """
    创建图种文件
    
    Args:
        zip_path: ZIP文件路径
        image_path: 图片文件路径
        output_path: 输出文件路径
        
    Returns:
        bool: 是否创建成功
    """
    try:
        # 确保输入文件存在
        if not os.path.exists(zip_path) or not os.path.exists(image_path):
            return False
            
        # 复制ZIP文件到输出路径
        # shutil.copy2(zip_path, output_path)
        
        # 以二进制追加模式打开输出文件
        with open(output_path, 'ab') as output_file:
            # 读取并追加图片数据
            with open(output_path, 'rb') as image_file:
                output_file.write(image_file.read())
                
        return True
    except Exception as e:
        logger.error(f"创建图种文件失败: {str(e)}")
        return False