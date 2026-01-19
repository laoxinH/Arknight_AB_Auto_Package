"""
资源提取器
"""
import os
import logging
import tempfile
import shutil
import traceback
from typing import List, Tuple, Optional, Dict, Union, Any
from UnityPy import AssetsManager
from PIL import Image
import io
import datetime
import json
from pathlib import Path

from UnityPy.enums import TextureFormat, CompressionFlags
from UnityPy.helpers import CompressionHelper

from src.core.crosscore_cryptor import CrosscoreCryptor
from src.core.abprocessor.BundleProcessorManager import BundleProcessorManager
from src.core.customdcompressor.lz4_ak import decompress_lz4ak


CompressionHelper.DECOMPRESSION_MAP[CompressionFlags.LZHAM] = decompress_lz4ak


class AssetExtractor:
    """资源提取器"""

    def __init__(self):
        """
        初始化资源提取器

        Args:
            output_dir: 输出目录，如果为None则使用当前目录
        """
        self.temp_dir = None

        # 配置日志
        self.logger = logging.getLogger(__name__)
        self.crosscoreCryptor = CrosscoreCryptor()
        self.bundle_processor_manager = BundleProcessorManager()

    def scan_asset(self, asset_path: str) -> (List[{str, str, str, str, str}], str):
        # print("开始执行扫描----")
        """
        扫描资源包中的文件

        Args:
            asset_path: 资源包路径，可以是字符串、列表或元组

        Returns:
            files: 文件列表，每个元素为(文件名, 文件类型, 临时文件路径)的元组
        """
        try:
            bundle_processor = self.bundle_processor_manager.get_processor_by_ab_type(asset_path)

            # 处理路径列表或元组
            if isinstance(asset_path, (list, tuple)):
                if not asset_path:
                    raise ValueError("资源包路径为空")
                asset_path = asset_path[0]  # 只处理第一个路径
                self.logger.info(f"从路径列表/元组中选择第一个路径: {asset_path}")

            # 确保路径是字符串
            if not isinstance(asset_path, (str, bytes, os.PathLike)):
                raise TypeError(f"资源包路径类型错误: {asset_path}")

            # 检查文件是否存在
            if not os.path.exists(asset_path):
                raise FileNotFoundError(f"资源包文件不存在: {asset_path}")

            # 检查文件大小
            if os.path.getsize(asset_path) == 0:
                raise ValueError(f"资源包文件为空: {asset_path}")

            # 创建临时目录
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
            self.temp_dir = tempfile.mkdtemp(prefix='arknight_ab_')
            self.logger.info(f"创建临时目录: {self.temp_dir}")

            # 加载资源包
            self.logger.info(f"正在加载资源包: {asset_path}")
            try:
                am = AssetsManager(bundle_processor.preprocess(asset_path)[0])
                if not am or not hasattr(am, 'objects'):
                    raise ValueError("无法正确加载资源包")
            except Exception as e:
                # 打印堆栈
                print(traceback.format_exc())
                raise ValueError(f"加载资源包失败: {str(e)}")

            files = []
            # 遍历所有对象
            for obj in am.objects:

                try:
                    if not hasattr(obj, 'read'):
                        self.logger.warning(f"跳过无效对象: {obj}")
                        continue

                    data = obj.read()
                    if not data:
                        self.logger.warning(f"跳过空数据对象: {obj}")
                        continue

                    file_type = obj.type.name if hasattr(obj, 'type') else "Unknown"

                    # 处理名称为空的情况
                    name = f"{data.m_Name}_{obj.path_id}" if hasattr(data,
                                                                     'm_Name') and f"{data.m_Name}_{obj.path_id}" else f"unnamed_{obj.path_id}"
                    if file_type != "TextAsset":
                        file_name = os.path.basename(name)
                        # 截取文件后缀
                        file_ext = os.path.splitext(file_name)[1]
                        name = name.replace(file_ext, "")
                    else:
                        # 截取文件后缀
                        file_name = os.path.basename(data.m_Name)
                        file_ext = os.path.splitext(file_name)[1]
                        name = name.replace(file_ext, "")
                    if file_type == "TextAsset":
                        temp_path = os.path.join(self.temp_dir, f"{name}{file_ext}")
                        # logging.debug(f"保存文本资源到临时文件: {temp_path}")
                        with open(temp_path, "wb") as f:
                            f.write(data.m_Script.encode("utf-8", "surrogateescape"))
                    elif file_type == "Texture2D":
                        # 保存图片资源到临时文件
                        file_ext = ".png"
                        temp_path = os.path.join(self.temp_dir, f"{name}{file_ext}")
                        data.image.save(temp_path)

                    elif file_type == "AudioClip":
                        # 保存音频资源到临时文件
                        file_ext = ".wav"
                        temp_path = os.path.join(self.temp_dir, f"{name}{file_ext}")
                        for name1, data1 in data.samples.items():
                            with open(temp_path, "wb") as f:
                                f.write(data1)
                        # files.append((f"{data_name}.wav", file_type, temp_path)) 
                        raw_dict = obj.read_typetree()
                    elif file_type == "Mesh":
                        # 保存网格资源到临时文件
                        file_ext = ".mesh"
                        temp_path = os.path.join(self.temp_dir, f"{name}{file_ext}")
                        with open(temp_path, "w") as f:
                            f.write(str(data.m_VertexData))
                        # files.append((data_name, file_type, temp_path))

                    elif file_type == "Material":
                        # 保存材质资源到临时文件
                        file_ext = ".mat"
                        temp_path = os.path.join(self.temp_dir, f"{name}{file_ext}")
                        with open(temp_path, "w") as f:
                            f.write(str(data.m_Shader))
                        # files.append((data_name, file_type, temp_path))
                    elif file_type == "MonoBehaviour":

                        # 保存材质资源到临时文件
                        file_ext = ".json"
                        temp_path = os.path.join(self.temp_dir, f"{name}{file_ext}")
                        if obj.serialized_type.node:
                            # save decoded data
                            tree = obj.read_typetree()
                            with open(temp_path, "wt", encoding = "utf8") as f:
                                json.dump(tree, f, ensure_ascii = False, indent = 4)
                        # files.append((data_name, file_type, temp_path))
                    else:
                        # 保存其他类型的资源到临时文件
                        temp_path = os.path.join(self.temp_dir, f"{name}.{file_type.lower()}")
                        #创建父目录
                        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
                        try:
                            # 尝试将对象转换为JSON字符串
                            obj_data = {
                                'type': file_type,
                                'name': name,
                                'path_id': obj.path_id,
                                'data': str(data)
                            }
                            with open(temp_path, "w", encoding='utf-8') as f:
                                json.dump(obj_data, f, ensure_ascii=False, indent=2)
                            # files.append((data_name, "Other", temp_path))
                        except Exception as e:
                            self.logger.warning(f"无法保存资源 {name} ({file_type}): {str(e)}")
                            continue
                    files.append({
                        "name": f"{name}{file_ext}",
                        "type": file_type,
                        "path": temp_path,
                        "path_id": obj.path_id,
                        "size": os.path.getsize(temp_path),
                    })

                except Exception as e:
                    self.logger.warning(f"处理资源时出错: {str(e)}")
                    #打印堆栈
                    self.logger.error(e, exc_info=True)
                    continue

            self.logger.info(f"扫描完成，找到 {len(files)} 个文件")
            return files, self.temp_dir

        except Exception as e:
            self.logger.error(f"扫描资源包时出错: {str(e)}")
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
            raise


    def export_ab(self, asset_path: str, output_dir: str,
                  replace_files: List[Tuple[Tuple[str, str, str], str]]) -> bool:
        # print(replace_files)
        """
        导出AB资源包

        Args:
            asset_path: 原始资源包路径
            output_dir: 输出目录
            replace_files: 替换文件列表，每个元素为(文件信息, 替换文件路径)的元组

        Returns:
            是否导出成功
        """
        try:
            bundle_processor = self.bundle_processor_manager.get_processor_by_ab_type(asset_path)
            # 创建输出目录
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                self.logger.info(f"创建输出目录: {output_dir}")
            # 加载资源包
            self.logger.info(f"正在加载资源包: {asset_path}")
            am = AssetsManager(bundle_processor.preprocess(asset_path)[0])

            # 创建替换文件字典
            replace_dict = {file_info: replace_path for file_info, replace_path in replace_files}
            # print(replace_dict)
            # 遍历所有对象
            for obj in am.objects:
                if obj.type.name in ["TextAsset", "Texture2D", "AudioClip", "MonoBehaviour"]:
                    data = obj.read()
                    try:
                        file_name = os.path.basename(data.m_Name)
                        # 截取文件后缀
                        file_ext = os.path.splitext(file_name)[1]
                        name = data.m_Name.replace(file_ext, "")
                    except Exception as e:
                        name = ""
                    obj_name = f"{name}_{obj.path_id}" if hasattr(data,
                                                                         'm_Name') and f"{name}_{obj.path_id}" else f"unnamed_{obj.path_id}"

                    # 检查是否有替换文件
                    file_info = next((f for f, _ in replace_files if obj_name in f[0]), None)
                    if file_info and file_info in replace_dict:
                        replace_path = replace_dict[file_info]

                        if obj.type.name == "TextAsset":
                            # 替换文本资源
                            with open(replace_path, "rb") as f:
                                data.m_Script = f.read().decode("utf-8", "surrogateescape")
                                data.save()
                            self.logger.info(f"已替换文本文件: {obj_name}->{replace_path}")

                        elif obj.type.name == "Texture2D":
                            # 替换图片资源
                            pil_img = Image.open(replace_path).convert("RGBA")
                            data.set_image(img=pil_img, target_format=TextureFormat.RGBA32)
                            data.save()
                            self.logger.info(f"已替换图片文件: {obj_name}->{replace_path}")
                        elif obj.type.name == "AudioClip":
                            # 替换音频资源
                            # 读取音频二进制到内存
                            with open(replace_path, 'rb') as f:
                                binary_data = bytearray(f.read())
                                # 设置音频数据
                                data.samples[f"{data.m_Name}.wav"] = binary_data
                                data.save()
                            self.logger.info(f"已替换音频文件: {obj_name}->{replace_path}")
                        elif obj.type.name == "MonoBehaviour":
                            # 替换MonoBehaviour资源
                            if obj.serialized_type.node:
                                # 读取为json
                                with open(replace_path, "r", encoding="utf-8") as f:
                                    # 读取json数据
                                    json_data = json.load(f)
                                    tree = obj.read_typetree()
                                    # apply modifications to the data within the tree
                                    obj.save_typetree(json_data)
                                    # 保存修改后的数据
                                    self.logger.info(f"已替换MonoBehaviour文件: {obj_name}->{replace_path}")
                            # with open(replace_path, "rb") as f:
                            #     data.set_samples(f.read())
                            # data.save()
                            # self.logger.info(f"已替换音频文件: {obj_name}")

            # 处理输出文件名
            base_name = os.path.basename(asset_path)
            name, ext = os.path.splitext(base_name)
            output_path = os.path.join(output_dir, f"{name}{ext}")

            # 如果文件已存在，添加时间戳
            if os.path.exists(output_path):
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                #获取output_path父目录
                output_path = os.path.dirname(output_path)
                output_path = os.path.join(output_path, f"{name}_{timestamp}{ext}")
            # 保存修改后的资源包
            with open(output_path, "wb") as f:
                envdata = am.file.save(packer=bundle_processor.compression_method().value)
                f.write(bundle_processor.postprocess(envdata))
            self.logger.info(f"已保存修改后的资源包: {output_path}")

            return True

        except Exception as e:
            # 打印堆栈
            self.logger.error(traceback.format_exc())
            self.logger.error(f"导出AB资源包时出错: {str(e)}")
            return False


    def decrypt_ab(self, asset_path: str, output_dir: str) -> bool:
        # print(replace_files)
        """
        导出AB资源包

        Args:
            asset_path: 原始资源包路径
            output_dir: 输出目录
            replace_files: 替换文件列表，每个元素为(文件信息, 替换文件路径)的元组

        Returns:
            是否导出成功
        """
        try:
            bundle_processor = self.bundle_processor_manager.get_processor_by_ab_type(asset_path)
            preprocess_data = bundle_processor.preprocess(asset_path)[0]
            # 创建输出目录
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                self.logger.info(f"创建输出目录: {output_dir}")
            # 加载资源包
            self.logger.info(f"正在加载资源包: {asset_path}")
            if bundle_processor.need_unpack():
                am = AssetsManager(preprocess_data)
                preprocess_data = am.file.save(packer="lz4")
            # 处理输出文件名
            base_name = os.path.basename(asset_path)
            name, ext = os.path.splitext(base_name)
            output_path = os.path.join(output_dir, f"{name}{ext}")

            # 如果文件已存在，添加时间戳
            if os.path.exists(output_path):
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                #获取output_path父目录
                output_path = os.path.dirname(output_path)
                output_path = os.path.join(output_path, f"{name}_{timestamp}{ext}")
            # 保存修改后的资源包
            with open(output_path, "wb") as f:
                envdata = bundle_processor.postprocess(preprocess_data)
                f.write(envdata)
            self.logger.info(f"成功解密 {asset_path} -> {output_path}")
            return True
        except Exception as e:
            # 打印堆栈
            self.logger.error(f"解密错误: {str(e)}")
            return False

