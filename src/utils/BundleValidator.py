"""
AB文件有效性检验工具类
用于验证文件是否为有效的Unity资源包
"""
from pathlib import Path
from typing import Union, Tuple
import logging
from binascii import hexlify


class BundleValidator:
    """AB文件有效性检验工具"""

    def __init__(self):
        """初始化验证器"""
        self.logger = logging.getLogger(__name__)
        # Unity资源包的标识字符串的十六进制表示
        self.unity_signature = b"556e6974794653"  # "UnityFS" in hex

    def is_valid_bundle(self, file_path: Union[str, Path]) -> Tuple[bool, str]:
        """
        验证文件是否为有效的Unity资源包

        Args:
            file_path: 文件路径

        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
            如果文件有效，错误信息为空字符串
        """
        try:
            if not Path(file_path).exists():
                return False, "文件不存在"
            if not Path(file_path).is_file():
                return False, "路径不是文件"

            with open(file_path, "rb") as f:
                # 读取文件头部数据
                header_data = f.read(1024)  # 读取前1KB数据进行检查
                if not header_data:
                    return False, "文件为空"

                # 转换为十六进制字符串
                hex_data = hexlify(header_data)

                # 查找Unity标识
                # 如果文件经过加密，可能不在文件开头
                if self.unity_signature not in hex_data:
                    return False, "未找到Unity资源包标识"

                return True, ""

        except Exception as e:
            self.logger.error(f"验证文件 {file_path} 时出错: {str(e)}")
            return False, f"验证出错: {str(e)}"

    def get_unity_header_position(self, file_path: Union[str, Path]) -> int:
        """
        获取Unity标识在文件中的位置

        Args:
            file_path: 文件路径

        Returns:
            int: Unity标识的位置
            如果未找到返回-1
        """
        try:
            with open(file_path, "rb") as f:
                file_data = f.read()
                hex_data = hexlify(file_data)

                # 查找Unity标识位置
                position = hex_data.find(self.unity_signature)
                if position != -1:
                    # 因为是十六进制字符串，所以实际位置需要除以2
                    return position // 2
                return -1

        except Exception as e:
            self.logger.error(f"获取Unity标识位置时出错: {str(e)}")
            return -1

    def get_header_info(self, file_path: Union[str, Path]) -> dict:
        """
        获取AB文件的头部信息

        Args:
            file_path: 文件路径

        Returns:
            dict: 头部信息
            包含以下字段:
            - valid: 是否有效
            - header_position: Unity标识位置
            - encrypted: 是否加密
            - error: 错误信息
        """
        result = {
            "valid": False,
            "header_position": -1,
            "encrypted": False,
            "error": ""
        }

        try:
            is_valid, error = self.is_valid_bundle(file_path)
            if not is_valid:
                result["error"] = error
                return result

            header_pos = self.get_unity_header_position(file_path)
            result["header_position"] = header_pos
            result["valid"] = True
            result["encrypted"] = header_pos > 0  # 如果标识不在开头，则认为是加密的

        except Exception as e:
            result["error"] = str(e)

        return result