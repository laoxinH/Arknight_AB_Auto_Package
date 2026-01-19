import re
from abc import ABC, abstractmethod
from binascii import hexlify
from pathlib import Path
from typing import Optional, Union, Tuple
import logging

from src.core.abprocessor.CompressionMethod import CompressionMethod
from src.core.abprocessor.BundleProcessor import BundleProcessor


class CommonBundleProcessor(BundleProcessor):
    """CrossCore游戏AB文件处理器实现"""

    def __init__(self):
        """初始化CrossCore处理器"""
        super().__init__()
        self.header_size = 0  # CrossCore固定header大小
        self.header = b""  # CrossCore固定header数据

    @staticmethod
    def is_valid_bundle(file_path: Union[str, Path]) -> bool:
        """
        判断是否为Common格式的资源包
        如果不是其他特殊格式（CrossCore、Re1999），则为Common格式

        Args:
            file_path: 文件路径

        Returns:
            bool: 如果是Common格式返回True
        """
        try:
            with open(file_path, "rb") as f:
                file_data = f.read()
            
            # 检查是否为CrossCore格式（交错加密）
            openFileHex = hexlify(file_data)
            unityFS_len = len(re.findall(b"556e6974794653000000000", openFileHex))
            if unityFS_len == 2:
                return False
            
            # 检查是否为Re1999格式
            if len(file_data) >= 2 and file_data[0] ^ 0x55 == file_data[1] ^ 0x6e:
                return False
            
            # 其他情况为Common格式
            return True
        except Exception:
            return False

    def preprocess(self, file_path: Union[str, Path]) -> Tuple[bytes, Optional[bytes]]:
        """
        预处理CrossCore的AB文件
        移除加密header并返回处理后的数据

        Args:
            file_path: AB文件路径

        Returns:
            Tuple[bytes, Optional[bytes]]: (处理后的数据, 原始header数据)
        """
        try:
            with open(file_path, "rb") as f:
                file_data = f.read()

            return file_data, None

        except Exception as e:
            self.logger.error(f"预处理文件 {file_path} 时出错: {str(e)}")
            return b"", None

    def postprocess(self, data: bytes) -> bytes:
        """
        后处理CrossCore的AB文件数据
        重新添加加密header

        Args:
            data: AB文件数据
            header: 原始header数据

        Returns:
            bytes: 处理完成的数据
        """
        if self.header_size == 0:
            return data

        try:
            return self.header + data
        except Exception as e:
            self.logger.error(f"后处理数据时出错: {str(e)}")
            return data

    def need_unpack(self) -> bool:
        """
        获取header大小
        Returns:
            bool: 是否需要解包
        """

        return True
    
    def compression_method(self) -> CompressionMethod:
        """
        获取压缩方法

        Returns:
            CompressionMethod: 压缩方法
        """
        return CompressionMethod.LZ4

