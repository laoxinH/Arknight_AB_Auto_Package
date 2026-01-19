"""
应用程序配置数据模型
定义所有可持久化的配置项
"""
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class AppSettings:
    """应用程序设置数据类"""
    
    # 主题设置
    theme_mode: str = "auto"  # "auto", "light", "dark"
    
    # 窗口设置
    window_width: Optional[int] = None
    window_height: Optional[int] = None
    window_x: Optional[int] = None
    window_y: Optional[int] = None
    window_maximized: bool = False
    
    # 路径设置
    last_output_dir: Optional[str] = None
    last_input_dir: Optional[str] = None
    
    # 日志设置
    log_enabled: bool = True  # 日志文件启用状态
    log_level: str = "INFO"  # 日志等级: DEBUG, INFO, WARNING, ERROR, CRITICAL
    
    # 资源编辑设置
    ab_export_default_dir: Optional[str] = None  # 导出AB资源包默认保存目录
    
    # 实验室MOD设置
    lab_mod_default_password: str = ""  # 默认压缩密码
    lab_mod_enable_image_steganography: bool = False  # 默认是否启用图种
    lab_mod_default_description: str = ""  # 默认MOD描述
    lab_mod_export_default_dir: Optional[str] = None  # 导出实验室MOD默认保存目录
    
    # 其他设置（预留扩展）
    auto_check_update: bool = True
    language: str = "zh_CN"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'AppSettings':
        """从字典创建实例"""
        # 过滤掉不存在的字段
        valid_fields = {k: v for k, v in data.items() if k in cls.__annotations__}
        return cls(**valid_fields)
    
    def update(self, **kwargs):
        """更新配置项"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
