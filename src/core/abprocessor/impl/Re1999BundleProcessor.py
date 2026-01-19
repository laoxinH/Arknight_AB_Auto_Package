import re
from abc import ABC, abstractmethod
from binascii import hexlify
from pathlib import Path
from typing import Optional, Union, Tuple
import logging

from src.core.abprocessor.CompressionMethod import CompressionMethod
from src.core.abprocessor.BundleProcessor import BundleProcessor


class Re1999BundleProcessor(BundleProcessor):
    """Re1999游戏AB文件处理器实现"""

    def __init__(self):
        """初始化Re1999处理器"""
        super().__init__()
        # 解密计算密钥
        self.decryption_key_A = 0x55
        self.decryption_key_B = 0x6e
        # 默认解密密钥
        self.key = None  # Re1999加密密钥

    @staticmethod
    def is_valid_bundle(file_path: Union[str, Path]) -> bool:
        """
        判断是否为Re1999的资源包（XOR加密格式）
        通过解密前几个字节检查是否为Unity标准前缀

        Args:
            file_path: 文件路径

        Returns:
            bool: 如果是Re1999资源包返回True，否则返回False
        """
        try:
            with open(file_path, "rb") as f:
                file_data = f.read()
            
            # 检查文件是否足够长（至少需要5个字节来验证"Unity"）
            if len(file_data) < 5:
                return False
            
            # 计算解密密钥
            key = file_data[0] ^ 0x55  # 'U' 的 ASCII 值
            
            # 排除密钥为0的情况（说明文件本身就是"Unity"开头，是普通AB文件）
            if key == 0:
                return False
            
            # 验证密钥是否正确（第二个字节解密后应该是 'n'）
            if key != file_data[1] ^ 0x6e:  # 'n' 的 ASCII 值
                return False
            
            # 解密前5个字节并检查是否为"Unity"
            decrypted = bytearray(5)
            for i in range(5):
                decrypted[i] = file_data[i] ^ key
            
            # 检查解密后的数据是否以"Unity"开头
            return bytes(decrypted) == b"Unity"
        except Exception:
            return False

    def preprocess(self, file_path: Union[str, Path]) -> Tuple[bytes, Optional[bytes]]:
        """
        解密Re1999的AB文件
        解密并返回处理后的数据

        Args:
            file_path: AB文件路径

        Returns:
            Tuple[bytes, Optional[bytes]]: (处理后的数据, 原始header数据)
        """
        try:
            with open(file_path, "rb") as f:
                file_data = f.read()

            result = bytearray(file_data)
            key = result[0] ^ self.decryption_key_A
            
            # 检查密钥是否为0（说明文件未加密）
            if key == 0:
                raise ValueError("文件未加密，不是Re1999格式")
            
            if not key == result[1] ^ self.decryption_key_B:
                # 抛出异常
                raise ValueError("无法识别的Re1999加密格式")
            self.key = key
            for i in range(0, len(result)):
                result[i] ^= key
            return bytes(result), self.key.to_bytes(1, 'big')

        except Exception as e:
            self.logger.error(f"预处理文件 {file_path} 时出错: {str(e)}")
            return b"", None

    def postprocess(self, data: bytes) -> bytes:
        """
        后处理Re1999的AB文件数据
        重新添加加密数据

        Args:
            data: AB文件数据

        Returns:
            bytes: 处理完成的数据
        """
        """对数据进行异或加密的核心函数"""
        if len(data) < 2:
            raise ValueError("原始数据必须至少包含2个字节。")
        if data[0] != self.decryption_key_A or data[1] != self.decryption_key_B:
            raise ValueError("数据格式不正确，无法进行加密。")
        if self.key is None:
            raise ValueError("加密密钥未设置，无法进行加密。")

        result = bytearray(data)
        for i in range(len(result)):
            result[i] ^= self.key
        return bytes(result)

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
        return CompressionMethod.LZMA