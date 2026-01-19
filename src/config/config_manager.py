"""
配置管理器
负责配置的读取、保存和管理
"""
import os
import json
import logging
from pathlib import Path
from typing import Optional
from .settings import AppSettings
from ..utils.path_helper import get_config_dir


class ConfigManager:
    """配置管理器（单例模式）"""
    
    _instance: Optional['ConfigManager'] = None
    _initialized: bool = False
    
    def __new__(cls):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化配置管理器"""
        if self._initialized:
            return
            
        self.logger = logging.getLogger(__name__)
        self.settings = AppSettings()
        
        # 使用统一的配置目录管理
        self.config_dir = get_config_dir()
        self.config_file = self.config_dir / "config.json"
        
        # 加载配置
        self.load()
        
        self._initialized = True
        self.logger.info(f"配置管理器初始化完成，配置文件路径: {self.config_file}")
    
    def _get_config_dir(self) -> Path:
        """
        已弃用：使用 path_helper.get_config_dir() 代替
        
        为了保持向后兼容而保留此方法
        
        Returns:
            Path: 配置文件目录路径
        """
        return get_config_dir()
    
    def load(self) -> bool:
        """
        从文件加载配置
        
        Returns:
            bool: 是否成功加载
        """
        try:
            if not self.config_file.exists():
                self.logger.info("配置文件不存在，使用默认配置")
                return False
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.settings = AppSettings.from_dict(data)
            self.logger.info("配置加载成功")
            return True
            
        except json.JSONDecodeError as e:
            self.logger.error(f"配置文件格式错误: {e}")
            self.logger.info("使用默认配置")
            return False
        except Exception as e:
            self.logger.error(f"加载配置失败: {e}")
            self.logger.info("使用默认配置")
            return False
    
    def save(self) -> bool:
        """
        保存配置到文件
        
        Returns:
            bool: 是否成功保存
        """
        try:
            # 确保目录存在
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存配置
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings.to_dict(), f, indent=4, ensure_ascii=False)
            
            self.logger.debug("配置保存成功")
            return True
            
        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")
            return False
    
    def get(self, key: str, default=None):
        """
        获取配置项
        
        Args:
            key: 配置项名称
            default: 默认值
            
        Returns:
            配置项的值
        """
        return getattr(self.settings, key, default)
    
    def set(self, key: str, value, save_immediately: bool = True):
        """
        设置配置项
        
        Args:
            key: 配置项名称
            value: 配置项的值
            save_immediately: 是否立即保存到文件
        """
        if hasattr(self.settings, key):
            setattr(self.settings, key, value)
            if save_immediately:
                self.save()
        else:
            self.logger.warning(f"尝试设置不存在的配置项: {key}")
    
    def update(self, save_immediately: bool = True, **kwargs):
        """
        批量更新配置项
        
        Args:
            save_immediately: 是否立即保存到文件
            **kwargs: 要更新的配置项
        """
        self.settings.update(**kwargs)
        if save_immediately:
            self.save()
    
    def reset(self, save_immediately: bool = True):
        """
        重置为默认配置
        
        Args:
            save_immediately: 是否立即保存到文件
        """
        self.settings = AppSettings()
        if save_immediately:
            self.save()
        self.logger.info("配置已重置为默认值")
    
    def get_config_path(self) -> str:
        """获取配置文件路径"""
        return str(self.config_file)
    
    def export_config(self, export_path: str) -> bool:
        """
        导出配置到指定路径
        
        Args:
            export_path: 导出路径
            
        Returns:
            bool: 是否成功导出
        """
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings.to_dict(), f, indent=4, ensure_ascii=False)
            self.logger.info(f"配置已导出到: {export_path}")
            return True
        except Exception as e:
            self.logger.error(f"导出配置失败: {e}")
            return False
    
    def import_config(self, import_path: str) -> bool:
        """
        从指定路径导入配置
        
        Args:
            import_path: 导入路径
            
        Returns:
            bool: 是否成功导入
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.settings = AppSettings.from_dict(data)
            self.save()
            self.logger.info(f"配置已从 {import_path} 导入")
            return True
        except Exception as e:
            self.logger.error(f"导入配置失败: {e}")
            return False
