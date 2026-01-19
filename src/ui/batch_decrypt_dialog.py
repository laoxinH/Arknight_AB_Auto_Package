"""
批量解密对话框
"""
import os
import logging
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QMutex
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QFileDialog, QTableWidget, QTableWidgetItem,
                             QProgressBar, QMessageBox, QHeaderView)

from src.core.asset_extractor import AssetExtractor
from src.worker.BundleValidateWorker import BundleValidateWorker


class DecryptThread(QThread):
    """单个解密线程"""
    progress = pyqtSignal(str,str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str,str)

    def __init__(self, ab_file: str, output_dir: str, mutex: QMutex):
        super().__init__()
        self.ab_file = ab_file
        self.output_dir = output_dir
        self.mutex = mutex
        self.extractor = AssetExtractor()

    def run(self):
        """执行解密"""
        try:
            # 先发送进度信号
            self.progress.emit(self.ab_file,"正在解密")
            
            # 创建输出子目录
            rel_path = os.path.relpath(self.ab_file, os.path.dirname(self.ab_file))
            output_subdir = os.path.join(self.output_dir, os.path.dirname(rel_path))
            os.makedirs(output_subdir, exist_ok=True)

            # 解密文件
            self.mutex.lock()  # 加锁
            try:
                result = self.extractor.decrypt_ab(self.ab_file, output_subdir)
                if result:
                    self.progress.emit(self.ab_file,"完成")
                else:
                    self.progress.emit(self.ab_file, "未加密")
            finally:
                self.mutex.unlock()  # 解锁
            
            self.finished.emit(self.ab_file)
        except Exception as e:
            error_msg = f"解密文件 {os.path.basename(self.ab_file)} 失败: {str(e)}"
            logging.error(error_msg)
            self.error.emit(self.ab_file,error_msg)
            self.finished.emit(self.ab_file)  # 确保在出错时也发送完成信号

