"""
主窗口界面
"""
import os
import shutil

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QPixmap
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QFileDialog, QTextEdit,
                             QMessageBox, QProgressBar, QGroupBox, QListWidget,
                             QListWidgetItem, QApplication, QTableWidget, QTableWidgetItem,
                             QHeaderView)

from src.core.asset_extractor import AssetExtractor
from src.ui.file_selector import FileSelectorDialog
from src.ui.batch_pack_dialog import BatchPackDialog
from src.ui.donate_dialog import DonateDialog
import logging

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
            extractor = AssetExtractor(self.output_dir)

            if self.is_scanning:
                # 扫描模式

                files, temp_path = extractor.scan_asset(self.source_file)
                self.scan_complete.emit(files, temp_path, self.source_file)
                self.progress.emit("扫描完成！")
                self.finished.emit()
            else:
                # 提取或替换模式
                success = extractor.extract_asset(
                    self.source_file,
                    self.selected_files,
                    self.mode,
                    self.replace_files
                )

                if success:
                    self.progress.emit("处理完成！")
                    self.finished.emit()
                else:
                    self.error.emit("处理失败，请查看日志")
        except Exception as e:
            self.error.emit(str(e))


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
            extractor = AssetExtractor(self.output_dir)

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


class MainWindow(QMainWindow):
    """主窗口类"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.asset_path = None
        self.asset_path_to_file_selector = {}
        self.setWindowTitle("明日方舟资源包处理工具")
        self.setMinimumSize(1100, 820)
        self.resize(1100, 820)  # 设置初始窗口大小
        self.setAcceptDrops(True)  # 启用拖拽功能

        # 添加已打开的资源窗口列表
        self.open_windows = []  # 存储已打开的FileSelectorDialog实例
        self.windows_to_files = {}  # 存储窗口与文件的映射关系
        self.window_list = QTableWidget()  # 用于显示已打开的窗口列表
        self.window_list.setColumnCount(3)  # 设置3列
        self.window_list.setHorizontalHeaderLabels(["名称", "路径", "大小"])  # 设置列标题
        # 设置表格属性
        self.window_list.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.window_list.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)  # 修改为多选模式
        self.window_list.verticalHeader().setVisible(False)
        self.window_list.setShowGrid(False)
        # 设置列宽
        header = self.window_list.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # 名称列自适应
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)  # 路径列可调整
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)  # 大小列固定宽度
        self.window_list.setColumnWidth(2, 80)  # 设置大小列宽度
        # 设置表格样式
        self.window_list.setStyleSheet("""
            QTableWidget {
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: white;
            }
            QTableWidget::item {
                padding: 5px;
                border-bottom: 1px solid #eeeeee;
            }
            QTableWidget::item:selected {
                background-color: #e6f3ff;
                color: #0066cc;
            }
            QTableWidget::item:hover {
                background-color: #f5f5f5;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 5px;
                border: 1px solid #dee2e6;
                font-weight: bold;
            }
        """)
        # 记录所有临时目录
        self.temp_paths = []

        # 设置应用图标
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resource", "icon.webp")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.setup_ui()

        # 设置样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
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
            QLabel {
                color: #333333;
            }
            QTextEdit {
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: white;
            }
            QProgressBar {
                border: 1px solid #cccccc;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4a86e8;
            }
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
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
        """)

    def setup_ui(self):
        """设置用户界面"""
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)  # 改为水平布局
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # 创建左侧面板（资源包处理）
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(15)

        # 创建标题
        title_label = QLabel("明日方舟资源处理器(MOD实验室)")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        left_layout.addWidget(title_label)

        # 创建解包区域
        extract_group = QGroupBox("资源包处理")
        extract_layout = QVBoxLayout()
        extract_layout.setSpacing(10)

        # 创建导入按钮布局
        import_buttons_layout = QHBoxLayout()
        
        # 单个导入按钮
        single_import_btn = QPushButton("单个导入")
        single_import_btn.setStyleSheet("""
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
        """)
        single_import_btn.clicked.connect(self.single_import)
        import_buttons_layout.addWidget(single_import_btn)
        
        # 批量导入按钮
        batch_import_btn = QPushButton("批量导入")
        batch_import_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        batch_import_btn.clicked.connect(self.batch_import)
        import_buttons_layout.addWidget(batch_import_btn)
        
        extract_layout.addLayout(import_buttons_layout)

        # 状态标签
        self.status_label = QLabel("请选择资源包文件")
        self.status_label.setStyleSheet("color: #666666;")
        extract_layout.addWidget(self.status_label)

        extract_group.setLayout(extract_layout)
        left_layout.addWidget(extract_group)

        # 创建批量打包区域
        package_group = QGroupBox("批量处理")
        package_layout = QVBoxLayout()
        package_layout.setSpacing(10)
        
        # 添加批量处理按钮
        batch_buttons_layout = QHBoxLayout()
        
        # 批量更新MOD按钮
        update_mod_btn = QPushButton("批量打包")
        update_mod_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        update_mod_btn.clicked.connect(self.show_batch_update_dialog)
        batch_buttons_layout.addWidget(update_mod_btn)
        
        package_layout.addLayout(batch_buttons_layout)
        
        # 添加状态标签
        self.batch_status_label = QLabel("请选择要处理的资源包")
        self.batch_status_label.setStyleSheet("color: #666666;")
        self.batch_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        package_layout.addWidget(self.batch_status_label)
        
        package_group.setLayout(package_layout)
        left_layout.addWidget(package_group)

        # 创建关于区域
        about_group = QGroupBox("关于")
        about_layout = QVBoxLayout()
        about_layout.setSpacing(15)
        
        # 创建图标布局
        icons_layout = QHBoxLayout()
        icons_layout.setSpacing(20)
        icons_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # GitHub图标和文字
        github_layout = QVBoxLayout()
        github_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        github_icon = QLabel()
        github_pixmap = QPixmap(os.path.join(os.path.dirname(os.path.dirname(__file__)), "resource", "about", "github.png"))
        github_icon.setPixmap(github_pixmap.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        github_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        github_layout.addWidget(github_icon)
        
        github_text = QLabel("GitHub")
        github_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        github_text.setStyleSheet("color: #333333;")
        github_layout.addWidget(github_text)
        
        github_link = QLabel('<a href="https://github.com/yourusername/yourrepo">项目地址</a>')
        github_link.setOpenExternalLinks(True)
        github_link.setAlignment(Qt.AlignmentFlag.AlignCenter)
        github_link.setStyleSheet("color: #0066cc;")
        github_layout.addWidget(github_link)
        
        icons_layout.addLayout(github_layout)
        
        # 支付宝图标和文字
        alipay_layout = QVBoxLayout()
        alipay_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        alipay_icon = QLabel()
        alipay_pixmap = QPixmap(os.path.join(os.path.dirname(os.path.dirname(__file__)), "resource", "about", "alipay.png"))
        alipay_icon.setPixmap(alipay_pixmap.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        alipay_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        alipay_layout.addWidget(alipay_icon)
        
        alipay_text = QLabel("捐赠")
        alipay_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        alipay_text.setStyleSheet("color: #333333;")
        alipay_layout.addWidget(alipay_text)
        
        alipay_link = QLabel('<a href="#" style="color: #0066cc;">支持作者</a>')
        alipay_link.setOpenExternalLinks(False)  # 改为False，使用自定义点击事件
        alipay_link.linkActivated.connect(self.show_donate_dialog)  # 连接点击事件
        alipay_link.setAlignment(Qt.AlignmentFlag.AlignCenter)
        alipay_layout.addWidget(alipay_link)
        
        icons_layout.addLayout(alipay_layout)
        
        about_layout.addLayout(icons_layout)
        
        # 添加说明文字
        about_text = QLabel("感谢您的使用！\n如果觉得这个工具对您有帮助，\n欢迎在GitHub上点个Star或支持作者。")
        about_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        about_text.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 12px;
                padding: 10px;
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 4px;
            }
        """)
        about_layout.addWidget(about_text)
        
        about_group.setLayout(about_layout)
        left_layout.addWidget(about_group)

        # 创建日志区域
        log_group = QGroupBox("处理日志")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(150)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        left_layout.addWidget(log_group)

        # 创建进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        left_layout.addWidget(self.progress_bar)

        # 添加左侧面板到主布局
        main_layout.addWidget(left_panel, stretch=1)

        # 创建右侧面板（已打开的资源窗口）
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(15)

        # 创建已打开窗口管理区域
        windows_group = QGroupBox("资源列表")
        windows_layout = QVBoxLayout()

        # 添加统计信息
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(10)
        
        # 创建统计标签
        self.stats_label = QLabel("已加载资源包: 0 个")
        self.stats_label.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 12px;
                padding: 5px;
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 4px;
            }
        """)
        stats_layout.addWidget(self.stats_label)
        
        # 添加弹性空间
        stats_layout.addStretch()
        
        windows_layout.addLayout(stats_layout)

        # 连接双击事件
        self.window_list.itemDoubleClicked.connect(self.on_window_double_clicked)
        windows_layout.addWidget(self.window_list)

        # 添加窗口管理按钮
        window_buttons_layout = QHBoxLayout()
        
        # 移除选中按钮
        close_selected_btn = QPushButton("移除选中")
        close_selected_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #bd2130;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        close_selected_btn.clicked.connect(self.close_selected_windows)
        window_buttons_layout.addWidget(close_selected_btn)
        
        # 移除全部按钮
        close_all_btn = QPushButton("移除全部")
        close_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #bd2130;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        close_all_btn.clicked.connect(self.close_all_windows)
        window_buttons_layout.addWidget(close_all_btn)
        
        windows_layout.addLayout(window_buttons_layout)

        windows_group.setLayout(windows_layout)
        right_layout.addWidget(windows_group)

        # 添加右侧面板到主布局
        main_layout.addWidget(right_panel, stretch=1)

        # 初始化变量
        self.scanned_files = []
        self.selected_files = []
        self.replace_files = {}
        self.package_files = []  # 存储要打包的文件列表

    def single_import(self):
        """单个导入资源包"""
        try:
            file_name, _ = QFileDialog.getOpenFileName(
                self,
                "选择资源包文件",
                "",
                "资源包文件 (*.ab);;所有文件 (*.*)"
            )
            if self.check_file_exists(file_name):
                return
            if file_name:
                self.asset_path = file_name
                self.status_label.setText("正在扫描资源包...")
                self.status_label.setStyleSheet("color: #4a86e8;")
                self.start_scan()
        except Exception as e:
            self.update_log(f"导入文件时出错: {str(e)}")
            QMessageBox.critical(self, "错误", f"导入文件时出错: {str(e)}")

    def batch_import(self):
        """批量导入资源包"""
        try:
            dir_path = QFileDialog.getExistingDirectory(
                self,
                "选择资源包文件夹",
                "",
                QFileDialog.Option.ShowDirsOnly
            )

            if not dir_path:
                return

            # 查找所有.ab文件
            ab_files = []
            for root, _, files in os.walk(dir_path):
                for file in files:
                    if file.endswith('.ab'):
                        ab_files.append(os.path.join(root, file))

            if not ab_files:
                QMessageBox.warning(self, "警告", "未找到任何资源包文件！")
                return

            # 更新状态
            self.status_label.setText(f"找到 {len(ab_files)} 个资源包文件")
            self.status_label.setStyleSheet("color: #4a86e8;")
            self.update_log(f"开始批量处理 {len(ab_files)} 个资源包文件")


            # 创建线程池存储所有工作线程
            self.workers = []

            # 批量处理文件
            for ab_file in ab_files:
                # 检查文件是否已存在
                if self.check_file_exists(ab_file):
                    continue
                try:
                    self.asset_path = ab_file
                    self.update_log(f"正在处理文件: {os.path.basename(ab_file)}")

                    # 创建工作线程
                    worker = AssetWorker(ab_file)
                    worker.progress.connect(self.update_log)
                    worker.finished.connect(self.scan_finished)
                    worker.error.connect(self.handle_error)
                    worker.scan_complete.connect(self.on_scan_complete)

                    # 将工作线程添加到线程池
                    self.workers.append(worker)
                    worker.start()

                except Exception as e:
                    self.update_log(f"处理文件 {os.path.basename(ab_file)} 时出错: {str(e)}")
                    continue

            # 等待所有线程完成并更新处理进度
            for worker in self.workers:
                id = self.workers.index(worker)
                self.progress_bar.setValue(int(id * (100 / len(self.workers))))


            self.update_log("批量处理完成")
            self.status_label.setText("批量处理完成")
            self.status_label.setStyleSheet("color: #28a745;")

        except Exception as e:
            self.update_log(f"批量导入时出错: {str(e)}")
            QMessageBox.critical(self, "错误", f"批量导入时出错: {str(e)}")

    def start_scan(self):
        """开始扫描资源包"""
        if self.asset_path is None:
            QMessageBox.warning(self, "警告", "请先选择要扫描的资源包文件！")
            return

        self.worker = AssetWorker(self.asset_path)
        self.worker.progress.connect(self.update_log)
        self.worker.finished.connect(self.scan_finished)
        self.worker.error.connect(self.handle_error)
        self.worker.scan_complete.connect(self.on_scan_complete)
        self.worker.start()

        # 更新进度条
        self.progress_bar.setValue(30)

    def on_scan_complete(self, files, temp_path, asset_path):
        """扫描完成回调"""
        self.scanned_files = files
        self.update_log(f"扫描到 {len(files)} 个文件")
        self.status_label.setText(f"扫描完成，找到 {len(files)} 个文件")
        self.status_label.setStyleSheet("color: #28a745;")
        self.temp_paths.append(temp_path)  # 记录临时目录

        # 显示文件选择对话框
        if files:
            dialog = FileSelectorDialog(asset_path, files, temp_path, self)
            dialog.files_selected.connect(self.on_files_selected)
            dialog.file_replaced.connect(self.on_file_replaced)
            dialog.export_ab.connect(self.on_export_ab)

            # 添加到已打开窗口列表
            self.open_windows.append(dialog)
            # 储存window与文件的映射关系
            self.windows_to_files[dialog] = files
            
            # 创建表格项
            row = self.window_list.rowCount()
            self.window_list.insertRow(row)
            
            # 设置名称列
            name_item = QTableWidgetItem(os.path.basename(asset_path))
            name_item.setData(Qt.ItemDataRole.UserRole, asset_path)  # 存储完整路径
            name_item.setToolTip(os.path.basename(asset_path))  # 设置工具提示
            self.window_list.setItem(row, 0, name_item)
            
            # 设置路径列
            path_item = QTableWidgetItem(asset_path)
            path_item.setToolTip(asset_path)  # 设置工具提示
            self.window_list.setItem(row, 1, path_item)
            
            # 设置大小列
            try:
                size = os.path.getsize(asset_path)
                size_str = self.format_size(size)
                size_item = QTableWidgetItem(size_str)
                size_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                size_item.setToolTip(f"{size:,} 字节")  # 设置工具提示显示原始字节数
                self.window_list.setItem(row, 2, size_item)
            except:
                size_item = QTableWidgetItem("未知")
                size_item.setToolTip("无法获取文件大小")  # 设置工具提示
                self.window_list.setItem(row, 2, size_item)

            # 更新统计信息
            self.update_stats()

            # 连接窗口关闭信号
            dialog.finished.connect(lambda: self.on_window_closed(dialog))
        else:
            QMessageBox.warning(self, "警告", "未找到可提取的文件！")
            self.status_label.setText("未找到可提取的文件")
            self.status_label.setStyleSheet("color: #dc3545;")

    def format_size(self, size):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def on_files_selected(self, selected_files, output_dir):
        """文件选择回调"""
        self.selected_files = selected_files
        self.update_log(f"已选择 {len(selected_files)} 个文件，输出目录: {output_dir}")

        # 开始提取
        self.start_extract(output_dir)

    def on_file_replaced(self, file_info, replace_file):
        """文件替换回调"""
        self.replace_files[file_info] = replace_file
        self.update_log(f"文件 {file_info[0]} 已标记为替换，替换文件: {replace_file}")

    def on_export_ab(self, output_dir,asset_path, replace_files):
        """导出AB资源包回调"""
        self.update_log(f"开始导出AB资源包，输出目录: {output_dir}")

        # 开始导出
        self.start_export_ab(output_dir,asset_path, replace_files)

    def start_extract(self, output_dir):
        """开始解包"""
        if self.asset_path is None:
            QMessageBox.warning(self, "警告", "请先选择要解包的资源包文件！")
            return

        if not self.selected_files:
            QMessageBox.warning(self, "警告", "请先扫描并选择要提取的文件！")
            return

        self.status_label.setText("正在提取文件...")
        self.status_label.setStyleSheet("color: #4a86e8;")

        self.worker = AssetWorker(
            self.asset_path,
            output_dir,
            self.selected_files,
            replace_files=self.replace_files
        )
        self.worker.progress.connect(self.update_log)
        self.worker.finished.connect(self.extract_finished)
        self.worker.error.connect(self.handle_error)
        self.worker.start()

        # 更新进度条
        self.progress_bar.setValue(50)

    def start_export_ab(self, output_dir,asset_path, replace_files):
        """开始导出AB资源包"""
        if self.asset_path is None:
            QMessageBox.warning(self, "警告", "请先选择要导出的资源包文件！")
            return

        if not replace_files:
            QMessageBox.warning(self, "警告", "没有要导出的替换文件！")
            return

        self.status_label.setText("正在导出AB资源包...")
        self.status_label.setStyleSheet("color: #4a86e8;")

        self.export_worker = ExportABWorker(
            asset_path,
            output_dir,
            replace_files
        )
        self.export_worker.progress.connect(self.update_log)
        self.export_worker.finished.connect(self.export_finished)
        self.export_worker.error.connect(self.handle_error)
        self.export_worker.start()

        # 更新进度条
        self.progress_bar.setValue(50)

    def update_log(self, message):
        """更新日志"""
        self.log_text.append(message)
        # 滚动到底部
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )

    def scan_finished(self):
        """扫描完成"""
        self.progress_bar.setValue(100)
        # 重置进度条
        self.progress_bar.setValue(0)

    def extract_finished(self):
        """解包完成"""
        self.progress_bar.setValue(100)
        self.status_label.setText("提取完成")
        self.status_label.setStyleSheet("color: #28a745;")
        # 重置进度条
        self.progress_bar.setValue(0)
        # 清空替换文件列表
        self.replace_files = {}

    def export_finished(self):
        """导出完成"""
        self.progress_bar.setValue(100)
        self.status_label.setText("导出完成")
        self.status_label.setStyleSheet("color: #28a745;")
        # QMessageBox.information(self, "完成", "AB资源包导出完成！")
        # 重置进度条
        self.progress_bar.setValue(0)
        # 清空替换文件列表
        self.replace_files = {}

    def handle_error(self, error_message):
        """处理错误"""
        self.progress_bar.setValue(0)
        self.status_label.setText("处理出错")
        self.status_label.setStyleSheet("color: #dc3545;")
        self.log_text.append(f"处理过程中出现错误：{error_message}")
        QMessageBox.critical(self, "错误", f"处理过程中出现错误：{error_message}")

    def on_window_closed(self, dialog):
        """处理窗口关闭事件"""
        if dialog in self.open_windows:
            index = self.open_windows.index(dialog)
            self.open_windows.remove(dialog)
            self.windows_to_files.pop(dialog)  # 删除映射关系
            self.window_list.removeRow(index)
            # 更新统计信息
            self.update_stats()

    def close_selected_windows(self):
        """移除选中的资源包"""
        # 获取选中的行
        selected_rows = set(item.row() for item in self.window_list.selectedItems())
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请先选择要移除的资源包！")
            return
            
        # 按行号从大到小排序，避免删除时行号变化导致的问题
        selected_rows = sorted(selected_rows, reverse=True)
        
        # 确认对话框
        reply = QMessageBox.question(
            self,
            "确认移除",
            f"确定要移除选中的 {len(selected_rows)} 个资源包吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            for row in selected_rows:
                if 0 <= row < len(self.open_windows):
                    window = self.open_windows[row]
                    window.close()
                    # 从列表中移除
                    self.window_list.removeRow(row)
                    self.windows_to_files.pop(window)  # 删除映射关系
                    self.open_windows.pop(row)
            
            # 更新统计信息
            self.update_stats()

    def close_all_windows(self):
        """移除所有资源包"""
        if self.window_list.rowCount() == 0:
            QMessageBox.warning(self, "警告", "没有可移除的资源包！")
            return
            
        # 确认对话框
        reply = QMessageBox.question(
            self,
            "确认移除",
            "确定要移除所有资源包吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 关闭所有窗口
            for window in self.open_windows:
                window.close()
            
            # 清空列表
            self.window_list.setRowCount(0)
            self.windows_to_files.clear()
            self.open_windows.clear()
            
            # 更新统计信息
            self.update_stats()

    def on_window_double_clicked(self, item):
        """处理窗口列表项双击事件"""
        # 获取双击的行
        row = item.row()
        if 0 <= row < len(self.open_windows):
            # 获取对应的窗口
            window = self.open_windows[row]
            # 如果窗口已经关闭，重新创建并显示
            if not window.isVisible():
                # 获取资源包路径
                asset_path = self.window_list.item(row, 0).data(Qt.ItemDataRole.UserRole)
                # 创建新的窗口
                files = self.windows_to_files[window]
                window = FileSelectorDialog(asset_path, self.windows_to_files[window], self.temp_paths[row], self)
                window.files_selected.connect(self.on_files_selected)
                window.file_replaced.connect(self.on_file_replaced)
                window.export_ab.connect(self.on_export_ab)
                window.finished.connect(lambda: self.on_window_closed(window))
                self.windows_to_files[window] = files
                # 替换原来的窗口
                self.open_windows[row] = window
                # 显示窗口
                window.show()
            else:
                # 如果窗口已经打开，则将其置顶
                window.raise_()
                window.activateWindow()

    def show_batch_update_dialog(self):
        """显示批量更新窗口"""
        dialog = BatchPackDialog(self)
        dialog.show()

    def show_donate_dialog(self):
        """显示捐赠窗口"""
        dialog = DonateDialog(self)
        dialog.exec()

    def closeEvent(self, event):
        """关闭事件"""
        try:
            self.logger.info("清理临时文件...")
            for file_path in self.temp_paths:
                if os.path.exists(file_path):
                    try:
                        # 使用shutil.rmtree强制删除目录
                        shutil.rmtree(file_path, ignore_errors=False)
                    except PermissionError as e:
                        self.logger.warning(f"删除临时文件失败: {file_path}, 权限错误: {str(e)}")
                    except Exception as e:
                        self.logger.warning(f"删除临时文件失败: {file_path}, {str(e)}")
        except Exception as e:
            self.logger.error(f"清理临时文件时出错: {str(e)}")
        finally:
            event.accept()

    def dragEnterEvent(self, event):
        """处理拖拽进入事件"""
        if event.mimeData().hasUrls():
            # 检查是否包含有效的AB文件
            has_valid_files = False
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if os.path.isfile(file_path) and file_path.lower().endswith('.ab'):
                    has_valid_files = True
                    break
            if has_valid_files:
                event.acceptProposedAction()

    def dragMoveEvent(self, event):
        """处理拖拽移动事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        """处理放置事件"""
        if event.mimeData().hasUrls():
            valid_files = []
            skipped_files = []
            
            # 收集有效的AB文件
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if os.path.isfile(file_path):
                    if file_path.lower().endswith('.ab'):
                        valid_files.append(file_path)
                    else:
                        skipped_files.append(os.path.basename(file_path))
                else:
                    skipped_files.append(os.path.basename(file_path))

            if valid_files:
                self.workers = []
                # 导入有效的AB文件
                for file_path in valid_files:
                    try:
                        # 检查文件是否已存在
                        if self.check_file_exists(file_path):
                            continue
                        self.asset_path = file_path
                        self.update_log(f"正在处理文件: {os.path.basename(file_path)}")

                        # 创建工作线程
                        worker = AssetWorker(file_path)
                        worker.progress.connect(self.update_log)
                        worker.finished.connect(self.scan_finished)
                        worker.error.connect(self.handle_error)
                        worker.scan_complete.connect(self.on_scan_complete)

                        # 将工作线程添加到线程池
                        self.workers.append(worker)
                        worker.start()


                        # 更新状态
                        self.update_log(f"已导入: {os.path.basename(file_path)}")
                        self.logger.info(f"导入AB文件: {file_path}")

                    except Exception as e:
                        self.logger.error(f"导入文件失败 {file_path}: {str(e)}")
                        QMessageBox.critical(self, "错误", f"导入文件失败 {os.path.basename(file_path)}: {str(e)}")
                        continue

                # 显示跳过的文件信息
                if skipped_files:
                    skipped_msg = "以下文件已跳过（非AB文件或文件夹）：\n" + "\n".join(skipped_files)
                    QMessageBox.information(self, "提示", skipped_msg)

                event.acceptProposedAction()
            else:
                if skipped_files:
                    QMessageBox.warning(self, "警告", "没有有效的AB文件可导入！")
                event.ignore()

    def check_file_exists(self, file_path):
        """检查文件是否已存在于列表中"""
        for row in range(self.window_list.rowCount()):
            item = self.window_list.item(row, 0)
            if item.data(Qt.ItemDataRole.UserRole) == file_path:
                return True
        return False

    def update_stats(self):
        """更新统计信息"""
        count = self.window_list.rowCount()
        self.stats_label.setText(f"已加载资源包: {count} 个")
