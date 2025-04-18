"""
资源提取器
"""
import os
import logging
import tempfile
import shutil
from typing import List, Tuple, Optional, Dict, Union, Any
from UnityPy import AssetsManager
from PIL import Image
import io
import datetime
import json

from UnityPy.enums import TextureFormat

# 设置UnityPy环境变量
os.environ['UNITYPY_AK'] = '1'


class AssetExtractor:
    """资源提取器"""

    def __init__(self, output_dir: Optional[str] = None):
        """
        初始化资源提取器
        
        Args:
            output_dir: 输出目录，如果为None则使用当前目录
        """
        self.output_dir = output_dir or os.getcwd()
        self.temp_dir = None

        # 配置日志
        self.logger = logging.getLogger(__name__)

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
                am = AssetsManager(asset_path)
                if not am or not hasattr(am, 'objects'):
                    raise ValueError("无法正确加载资源包")
            except Exception as e:
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
                    data_name = f"{name}" if hasattr(data, 'm_Name') and data.m_Name else f"unnamed_{obj.path_id}"
                    file_name = os.path.basename(name)
                    # 截取文件后缀
                    file_ext = os.path.splitext(file_name)[1]
                    name = name.replace(file_ext, "")
                    if file_type == "TextAsset":
                        # 保存文本资源到临时文件
                        # 截取path地文件名
                        file_name = os.path.basename(data.m_Name)
                        # 截取文件后缀
                        file_ext = os.path.splitext(file_name)[1]
                        # name = f"{name}{file_ext}"
                        temp_path = os.path.join(self.temp_dir, f"{name.replace(file_ext,"")}{file_ext}")
                        with open(temp_path, "wb") as f:
                            f.write(data.m_Script.encode("utf-8", "surrogateescape"))
                    elif file_type == "Texture2D":
                        # 保存图片资源到临时文件
                        temp_path = os.path.join(self.temp_dir, f"{name}.png")
                        data.image.save(temp_path)

                    elif file_type == "AudioClip":
                        # 保存音频资源到临时文件

                        temp_path = os.path.join(self.temp_dir, f"{name}.wav")
                        for name1, data in data.samples.items():
                            with open(temp_path, "wb") as f:
                                f.write(data)
                        # files.append((f"{data_name}.wav", file_type, temp_path))

                    elif file_type == "Mesh":
                        # 保存网格资源到临时文件
                        temp_path = os.path.join(self.temp_dir, f"{name}.obj")
                        with open(temp_path, "w") as f:
                            f.write(str(data.m_VertexData))
                        # files.append((data_name, file_type, temp_path))

                    elif file_type == "Material":
                        # 保存材质资源到临时文件
                        temp_path = os.path.join(self.temp_dir, f"{name}.mat")
                        with open(temp_path, "w") as f:
                            f.write(str(data.m_Shader))
                        # files.append((data_name, file_type, temp_path))
                    elif file_type == "MonoBehaviour":

                        # 保存材质资源到临时文件
                        temp_path = os.path.join(self.temp_dir, f"{name}.json")
                        with open(temp_path, "w") as f:
                            f.write(str(data.m_Script))
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
                        "name": name,
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

    def extract_asset(self, asset_path: str, selected_files: Optional[List[Tuple[str, str, str]]] = None,
                      mode: str = "extract", replace_files: Optional[Dict[Tuple[str, str, str], str]] = None) -> bool:
        """
        从资源包中提取资源

        Args:
            asset_path: 资源包路径
            selected_files: 要提取的文件列表，每个元素为(文件名, 文件类型, 临时文件路径)的元组
                           如果为None则提取所有文件
            mode: 处理模式，"extract" 为提取，"replace" 为替换
            replace_files: 替换文件字典，键为文件信息，值为替换文件路径

        Returns:
            是否提取成功
        """
        try:
            # 创建临时目录
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
            self.temp_dir = tempfile.mkdtemp(prefix='arknight_ab_')
            self.logger.info(f"创建临时目录: {self.temp_dir}")

            # 加载资源包
            self.logger.info(f"正在加载资源包: {asset_path}")
            am = AssetsManager(asset_path)

            # 创建输出目录
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir)
                self.logger.info(f"创建输出目录: {self.output_dir}")

            # 遍历所有对象
            for obj in am.objects:
                data = obj.read()
                obj_name = data.m_Name if hasattr(data,
                                                  'm_Name') and f"{data.m_Name}_{obj.path_id}" else f"unnamed_{obj.path_id}"
                if obj.type.name in ["TextAsset", "Texture2D"]:
                    # 如果指定了要提取的文件，则检查当前文件是否在列表中
                    if selected_files is not None:
                        file_info = next((f for f in selected_files if f[0] == obj_name), None)
                        if not file_info:
                            continue

                    # 创建子目录
                    sub_dir = os.path.join(self.output_dir, os.path.splitext(os.path.basename(asset_path))[0])
                    if not os.path.exists(sub_dir):
                        os.makedirs(sub_dir)
                        self.logger.info(f"创建子目录: {sub_dir}")

                    if obj.type.name == "TextAsset":
                        # 保存文本资源
                        output_path = os.path.join(sub_dir, f"{obj_name}.txt")
                        with open(output_path, "w", encoding="utf-8", errors='surrogateescape') as f:
                            f.write(data.m_Script)
                        self.logger.info(f"已保存文本文件: {output_path}")

                    elif obj.type.name == "Texture2D":
                        # 保存图片资源
                        output_path = os.path.join(sub_dir, f"{obj_name}.png")
                        data.image.save(output_path)
                        self.logger.info(f"已保存图片文件: {output_path}")

            # 清理临时目录
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                self.logger.info("已清理临时目录")
            return True

        except Exception as e:
            self.logger.error(f"提取资源时出错: {str(e)}")
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
            return False

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
            # 创建输出目录
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                self.logger.info(f"创建输出目录: {output_dir}")
            # 加载资源包
            self.logger.info(f"正在加载资源包: {asset_path}")
            am = AssetsManager(asset_path)

            # 创建替换文件字典
            replace_dict = {file_info: replace_path for file_info, replace_path in replace_files}
            # print(replace_dict)
            # 遍历所有对象
            for obj in am.objects:
                if obj.type.name in ["TextAsset", "Texture2D", "AudioClip"]:
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
                envdata = am.file.save(packer="lz4")
                f.write(envdata)
            self.logger.info(f"已保存修改后的资源包: {output_path}")

            return True

        except Exception as e:
            # 打印堆栈
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
            # 创建输出目录
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                self.logger.info(f"创建输出目录: {output_dir}")
            # 加载资源包
            self.logger.info(f"正在加载资源包: {asset_path}")
            am = AssetsManager(asset_path)

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
                envdata = am.file.save()
                f.write(envdata)
            self.logger.info(f"成功解密 {asset_path} -> {output_path}")
            return True

        except Exception as e:
            # 打印堆栈
            self.logger.error(f"解密错误: {str(e)}")
            return False