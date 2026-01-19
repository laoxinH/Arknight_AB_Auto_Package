"""
主窗口界面
"""
import os
import shutil
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import List
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSize, QUrl
from PyQt6.QtGui import QFont, QIcon, QDesktopServices
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QFileDialog, QTextEdit,
                             QMessageBox, QProgressBar, QGroupBox,
                             QApplication, QTableWidget, QTableWidgetItem,
                             QHeaderView, QMenu)
from src.ui.file_selector import FileSelectorDialog
from src.ui.batch_pack_dialog import BatchPackDialog
from src.ui.donate_dialog import DonateDialog
from src.ui.settings_dialog import SettingsDialog
import logging
from queue import Queue,Empty

from src.worker.BundleValidateWorker import BundleValidateWorker
from src.worker.asset_worker import AssetWorker
from src.worker.export_ab_worker import ExportABWorker
from src.ui.batch_decrypt_dialog import BatchDecryptDialog
from src.utils.BundleValidator import BundleValidator
from src.ui.themes.main_window_theme_manager import ThemeManager
from src.config.config_manager import ConfigManager


class MainWindow(QMainWindow):
    progress_signal = pyqtSignal(int, str)
    """主窗口类"""
    def __init__(self):
        super().__init__()
        # self.open_windows = []
        self.logger = logging.getLogger(__name__)
        self.asset_path = None
        self.asset_path_to_file_selector = {}
        self.setWindowTitle("AssetBundle资源包处理工具")
        self.bundle_validator = BundleValidator()
        self.is_shutting_down = False  # 添加关闭标志
        self.workers = []  # 存储所有工作线程
        self.thread_pool = None  # 线程池引用
        self.progress_signal.connect(self.update_progress)

        # 初始化配置管理器
        self.config = ConfigManager()

        # 创建主题管理器
        self.theme_manager = ThemeManager(self)

        # 获取主屏幕
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        
        # 计算窗口大小（使用屏幕宽度的60%和高度的70%）
        default_width = int(screen_geometry.width() * 0.6)
        default_height = int(screen_geometry.height() * 0.7)
        
        # 设置最小窗口大小（屏幕宽度的40%和高度的50%）
        min_width = int(screen_geometry.width() * 0.4)
        min_height = int(screen_geometry.height() * 0.5)
        self.setMinimumSize(min_width, min_height)
        
        # 从配置恢复窗口大小和位置
        saved_width = self.config.get('window_width')
        saved_height = self.config.get('window_height')
        saved_x = self.config.get('window_x')
        saved_y = self.config.get('window_y')
        saved_maximized = self.config.get('window_maximized', False)
        
        # 设置窗口大小
        if saved_width and saved_height:
            self.resize(saved_width, saved_height)
        else:
            self.resize(default_width, default_height)
        
        # 设置窗口位置
        if saved_x is not None and saved_y is not None:
            # 确保窗口在屏幕范围内
            if 0 <= saved_x < screen_geometry.width() and 0 <= saved_y < screen_geometry.height():
                self.move(saved_x, saved_y)
            else:
                # 如果保存的位置无效，则居中显示
                x = (screen_geometry.width() - self.width()) // 2
                y = (screen_geometry.height() - self.height()) // 2
                self.move(x, y)
        else:
            # 没有保存位置，则居中显示
            x = (screen_geometry.width() - self.width()) // 2
            y = (screen_geometry.height() - self.height()) // 2
            self.move(x, y)
        
        # 恢复最大化状态
        if saved_maximized:
            self.showMaximized()
        
        # 计算基础字体大小（基于屏幕高度）
        self.base_font_size = max(8, int(screen_geometry.height() * 0.01))
        
        self.setAcceptDrops(True)  # 启用拖拽功能
        self.lock = threading.Lock()
        # 添加已打开的资源窗口列表
        self.path_to_windows = {}  # 存储已打开的FileSelectorDialog实例
        self.windows_to_files = {}  # 存储窗口与文件的映射关系
        self.path_to_files = {}  # 存储资源路径与文件列表的映射关系（持久化，即使窗口关闭也保留）
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
        self.window_list.setColumnWidth(2, int(self.width() * 0.08))  # 设置大小列宽度为窗口宽度的8%
        
        # 启用排序
        self.window_list.setSortingEnabled(True)
        # 连接排序信号
        self.window_list.horizontalHeader().sectionClicked.connect(self.on_header_clicked)
        # 启用右键菜单
        self.window_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.window_list.customContextMenuRequested.connect(self.show_context_menu)
        
        # 记录所有临时目录
        self.temp_paths = []

        # 设置应用图标
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resource", "icon.webp")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.setup_ui()
        self.theme_manager.update_theme()  # 初始化主题

        # 创建定时器来检查系统主题变化
        self.theme_check_timer = QTimer(self)
        self.theme_check_timer.timeout.connect(self.theme_manager.check_theme_change)
        self.theme_check_timer.start(1000)  # 每秒检查一次
        
        # 添加窗口大小变化事件处理
        self.resizeEvent = self.on_resize

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
        self.title_label = QLabel("AssetBundle资源包编辑器(MOD实验室)")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        left_layout.addWidget(self.title_label)

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
        batch_buttons_layout.addWidget(self.update_mod_btn)

        # 批量解密按钮
        self.batch_decrypt_btn = QPushButton("批量解密")
        self.batch_decrypt_btn.clicked.connect(self.show_batch_decrypt_dialog)
        batch_buttons_layout.addWidget(self.batch_decrypt_btn)
        package_layout.addLayout(batch_buttons_layout)
        
        package_group.setLayout(package_layout)
        left_layout.addWidget(package_group)

        # 创建关于区域
        about_group = QGroupBox("关于")
        about_layout = QVBoxLayout()
        about_layout.setSpacing(20)
        
        # 添加弹性空间在顶部
        about_layout.addStretch(1)
        
        # 创建图标布局
        icons_layout = QHBoxLayout()
        icons_layout.setSpacing(30)
        icons_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # GitHub按钮容器
        github_container = QWidget()
        github_layout = QVBoxLayout(github_container)
        github_layout.setContentsMargins(0, 0, 0, 0)
        github_layout.setSpacing(8)
        github_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.github_btn = QPushButton()
        self.github_btn.setFixedSize(56, 56)
        self.github_btn.setFlat(True)
        self.github_btn.setText("🔗")  # 链接符号
        self.github_btn.setStyleSheet("font-size: 36px; border-radius: 8px;")
        self.github_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.github_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/laoxinH/Arknight_AB_Auto_Package")))
        github_layout.addWidget(self.github_btn)
        
        # GitHub标签
        self.github_label = QLabel("项目地址")
        self.github_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.github_label.setStyleSheet("color: #666666; font-size: 12px;")
        github_layout.addWidget(self.github_label)
        
        # 支付宝按钮容器
        alipay_container = QWidget()
        alipay_layout = QVBoxLayout(alipay_container)
        alipay_layout.setContentsMargins(0, 0, 0, 0)
        alipay_layout.setSpacing(8)
        alipay_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.alipay_btn = QPushButton()
        self.alipay_btn.setFixedSize(56, 56)
        self.alipay_btn.setFlat(True)
        self.alipay_btn.setText("💰")  # 钱袋符号
        self.alipay_btn.setStyleSheet("font-size: 36px; border-radius: 8px;")
        self.alipay_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.alipay_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://www.modwu.com/?p=219")))
        alipay_layout.addWidget(self.alipay_btn)
        
        # 支付宝标签
        self.alipay_label = QLabel("支持作者")
        self.alipay_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.alipay_label.setStyleSheet("color: #666666; font-size: 12px;")
        alipay_layout.addWidget(self.alipay_label)
        
        # MOD社区按钮容器
        community_container = QWidget()
        community_layout = QVBoxLayout(community_container)
        community_layout.setContentsMargins(0, 0, 0, 0)
        community_layout.setSpacing(8)
        community_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.community_btn = QPushButton()
        self.community_btn.setFixedSize(56, 56)
        self.community_btn.setFlat(True)
        self.community_btn.setText("🏘️")  # 社区符号
        self.community_btn.setStyleSheet("font-size: 36px; border-radius: 8px;")
        self.community_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.community_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://www.modwu.com/")))
        community_layout.addWidget(self.community_btn)
        
        # MOD社区标签
        self.community_label = QLabel("MOD社区")
        self.community_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.community_label.setStyleSheet("color: #666666; font-size: 12px;")
        community_layout.addWidget(self.community_label)
        
        # 主题切换按钮容器
        theme_container = QWidget()
        theme_layout = QVBoxLayout(theme_container)
        theme_layout.setContentsMargins(0, 0, 0, 0)
        theme_layout.setSpacing(8)
        theme_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.theme_btn = QPushButton()
        self.theme_btn.setFixedSize(56, 56)
        self.theme_btn.setFlat(True)
        self.theme_btn.setStyleSheet("font-size: 36px; border-radius: 8px;")
        self.theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_btn.clicked.connect(self.toggle_theme)
        # 初始化主题图标（使用emoji）
        self.theme_manager.update_theme_icon()
        theme_layout.addWidget(self.theme_btn)
        
        # 主题标签
        self.theme_label = QLabel("主题")
        self.theme_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.theme_label.setStyleSheet("color: #666666; font-size: 12px;")
        theme_layout.addWidget(self.theme_label)
        
        # 设置按钮容器
        settings_container = QWidget()
        settings_layout = QVBoxLayout(settings_container)
        settings_layout.setContentsMargins(0, 0, 0, 0)
        settings_layout.setSpacing(8)
        settings_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.settings_btn = QPushButton()
        self.settings_btn.setFixedSize(56, 56)
        self.settings_btn.setFlat(True)
        self.settings_btn.setText("⚙️")  # 齿轮符号
        self.settings_btn.setStyleSheet("font-size: 36px; border-radius: 8px;")
        self.settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.settings_btn.clicked.connect(self.show_settings_dialog)
        settings_layout.addWidget(self.settings_btn)
        
        # 设置标签
        self.settings_label = QLabel("设置")
        self.settings_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.settings_label.setStyleSheet("color: #666666; font-size: 12px;")
        settings_layout.addWidget(self.settings_label)
        
        # 添加所有按钮到布局
        icons_layout.addWidget(github_container)
        icons_layout.addWidget(alipay_container)
        icons_layout.addWidget(community_container)
        icons_layout.addWidget(theme_container)
        icons_layout.addWidget(settings_container)
        
        about_layout.addLayout(icons_layout)
        
        # 添加说明文字
        self.about_text = QLabel("感谢您的使用！\n\n如果觉得这个工具对您有帮助，\n欢迎在GitHub上点个Star或支持作者。\n\n日志文件保存在程序目录的 logs 文件夹中。")
        self.about_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.about_text.setStyleSheet("color: #666666; font-size: 13px; line-height: 1.6;")
        about_layout.addWidget(self.about_text)
        
        # 添加弹性空间在底部
        about_layout.addStretch(1)
        
        about_group.setLayout(about_layout)
        left_layout.addWidget(about_group)

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
            # 获取上次使用的目录
            last_dir = self.config.get('last_input_dir', '')
            
            file_name, _ = QFileDialog.getOpenFileName(
                self,
                "选择资源包文件",
                last_dir,
                "所有文件 (*.*)"
            )
            if self.check_file_exists(file_name):
                return
            if file_name:
                # 保存当前目录
                self.config.set('last_input_dir', os.path.dirname(file_name))
                
                self.asset_path = file_name
                self.status_label.setText("正在扫描资源包...")
                self.status_label.setStyleSheet("color: #4a86e8;")
                self.start_scan()
        except Exception as e:
            self.update_log(f"导入文件时出错: {str(e)}")
            QMessageBox.critical(self, "错误", f"导入文件时出错: {str(e)}")

    def batch_import(self):
        """批量导入资源包"""

        """批量导入资源包"""
        try:
            # 获取上次使用的目录
            last_dir = self.config.get('last_input_dir', '')
            
            dir_path = QFileDialog.getExistingDirectory(
                self,
                "选择资源包文件夹",
                last_dir,
                QFileDialog.Option.ShowDirsOnly
            )

            if not dir_path:
                return
            
            # 保存当前目录
            self.config.set('last_input_dir', dir_path)

            # 收集所有文件
            all_files = []
            for root, _, files in os.walk(dir_path):
                for file in files:
                    all_files.append(os.path.join(root, file))

            if not all_files:
                QMessageBox.warning(self, "警告", "选择的文件夹为空！")
                return

            # 更新状态
            self.status_label.setText("正在验证文件...")
            self.status_label.setStyleSheet("color: #4a86e8;")
            self.update_log("开始验证文件...")

            # 创建并启动验证线程
            self.validate_worker = BundleValidateWorker(all_files)
            # self.validate_worker.progress.connect(self.progress_bar.)

            self.validate_worker.validated.connect(self.on_validate_complete)
            self.validate_worker.error.connect(self.handle_error)
            self.validate_worker.start()

        except Exception as e:
            self.update_log(f"批量导入时出错: {str(e)}")
            QMessageBox.critical(self, "错误", f"批量导入时出错: {str(e)}")

    #
    # try:
    #         dir_path = QFileDialog.getExistingDirectory(
    #             self,
    #             "选择资源包文件夹",
    #             "",
    #             QFileDialog.Option.ShowDirsOnly
    #         )
    #
    #         if not dir_path:
    #             return
    #
    #         # 查找所有.ab文件
    #         ab_files = []
    #         for root, _, files in os.walk(dir_path):
    #             for file in files:
    #                 if self.bundle_validator.is_valid_bundle(os.path.join(root, file))[0]:
    #                     ab_files.append(os.path.join(root, file))
    #
    #         if not ab_files:
    #             QMessageBox.warning(self, "警告", "未找到任何资源包文件！")
    #             return
    #
    #         # 更新状态
    #         self.status_label.setText(f"找到 {len(ab_files)} 个资源包文件")
    #         self.status_label.setStyleSheet("color: #4a86e8;")
    #         self.update_log(f"开始批量处理 {len(ab_files)} 个资源包文件")
    #
    #
    #
    #     except Exception as e:
    #         self.update_log(f"批量导入时出错: {str(e)}")
    #         QMessageBox.critical(self, "错误", f"批量导入时出错: {str(e)}")

    def on_validate_complete(self, valid_files: List[str]):
        if not valid_files:
            self.update_log("未找到有效的资源包文件")
            QMessageBox.warning(self, "警告", "未找到任何有效的资源包文件！")
            return

        # 更新状态
        self.status_label.setText(f"找到 {len(valid_files)} 个有效资源包文件")
        self.status_label.setStyleSheet("color: #4a86e8;")
        self.update_log(f"开始批量处理 {len(valid_files)} 个资源包文件")

        # 创建任务队列和处理进度计数器
        self.task_queue = Queue()
        self.completed_tasks = 0
        self.total_tasks = len(valid_files)
        self.task_lock = threading.Lock()

        # 将所有文件添加到任务队列
        for file_path in valid_files:
            if not self.check_file_exists(file_path):
                self.task_queue.put(file_path)

        # 创建线程池（设置合适的线程数，比如CPU核心数的2倍）
        max_workers = os.cpu_count() * 2 or 4
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)

        # 启动处理线程
        for _ in range(max_workers):
            self.thread_pool.submit(self.process_file_task)

    def process_file_task(self):
        """处理单个文件的任务"""
        while not self.is_shutting_down:
            try:
                # 从队列获取任务，设置较短的超时时间以便及时响应终止信号
                try:
                    file_path = self.task_queue.get(timeout=0.5)
                except Empty:
                    continue

                # 检查是否正在关闭
                if self.is_shutting_down:
                    break

                try:
                    self.update_log(f"正在处理文件: {os.path.basename(file_path)}")
                    self.asset_path = file_path

                    worker = AssetWorker(file_path)
                    worker.progress.connect(self.update_log)
                    worker.finished.connect(self.scan_finished)
                    worker.error.connect(self.handle_error)
                    worker.scan_complete.connect(self.on_scan_complete)

                    # 添加到工作线程列表
                    with self.task_lock:
                        self.workers.append(worker)

                    worker.start()
                    worker.wait()

                    # 从列表中移除完成的线程
                    with self.task_lock:
                        if worker in self.workers:
                            self.workers.remove(worker)

                    # 更新进度
                    with self.task_lock:
                        if not self.is_shutting_down:
                            self.completed_tasks += 1
                            progress = (self.completed_tasks / self.total_tasks) * 100
                            # 使用 QMetaObject.invokeMethod 在主线程中更新进度
                            self.progress_signal.emit(int(progress), f"正在处理: {self.completed_tasks}/{self.total_tasks} ({progress:.1f}%)")
                            if self.completed_tasks == self.total_tasks:
                                self.progress_signal.emit(0, "处理完成！")

                except Exception as e:
                    self.logger.error(f"处理文件失败 {file_path}: {str(e)}")
                    self.update_log(f"处理文件失败 {os.path.basename(file_path)}: {str(e)}")

                finally:
                    self.task_queue.task_done()

            except Exception as e:
                if not self.is_shutting_down:
                    self.logger.error(f"处理任务时出错: {str(e)}")

    def update_progress(self, value,message):
        """更新进度条的槽函数"""
        self.progress_bar.setValue(min(value, 100))
        self.progress_bar.setFormat(message)
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
            self.path_to_files[asset_path] = files  # 持久化保存文件列表

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

            # 连接窗口关闭信号，当窗口关闭时自动清理引用
            dialog.destroyed.connect(lambda: self.on_window_closed(asset_path))
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
        """更新日志（仅记录到日志文件，不再显示在UI中）"""
        # 只记录到日志文件
        self.logger.info(message)

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
        self.logger.error(f"处理过程中出现错误：{error_message}")
        QMessageBox.critical(self, "错误", f"处理过程中出现错误：{error_message}")


    def close_selected_windows(self):
        """移除选中的资源包"""
        try:
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
                    
                    # 如果存在对应的窗口，先关闭窗口并清理引用
                    if asset_path in self.path_to_windows:
                        window = self.path_to_windows[asset_path]
                        try:
                            # 检查窗口对象是否已被删除
                            # 尝试访问窗口属性，如果对象已删除会抛出RuntimeError
                            _ = window.isVisible()
                            # 窗口对象存在，正常关闭
                            window.close()
                        except RuntimeError:
                            # 窗口对象已被删除，只需清理引用
                            self.logger.info(f"窗口已被删除，直接清理引用: {asset_path}")
                        
                        # 从字典中移除
                        del self.path_to_windows[asset_path]
                        if window in self.windows_to_files:
                            del self.windows_to_files[window]
                    
                    # 清理文件列表映射（移除资源时才清理，关闭窗口时不清理）
                    if asset_path in self.path_to_files:
                        del self.path_to_files[asset_path]
                    
                    # 无论窗口是否存在，都要从列表中移除行
                    self.window_list.removeRow(row)
                    
                # 更新统计信息
                self.update_stats()
        except Exception as e:
            self.logger.error(f"关闭窗口时出错: {str(e)}")
            QMessageBox.critical(self, "错误", f"关闭窗口失败: {str(e)}")

    def close_all_windows(self):
        """移除所有资源包"""
        try:
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
                for path in list(self.path_to_windows.keys()):
                    window = self.path_to_windows[path]
                    try:
                        # 检查窗口对象是否已被删除
                        _ = window.isVisible()
                        # 窗口对象存在，正常关闭
                        window.close()
                    except RuntimeError:
                        # 窗口对象已被删除，只需清理引用
                        self.logger.info(f"窗口已被删除，直接清理引用: {path}")
                    
                    del self.path_to_windows[path]
                    if window in self.windows_to_files:
                        del self.windows_to_files[window]
                
                # 清理所有文件列表映射（移除所有资源时才清理）
                self.path_to_files.clear()
                
                # 清空列表
                self.window_list.setRowCount(0)
                
                # 更新统计信息
                self.update_stats()
        except Exception as e:
            self.logger.error(f"关闭所有窗口时出错: {str(e)}")
            QMessageBox.critical(self, "错误", f"关闭所有窗口失败: {str(e)}")

    def on_window_closed(self, asset_path):
        """处理窗口关闭事件，清理主窗口中的窗口引用（但保留列表显示和文件列表）"""
        try:
            # 只从字典中移除窗口引用，保留列表显示和文件列表以便后续可以重新打开
            if asset_path in self.path_to_windows:
                window = self.path_to_windows[asset_path]
                del self.path_to_windows[asset_path]
                if window in self.windows_to_files:
                    del self.windows_to_files[window]
                # 注意：不删除 self.path_to_files[asset_path]，保留文件列表
                
                self.logger.info(f"已清理窗口引用（保留列表显示和文件列表）: {asset_path}")
        except Exception as e:
            self.logger.error(f"处理窗口关闭事件时出错: {str(e)}")

    def on_window_double_clicked(self, item):
        """处理窗口列表项双击事件"""
        try:
            # 获取双击的行
            row = item.row()
            asset_path = self.window_list.item(row, 0).data(Qt.ItemDataRole.UserRole)
            
            # 检查窗口是否已经存在
            if asset_path in self.path_to_windows:
                window = self.path_to_windows[asset_path]
                # 如果窗口已经关闭，重新创建
                try:
                    window.isVisible()
                except RuntimeError:
                    # 窗口对象已被删除，重新创建
                    # 从持久化字典中获取文件列表
                    files = self.path_to_files.get(asset_path, [])
                    window = FileSelectorDialog(asset_path, files, self.temp_paths[row], self)
                    window.files_selected.connect(self.on_files_selected)
                    window.file_replaced.connect(self.on_file_replaced)
                    window.export_ab.connect(self.on_export_ab)
                    window.destroyed.connect(lambda: self.on_window_closed(asset_path))
                    # 更新窗口引用
                    self.path_to_windows[asset_path] = window
                    self.windows_to_files[window] = files
                    # 显示窗口
                    window.check_theme_change()
                    window.show()
                else:
                    # 窗口对象存在，检查是否可见
                    if not window.isVisible():
                        # 窗口被隐藏了，显示它
                        window.check_theme_change()
                        window.show()
                    else:
                        # 如果窗口已经打开，则将其置顶
                        window.raise_()
                        window.activateWindow()
            else:
                # 如果窗口不存在，创建新窗口
                # 从持久化字典中获取文件列表
                files = self.path_to_files.get(asset_path, [])
                window = FileSelectorDialog(asset_path, files, self.temp_paths[row], self)
                window.files_selected.connect(self.on_files_selected)
                window.file_replaced.connect(self.on_file_replaced)
                window.export_ab.connect(self.on_export_ab)
                window.destroyed.connect(lambda: self.on_window_closed(asset_path))
                # 更新窗口引用
                self.path_to_windows[asset_path] = window
                self.windows_to_files[window] = files
                # 显示窗口
                window.check_theme_change()
                window.show()
        except Exception as e:
            self.logger.error(f"打开窗口时出错: {str(e)}")
            QMessageBox.critical(self, "错误", f"打开窗口失败: {str(e)}")

    def show_batch_update_dialog(self):
        """显示批量更新窗口"""
        dialog = BatchPackDialog(self)
        dialog.show()

    def show_donate_dialog(self):
        """显示捐赠窗口"""
        dialog = DonateDialog(self)
        dialog.exec()

    def show_settings_dialog(self):
        """显示设置窗口"""
        dialog = SettingsDialog(self)
        dialog.exec()

    def show_batch_decrypt_dialog(self):
        """显示批量解密窗口"""
        dialog = BatchDecryptDialog(self)
        dialog.show()

    def closeEvent(self, event):
        """关闭事件处理"""
        try:
            # 保存窗口状态到配置
            self.save_window_state()
            
            # 设置关闭标志
            self.is_shutting_down = True

            # 关闭所有 FileSelectorDialog 窗口
            for path in self.path_to_windows:
                window = self.path_to_windows[path]
                try:
                    if window.isVisible():
                        window.close()
                except Exception as e:
                    pass
                    # self.logger.error(f"关闭窗口时出错: {str(e)}")

            # 等待所有任务完成
            if hasattr(self, 'task_queue'):
                while not self.task_queue.empty():
                    try:
                        self.task_queue.get_nowait()
                        self.task_queue.task_done()
                    except Empty:
                        break

            # 关闭线程池
            if self.thread_pool:
                self.thread_pool.shutdown(wait=False)
                self.thread_pool = None

            # 终止所有工作线程
            for worker in self.workers:
                if worker.isRunning():
                    worker.terminate()
                    worker.wait(1000)  # 等待最多1秒

            # 清理临时目录
            count = 0
            for temp_path in self.temp_paths:
                try:
                    if os.path.exists(temp_path):
                        count += 1
                        shutil.rmtree(temp_path)

                except Exception as e:
                    self.logger.error(f"清理临时目录失败: {str(e)}")
            self.logger.info(f"临时目录已删除: {count} 个")
        except Exception as e:
            self.logger.error(f"关闭应用时出错: {str(e)}")
        finally:
            event.accept()

    def dragEnterEvent(self, event):
        """处理拖拽进入事件"""
        if event.mimeData().hasUrls():
            # 检查是否包含有效的AB文件
            has_valid_files = True

            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if os.path.isfile(file_path) and self.bundle_validator.is_valid_bundle(file_path)[0]:
                    has_valid_files = True
                    break
                if os.path.isdir(file_path):
                    # 如果是目录，则检查目录下是否有AB文件
                    for root, _, files in os.walk(file_path):
                        for file in files:
                            if self.bundle_validator.is_valid_bundle(file_path)[0]:
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
            all_files = []
            # 收集有效的AB文件
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if os.path.isfile(file_path):
                    all_files.append(file_path)
                elif os.path.isdir(file_path):
                    # 如果是目录，则检查目录下是否有AB文件
                    for root, _, files in os.walk(file_path):
                        for file in files:
                            all_files.append(os.path.join(root, file))


            # 创建并启动验证线程
            self.validate_worker = BundleValidateWorker(all_files)
            self.validate_worker.progress.connect(self.update_log)
            self.validate_worker.validated.connect(self.on_validate_complete)
            self.validate_worker.error.connect(self.handle_error)
            self.validate_worker.start()

    def check_file_exists(self, file_path):
        """检查文件是否已存在于列表中"""
        # file_path 转化为标准路径统一斜杠
        file_path = os.path.normpath(file_path)
        for row in range(self.window_list.rowCount()):
            item = self.window_list.item(row, 0)
            if os.path.normpath(item.data(Qt.ItemDataRole.UserRole)) == file_path:
                return True
        return False

    def update_stats(self):
        """更新统计信息"""
        count = self.window_list.rowCount()
        self.stats_label.setText(f"已加载资源包: {count} 个")

    def save_window_state(self):
        """保存窗口状态到配置"""
        try:
            # 保存窗口大小和位置（仅在非最大化状态下）
            is_maximized = self.isMaximized()
            self.config.set('window_maximized', is_maximized, save_immediately=False)
            
            if not is_maximized:
                # 只在非最大化状态下保存位置和大小
                self.config.set('window_width', self.width(), save_immediately=False)
                self.config.set('window_height', self.height(), save_immediately=False)
                self.config.set('window_x', self.x(), save_immediately=False)
                self.config.set('window_y', self.y(), save_immediately=False)
            
            # 一次性保存所有配置
            self.config.save()
            self.logger.info("窗口状态已保存")
        except Exception as e:
            self.logger.error(f"保存窗口状态失败: {e}")

    def toggle_theme(self):
        """切换主题"""
        self.theme_manager.toggle_theme()

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

    def on_resize(self, event):
        """处理窗口大小变化事件"""
        try:
            # 获取当前窗口大小
            current_width = self.width()
            current_height = self.height()
            
            # 更新基础字体大小
            self.base_font_size = max(6, int(current_height * 0.015))
            self.base_font_size = min(self.base_font_size, 10)
            
            # 更新标题字体
            title_font = QFont()
            title_font.setPointSize(self.base_font_size + 4)
            title_font.setBold(True)
            self.title_label.setFont(title_font)
            
            # 更新按钮字体
            button_font = QFont()
            # 设置最大字体大小为固定值


            button_font.setPointSize(self.base_font_size)
            for button in [self.single_import_btn, self.batch_import_btn, 
                         self.update_mod_btn, self.batch_decrypt_btn,
                         self.close_selected_btn, self.close_all_btn]:
                button.setFont(button_font)
            
            # 更新标签字体
            label_font = QFont()
            label_font.setPointSize(self.base_font_size)
            for label in [self.status_label,
                         self.stats_label, self.about_text]:
                label.setFont(label_font)
            
            # 更新表格列宽
            self.window_list.setColumnWidth(2, int(current_width * 0.08))
            
            # 更新搜索框字体
            search_font = QFont()
            search_font.setPointSize(self.base_font_size)
            self.search_input.setFont(search_font)
            
            # 更新进度条高度
            self.progress_bar.setFixedHeight(int(current_height * 0.03))
            
            # 更新组框标题字体
            group_font = QFont()
            group_font.setPointSize(self.base_font_size + 1)
            group_font.setBold(True)
            for group in self.findChildren(QGroupBox):
                group.setFont(group_font)
            
            # 更新表格字体
            table_font = QFont()
            table_font.setPointSize(self.base_font_size)
            self.window_list.setFont(table_font)
            self.window_list.horizontalHeader().setFont(table_font)
            
            # 更新链接字体
            link_font = QFont()
            link_font.setPointSize(self.base_font_size)
            self.github_label.setFont(link_font)
            self.alipay_label.setFont(link_font)
            
            # 更新主题标签字体
            self.theme_label.setFont(label_font)
            
            # 更新图标大小
            icon_size = int(current_height * 0.04)
            self.theme_btn.setIconSize(QSize(icon_size, icon_size))
            
            # # 更新布局间距
            # for layout in self.findChildren(QVBoxLayout):
            #     layout.setSpacing(int(current_height * 0.02))
            # for layout in self.findChildren(QHBoxLayout):
            #     layout.setSpacing(int(current_width * 0.02))
            #
            # # 更新边距
            # for widget in self.findChildren(QWidget):
            #     if isinstance(widget, (QGroupBox, QTextEdit, QTableWidget)):
            #         widget.setContentsMargins(
            #             int(current_width * 0.02),
            #             int(current_height * 0.02),
            #             int(current_width * 0.02),
            #             int(current_height * 0.02)
            #         )
            
        except Exception as e:
            self.logger.error(f"调整窗口大小时出错: {str(e)}")
        
        # 调用父类的resizeEvent
        super().resizeEvent(event)