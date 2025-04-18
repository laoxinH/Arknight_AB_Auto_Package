"""
明日方舟资源包处理工具主入口
"""
import sys
import os
import traceback

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from src.utils.logger import setup_logger, log_exception

def main():
    """程序入口函数"""
    try:
        # 设置日志系统
        logger = setup_logger()
        logger.info("程序启动")
        
        # 设置全局异常处理器
        sys.excepthook = lambda exc_type, exc_value, exc_traceback: log_exception(logger, exc_type, exc_value, exc_traceback)
        
        # 记录系统信息
        logger.info(f"Python版本: {sys.version}")
        logger.info(f"操作系统: {sys.platform}")
        logger.info(f"工作目录: {os.getcwd()}")
        
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        logger.info("主窗口显示完成")
        sys.exit(app.exec())
    except Exception as e:
        logger.error(f"程序启动失败: {str(e)}")
        logger.error(traceback.format_exc())
        raise

if __name__ == "__main__":
    main() 