import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from .path_helper import get_logs_dir

def setup_logger():
    """设置日志系统"""
    # 使用统一的日志目录管理
    log_dir = get_logs_dir()
    
    # 生成日志文件名（包含时间戳）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"app_{timestamp}.log"
    
    # 配置日志格式
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger("ArknightAB")
    logger.info("日志系统初始化完成")
    logger.info(f"日志文件位置: {log_file}")
    return logger

def log_exception(logger, exc_type, exc_value, exc_traceback):
    """处理未捕获的异常"""
    if exc_type is KeyboardInterrupt:
        logger.info("程序被用户中断")
        return False
    logger.error("未捕获的异常:", exc_info=(exc_type, exc_value, exc_traceback))
    return False  # 返回False以允许默认的异常处理继续执行 