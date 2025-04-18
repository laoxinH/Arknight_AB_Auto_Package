"""
批量更新MOD窗口
"""
import os
import logging
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QFileDialog, QListWidget, QListWidgetItem,
                             QProgressBar, QMessageBox)

from src.core.asset_batch_replacer import AssetBatchReplacer

class BatchPackWorker(QThread):
    """批量打包工作线程"""
    progress = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, source_dir: str, replace_dir: str, target_dir: str):
        super().__init__()
        self.source_dir = source_dir
        self.replace_dir = replace_dir
        self.target_dir = target_dir
        self.replacer = AssetBatchReplacer()

    def run(self):
        """执行批量打包"""
        try:
            self.progress.emit("开始批量打包...")
            success = self.replacer.replace_spine_files(
                self.source_dir,
                self.replace_dir,
                self.target_dir
            )
            if success:
                self.progress.emit("批量打包完成！")
                self.finished.emit()
            else:
                self.error.emit("批量打包失败")
        except Exception as e:
            self.error.emit(f"批量打包出错: {str(e)}")

class BatchPackDialog(QDialog):
    """批量打包MOD窗口"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("批量打包MOD")
        self.setMinimumSize(800, 600)
        
        # 设置为非模态对话框
        self.setModal(False)
        
        # 存储选择的目录
        self.source_mod_dir = None
        self.replace_file_dir = None
        
        self.setup_ui()
        # 储存的源文件列表
        self.source_file_lists = []
        # 储存的替换文件列表
        self.replace_file_lists = []
        
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
        
    def is_dark_mode(self):
        """检测系统是否处于深色模式"""
        palette = self.parent().palette()
        return palette.window().color().lightness() < 128
        
    def check_theme_change(self):
        """检查系统主题是否发生变化"""
        current_is_dark = self.is_dark_mode()
        if current_is_dark != self.last_theme_is_dark:
            self.last_theme_is_dark = current_is_dark
            self.update_theme()
            
    def update_theme(self):
        """更新主题样式"""
        is_dark = self.is_dark_mode()
        if is_dark:
            self.apply_dark_theme()
        else:
            self.apply_light_theme()
            
    def apply_dark_theme(self):
        """应用深色主题"""
        # 设置全局样式
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
            }
            QProgressBar {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #28a745;
                border-radius: 4px;
            }
        """)
        
        # 更新按钮样式
        self.select_source_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3c3c3c;
                padding: 8px 15px;
                border-radius: 4px;
                min-width: 150px;
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
        
        self.select_replace_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3c3c3c;
                padding: 8px 15px;
                border-radius: 4px;
                min-width: 150px;
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
        
        self.pack_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3c3c3c;
                padding: 8px 15px;
                border-radius: 4px;
                min-width: 150px;
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
        
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3c3c3c;
                padding: 8px 15px;
                border-radius: 4px;
                min-width: 150px;
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
        
        # 更新列表样式
        self.source_file_list.setStyleSheet("""
            QListWidget {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #3c3c3c;
            }
            QListWidget::item:selected {
                background-color: #3d3d3d;
                color: #ffffff;
            }
            QListWidget::item:hover {
                background-color: #3d3d3d;
                color: #ffffff;
            }
        """)
        
        self.replace_file_list.setStyleSheet("""
            QListWidget {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #3c3c3c;
            }
            QListWidget::item:selected {
                background-color: #3d3d3d;
                color: #ffffff;
            }
            QListWidget::item:hover {
                background-color: #3d3d3d;
                color: #ffffff;
            }
        """)
        
    def apply_light_theme(self):
        """应用浅色主题"""
        # 设置全局样式
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                color: #333333;
            }
            QLabel {
                color: #333333;
            }
            QProgressBar {
                background-color: #f8f9fa;
                color: #333333;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #28a745;
                border-radius: 4px;
            }
        """)
        
        # 更新按钮样式
        self.select_source_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:pressed {
                background-color: #545b62;
            }
        """)
        
        self.select_replace_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:pressed {
                background-color: #545b62;
            }
        """)
        
        self.pack_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #bd2130;
            }
        """)
        
        # 更新列表样式
        self.source_file_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: white;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #eeeeee;
            }
            QListWidget::item:selected {
                background-color: #e6f3ff;
                color: #0066cc;
            }
        """)
        
        self.replace_file_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: white;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #eeeeee;
            }
            QListWidget::item:selected {
                background-color: #e6f3ff;
                color: #0066cc;
            }
        """)
        
    def setup_ui(self):
        """设置用户界面"""
        main_layout = QHBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 左侧面板 - 源文件
        left_panel = QVBoxLayout()
        left_panel.setSpacing(10)
        
        # 标题
        old_title = QLabel("源文件")
        old_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        old_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        left_panel.addWidget(old_title)
        
        # 选择文件夹按钮
        self.select_source_btn = QPushButton("选择源文件目录")
        self.select_source_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:pressed {
                background-color: #545b62;
            }
        """)
        self.select_source_btn.clicked.connect(self.select_source_dir)
        left_panel.addWidget(self.select_source_btn)
        
        # 文件夹路径显示
        self.source_dir_label = QLabel("未选择文件夹")
        self.source_dir_label.setStyleSheet("color: #666666;")
        self.source_dir_label.setWordWrap(True)
        left_panel.addWidget(self.source_dir_label)
        
        # 文件列表
        self.source_file_list = QListWidget()
        self.source_file_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: white;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #eeeeee;
            }
            QListWidget::item:selected {
                background-color: #e6f3ff;
                color: #0066cc;
            }
        """)
        left_panel.addWidget(self.source_file_list)
        
        # 右侧面板 - 替换文件
        right_panel = QVBoxLayout()
        right_panel.setSpacing(10)
        
        # 标题
        new_title = QLabel("替换文件目录")
        new_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        new_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        right_panel.addWidget(new_title)
        
        # 选择文件夹按钮
        self.select_replace_btn = QPushButton("选择替换文件目录")
        self.select_replace_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:pressed {
                background-color: #545b62;
            }
        """)
        self.select_replace_btn.clicked.connect(self.select_repace_dir)
        right_panel.addWidget(self.select_replace_btn)
        
        # 文件夹路径显示
        self.replace_dir_label = QLabel("未选择文件夹")
        self.replace_dir_label.setStyleSheet("color: #666666;")
        self.replace_dir_label.setWordWrap(True)
        right_panel.addWidget(self.replace_dir_label)
        
        # 文件列表
        self.replace_file_list = QListWidget()
        self.replace_file_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: white;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #eeeeee;
            }
            QListWidget::item:selected {
                background-color: #e6f3ff;
                color: #0066cc;
            }
        """)
        right_panel.addWidget(self.replace_file_list)
        
        # 添加左右面板到主布局
        main_layout.addLayout(left_panel, stretch=1)
        main_layout.addLayout(right_panel, stretch=1)
        
        # 创建主布局
        layout = QVBoxLayout()
        layout.addLayout(main_layout)
        
        # 添加进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # 底部按钮区域
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(10)
        
        # 一键打包按钮
        self.pack_btn = QPushButton("一键打包")
        self.pack_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        self.pack_btn.clicked.connect(self.start_batch_pack)
        bottom_layout.addWidget(self.pack_btn)
        
        # 取消按钮
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #bd2130;
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        bottom_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(bottom_layout)
        self.setLayout(layout)
        
    def select_source_dir(self):
        """选择源文件目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "选择源文件目录",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        
        if dir_path:
            self.source_mod_dir = dir_path
            self.source_dir_label.setText(dir_path)
            self.update_source_file_list()
            
    def select_repace_dir(self):
        """选择替换文件目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "选择替换文件目录",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        
        if dir_path:
            self.replace_file_dir = dir_path
            self.replace_dir_label.setText(dir_path)
            self.update_relace_file_list()
            
    def update_source_file_list(self):
        """更新源文件列表"""
        self.source_file_list.clear()
        self.source_file_lists = []
        if self.source_mod_dir:
            # 添加提示信息
            tip_item = QListWidgetItem("提示：源文件必须以 .ab 结尾")
            tip_item.setForeground(Qt.GlobalColor.red)
            self.source_file_list.addItem(tip_item)
            
            for root, _, files in os.walk(self.source_mod_dir):
                for file in files:
                    if file.endswith('.ab'):
                        item = QListWidgetItem(file)
                        item.setToolTip(os.path.join(root, file))
                        self.source_file_lists.append(os.path.join(root, file))
                        self.source_file_list.addItem(item)
                        
    def update_relace_file_list(self):
        """更新替换文件列表"""
        self.replace_file_list.clear()
        self.replace_file_lists = []
        if self.replace_file_dir:
            # 添加提示信息
            tip_item = QListWidgetItem("提示：替换资源需要命名为 {名称}_{Path_ID} 形式")
            tip_item.setForeground(Qt.GlobalColor.red)
            self.replace_file_list.addItem(tip_item)
            
            for root, _, files in os.walk(self.replace_file_dir):
                for file in files:
                    item = QListWidgetItem(file)
                    item.setToolTip(os.path.join(root, file))
                    self.replace_file_lists.append(os.path.join(root, file))
                    self.replace_file_list.addItem(item)
                    
    def start_batch_pack(self):
        """开始批量打包"""
        if not self.source_mod_dir or not self.replace_file_dir:
            QMessageBox.warning(self, "警告", "请先选择源文件目录和替换文件目录！")
            return
            
        # 选择输出目录
        output_dir = QFileDialog.getExistingDirectory(
            self,
            "选择输出目录",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        
        if not output_dir:
            return
            
        # 创建并启动工作线程
        self.worker = BatchPackWorker(
            self.source_mod_dir,
            self.replace_file_dir,
            output_dir
        )
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_pack_finished)
        self.worker.error.connect(self.on_pack_error)
        
        # 禁用按钮
        self.pack_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.select_source_btn.setEnabled(False)
        self.select_replace_btn.setEnabled(False)
        
        # 更新进度条
        self.progress_bar.setValue(50)
        
        # 启动线程
        self.worker.start()
        
    def update_progress(self, message):
        """更新进度"""
        self.progress_bar.setFormat(f"{message} %p%")
        
    def on_pack_finished(self):
        """打包完成"""
        self.progress_bar.setValue(100)
        QMessageBox.information(self, "完成", "批量打包完成！")
        
        # 恢复按钮状态
        self.pack_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)
        self.select_source_btn.setEnabled(True)
        self.select_replace_btn.setEnabled(True)
        
        # 重置进度条
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("%p%")
        
    def on_pack_error(self, error_message):
        """打包出错"""
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("%p%")
        QMessageBox.critical(self, "错误", f"批量打包失败：{error_message}")
        
        # 恢复按钮状态
        self.pack_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)
        self.select_source_btn.setEnabled(True)
        self.select_replace_btn.setEnabled(True)

    def closeEvent(self, event):
        """窗口关闭事件处理"""
        if hasattr(self, 'worker') and self.worker.isRunning():
            reply = QMessageBox.question(
                self,
                '确认关闭',
                '批量打包正在进行中，确定要关闭窗口吗？',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.worker.terminate()
                self.worker.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()