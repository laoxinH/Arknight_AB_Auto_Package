"""
路径辅助模块
提供统一的路径管理，确保在开发环境和打包环境都能正常工作
"""
import os
import sys
from pathlib import Path


def get_app_root() -> Path:
    """
    获取应用程序根目录
    
    在开发环境下返回项目根目录
    在打包环境下返回 exe 所在目录
    
    Returns:
        Path: 应用程序根目录
    """
    if getattr(sys, 'frozen', False):
        # 打包后的环境
        # sys.executable 是 exe 文件的路径
        return Path(sys.executable).parent
    else:
        # 开发环境
        # 返回项目根目录（src 的上级目录）
        return Path(__file__).parent.parent.parent


def get_user_data_dir() -> Path:
    """
    获取用户数据目录
    用于存储配置、日志等用户数据
    
    Returns:
        Path: 用户数据目录
    """
    if os.name == 'nt':  # Windows
        base_dir = Path(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')))
        data_dir = base_dir / "UnityABTool"
    else:  # Linux/Mac
        base_dir = Path.home() / ".local" / "share"
        data_dir = base_dir / "UnityABTool"
    
    # 确保目录存在
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_config_dir() -> Path:
    """
    获取配置目录
    
    Returns:
        Path: 配置目录路径
    """
    try:
        # 优先使用APP运行位置
        config_dir = get_app_root()
        # logs_dir.mkdir(parents=True, exist_ok=True)
        return config_dir
    except (OSError, PermissionError):
        # 如果APP运行位置目录不可用，使用用户数据目录
        config_dir = get_user_data_dir()
        config_dir.mkdir(parents=True, exist_ok=True)
        # 测试是否有写权限
        test_file = config_dir / ".test"
        test_file.touch()
        test_file.unlink()
        return config_dir


    if os.name == 'nt':  # Windows
        base_dir = Path(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')))
        config_dir = base_dir / "ArknightABTool"
    else:  # Linux/Mac
        base_dir = Path.home() / ".config"
        config_dir = base_dir / "ArknightABTool"
    
    # 确保目录存在
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_logs_dir() -> Path:
    """
    获取日志目录
    
    优先使用用户数据目录，如果失败则使用应用程序目录
    
    Returns:
        Path: 日志目录路径
    """
    try:
        # 优先使用APP运行位置
        logs_dir = get_app_root() / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        return logs_dir
    except (OSError, PermissionError):
        # 如果APP运行位置目录不可用，使用用户数据目录
        logs_dir = get_user_data_dir() / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        # 测试是否有写权限
        test_file = logs_dir / ".test"
        test_file.touch()
        test_file.unlink()
        return logs_dir



def get_temp_dir() -> Path:
    """
    获取临时文件目录
    
    Returns:
        Path: 临时文件目录路径
    """
    temp_dir = get_user_data_dir() / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def get_resource_path(relative_path: str) -> Path:
    """
    获取资源文件路径
    
    在开发环境和打包环境下都能正确找到资源文件
    
    Args:
        relative_path: 相对路径（相对于 src/resource）
    
    Returns:
        Path: 资源文件的绝对路径
    """
    if getattr(sys, 'frozen', False):
        # 打包后的环境，资源在 _internal 目录
        if hasattr(sys, '_MEIPASS'):
            # 单文件模式
            base_path = Path(sys._MEIPASS)
        else:
            # 目录模式
            base_path = Path(sys.executable).parent / "_internal"
        
        resource_path = base_path / "src" / "resource" / relative_path
    else:
        # 开发环境
        resource_path = get_app_root() / "src" / "resource" / relative_path
    
    return resource_path


# 初始化时打印路径信息（用于调试）
if __name__ != "__main__":
    import logging
    logger = logging.getLogger(__name__)
    logger.debug(f"应用根目录: {get_app_root()}")
    logger.debug(f"用户数据目录: {get_user_data_dir()}")
    logger.debug(f"配置目录: {get_config_dir()}")
    logger.debug(f"日志目录: {get_logs_dir()}")