class BatchDecryptWorker(QThread):
    """批量解密工作线程"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(int)
    error = pyqtSignal(str)
    file_progress = pyqtSignal(int, str)  # 文件索引, 状态

    def __init__(self, ab_files: list[str], target_dir: str, max_threads: int = 10):
        super().__init__()
        self.ab_files = ab_files
        self.target_dir = target_dir
        self.max_threads = max_threads
        self.mutex = QMutex()
        self.threads = []
        self.completed_files = 0
        self.is_running = True
        self.file_status = {}  # 用于跟踪文件状态

    def run(self):
        """执行批量解密"""
        try:
            self.progress.emit("开始批量解密...")

            # 创建输出目录
            os.makedirs(self.target_dir, exist_ok=True)

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

    def on_thread_progress(self, path: str, message: str):
        """处理线程进度信号"""
        if self.is_running:
            # 根据路径获取文件索引
            file_index = self.ab_files.index(path)
            self.file_status[file_index] = message
            self.file_progress.emit(file_index, message)

    def on_thread_error(self, path: str, error_message: str):
        """处理线程错误信号"""
        if self.is_running:
            # 根据路径获取文件索引
            file_index = self.ab_files.index(path)
            self.file_status[file_index] = f"错误: {error_message}"
            self.file_progress.emit(file_index, f"失败,请查看日志")

    def on_file_finished(self,path):
        """文件解密完成处理"""
        if self.is_running:
            # 根据路径获取文件索引
            file_index = self.ab_files.index(path)
            # 更新文件状态
            self.file_status[file_index] = "完成"
            self.completed_files += 1
            # 更新进度条
            self.progress.emit(f"已完成 {self.completed_files}/{len(self.ab_files)}")

    def stop(self):
        """停止解密"""
        self.is_running = False

        for thread in self.threads:
            if thread.isRunning():
                thread.terminate()
                thread.wait()
        # self.finished.emit(1)


class BatchDecryptDialog(QDialog):
    """批量解密对话框类"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.all_files = []
        self.setWindowTitle("批量解密")
        self.setMinimumSize(800, 600)
        self.resize(800, 600)
        self.parent = parent
        self.input_dir = None
        self.ab_files = []
        self.worker = None
        self.file_status = {}  # 添加file_status属性

        self.setup_ui()
        self.update_theme()

        # 设置为非模态对话框
        self.setModal(False)
        
        # 设置窗口标志，允许最小化和关闭
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        
        # 初始化主题
        self.last_theme_is_dark = self.is_dark_mode()
        self.update_theme()
        
        # 创建定时器来检查系统主题变化
        self.theme_check_timer = QTimer(self)
        self.theme_check_timer.timeout.connect(self.check_theme_change)
        self.theme_check_timer.start(10)  # 每秒检查一次

    def setup_ui(self):
        """设置用户界面"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # 导入区域
        import_layout = QHBoxLayout()

        # 导入按钮
        self.import_btn = QPushButton("导入资源包")
        self.import_btn.clicked.connect(self.import_files)
        import_layout.addWidget(self.import_btn)

        # 路径显示
        self.path_label = QLabel("未选择文件夹")
        self.path_label.setStyleSheet("color: #666666;")
        import_layout.addWidget(self.path_label, stretch=1)

        main_layout.addLayout(import_layout)

        # 文件列表
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(3)  # 添加状态列
        self.file_table.setHorizontalHeaderLabels(["文件名", "路径", "状态"])
        self.file_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.file_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.file_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.file_table.setColumnWidth(2, 100)
        self.file_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.file_table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.file_table.verticalHeader().setVisible(False)
        self.file_table.setShowGrid(False)
        main_layout.addWidget(self.file_table)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)  # 设置文字居中对齐
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #cccccc;
                border-radius: 4px;
                text-align: center;
                height: 25px;
                font-size: 12px;
            }
            QProgressBar::chunk {
                background-color: #4a86e8;
                border-radius: 3px;
            }
        """)
        main_layout.addWidget(self.progress_bar)

        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # 取消按钮
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        # 导出按钮
        self.export_btn = QPushButton("导出")
        self.export_btn.clicked.connect(self.export_files)
        self.export_btn.setEnabled(False)
        button_layout.addWidget(self.export_btn)

        main_layout.addLayout(button_layout)

    def import_files(self):
        """导入资源包文件"""
        try:
            dir_path = QFileDialog.getExistingDirectory(
                self,
                "选择资源包文件夹",
                "",
                QFileDialog.Option.ShowDirsOnly
            )

            if not dir_path:
                return

            self.input_dir = dir_path
            self.path_label.setText(dir_path)
            self.ab_files = []
            self.all_files = []

            # 查找所有.ab文件
            for root, _, files in os.walk(dir_path):
                for file in files:
                    self.all_files.append(os.path.join(root, file))

            # 创建并启动验证线程
            self.validate_worker = BundleValidateWorker(self.all_files)
            # self.validate_worker.progress.connect(self.progress_bar.)

            self.validate_worker.validated.connect(self.on_validate_complete)
            # self.validate_worker.error.connect(self.handle_error)
            self.validate_worker.start()



            # 更新文件列表
            # self.update_file_list()
            # self.export_btn.setEnabled(len(self.ab_files) > 0)

        except Exception as e:
            QMessageBox.critical(self, "错误", f"导入文件时出错: {str(e)}")

    def on_validate_complete(self, valid_files):
        """验证完成处理"""
        try:
            self.ab_files = valid_files
            self.update_file_list()
            self.export_btn.setEnabled(len(self.ab_files) > 0)
        except Exception as e:
            logging.error(f"处理验证完成时出错: {str(e)}")
            QMessageBox.critical(self, "错误", f"处理验证完成时出错: {str(e)}")

    def update_file_list(self):
        """更新文件列表"""
        self.file_table.setRowCount(0)
        self.file_status = {}  # 重置文件状态
        for i, file_path in enumerate(self.ab_files):
            row = self.file_table.rowCount()
            self.file_table.insertRow(row)

            # 文件名
            name_item = QTableWidgetItem(os.path.basename(file_path))
            self.file_table.setItem(row, 0, name_item)

            # 文件路径
            path_item = QTableWidgetItem(file_path)
            self.file_table.setItem(row, 1, path_item)

            # 状态
            self.file_status[i] = "等待解密"  # 初始化状态
            status_item = QTableWidgetItem("等待解密")
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.file_table.setItem(row, 2, status_item)

    def export_files(self):
        """导出文件"""
        try:
            output_dir = QFileDialog.getExistingDirectory(
                self,
                "选择导出位置",
                "",
                QFileDialog.Option.ShowDirsOnly
            )

            if not output_dir:
                return

            # 禁用按钮
            self.import_btn.setEnabled(False)
            self.export_btn.setEnabled(False)
            self.cancel_btn.setEnabled(False)

            # 创建并启动工作线程
            self.worker = BatchDecryptWorker(self.ab_files, output_dir)
            self.worker.progress.connect(self.update_progress)
            self.worker.finished.connect(self.on_decrypt_finished)
            self.worker.error.connect(self.on_decrypt_error)
            self.worker.file_progress.connect(self.update_file_status)
            
            # 设置进度条
            self.progress_bar.setMaximum(len(self.ab_files))
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("准备开始解密...")

            # 启动线程
            self.worker.start()

        except Exception as e:
            error_msg = f"导出文件时出错: {str(e)}"
            logging.error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)
            self.reset_ui()

    def update_progress(self, message):
        """更新进度信息"""
        try:
            self.progress_bar.setFormat(message)  # 直接设置消息文本，不需要添加百分比
        except Exception as e:
            logging.error(f"更新进度时出错: {str(e)}")

    def update_file_status(self, file_index: int, status: str):
        """更新文件状态"""
        try:
            if 0 <= file_index < self.file_table.rowCount():
                # 更新状态字典
                self.file_status[file_index] = status
                
                # 更新表格显示
                status_item = QTableWidgetItem(status)
                status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.file_table.setItem(file_index, 2, status_item)
                
                # 更新进度条
                if status in ["完成", "未加密"]:
                    current_value = self.progress_bar.value() + 1
                    self.progress_bar.setValue(current_value)
                    total = len(self.ab_files)
                    self.progress_bar.setFormat(f"正在解密... {current_value}/{total}")
        except Exception as e:
            logging.error(f"更新文件状态时出错: {str(e)}")

    def on_decrypt_finished(self,flag):
        """解密完成"""
        try:
            if flag == 0:
                self.progress_bar.setFormat("批量解密完成！")
                QMessageBox.information(self, "完成", "批量解密完成！")
            if flag == 1:
                self.progress_bar.setFormat("批量解密已取消！")
                QMessageBox.information(self, "取消", "批量解密已取消！")

            self.reset_ui()
        except Exception as e:
            logging.error(f"处理解密完成时出错: {str(e)}")
            self.reset_ui()

    def on_decrypt_error(self, error_message):
        """解密出错"""
        try:
            QMessageBox.critical(self, "错误", f"批量解密失败：{error_message}")
            self.reset_ui()
        except Exception as e:
            logging.error(f"处理解密错误时出错: {str(e)}")
            self.reset_ui()

    def reset_ui(self):
        """重置UI状态"""
        try:
            self.import_btn.setEnabled(True)
            self.export_btn.setEnabled(True)
            self.cancel_btn.setEnabled(True)
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("就绪")
        except Exception as e:
            logging.error(f"重置UI时出错: {str(e)}")

    def closeEvent(self, event):
        """窗口关闭事件处理"""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self,
                '确认关闭',
                '批量解密正在进行中，确定要关闭窗口吗？',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.worker.stop()
                self.worker.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def update_theme(self):
        """更新主题样式"""
        is_dark = self.is_dark_mode()
        if is_dark:
            self.apply_dark_theme()
        else:
            self.apply_light_theme()

    def apply_dark_theme(self):
        """应用深色主题"""
        try:
            # 设置对话框背景
            self.setStyleSheet("""
                QDialog {
                    background-color: #1e1e1e;
                }
                QLabel {
                    color: #ffffff;
                }
                QPushButton {
                    background-color: #2d2d2d;
                    color: #ffffff;
                    border: 1px solid #3c3c3c;
                    padding: 8px 15px;
                    border-radius: 4px;
                    min-width: 100px;
                }
                QPushButton:hover {
                    background-color: #3d3d3d;
                    border: 1px solid #4c4c4c;
                }
                QPushButton:pressed {
                    background-color: #2d2d2d;
                    border: 1px solid #3c3c3c;
                }
                QPushButton:disabled {
                    background-color: #1a1a1a;
                    color: #666666;
                    border: 1px solid #2c2c2c;
                }
            """)

            # 设置表格样式
            self.file_table.setStyleSheet("""
                QTableWidget {
                    background-color: #1e1e1e;
                    color: #ffffff;
                    border: 1px solid #3c3c3c;
                    border-radius: 4px;
                    gridline-color: #3c3c3c;
                }
                QTableWidget::item {
                    padding: 5px;
                    border-bottom: 1px solid #3c3c3c;
                    color: #ffffff;
                }
                QTableWidget::item:selected {
                    background-color: #3d3d3d;
                    color: #ffffff;
                }
                QTableWidget::item:hover {
                    background-color: #3d3d3d;
                    color: #ffffff;
                }
                QHeaderView::section {
                    background-color: #2d2d2d;
                    color: #ffffff;
                    padding: 5px;
                    border: 1px solid #3c3c3c;
                    font-weight: bold;
                }
                QScrollBar:vertical {
                    background-color: #1e1e1e;
                    width: 15px;
                    margin: 0px;
                }
                QScrollBar::handle:vertical {
                    background-color: #3c3c3c;
                    min-height: 20px;
                    border-radius: 3px;
                }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    height: 0px;
                }
                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                    background: none;
                }
                QScrollBar:horizontal {
                    background-color: #1e1e1e;
                    height: 15px;
                    margin: 0px;
                }
                QScrollBar::handle:horizontal {
                    background-color: #3c3c3c;
                    min-width: 20px;
                    border-radius: 3px;
                }
                QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                    width: 0px;
                }
                QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                    background: none;
                }
            """)

        except Exception as e:
            QMessageBox.critical(self, "错误", f"应用深色主题时出错: {str(e)}")

    def apply_light_theme(self):
        """应用浅色主题"""
        try:
            # 设置对话框背景
            self.setStyleSheet("""
                QDialog {
                    background-color: #ffffff;
                }
                QLabel {
                    color: #333333;
                }
                QPushButton {
                    background-color: #4a86e8;
                    color: white;
                    border: none;
                    padding: 8px 15px;
                    border-radius: 4px;
                    min-width: 100px;
                }
                QPushButton:hover {
                    background-color: #3a76d8;
                }
                QPushButton:pressed {
                    background-color: #2a66c8;
                }
                QPushButton:disabled {
                    background-color: #cccccc;
                    color: #666666;
                }
            """)

            # 设置表格样式
            self.file_table.setStyleSheet("""
                QTableWidget {
                    background-color: #ffffff;
                    color: #333333;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    gridline-color: #dee2e6;
                }
                QTableWidget::item {
                    padding: 5px;
                    border-bottom: 1px solid #dee2e6;
                    color: #333333;
                }
                QTableWidget::item:selected {
                    background-color: #e6f3ff;
                    color: #0066cc;
                }
                QTableWidget::item:hover {
                    background-color: #f5f5f5;
                    color: #333333;
                }
                QHeaderView::section {
                    background-color: #f8f9fa;
                    color: #333333;
                    padding: 5px;
                    border: 1px solid #dee2e6;
                    font-weight: bold;
                }
                QScrollBar:vertical {
                    background-color: #f8f9fa;
                    width: 15px;
                    margin: 0px;
                }
                QScrollBar::handle:vertical {
                    background-color: #dee2e6;
                    min-height: 20px;
                    border-radius: 3px;
                }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    height: 0px;
                }
                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                    background: none;
                }
                QScrollBar:horizontal {
                    background-color: #f8f9fa;
                    height: 15px;
                    margin: 0px;
                }
                QScrollBar::handle:horizontal {
                    background-color: #dee2e6;
                    min-width: 20px;
                    border-radius: 3px;
                }
                QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                    width: 0px;
                }
                QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                    background: none;
                }
            """)

        except Exception as e:
            QMessageBox.critical(self, "错误", f"应用浅色主题时出错: {str(e)}")

    def is_dark_mode(self):
        """检测系统是否处于深色模式"""
        palette = self.parent.palette()
        return palette.window().color().lightness() < 128

    def check_theme_change(self):
        """检查系统主题是否发生变化"""
        current_is_dark = self.is_dark_mode()
        if current_is_dark != self.last_theme_is_dark:
            self.last_theme_is_dark = current_is_dark
            self.update_theme()