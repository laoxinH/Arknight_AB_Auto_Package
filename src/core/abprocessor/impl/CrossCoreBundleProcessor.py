import re
from abc import ABC, abstractmethod
from binascii import hexlify
from pathlib import Path
from typing import Optional, Union, Tuple
import logging

from src.core.abprocessor.CompressionMethod import CompressionMethod
from src.core.abprocessor.BundleProcessor import BundleProcessor


class CrossCoreBundleProcessor(BundleProcessor):
    """CrossCore游戏AB文件处理器实现"""

    def __init__(self):
        """初始化CrossCore处理器"""
        super().__init__()
        self.header_size = 0  # CrossCore固定header大小
        self.header = b""  # CrossCore固定header数据

    @staticmethod
    def is_valid_bundle(file_path: Union[str, Path]) -> bool:
        """
        判断是否为CrossCore的资源包（交错加密格式）
        通过检查UnityFS标识出现次数判断

        Args:
            file_path: 文件路径

        Returns:
            bool: 如果是CrossCore资源包返回True，否则返回False
        """
        try:
            with open(file_path, "rb") as f:
                file_data = f.read()
            openFileHex = hexlify(file_data)
            unityFS_len = len(re.findall(b"556e6974794653000000000", openFileHex))
            return unityFS_len == 2  # 交错加密格式有两个UnityFS标识
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

            openFileHex = hexlify(file_data)
            unityFS_len = len(re.findall(b"556e6974794653000000000", openFileHex))
            if unityFS_len < 2:
                return file_data, None
            else:
                unityFS_index = openFileHex.find(b"556e6974794653000000000",1)

            # 处理数据
            self.header_size = unityFS_index // 2
            processed_data = file_data[self.header_size:]
            # 保存处理后的数据
            header = file_data[:self.header_size]
            self.header = header
            # self.logger.info(f"交错战线AB预处理文件 {file_path} 完成，移除header大小: {self.header_size} 字节")

            return processed_data, header

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