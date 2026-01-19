from PyQt6.QtCore import pyqtSignal, QThread

from src.core.asset_extractor import AssetExtractor


class ExportABWorker(QThread):
    """导出AB资源包工作线程"""
    progress = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, source_file, output_dir, replace_files):
        super().__init__()
        self.source_file = source_file
        self.output_dir = output_dir
        self.replace_files = replace_files

    def run(self):
        try:
            self.progress.emit(f"正在导出AB资源包: {self.source_file}")
            extractor = AssetExtractor()

            # 导出AB资源包
            success = extractor.export_ab(
                self.source_file,
                self.output_dir,
                self.replace_files
            )

            if success:
                self.progress.emit("导出完成！")
                self.finished.emit()
            else:
                self.error.emit("导出失败，请查看日志")
        except Exception as e:
            self.error.emit(str(e))