from PyQt6.QtCore import QThread, pyqtSignal
from typing import List, Tuple

from src.utils.BundleValidator import BundleValidator


class BundleValidateWorker(QThread):
    """AB文件验证工作线程"""
    progress = pyqtSignal(str)  # 进度信号
    validated = pyqtSignal(list)  # 验证完成信号，发送有效的文件列表
    error = pyqtSignal(str)  # 错误信号
    validator = BundleValidator()  # AB文件验证器实例

    def __init__(self, files: List[str]):
        """
        初始化验证工作线程

        Args:
            files: 要验证的文件路径列表
            validator: AB文件验证器实例
        """
        super().__init__()
        self.files = files

    def run(self):
        """执行验证任务"""
        try:

            valid_files = []
            total = len(self.files)

            for index, file_path in enumerate(self.files, 1):
                try:
                    is_valid, _ = self.validator.is_valid_bundle(file_path)
                    if is_valid:
                        valid_files.append(file_path)

                    # 发送进度信息
                    progress = (index / total) * 100
                    self.progress.emit(f"正在验证: {index}/{total} ({progress:.1f}%)")

                except Exception as e:
                    self.progress.emit(f"验证文件 {file_path} 时出错: {str(e)}")
                    continue

            self.validated.emit(valid_files)

        except Exception as e:
            self.error.emit(f"验证过程出错: {str(e)}")