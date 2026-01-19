from PyQt6.QtCore import QThread, pyqtSignal, QMutex

from src.core.asset_extractor import AssetExtractor


class BatchAssetWorker(QThread):
    """资源处理工作线程"""
    """批量解密工作线程"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(int)
    error = pyqtSignal(str)
    file_progress = pyqtSignal(int, str)  # 文件索引, 状态

    def __init__(self, file_list: list[str], max_threads: int = 10):
        super().__init__()
        self.file_list = file_list
        self.max_threads = max_threads
        self.mutex = QMutex()
        self.threads = []
        self.ab_files = []
        self.completed_files = 0
        self.is_running = True
        self.file_status = {}  # 用于跟踪文件状态

    def run(self):
        """执行批量解密"""
        try:
            self.progress.emit("开始批量导入...")

            # 初始化进度
            self.completed_files = 0
            total_files = len(self.ab_files)
            self.progress.emit(f"找到 {total_files} 个文件，开始解密...")

            # 初始化文件状态
            self.file_status = {i: "等待解密" for i in range(total_files)}

            # 创建并启动线程
            for i, ab_file in enumerate(self.ab_files):
                if not self.is_running:
                    break

                # 等待可用线程
                while len(self.threads) >= self.max_threads and self.is_running:
                    for thread in self.threads[:]:
                        if not thread.isRunning():
                            self.threads.remove(thread)
                    self.msleep(100)

                if not self.is_running:
                    break

                # 创建新线程
                thread = DecryptThread(ab_file, self.target_dir, self.mutex)
                thread.progress.connect(self.on_thread_progress)
                thread.finished.connect(self.on_file_finished)
                thread.error.connect(self.on_thread_error)

                self.threads.append(thread)
                thread.start()

            # 等待所有线程完成
            while self.completed_files < total_files and self.is_running:
                self.msleep(100)

            if self.is_running:
                self.progress.emit("批量解密完成！")
                self.finished.emit(0)
            else:
                self.progress.emit("批量解密已取消！")
                self.finished.emit(1)

        except Exception as e:
            error_msg = f"批量解密出错: {str(e)}"
            logging.error(error_msg)
            self.error.emit(error_msg)



