"""
主窗口界面
"""
import os
import shutil
import threading

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QFont, QIcon, QPixmap, QPalette, QColor
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QFileDialog, QTextEdit,
                             QMessageBox, QProgressBar, QGroupBox, QListWidget,
                             QListWidgetItem, QApplication, QTableWidget, QTableWidgetItem,
                             QHeaderView, QMenu)

from src.core.asset_extractor import AssetExtractor
from src.ui.file_selector import FileSelectorDialog
from src.ui.batch_pack_dialog import BatchPackDialog
from src.ui.donate_dialog import DonateDialog
import logging
from queue import Queue
from src.worker.asset_worker import AssetWorker
from src.worker.export_ab_worker import ExportABWorker
from src.ui.batch_decrypt_dialog import BatchDecryptDialog


class MainWindow(QMainWindow):

    """主窗口类"""
    def __init__(self):
        super().__init__()
        # self.open_windows = []
        self.logger = logging.getLogger(__name__)
        self.asset_path = None
        self.asset_path_to_file_selector = {}
        self.setWindowTitle("明日方舟资源包处理工具")
        self.setMinimumSize(1100, 820)
        self.resize(1100, 820)  # 设置初始窗口大小
        self.setAcceptDrops(True)  # 启用拖拽功能
        self.lock = threading.Lock()
        # 添加已打开的资源窗口列表
        self.path_to_windows = {}  # 存储已打开的FileSelectorDialog实例
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
        # 启用排序
        self.window_list.setSortingEnabled(True)
        # 连接排序信号
        self.window_list.horizontalHeader().sectionClicked.connect(self.on_header_clicked)
        # 启用右键菜单
        self.window_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.window_list.customContextMenuRequested.connect(self.show_context_menu)
        # 设置表格样式
        self.window_list.setStyleSheet("""
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
        # 记录所有临时目录
        self.temp_paths = []

        # 设置应用图标
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resource", "icon.webp")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.setup_ui()
        self.update_theme()  # 初始化主题

        # 创建定时器来检查系统主题变化
        self.theme_check_timer = QTimer(self)
        self.theme_check_timer.timeout.connect(self.check_theme_change)
        self.theme_check_timer.start(1000)  # 每秒检查一次
        self.last_theme_is_dark = self.is_dark_mode()

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
        self.single_import_btn = QPushButton("单个导入")
        self.single_import_btn.clicked.connect(self.single_import)
        import_buttons_layout.addWidget(self.single_import_btn)
        
        # 批量导入按钮
        self.batch_import_btn = QPushButton("批量导入")
        self.batch_import_btn.clicked.connect(self.batch_import)
        import_buttons_layout.addWidget(self.batch_import_btn)
        
    
        
        # 批量解密按钮
        

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
        self.update_mod_btn = QPushButton("批量打包")
        self.update_mod_btn.clicked.connect(self.show_batch_update_dialog)

        self.batch_decrypt_btn = QPushButton("批量解密")
        self.batch_decrypt_btn.clicked.connect(self.show_batch_decrypt_dialog)
        batch_buttons_layout.addWidget(self.batch_decrypt_btn)
        batch_buttons_layout.addWidget(self.update_mod_btn)
        
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
        github_layout.setSpacing(5)
        github_icon = QLabel()
        github_pixmap = QPixmap(os.path.join(os.path.dirname(os.path.dirname(__file__)), "resource", "about", "github.png"))
        github_icon.setPixmap(github_pixmap.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        github_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        github_layout.addWidget(github_icon)
        
        self.github_link = QLabel('<a href="https://github.com/laoxinH/Arknight_AB_Auto_Package">项目地址</a>')
        self.github_link.setOpenExternalLinks(True)
        self.github_link.setAlignment(Qt.AlignmentFlag.AlignCenter)
        github_layout.addWidget(self.github_link)
        
        icons_layout.addLayout(github_layout)
        
        # 支付宝图标和文字
        alipay_layout = QVBoxLayout()
        alipay_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        alipay_layout.setSpacing(5)
        alipay_icon = QLabel()
        alipay_pixmap = QPixmap(os.path.join(os.path.dirname(os.path.dirname(__file__)), "resource", "about", "alipay.png"))
        alipay_icon.setPixmap(alipay_pixmap.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        alipay_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        alipay_layout.addWidget(alipay_icon)
        
        self.alipay_link = QLabel('<a href="#">支持作者</a>')
        self.alipay_link.setOpenExternalLinks(False)
        self.alipay_link.linkActivated.connect(self.show_donate_dialog)
        self.alipay_link.setAlignment(Qt.AlignmentFlag.AlignCenter)
        alipay_layout.addWidget(self.alipay_link)
        
        icons_layout.addLayout(alipay_layout)
        
        # 主题切换按钮
        theme_layout = QVBoxLayout()
        theme_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        theme_layout.setSpacing(5)
        
        # 主题切换按钮容器
        theme_container = QWidget()
        theme_container.setFixedSize(32, 32)
        theme_container_layout = QVBoxLayout(theme_container)
        theme_container_layout.setContentsMargins(0, 0, 0, 0)
        theme_container_layout.setSpacing(0)
        theme_container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.theme_btn = QPushButton()
        self.theme_btn.setFixedSize(32, 32)
        self.theme_btn.setIconSize(QSize(32, 32))
        self.theme_btn.setFlat(True)
        self.theme_btn.clicked.connect(self.toggle_theme)
        # 初始化主题图标
        self.update_theme_icon()
        theme_container_layout.addWidget(self.theme_btn)
        
        theme_layout.addWidget(theme_container)
        
        # 主题切换说明文字
        self.theme_label = QLabel("主题")
        self.theme_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.theme_label.setFixedWidth(32)  # 设置固定宽度与图标一致
        self.theme_label.setStyleSheet("color: #666666;")
        theme_layout.addWidget(self.theme_label)

        icons_layout.addLayout(theme_layout)
        
        about_layout.addLayout(icons_layout)
        
        # 添加说明文字
        self.about_text = QLabel("感谢您的使用！\n如果觉得这个工具对您有帮助，\n欢迎在GitHub上点个Star或支持作者。")
        self.about_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        about_layout.addWidget(self.about_text)
        
        about_group.setLayout(about_layout)
        left_layout.addWidget(about_group)

        # 创建日志区域
        log_group = QGroupBox("处理日志")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(150)
        self.log_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: white;
                color: #333333;
                padding: 5px;
            }
            QScrollBar:vertical {
                background-color: #f8f9fa;
                width: 12px;
                margin: 0px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background-color: #dee2e6;
                min-height: 30px;
                border-radius: 6px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #ced4da;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            QScrollBar:horizontal {
                background-color: #f8f9fa;
                height: 12px;
                margin: 0px;
                border: none;
            }
            QScrollBar::handle:horizontal {
                background-color: #dee2e6;
                min-width: 30px;
                border-radius: 6px;
                margin: 2px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #ced4da;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
        """)
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

        # 添加搜索框
        search_layout = QHBoxLayout()
        self.search_input = QTextEdit()
        self.search_input.setMaximumHeight(30)
        self.search_input.setPlaceholderText("搜索文件名...")
        self.search_input.textChanged.connect(self.filter_files)
        search_layout.addWidget(self.search_input)
        windows_layout.addLayout(search_layout)

        # 添加统计信息
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(10)
        
        # 创建统计标签
        self.stats_label = QLabel("已加载资源包: 0 个")
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
        self.close_selected_btn = QPushButton("移除选中")
        self.close_selected_btn.clicked.connect(self.close_selected_windows)
        window_buttons_layout.addWidget(self.close_selected_btn)
        
        # 移除全部按钮
        self.close_all_btn = QPushButton("移除全部")
        self.close_all_btn.clicked.connect(self.close_all_windows)
        window_buttons_layout.addWidget(self.close_all_btn)
        
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


                except Exception as e:
                    self.update_log(f"处理文件 {os.path.basename(ab_file)} 时出错: {str(e)}")
                    continue

            # 等待所有线程完成并更新处理进度
            for worker in self.workers:
                worker.start()
                id = self.workers.index(worker)
                # self.progress_bar.setValue(int(id * (100 / len(self.workers))))

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
        self.progress_bar.setValue(90)

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
            # 储存window与文件的映射关系


            self.path_to_windows[asset_path] = dialog
            self.windows_to_files[dialog] = files

            # 临时禁用排序
            self.window_list.setSortingEnabled(False)

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

            # 重新启用排序
            # self.window_list.setSortingEnabled(True)

            # 更新统计信息
            self.update_stats()

            # 连接窗口关闭信号
            # dialog.finished.connect(lambda: self.on_window_closed(dialog))
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
                asset_path = self.window_list.item(row, 0).data(Qt.ItemDataRole.UserRole)
                # 获取对应的窗口
                if asset_path in self.path_to_windows:
                    window = self.path_to_windows[asset_path]
                    # 关闭窗口
                    window.close()
                    # 从字典中移除
                    self.window_list.removeRow(row)
                    del self.path_to_windows[asset_path]
                    self.windows_to_files.pop(window)  # 删除映射关系
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
            for path in self.path_to_windows:
                window = self.path_to_windows[path]
                window.close()
            
            # 清空列表
            self.window_list.setRowCount(0)
            self.windows_to_files.clear()
            
            # 更新统计信息
            self.update_stats()

    def on_window_double_clicked(self, item):

        """处理窗口列表项双击事件"""
        # 获取双击的行
        row = item.row()
        asset_path = self.window_list.item(row, 0).data(Qt.ItemDataRole.UserRole)
        # 获取对应的窗口
        window = self.path_to_windows[asset_path]
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
            # window.finished.connect(lambda: self.on_window_closed(window))
            self.windows_to_files[window] = files
            # 替换原来的窗口
            self.path_to_windows[asset_path] = window
            # 显示窗口
            window.check_theme_change()
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

    def show_batch_decrypt_dialog(self):
        """显示批量解密窗口"""
        dialog = BatchDecryptDialog(self)
        dialog.show()

    def closeEvent(self, event):
        """关闭事件"""
        count = 0
        try:
            self.logger.info("清理临时文件...")
            for file_path in self.temp_paths:
                if os.path.exists(file_path):
                    try:
                        # 使用shutil.rmtree强制删除目录
                        shutil.rmtree(file_path, ignore_errors=False)
                        count += 1
                    except PermissionError as e:
                        self.logger.warning(f"删除临时文件失败: {file_path}, 权限错误: {str(e)}")
                    except Exception as e:
                        self.logger.warning(f"删除临时文件失败: {file_path}, {str(e)}")
        except Exception as e:
            self.logger.error(f"清理临时文件时出错: {str(e)}")
        finally:
            if count > 0:
                self.logger.info(f"成功删除临时文件夹: {count} 个")
            else:
                self.logger.info("没有临时文件需要删除")
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
                if os.path.isdir(file_path):
                    # 如果是目录，则检查目录下是否有AB文件
                    for root, _, files in os.walk(file_path):
                        for file in files:
                            if file.lower().endswith('.ab'):
                                has_valid_files = True
                                break
                        if has_valid_files:
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
                elif os.path.isdir(file_path):
                    # 如果是目录，则检查目录下是否有AB文件
                    for root, _, files in os.walk(file_path):
                        for file in files:
                            if file.lower().endswith('.ab'):
                                valid_files.append(os.path.join(root, file))
                            else:
                                skipped_files.append(os.path.basename(file))

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
                    QMessageBox.information(self, "提示", f"已跳过{len(skipped_files)}个非AB文件")

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
        self.update_theme_icon()

    def update_theme_icon(self):
        """更新主题切换按钮图标"""
        is_dark = self.is_dark_mode()
        if is_dark:
            # 在深色模式下显示太阳图标（用于切换到浅色模式）
            self.theme_btn.setIcon(QIcon(os.path.join(os.path.dirname(os.path.dirname(__file__)), "resource", "about", "sun.png")))
            self.theme_btn.setToolTip("切换到浅色主题")
        else:
            # 在浅色模式下显示月亮图标（用于切换到深色模式）
            self.theme_btn.setIcon(QIcon(os.path.join(os.path.dirname(os.path.dirname(__file__)), "resource", "about", "moon.png")))
            self.theme_btn.setToolTip("切换到深色主题")

    def is_dark_mode(self):
        """检测系统是否处于深色模式"""
        palette = self.palette()
        return palette.window().color().lightness() < 128

    def apply_dark_theme(self):
        """应用深色主题"""
        try:
            # 更新日志框样式
            if hasattr(self, 'log_text'):
                self.log_text.setStyleSheet("""
                    QTextEdit {
                        border: 1px solid #3c3c3c;
                        border-radius: 4px;
                        background-color: #2d2d2d;
                        color: #ffffff;
                        padding: 5px;
                    }
                    QScrollBar:vertical {
                        background-color: #1e1e1e;
                        width: 12px;
                        margin: 0px;
                        border: none;
                    }
                    QScrollBar::handle:vertical {
                        background-color: #3c3c3c;
                        min-height: 30px;
                        border-radius: 6px;
                        margin: 2px;
                    }
                    QScrollBar::handle:vertical:hover {
                        background-color: #4c4c4c;
                    }
                    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                        height: 0px;
                    }
                    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                        background: none;
                    }
                    QScrollBar:horizontal {
                        background-color: #1e1e1e;
                        height: 12px;
                        margin: 0px;
                        border: none;
                    }
                    QScrollBar::handle:horizontal {
                        background-color: #3c3c3c;
                        min-width: 30px;
                        border-radius: 6px;
                        margin: 2px;
                    }
                    QScrollBar::handle:horizontal:hover {
                        background-color: #4c4c4c;
                    }
                    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                        width: 0px;
                    }
                    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                        background: none;
                    }
                """)

            # 更新关于区域样式
            self.github_link.setStyleSheet("a { color: #4a86e8; }")
            self.alipay_link.setStyleSheet("a { color: #4a86e8; }")
            self.about_text.setStyleSheet("""
                color: #cccccc;
                font-size: 12px;
                padding: 10px;
                background-color: #2d2d2d;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
            """)
            self.stats_label.setStyleSheet("""
                color: #cccccc;
                font-size: 12px;
                padding: 5px;
                background-color: #2d2d2d;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
            """)

            # 更新主界面按钮样式
            self.single_import_btn.setStyleSheet("""
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
            self.batch_import_btn.setStyleSheet("""
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
            self.update_mod_btn.setStyleSheet("""
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
            self.batch_decrypt_btn.setStyleSheet("""
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
            # 更新按钮样式
            self.close_selected_btn.setStyleSheet("""
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
            self.close_all_btn.setStyleSheet("""
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

            # 更新表格样式
            self.window_list.setStyleSheet("""
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

            # 设置全局深色主题样式
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #1e1e1e;
                }
                QWidget {
                    background-color: #1e1e1e;
                    color: #ffffff;
                }
                QGroupBox {
                    font-weight: bold;
                    border: 1px solid #3c3c3c;
                    border-radius: 5px;
                    margin-top: 10px;
                    padding-top: 15px;
                    color: #ffffff;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px;
                    color: #ffffff;
                }
                QTextEdit {
                    background-color: #2d2d2d;
                    color: #ffffff;
                    border: 1px solid #3c3c3c;
                    border-radius: 4px;
                }
                QProgressBar {
                    background-color: #2d2d2d;
                    color: #ffffff;
                    border: 1px solid #3c3c3c;
                    border-radius: 4px;
                }
                QProgressBar::chunk {
                    background-color: #4a86e8;
                }
            """)

        except Exception as e:
            self.logger.error(f"应用深色主题时出错: {str(e)}")
            QMessageBox.critical(self, "错误", f"应用深色主题时出错: {str(e)}")

    def apply_light_theme(self):
        """应用浅色主题"""
        try:
            # 更新日志框样式
            if hasattr(self, 'log_text'):
                self.log_text.setStyleSheet("""
                    QTextEdit {
                        border: 1px solid #cccccc;
                        border-radius: 4px;
                        background-color: white;
                        color: #333333;
                        padding: 5px;
                    }
                    QScrollBar:vertical {
                        background-color: #f8f9fa;
                        width: 12px;
                        margin: 0px;
                        border: none;
                    }
                    QScrollBar::handle:vertical {
                        background-color: #dee2e6;
                        min-height: 30px;
                        border-radius: 6px;
                        margin: 2px;
                    }
                    QScrollBar::handle:vertical:hover {
                        background-color: #ced4da;
                    }
                    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                        height: 0px;
                    }
                    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                        background: none;
                    }
                    QScrollBar:horizontal {
                        background-color: #f8f9fa;
                        height: 12px;
                        margin: 0px;
                        border: none;
                    }
                    QScrollBar::handle:horizontal {
                        background-color: #dee2e6;
                        min-width: 30px;
                        border-radius: 6px;
                        margin: 2px;
                    }
                    QScrollBar::handle:horizontal:hover {
                        background-color: #ced4da;
                    }
                    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                        width: 0px;
                    }
                    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                        background: none;
                    }
                """)

            # 更新关于区域样式
            self.github_link.setStyleSheet("a { color: #0066cc; }")
            self.alipay_link.setStyleSheet("a { color: #0066cc; }")
            self.about_text.setStyleSheet("""
                color: #666666;
                font-size: 12px;
                padding: 10px;
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 4px;
            """)
            self.stats_label.setStyleSheet("""
                color: #666666;
                font-size: 12px;
                padding: 5px;
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 4px;
            """)

            # 更新主界面按钮样式
            self.single_import_btn.setStyleSheet("""
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
            self.batch_decrypt_btn.setStyleSheet("""
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
            self.batch_import_btn.setStyleSheet("""
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
            self.update_mod_btn.setStyleSheet("""
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

            # 更新按钮样式
            self.close_selected_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f8f9fa;
                    color: #333333;
                    border: 1px solid #dee2e6;
                    padding: 8px 15px;
                    border-radius: 4px;
                    min-width: 100px;
                }
                QPushButton:hover {
                    background-color: #e9ecef;
                    border: 1px solid #ced4da;
                }
                QPushButton:pressed {
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                }
                QPushButton:disabled {
                    background-color: #f8f9fa;
                    color: #6c757d;
                    border: 1px solid #dee2e6;
                }
            """)
            self.close_all_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f8f9fa;
                    color: #333333;
                    border: 1px solid #dee2e6;
                    padding: 8px 15px;
                    border-radius: 4px;
                    min-width: 100px;
                }
                QPushButton:hover {
                    background-color: #e9ecef;
                    border: 1px solid #ced4da;
                }
                QPushButton:pressed {
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                }
                QPushButton:disabled {
                    background-color: #f8f9fa;
                    color: #6c757d;
                    border: 1px solid #dee2e6;
                }
            """)

            # 更新表格样式
            self.window_list.setStyleSheet("""
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

            # 设置全局浅色主题样式
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #ffffff;
                }
                QWidget {
                    background-color: #ffffff;
                    color: #333333;
                }
                QGroupBox {
                    font-weight: bold;
                    border: 1px solid #dee2e6;
                    border-radius: 5px;
                    margin-top: 10px;
                    padding-top: 15px;
                    color: #333333;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px;
                    color: #333333;
                }
                QTextEdit {
                    background-color: #ffffff;
                    color: #333333;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                }
                QProgressBar {
                    background-color: #f8f9fa;
                    color: #333333;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                }
                QProgressBar::chunk {
                    background-color: #4a86e8;
                }
            """)

        except Exception as e:
            self.logger.error(f"应用浅色主题时出错: {str(e)}")
            QMessageBox.critical(self, "错误", f"应用浅色主题时出错: {str(e)}")

    def toggle_theme(self):
        """切换主题"""
        is_dark = self.is_dark_mode()
        if is_dark:
            is_dark_mode = False
            self.apply_light_theme()
        else:
            self.apply_dark_theme()
        self.last_theme_is_dark = not is_dark
        self.update_theme_icon()

    def filter_files(self):
        """根据搜索框内容过滤文件列表"""
        search_text = self.search_input.toPlainText().lower()
        for row in range(self.window_list.rowCount()):
            name_item = self.window_list.item(row, 0)
            path_item = self.window_list.item(row, 1)
            if name_item and path_item:
                name = name_item.text().lower()
                path = path_item.text().lower()
                if search_text in name or search_text in path:
                    self.window_list.setRowHidden(row, False)
                else:
                    self.window_list.setRowHidden(row, True)

    def on_header_clicked(self, logical_index):
        """处理表头点击事件，实现排序功能"""
        # 获取当前排序状态
        current_order = self.window_list.horizontalHeader().sortIndicatorOrder()

        # 如果是大小列，使用自定义排序
        if logical_index == 2:
            # 保存所有行的数据
            rows_data = []
            for row in range(self.window_list.rowCount()):
                size_item = self.window_list.item(row, 2)
                if size_item:
                    size_str = size_item.text()
                    bytes_value = self.convert_size_to_bytes(size_str)
                    # 保存整行数据
                    row_data = []
                    for col in range(self.window_list.columnCount()):
                        item = self.window_list.item(row, col)
                        if item:
                            row_data.append({
                                'text': item.text(),
                                'user_data': item.data(Qt.ItemDataRole.UserRole),
                                'tooltip': item.toolTip()
                            })
                        else:
                            row_data.append(None)
                    rows_data.append((bytes_value, row_data))
            
            # 按字节数排序
            rows_data.sort(key=lambda x: x[0], reverse=(current_order == Qt.SortOrder.DescendingOrder))
            
            # 重新填充表格
            self.window_list.setSortingEnabled(False)  # 临时禁用排序
            self.window_list.setRowCount(0)
            
            # 添加排序后的数据
            for _, row_data in rows_data:
                row = self.window_list.rowCount()
                self.window_list.insertRow(row)
                for col, item_data in enumerate(row_data):
                    if item_data:
                        new_item = QTableWidgetItem(item_data['text'])
                        if item_data['user_data'] is not None:
                            new_item.setData(Qt.ItemDataRole.UserRole, item_data['user_data'])
                        if item_data['tooltip']:
                            new_item.setToolTip(item_data['tooltip'])
                        if col == 2:  # 大小列
                            new_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                        self.window_list.setItem(row, col, new_item)
            # self.window_list.setSortingEnabled(True)  # 重新启用排序

            
        else:
            # 对于其他列，使用内置排序
            self.window_list.sortItems(logical_index, current_order)
            self.window_list.setSortingEnabled(True)

    def convert_size_to_bytes(self, size_str):
        """将大小字符串转换为字节数"""
        size_str = size_str.strip().upper()
        if size_str == "未知":
            return 0
        try:
            # 分离数值和单位
            parts = size_str.split()
            if len(parts) != 2:
                print(f"大小格式错误: {size_str}")
                return 0
                
            value = float(parts[0])
            unit = parts[1]
            
            # 根据单位转换为字节
            if unit == "B":
                return value
            elif unit == "KB":
                return value * 1024
            elif unit == "MB":
                return value * 1024 * 1024
            elif unit == "GB":
                return value * 1024 * 1024 * 1024
            elif unit == "TB":
                return value * 1024 * 1024 * 1024 * 1024
            print(f"未知单位: {unit}")
            return 0
        except Exception as e:
            print(f"转换大小出错: {e}, 输入: {size_str}")
            return 0

    def show_context_menu(self, position):
        """显示右键菜单"""
        # 获取选中的行
        selected_rows = set(item.row() for item in self.window_list.selectedItems())
        if not selected_rows:
            return
            
        # 创建右键菜单
        menu = QMenu(self)
        
        # 添加"打开文件所在位置"选项
        open_location_action = menu.addAction("打开文件所在位置")
        open_location_action.triggered.connect(lambda: self.open_file_location(selected_rows))
        
        # 显示菜单
        menu.exec(self.window_list.viewport().mapToGlobal(position))

    def open_file_location(self, selected_rows):
        """打开文件所在位置"""
        try:
            for row in selected_rows:
                # 获取文件路径
                path_item = self.window_list.item(row, 1)
                if path_item:
                    file_path = path_item.text()
                    if os.path.exists(file_path):
                        # 获取文件所在目录
                        folder_path = os.path.dirname(file_path)
                        # 使用系统默认方式打开文件夹
                        os.startfile(folder_path)
        except Exception as e:
            self.logger.error(f"打开文件所在位置失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"打开文件所在位置失败: {str(e)}")