class AssetWindow(QMainWindow):
    """资源包处理窗口"""

    def __init__(self, asset_path=None):
        super().__init__()
        self.asset_path = asset_path
        self.setWindowTitle("资源包处理")
        self.setMinimumSize(800, 600)

        # 设置应用图标
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resource", "icon.webp")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # 初始化变量
        self.scanned_files = []
        self.selected_files = []
        self.replace_files = {}

        self.setup_ui()

        # 如果传入了资源包路径，直接开始处理
        if asset_path:
            self.file_path_label.setText(asset_path)
            self.file_path_label.setStyleSheet("color: #333333;")
            self.start_scan()

    def setup_ui(self):
        """设置UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 文件选择区域
        file_select_layout = QHBoxLayout()
        self.file_path_label = QLabel("未选择文件")
        self.file_path_label.setStyleSheet("color: #666666;")
        select_file_btn = QPushButton("选择资源包")
        select_file_btn.clicked.connect(self.select_file)
        file_select_layout.addWidget(self.file_path_label)
        file_select_layout.addWidget(select_file_btn)
        layout.addLayout(file_select_layout)

        # 状态标签
        self.status_label = QLabel("请选择资源包文件")
        self.status_label.setStyleSheet("color: #666666;")
        layout.addWidget(self.status_label)

        # 日志区域
        log_group = QGroupBox("处理日志")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(150)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

    # 复制其他必要的方法（select_file, start_scan等）
    # ...（与原AssetTabPage类相同的方法）