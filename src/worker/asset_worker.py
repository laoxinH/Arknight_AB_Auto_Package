from PyQt6.QtCore import QThread, pyqtSignal

from src.core.asset_extractor import AssetExtractor


class AssetWorker(QThread):
    """资源处理工作线程"""
    progress = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)
    scan_complete = pyqtSignal(list, str,str)


    def __init__(self, source_file, output_dir=None, selected_files=None, mode="extract", replace_files=None):
        super().__init__()
        self.source_file = source_file
        self.output_dir = output_dir
        self.selected_files = selected_files
        self.mode = mode
        self.replace_files = replace_files or {}
        self.is_scanning = selected_files is None

    def run(self):
        try:
            self.progress.emit(f"正在处理文件: {self.source_file}")
            extractor = AssetExtractor()

            if self.is_scanning:
                # 扫描模式

                files, temp_path = extractor.scan_asset(self.source_file)
                self.scan_complete.emit(files, temp_path, self.source_file)
                self.progress.emit("扫描完成！")
                self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))



