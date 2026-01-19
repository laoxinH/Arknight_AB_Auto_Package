"""
AB文件处理器管理器
用于管理和获取不同游戏的AB文件处理器
"""
import re
from binascii import hexlify
from enum import Enum, auto
from typing import Dict, Type

from src.core.abprocessor.BundleProcessor import BundleProcessor
from src.core.abprocessor.impl.Re1999BundleProcessor import Re1999BundleProcessor
from src.core.abprocessor.impl.CommonBundleProcessor import CommonBundleProcessor
from src.core.abprocessor.impl.CrossCoreBundleProcessor import CrossCoreBundleProcessor


class GameType(Enum):
    """游戏类型枚举"""
    ARKNIGHTS = auto()
    CROSSCORE = auto()
    RE1999 = auto()
    Common = auto()


class BundleProcessorManager:
    """AB文件处理器管理器（单例）"""
    _processors: Dict[GameType, Type[BundleProcessor]] = {
        GameType.ARKNIGHTS: CommonBundleProcessor,
        GameType.CROSSCORE: CrossCoreBundleProcessor,
        GameType.RE1999: Re1999BundleProcessor,
        GameType.Common: CommonBundleProcessor,
    }
    _path_processors = {}

    def get_processor_by_game_type(self, game_type: GameType) -> BundleProcessor:
        """
        获取指定游戏类型的处理器实例

        Args:
            game_type: 游戏类型

        Returns:
            BundleProcessor: 对应的处理器实例

        Raises:
            ValueError: 如果指定的游戏类型不存在
        """
        if game_type not in self._processors:
            raise ValueError(f"未找到游戏类型 {game_type} 的处理器")

        # 每次都创建新实例
        processor_class = self._processors[game_type]
        return processor_class()

    # 重载get_processor方法
    def get_processor_by_ab_type(self, file_path: str) -> BundleProcessor:
        """
        根据AB文件类型自动获取对应的处理器实例

        Args:
            file_path: ab文件路径

        Returns:
            BundleProcessor: 对应的处理器实例

        Raises:
            ValueError: 如果指定的游戏类型不存在
        """
        # 使用各个处理器的 is_valid_bundle 方法判断文件类型
     
        if Re1999BundleProcessor.is_valid_bundle(file_path):
            processor_class = self._processors[GameType.RE1999]
        elif CrossCoreBundleProcessor.is_valid_bundle(file_path):
             processor_class = self._processors[GameType.CROSSCORE]
        else:  # Common格式（包括Arknights等）
            processor_class = self._processors[GameType.Common]
   
        # 缓存处理器实例，避免重复创建
        if self._path_processors.get(file_path) is None:
            processor = processor_class()
            self._path_processors[file_path] = processor
        else:
            processor = self._path_processors[file_path]
        
        return processor



    @classmethod
    def register_processor(cls, game_type: GameType, processor_class: Type[BundleProcessor]):
        """
        注册新的处理器类型

        Args:
            game_type: 游戏类型
            processor_class: 处理器类
        """
        cls._processors[game_type] = processor_class
