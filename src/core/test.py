import json
import os
import shutil
import tempfile
from typing import List
import logging
from UnityPy import AssetsManager

logger = logging.getLogger(__name__)

def scan_asset( asset_path: str) -> (List[{str, str, str, str, str}], str):
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
            logger.info(f"从路径列表/元组中选择第一个路径: {asset_path}")

        # 确保路径是字符串
        if not isinstance(asset_path, (str, bytes, os.PathLike)):
            raise TypeError(f"资源包路径类型错误: {asset_path}")

        # 检查文件是否存在
        if not os.path.exists(asset_path):
            raise FileNotFoundError(f"资源包文件不存在: {asset_path}")

        # 检查文件大小
        if os.path.getsize(asset_path) == 0:
            raise ValueError(f"资源包文件为空: {asset_path}")



        # 加载资源包
        logger.info(f"正在加载资源包: {asset_path}")
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
                    logger.warning(f"跳过无效对象: {obj}")
                    continue

                data = obj.read()
                if not data:
                    logger.warning(f"跳过空数据对象: {obj}")
                    continue

                file_type = obj.type.name if hasattr(obj, 'type') else "Unknown"

                # 处理名称为空的情况
                name = f"{data.m_Name}_{obj.path_id}" if hasattr(data,
                                                                 'm_Name') and f"{data.m_Name}_{obj.path_id}" else f"unnamed_{obj.path_id}"


                if file_type == "AudioClip":
                    tree = obj.read_typetree()
                    print(tree)
                    print(tree["m_Resource"]["m_Source"])


            except Exception as e:
                logger.warning(f"处理资源时出错: {str(e)}")
                #打印堆栈
                logger.error(e, exc_info=True)
                continue

        logger.info(f"扫描完成，找到 {len(files)} 个文件")
        return files

    except Exception as e:
        logger.error(f"扫描资源包时出错: {str(e)}")
        raise

if __name__ == "__main__":
    scan_asset("./char_421_crow.ab")