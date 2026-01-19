"""
AB文件处理器接口
定义了对AB文件进行预处理和后处理的标准接口
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Union, Tuple
import logging

from src.core.abprocessor import CompressionMethod


class BundleProcessor(ABC):
    """AB文件处理器接口"""

    def __init__(self):
        """初始化处理器"""
        self.logger = logging.getLogger(__name__)

    @abstractmethod
    def preprocess(self, file_path: Union[str, Path]) -> Tuple[bytes, Optional[bytes]]:
        """
        预处理AB文件

        Args:
            file_path: 文件路径

        Returns:
            Tuple[bytes, Optional[bytes]]: (处理后的数据, 原始header数据)
            如果文件不需要处理，返回原始数据和None
        """
        pass

    @abstractmethod
    def postprocess(self, data: bytes) -> bytes:
        """
        后处理AB文件数据

        Args:
            data: 处理后的AB文件数据

        Returns:
            bytes: 处理完成的数据
        """
        pass

    @abstractmethod
    def need_unpack(self) -> bool:
        """
        获取header大小

        Returns:
            int: header大小
        """
        pass

    @abstractmethod
    def compression_method(self) -> CompressionMethod:
        """
        获取压缩方法

        Returns:
            CompressionMethod: 压缩方法
        """
        pass

    @staticmethod
    @abstractmethod
    def is_valid_bundle(file_path: Union[str, Path]) -> bool:
        """
        判断是否为本游戏的资源包

        Args:
            file_path: 文件路径

        Returns:
            bool: 如果是本游戏资源包返回True，否则返回False
        """
        pass


