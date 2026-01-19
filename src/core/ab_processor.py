"""
AB文件处理接口
提供AB文件的前处理和后处理功能
具体实现由继承类完成
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Union

class ABProcessorInterface(ABC):
    """AB文件处理器接口"""
    
    @abstractmethod
    def pre_process(self, ab_files: Union[str, List[str]], output_dir: Optional[str] = None) -> List[Dict]:
        """
        AB文件前处理
        包括文件验证、解密、解压等操作
        
        Args:
            ab_files: 单个AB文件路径或AB文件路径列表
            output_dir: 输出目录，如果为None则使用临时目录
            
        Returns:
            List[Dict]: 处理后的文件信息列表
        """
        pass
    
    @abstractmethod
    def post_process(self, processed_files: List[Dict], output_dir: str) -> List[str]:
        """
        AB文件后处理
        包括文件打包、加密等操作
        
        Args:
            processed_files: 处理后的文件信息列表
            output_dir: 输出目录
            
        Returns:
            List[str]: 处理后的文件路径列表
        """
        pass
    
    @abstractmethod
    def cleanup(self):
        """清理临时文件和目录"""
        pass 