"""
文件选择器对话框
"""
import os
import logging
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget,
                             QLabel, QPushButton, QSplitter, QListWidgetItem,
                             QFileDialog, QMessageBox, QFrame, QMenu, QGroupBox, QButtonGroup, QRadioButton,
                             QProgressBar, QSlider, QScrollArea, QWidget, QTableWidget, QTableWidgetItem, QHeaderView,
                             QLineEdit)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QUrl, QTimer, QMimeData, QByteArray
from PyQt6.QtGui import QPixmap, QImage, QContextMenuEvent, QColor, QBrush, QIcon, QDrag, QPainter
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

from ..core.asset_extractor import AssetExtractor


class FileSelectorDialog(QDialog):
    """文件选择器对话框"""
    files_selected = pyqtSignal(list)  # 选中的文件列表
    file_replaced = pyqtSignal(dict)  # 文件替换信号
    export_ab = pyqtSignal(str,str, list)  # 导出AB资源包信号

    def __init__(self, asset_path: str, files: list, temp_path: str, parent=None):
        """
        初始化文件选择对话框
        
        Args:
            asset_path: 资源包路径
            parent: 父窗口
        """
        super().__init__(parent)
        self.asset_path = asset_path
        self.files = files  # 存储所有文件信息
        self.replace_files = {}  # 存储替换文件信息
        self.current_type = "All"  # 当前选择的文件类型
        self.temp_files = []  # 存储临时文件路径
        self.temp_path = temp_path  # 临时文件路径

        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

        # 设置窗口标题为资源路径
        self.setWindowTitle(f"资源包: {os.path.basename(asset_path)}")
        self.setMinimumSize(900, 600)
        self.setup_ui()
        self.load_files()

    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)

        # 创建文件类型切换按钮组
        type_group = QGroupBox("文件类型")
        type_layout = QHBoxLayout()
        type_layout.setSpacing(10)  # 保持按钮间距
        # 固定高度
        type_group.setFixedHeight(80)
        type_layout.setContentsMargins(10, 10, 10, 10)  # 保持边距
        self.type_group = QButtonGroup()

        # 添加文件类型按钮
        types = ["All", "TextAsset", "Texture2D", "AudioClip", "Mesh", "MonoBehaviour", "Material", "Other"]
        for type_name in types:
            btn = QRadioButton(type_name)
            btn.setChecked(type_name == "All")
            btn.setMinimumWidth(100)  # 保持按钮最小宽度
            self.type_group.addButton(btn)
            type_layout.addWidget(btn)

        # 添加弹性空间
        type_layout.addStretch()

        type_group.setLayout(type_layout)
        layout.addWidget(type_group)

        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStretchFactor(0, 1)  # 文件列表区域
        splitter.setStretchFactor(1, 1)  # 预览区域
        
        # 设置分割器初始大小
        total_width = self.width()
        splitter.setSizes([total_width // 2, total_width // 2])

        # 左侧文件列表
        list_frame = QFrame()
        list_frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Sunken)
        list_layout = QVBoxLayout(list_frame)

        # 添加标题和提示信息
        title_layout = QVBoxLayout()
        list_title = QLabel("文件列表")
        list_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        title_layout.addWidget(list_title)

        # 添加搜索框
        search_layout = QHBoxLayout()
        search_label = QLabel("搜索:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入文件名搜索...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 5px;
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 1px solid #4a86e8;
            }
        """)
        self.search_input.textChanged.connect(self.on_search_text_changed)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        title_layout.addLayout(search_layout)

        # 添加操作提示
        tips_label = QLabel("操作提示：\n"
                            "• 按住Ctrl键可多选文件\n"
                            "• 按住Shift键可区域选择\n"
                            "• 右键点击文件可进行替换操作\n"
                            "• 已替换的文件将显示为绿色\n"
                            "• 可拖拽文件到其他窗口进行替换\n"
                            "• 点击表头可排序文件列表")
        tips_label.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 12px;
                padding: 5px;
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 4px;
            }
        """)
        title_layout.addWidget(tips_label)
        list_layout.addLayout(title_layout)

        # 创建表格控件替代列表控件
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(4)
        self.file_table.setHorizontalHeaderLabels(["名称", "类型", "路径ID", "大小"])
        
        # 设置表格样式
        self.file_table.setStyleSheet("""
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
            QHeaderView::section:checked {
                background-color: #e6f3ff;
            }
        """)
        
        # 设置表格属性
        self.file_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.file_table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.file_table.setAlternatingRowColors(True)
        self.file_table.verticalHeader().setVisible(False)
        self.file_table.setShowGrid(False)
        
        # 设置列宽
        header = self.file_table.horizontalHeader()
        # 设置名称列为主要显示列
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # 名称列自适应
        # 其他列固定宽度
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)  # 类型列固定宽度
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)  # 路径ID列固定宽度
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # 大小列固定宽度
        
        # 设置固定列宽
        self.file_table.setColumnWidth(1, 80)  # 类型列
        self.file_table.setColumnWidth(2, 80)  # 路径ID列
        self.file_table.setColumnWidth(3, 80)  # 大小列
        
        # 启用排序
        self.file_table.setSortingEnabled(True)
        # 连接排序信号
        self.file_table.horizontalHeader().sortIndicatorChanged.connect(self.on_sort_changed)
        
        # 连接信号
        self.file_table.itemSelectionChanged.connect(self.on_selection_changed)
        self.file_table.itemClicked.connect(self.on_file_clicked)
        self.file_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.file_table.customContextMenuRequested.connect(self.show_context_menu)

        # 启用拖拽功能
        self.file_table.setDragEnabled(True)
        self.file_table.setAcceptDrops(True)
        self.file_table.setDropIndicatorShown(True)
        self.file_table.dragEnterEvent = self.dragEnterEvent
        self.file_table.dragMoveEvent = self.dragMoveEvent
        self.file_table.dropEvent = self.dropEvent
        self.file_table.startDrag = self.startDrag

        list_layout.addWidget(self.file_table)

        # 添加全选和取消全选按钮
        select_buttons_layout = QHBoxLayout()
        select_all_btn = QPushButton("全选")
        select_all_btn.clicked.connect(self.select_all_files)
        select_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a86e8;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #3a76d8;
            }
        """)

        deselect_all_btn = QPushButton("取消全选")
        deselect_all_btn.clicked.connect(self.deselect_all_files)
        deselect_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)

        select_buttons_layout.addWidget(select_all_btn)
        select_buttons_layout.addWidget(deselect_all_btn)
        list_layout.addLayout(select_buttons_layout)

        splitter.addWidget(list_frame)

        # 右侧预览区域
        preview_frame = QFrame()
        preview_frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Sunken)
        preview_layout = QVBoxLayout(preview_frame)

        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #f8f8f8;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        # 创建预览容器
        preview_container = QWidget()
        preview_container_layout = QVBoxLayout(preview_container)
        preview_container_layout.setContentsMargins(0, 0, 0, 0)
        preview_container_layout.setSpacing(0)

        # 添加图片信息标签
        self.image_info_label = QLabel()
        self.image_info_label.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 0.7);
                color: white;
                padding: 8px;
                border-radius: 4px;
                font-size: 12px;
            }
        """)
        self.image_info_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.image_info_label.setWordWrap(True)
        self.image_info_label.setVisible(False)
        preview_container_layout.addWidget(self.image_info_label)

        # 图片预览
        self.image_preview = QLabel()
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setMinimumSize(400, 400)
        self.image_preview.setStyleSheet("""
            QLabel {
                background-color: #f8f8f8;
                border: 1px solid #dddddd;
                border-radius: 4px;
                font-size: 14px;
                color: #666666;
            }
        """)
        self.image_preview.setText("请选择要处理的文件\n\n"
                                   "提示：\n"
                                   "• 预览仅支持文本、图片、音频\n"
                                   "• 替换只支持TextAsset、Texture2D\n"
                                   "• 支持跨窗口拖拽替换\n"
                                   "• 文件支持排序和搜索\n"
                                   "• 支持拖拽导出文件")
        self.image_preview.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.image_preview.customContextMenuRequested.connect(self.show_preview_context_menu)
        preview_container_layout.addWidget(self.image_preview)

        # 设置滚动区域的widget
        scroll_area.setWidget(preview_container)
        preview_layout.addWidget(scroll_area)

        # 音频预览控件
        self.audio_preview = QFrame()
        self.audio_preview.setVisible(False)  # 初始隐藏
        audio_layout = QVBoxLayout(self.audio_preview)

        # 音频信息显示
        self.audio_info = QLabel()
        self.audio_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.audio_info.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 14px;
                padding: 10px;
            }
        """)
        audio_layout.addWidget(self.audio_info)

        # 播放控制区域
        play_control_layout = QHBoxLayout()
        play_control_layout.addStretch()

        # 播放/暂停按钮
        self.play_button = QPushButton()
        self.play_button.setIcon(QIcon.fromTheme("media-playback-start"))
        self.play_button.setFixedSize(60, 60)  # 增大按钮尺寸
        self.play_button.setStyleSheet("""
            QPushButton {
                background-color: #4a86e8;
                color: white;
                border: none;
                border-radius: 30px;  /* 圆形按钮 */
                padding: 0;
            }
            QPushButton:hover {
                background-color: #3a76d8;
            }
            QPushButton:pressed {
                background-color: #2a66c8;
            }
        """)
        self.play_button.clicked.connect(self.toggle_audio_playback)
        play_control_layout.addWidget(self.play_button)
        play_control_layout.addStretch()

        audio_layout.addLayout(play_control_layout)

        # 进度条区域
        progress_layout = QHBoxLayout()

        # 当前时间标签
        self.current_time = QLabel("00:00")
        self.current_time.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 12px;
                min-width: 50px;
            }
        """)
        progress_layout.addWidget(self.current_time)

        # 进度条
        self.audio_progress = QSlider(Qt.Orientation.Horizontal)
        self.audio_progress.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #cccccc;
                height: 8px;
                background: #f0f0f0;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #4a86e8;
                border: none;
                width: 16px;
                margin: -4px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: #3a76d8;
            }
            QSlider::sub-page:horizontal {
                background: #4a86e8;
                border-radius: 4px;
            }
        """)
        self.audio_progress.setMinimum(0)
        self.audio_progress.setMaximum(100)
        self.audio_progress.sliderPressed.connect(self.on_progress_slider_pressed)
        self.audio_progress.sliderReleased.connect(self.on_progress_slider_released)
        self.audio_progress.valueChanged.connect(self.on_progress_changed)
        progress_layout.addWidget(self.audio_progress)

        # 总时长标签
        self.total_time = QLabel("00:00")
        self.total_time.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 12px;
                min-width: 50px;
            }
        """)
        progress_layout.addWidget(self.total_time)

        audio_layout.addLayout(progress_layout)
        preview_layout.addWidget(self.audio_preview)

        splitter.addWidget(preview_frame)
        layout.addWidget(splitter)

        # 按钮区域
        button_layout = QHBoxLayout()

        # 导出AB按钮
        self.export_ab_btn = QPushButton("导出AB资源包")
        self.export_ab_btn.clicked.connect(self.export_ab_package)
        self.export_ab_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.export_ab_btn.setEnabled(False)  # 初始禁用

        # 确认按钮
        self.confirm_btn = QPushButton("提取资源")
        self.confirm_btn.clicked.connect(self.on_confirm)
        self.confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)

        button_layout.addStretch()
        button_layout.addWidget(self.export_ab_btn)
        button_layout.addWidget(self.confirm_btn)

        layout.addLayout(button_layout)

        # 连接信号
        self.type_group.buttonClicked.connect(self.on_type_changed)

        # 初始化音频播放器
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.positionChanged.connect(self.update_audio_progress)
        self.media_player.durationChanged.connect(self.update_audio_duration)
        self.media_player.playbackStateChanged.connect(self.update_play_button)
        self.media_player.errorOccurred.connect(self.handle_media_error)

        # 添加缓冲控制
        self.last_position = 0
        self.position_update_timer = QTimer()
        self.position_update_timer.setInterval(200)  # 增加更新间隔到200ms
        self.position_update_timer.timeout.connect(self.update_position)
        self.is_dragging = False

    def load_files(self):
        """加载文件列表"""
        try:
            # 记录临时文件路径
            for file in self.files:
                if file not in self.temp_files:
                    self.temp_files.append(file["path"])

            # 更新文件列表
            self.update_file_list()

        except Exception as e:
            self.logger.error(f"加载文件列表时出错: {str(e)}")
            QMessageBox.critical(self, "错误", f"加载文件列表失败: {str(e)}")

    def update_file_list(self):
        """更新文件列表"""
        # 保存当前排序状态
        header = self.file_table.horizontalHeader()
        sort_column = header.sortIndicatorSection()
        sort_order = header.sortIndicatorOrder()
        
        self.file_table.setSortingEnabled(False)  # 暂时禁用排序
        self.file_table.setRowCount(0)  # 清空表格
        search_text = self.search_input.text().lower()  # 获取搜索文本并转换为小写
        
        for file in self.files:
            # 检查文件类型和搜索文本
            if (self.current_type == "All" or file["type"] == self.current_type) and \
               (not search_text or search_text in file["name"].lower()):
                row = self.file_table.rowCount()
                self.file_table.insertRow(row)
                
                # 设置各列的数据
                name_item = QTableWidgetItem(file["name"].replace(f"_{file["path_id"]}", ""))
                type_item = QTableWidgetItem(file["type"])
                path_id_item = QTableWidgetItem(str(file["path_id"]))
                
                # 大小列：使用原始大小值作为排序数据，格式化大小作为显示数据
                size_item = QTableWidgetItem()
                size_item.setData(Qt.ItemDataRole.UserRole, file["size"])  # 存储原始大小值用于排序
                size_item.setText(self.format_file_size(file["size"]))  # 设置显示文本
                
                # 存储完整文件信息
                file_info = (file["name"], file["type"], file["path"])
                for item in [name_item, type_item, path_id_item, size_item]:
                    item.setData(Qt.ItemDataRole.UserRole + 1, file_info)  # 存储文件信息
                
                # 设置工具提示
                tooltip = f"完整文件名: {file['name']}\n"
                tooltip += f"类型: {file['type']}\n"
                tooltip += f"路径ID: {file['path_id']}\n"
                tooltip += f"大小: {self.format_file_size(file['size'])}\n"
                tooltip += f"路径: {file['path']}"
                
                name_item.setToolTip(tooltip)
                type_item.setToolTip(tooltip)
                path_id_item.setToolTip(tooltip)
                size_item.setToolTip(tooltip)
                
                # 添加到表格
                self.file_table.setItem(row, 0, name_item)
                self.file_table.setItem(row, 1, type_item)
                self.file_table.setItem(row, 2, path_id_item)
                self.file_table.setItem(row, 3, size_item)

                # 检查文件是否被替换，如果是则设置颜色
                if file_info in self.replace_files:
                    for col in range(self.file_table.columnCount()):
                        item = self.file_table.item(row, col)
                        if item:
                            item.setBackground(QBrush(QColor("#e8f5e9")))  # 浅绿色背景
                            item.setForeground(QBrush(QColor("#2e7d32")))  # 深绿色文本
        
        # 恢复排序状态
        self.file_table.setSortingEnabled(True)
        if sort_column >= 0:
            header.setSortIndicator(sort_column, sort_order)

    def on_type_changed(self, button):
        """处理文件类型切换"""
        self.current_type = button.text()
        self.update_file_list()

    def on_file_clicked(self, item):
        """处理文件点击事件"""
        try:
            file_info = item.data(Qt.ItemDataRole.UserRole + 1)  # 从 UserRole + 1 获取文件信息
            if isinstance(file_info, tuple) and len(file_info) == 3:
                name, file_type, path = file_info
                # 检查是否有替换文件
                if file_info in self.replace_files:
                    path = self.replace_files[file_info]
                self.update_preview(name, file_type, path)
        except Exception as e:
            self.logger.error(f"更新预览时出错: {str(e)}")
            self.image_preview.setText(f"预览出错: {str(e)}")

    def update_preview(self, name: str, file_type: str, path: str):
        """更新预览"""
        try:
            # 检查是否有替换文件
            if (name, file_type, path) in self.replace_files:
                path = self.replace_files[(name, file_type, path)]

            # 默认隐藏图片信息标签
            self.image_info_label.setVisible(False)

            if file_type == "Texture2D":
                # 显示图片预览
                self.image_preview.setVisible(True)
                self.audio_preview.setVisible(False)
                self.image_info_label.setVisible(True)
                
                # 加载图片
                pixmap = QPixmap(path)
                if not pixmap.isNull():
                    # 获取图片信息
                    image = QImage(path)
                    width = image.width()
                    height = image.height()
                    format = image.format()
                    depth = image.depth()
                    file_size = os.path.getsize(path)
                    
                    # 计算文件大小显示
                    size_str = self.format_file_size(file_size)
                    
                    # 获取色彩空间信息
                    color_space = "RGB" if format in [QImage.Format.Format_RGB32, QImage.Format.Format_ARGB32] else "RGBA"
                    
                    # 设置图片信息文本
                    info_text = f"文件名: {name}\n"
                    info_text += f"分辨率: {width}x{height}\n"
                    info_text += f"文件大小: {size_str}\n"
                    info_text += f"色彩深度: {depth}位\n"
                    info_text += f"色彩空间: {color_space}\n"
                    info_text += f"格式: {format}"
                    
                    self.image_info_label.setText(info_text)
                    
                    # 缩放图片以适应预览区域
                    scaled_pixmap = pixmap.scaled(
                        self.image_preview.size(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.image_preview.setPixmap(scaled_pixmap)
                else:
                    self.image_preview.setText("无法加载图片")
                    self.image_info_label.setVisible(False)

            elif file_type == "TextAsset":
                # 显示文本预览
                self.image_preview.setVisible(True)
                self.audio_preview.setVisible(False)
                self.image_info_label.setVisible(True)
                
                # 获取文件信息
                file_size = os.path.getsize(path)
                size_str = self.format_file_size(file_size)
                
                # 读取文件内容
                with open(path, "r", encoding="utf-8", errors='surrogateescape') as f:
                    text = f.read()
                
                # 设置文件信息
                info_text = f"文件名: {name}\n"
                info_text += f"类型: TextAsset\n"
                info_text += f"文件大小: {size_str}\n"
                info_text += f"编码: UTF-8"
                
                self.image_info_label.setText(info_text)
                self.image_preview.setText(text)

            elif file_type == "MonoBehaviour":
                # 显示文本预览
                self.image_preview.setVisible(True)
                self.audio_preview.setVisible(False)
                self.image_info_label.setVisible(True)
                
                # 获取文件信息
                file_size = os.path.getsize(path)
                size_str = self.format_file_size(file_size)
                
                # 读取文件内容
                with open(path, "r", encoding="utf-8", errors='surrogateescape') as f:
                    text = f.read()
                
                # 设置文件信息
                info_text = f"文件名: {name}\n"
                info_text += f"类型: MonoBehaviour\n"
                info_text += f"文件大小: {size_str}\n"
                info_text += f"编码: UTF-8"
                
                self.image_info_label.setText(info_text)
                self.image_preview.setText(text)

            elif file_type == "AudioClip":
                # 显示音频预览
                self.image_preview.setVisible(False)
                self.audio_preview.setVisible(True)
                self.image_info_label.setVisible(True)
                
                # 获取文件信息
                file_size = os.path.getsize(path)
                size_str = self.format_file_size(file_size)
                
                # 设置文件信息
                info_text = f"文件名: {name}\n"
                info_text += f"类型: AudioClip\n"
                info_text += f"文件大小: {size_str}"
                
                self.image_info_label.setText(info_text)
                self.audio_info.setText(f"音频文件: {name}")
                self.media_player.setSource(QUrl.fromLocalFile(path))
                self.audio_progress.setValue(0)
                self.update_play_button(QMediaPlayer.PlaybackState.StoppedState)
                self.position_update_timer.start()  # 开始定时更新

            elif file_type == "Mesh":
                # 显示网格信息
                self.image_preview.setVisible(True)
                self.audio_preview.setVisible(False)
                self.image_info_label.setVisible(True)
                
                # 获取文件信息
                file_size = os.path.getsize(path)
                size_str = self.format_file_size(file_size)
                
                # 设置文件信息
                info_text = f"文件名: {name}\n"
                info_text += f"类型: Mesh\n"
                info_text += f"文件大小: {size_str}\n"
                info_text += f"格式: OBJ"
                
                self.image_info_label.setText(info_text)
                self.image_preview.setText(f"网格文件: {name}\n格式: OBJ")

            elif file_type == "Material":
                # 显示材质信息
                self.image_preview.setVisible(True)
                self.audio_preview.setVisible(False)
                self.image_info_label.setVisible(True)
                
                # 获取文件信息
                file_size = os.path.getsize(path)
                size_str = self.format_file_size(file_size)
                
                # 设置文件信息
                info_text = f"文件名: {name}\n"
                info_text += f"类型: Material\n"
                info_text += f"文件大小: {size_str}\n"
                info_text += f"格式: MAT"
                
                self.image_info_label.setText(info_text)
                self.image_preview.setText(f"材质文件: {name}\n格式: MAT")

            else:
                # 显示其他类型文件信息
                self.image_preview.setVisible(True)
                self.audio_preview.setVisible(False)
                self.image_info_label.setVisible(True)
                
                # 获取文件信息
                file_size = os.path.getsize(path)
                size_str = self.format_file_size(file_size)
                
                # 设置文件信息
                info_text = f"文件名: {name}\n"
                info_text += f"类型: {file_type}\n"
                info_text += f"文件大小: {size_str}"
                
                self.image_info_label.setText(info_text)
                self.image_preview.setText(f"文件: {name}\n类型: {file_type}")
        except Exception as e:
            self.logger.error(f"更新预览时出错: {str(e)}")
            self.image_preview.setText(f"预览出错: {str(e)}")
            self.image_info_label.setVisible(False)

    def select_all_files(self):
        """全选文件"""
        self.file_table.selectAll()

    def deselect_all_files(self):
        """取消全选"""
        self.file_table.clearSelection()

    def show_context_menu(self, position):
        """显示文件列表的右键菜单"""
        item = self.file_table.itemAt(position)
        if item:
            menu = QMenu()
            replace_action = menu.addAction("替换此文件")
            replace_action.triggered.connect(lambda: self.replace_file(item.data(Qt.ItemDataRole.UserRole + 1)))
            menu.exec(self.file_table.mapToGlobal(position))

    def show_preview_context_menu(self, position):
        """显示预览区域的右键菜单"""
        selected_items = self.file_table.selectedItems()
        if selected_items:
            menu = QMenu()
            replace_action = menu.addAction("替换此文件")
            replace_action.triggered.connect(
                lambda: self.replace_file(selected_items[0].data(Qt.ItemDataRole.UserRole + 1)))
            menu.exec(self.image_preview.mapToGlobal(position))

    def replace_file(self, file_info):
        """替换文件"""
        try:
            if not file_info or not isinstance(file_info, tuple) or len(file_info) != 3:
                return

            # 选择替换文件
            name, file_type, path = file_info
            file_filter = "所有文件 (*.*)"
            if file_type == "Texture2D":
                file_filter = "图片文件 (*.png *.jpg *.jpeg)"
            elif file_type == "TextAsset":
                file_filter = "文本文件 (*.txt *.json *.xml *.skel *.atlas)"
            elif file_type == "AudioClip":
                file_filter = "音频文件 (*.wav *.mp3)"
            elif file_type == "Mesh":
                file_filter = "网格文件 (*.obj)"
            elif file_type == "Material":
                file_filter = "材质文件 (*.mat)"

            file_path, _ = QFileDialog.getOpenFileName(
                self,
                f"选择替换文件 - {name}",
                "",
                file_filter
            )

            if not file_path:
                return

            self.replace_files[file_info] = file_path
            self.logger.info(f"已选择替换文件: {file_path}")

            # 更新预览
            self.update_preview(name, file_type, file_path)

            # 更新导出AB按钮状态
            self.export_ab_btn.setEnabled(True)

            # 更新文件项的颜色
            for row in range(self.file_table.rowCount()):
                first_item = self.file_table.item(row, 0)
                if first_item and first_item.data(Qt.ItemDataRole.UserRole + 1) == file_info:
                    # 更新整行的颜色
                    for col in range(self.file_table.columnCount()):
                        item = self.file_table.item(row, col)
                        if item:
                            item.setBackground(QBrush(QColor("#e8f5e9")))  # 浅绿色背景
                            item.setForeground(QBrush(QColor("#2e7d32")))  # 深绿色文本
                    break

            QMessageBox.information(self, "成功", f"文件 {name} 已标记为替换")
        except Exception as e:
            self.logger.error(f"替换文件时出错: {str(e)}")
            QMessageBox.critical(self, "错误", f"替换文件失败: {str(e)}")

    def export_ab_package(self):
        """导出AB资源包"""
        try:
            if not self.replace_files:
                QMessageBox.warning(self, "警告", "没有要导出的替换文件！")
                return

            # 选择输出目录
            output_dir = QFileDialog.getExistingDirectory(
                self,
                "选择输出目录",
                ""
            )

            if not output_dir:
                return

            # 发送导出信号
            try:
                self.export_ab.emit(output_dir, self.asset_path, list(self.replace_files.items()))
                self.logger.info(f"已发送导出信号，共 {len(self.replace_files)} 个替换文件")

                # 显示成功消息
                QMessageBox.information(self, "成功", "AB资源包导出完成！")
            except Exception as e:
                self.logger.error(f"发送导出信号时出错: {str(e)}")
                QMessageBox.critical(self, "错误", f"导出AB资源包失败: {str(e)}")

        except Exception as e:
            self.logger.error(f"导出AB资源包时出错: {str(e)}")
            QMessageBox.critical(self, "错误", f"导出AB资源包失败: {str(e)}")

    def on_selection_changed(self):
        """当选择改变时"""
        try:
            selected_items = self.file_table.selectedItems()
            if selected_items:
                # 获取选中行的第一个单元格
                item = selected_items[0]
                self.on_file_clicked(item)
            else:
                # 未选择时显示提示
                self.image_preview.setText("请选择要处理的文件\n\n"
                                           "操作提示：\n"
                                           "• 右键点击可替换当前文件\n"
                                           "• 已替换的文件将显示为绿色")
        except Exception as e:
            self.logger.error(f"选择改变时出错: {str(e)}")
            self.image_preview.setText(f"选择出错: {str(e)}")

    def on_confirm(self):
        """确认选择"""
        try:
            selected_items = self.file_table.selectedItems()
            if not selected_items:
                QMessageBox.warning(self, "警告", "请选择一个文件！")
                return

            # 获取选中的文件信息
            self.selected_files = []
            # 获取选中行的第一个单元格
            for item in selected_items:
                if item.column() == 0:  # 只处理第一列
                    try:
                        file_info = item.data(Qt.ItemDataRole.UserRole + 1)
                        if isinstance(file_info, tuple) and len(file_info) == 3:
                            name, file_type, path = file_info
                            # 检查文件是否存在
                            if os.path.exists(path):
                                self.selected_files.append((name, file_type, path))
                            else:
                                self.logger.warning(f"文件不存在: {path}")
                    except Exception as e:
                        self.logger.error(f"获取文件信息时出错: {str(e)}")
                        continue

            if not self.selected_files:
                QMessageBox.warning(self, "警告", "没有有效的文件被选中！")
                return

            # 选择保存目录
            save_dir = QFileDialog.getExistingDirectory(
                self,
                "选择保存目录",
                "",
                QFileDialog.Option.ShowDirsOnly
            )

            if not save_dir:
                return

            # 创建保存目录
            try:
                # 获取AB文件名（不包含扩展名）
                ab_name = os.path.splitext(os.path.basename(self.asset_path))[0]

                # 创建AB文件目录
                ab_dir = os.path.join(save_dir, ab_name)
                os.makedirs(ab_dir, exist_ok=True)

                # 按文件类型分组
                type_groups = {}
                for name, file_type, path in self.selected_files:
                    if file_type not in type_groups:
                        type_groups[file_type] = []
                    type_groups[file_type].append((name, path))

                # 为每种类型创建子目录并保存文件
                for file_type, files in type_groups.items():
                    # 创建类型子目录
                    type_dir = os.path.join(ab_dir, file_type)
                    os.makedirs(type_dir, exist_ok=True)

                    # 保存文件
                    for name, path in files:
                        try:
                            # 构建目标路径
                            target_path = os.path.join(type_dir, f"{name}")
                            # 截取path地文件名
                            file_name = os.path.basename(path)
                            # 截取文件后缀
                            file_ext = os.path.splitext(file_name)[1]
                            # 替换文件后缀
                            target_path = os.path.join(type_dir, f"{name}{file_ext}")

                            # 复制文件
                            import shutil
                            shutil.copy2(path, target_path)
                            self.logger.info(f"已保存文件: {target_path}")
                        except Exception as e:
                            self.logger.error(f"保存文件失败 {name}: {str(e)}")
                            continue

                # 显示成功消息
                QMessageBox.information(self, "成功", "资源提取完成！")

            except Exception as e:
                self.logger.error(f"保存文件时出错: {str(e)}")
                QMessageBox.critical(self, "错误", f"保存文件失败: {str(e)}")

        except Exception as e:
            self.logger.error(f"确认选择时出错: {str(e)}")
            QMessageBox.critical(self, "错误", f"资源提取失败: {str(e)}")
            # 不关闭对话框，让用户可以看到错误信息

    def toggle_audio_playback(self):
        """切换音频播放状态"""
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
            self.position_update_timer.stop()
        else:
            self.media_player.play()
            self.position_update_timer.start()

    def update_audio_progress(self, position):
        """更新音频进度条"""
        if not self.is_dragging and self.media_player.duration() > 0:
            self.last_position = position
            progress = int((position / self.media_player.duration()) * 100)
            self.audio_progress.setValue(progress)
            self.current_time.setText(self.format_time(position))

    def update_audio_duration(self, duration):
        """更新音频总时长"""
        self.audio_progress.setMaximum(100)
        # 更新总时长
        self.total_time.setText(self.format_time(duration))

    def update_play_button(self, state):
        """更新播放按钮状态"""
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_button.setIcon(QIcon.fromTheme("media-playback-pause"))
            self.position_update_timer.start()
        else:
            self.play_button.setIcon(QIcon.fromTheme("media-playback-start"))
            self.position_update_timer.stop()

    def handle_media_error(self, error, error_string):
        """处理媒体错误"""
        self.logger.error(f"媒体播放错误: {error_string}")
        self.image_preview.setText(f"音频播放错误: {error_string}")

    def update_position(self):
        """定时更新位置"""
        if not self.is_dragging and self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.update_audio_progress(self.media_player.position())

    def on_progress_changed(self, value):
        """处理进度条值改变"""
        if self.media_player.duration() > 0 and self.is_dragging:
            position = int((value / 100) * self.media_player.duration())
            self.media_player.setPosition(position)
            self.current_time.setText(self.format_time(position))

    def on_progress_slider_pressed(self):
        """进度条按下时"""
        self.is_dragging = True
        self.position_update_timer.stop()

    def on_progress_slider_released(self):
        """进度条释放时"""
        self.is_dragging = False
        position = int((self.audio_progress.value() / 100) * self.media_player.duration())
        self.media_player.setPosition(position)
        self.position_update_timer.start()

    def format_time(self, milliseconds):
        """格式化时间显示"""
        seconds = int(milliseconds / 1000)
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    def format_file_size(self, size_in_bytes):
        """格式化文件大小显示"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_in_bytes < 1024.0:
                return f"{size_in_bytes:.2f} {unit}"
            size_in_bytes /= 1024.0
        return f"{size_in_bytes:.2f} TB"

    def closeEvent(self, event):
        """关闭事件"""
        try:
            # 停止音频播放并释放资源
            if hasattr(self, 'media_player'):
                self.position_update_timer.stop()  # 停止定时器
                if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                    self.media_player.stop()
                self.media_player.setSource(QUrl())  # 清除音频源
                self.media_player.setAudioOutput(None)  # 断开音频输出
                self.audio_output = None  # 释放音频输出
                self.media_player = None  # 释放媒体播放器

        finally:
            event.accept()

    def dragEnterEvent(self, event):
        """处理拖拽进入事件"""
        # 检查是否是文件拖拽
        if event.mimeData().hasUrls():
            # 获取拖入的文件路径
            urls = event.mimeData().urls()
            if urls:
                # 获取第一个文件的路径
                file_path = urls[0].toLocalFile()
                # 检查文件是否存在
                if os.path.exists(file_path):
                    event.acceptProposedAction()
                    return
        
        # 检查是否是表格项目拖拽
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        """处理拖拽移动事件"""
        # 检查是否是文件拖拽
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            return
        
        # 检查是否是表格项目拖拽
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            event.acceptProposedAction()

    def startDrag(self, supportedActions):
        """开始拖拽"""
        # 获取选中的行
        selected_rows = set(item.row() for item in self.file_table.selectedItems())
        if not selected_rows:
            return

        # 创建拖拽数据
        mime_data = QMimeData()
        
        # 创建用于文件替换的数据
        items_data = []
        for row in selected_rows:
            items = []
            for col in range(self.file_table.columnCount()):
                item = self.file_table.item(row, col)
                if item:
                    items.append(item)
            if items:
                items_data.append(items)
        
        # 设置用于文件替换的数据
        if items_data:
            mime_data.setData("application/x-qabstractitemmodeldatalist", QByteArray())
        
        # 创建用于文件导出的URL列表
        urls = []
        for row in selected_rows:
            item = self.file_table.item(row, 0)  # 获取第一列的项目
            if item:
                file_info = item.data(Qt.ItemDataRole.UserRole + 1)  # 获取文件信息
                if isinstance(file_info, tuple) and len(file_info) == 3:
                    name, file_type, path = file_info
                    # 检查是否有替换文件
                    if file_info in self.replace_files:
                        path = self.replace_files[file_info]
                    # 添加文件URL
                    urls.append(QUrl.fromLocalFile(path))

        if urls:
            mime_data.setUrls(urls)

        # 创建拖拽图标
        pixmap = QPixmap(100, 30)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setPen(Qt.GlobalColor.black)
        painter.drawText(10, 20, f"拖拽 {len(selected_rows)} 个文件")
        painter.end()

        # 创建拖拽对象
        drag = QDrag(self.file_table)
        drag.setMimeData(mime_data)
        drag.setPixmap(pixmap)
        drag.setHotSpot(QPoint(50, 15))

        # 执行拖拽
        drag.exec(Qt.DropAction.CopyAction)

    def dropEvent(self, event):
        """处理放置事件"""
        # 获取放置位置
        item = self.file_table.itemAt(event.position().toPoint())
        if not item:
            return

        # 获取目标文件信息
        target_info = item.data(Qt.ItemDataRole.UserRole + 1)  # 从 UserRole + 1 获取文件信息
        if not isinstance(target_info, tuple) or len(target_info) != 3:
            return

        # 处理从系统文件管理器拖入的文件
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                file_path = urls[0].toLocalFile()
                if os.path.exists(file_path):
                    # 显示确认对话框
                    reply = QMessageBox.question(
                        self,
                        "确认替换",
                        f"是否确认将文件 {target_info[0]} 替换为 {os.path.basename(file_path)}？",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No
                    )

                    if reply == QMessageBox.StandardButton.Yes:
                        # 执行替换
                        self.replace_files[target_info] = file_path
                        self.logger.info(f"通过系统文件拖拽替换文件: {target_info[0]} -> {os.path.basename(file_path)}")

                        # 更新预览
                        self.update_preview(target_info[0], target_info[1], file_path)

                        # 更新文件项的颜色
                        row = item.row()
                        for col in range(self.file_table.columnCount()):
                            table_item = self.file_table.item(row, col)
                            if table_item:
                                table_item.setBackground(QBrush(QColor("#e8f5e9")))  # 浅绿色背景
                                table_item.setForeground(QBrush(QColor("#2e7d32")))  # 深绿色文本

                        # 更新导出AB按钮状态
                        self.export_ab_btn.setEnabled(True)

                        event.acceptProposedAction()
                        return

        # 处理从表格拖拽的项目
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            # 获取拖拽的文件信息
            source_widget = event.source()
            if not isinstance(source_widget, QTableWidget):
                return

            # 获取源文件信息（只取第一列的数据）
            source_items = [item for item in source_widget.selectedItems() if item.column() == 0]
            if not source_items:
                return

            # 获取源文件信息
            source_info = source_items[0].data(Qt.ItemDataRole.UserRole + 1)  # 从 UserRole + 1 获取文件信息
            if not isinstance(source_info, tuple) or len(source_info) != 3:
                return

            # 显示确认对话框
            reply = QMessageBox.question(
                self,
                "确认替换",
                f"是否确认将文件 {target_info[0]} 替换为 {source_info[0]}？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                # 执行替换
                self.replace_files[target_info] = source_info[2]  # 使用源文件的路径
                self.logger.info(f"通过拖拽替换文件: {target_info[0]} -> {source_info[0]}")

                # 更新预览
                self.update_preview(target_info[0], target_info[1], source_info[2])

                # 更新文件项的颜色
                row = item.row()
                for col in range(self.file_table.columnCount()):
                    table_item = self.file_table.item(row, col)
                    if table_item:
                        table_item.setBackground(QBrush(QColor("#e8f5e9")))  # 浅绿色背景
                        table_item.setForeground(QBrush(QColor("#2e7d32")))  # 深绿色文本

                # 更新导出AB按钮状态
                self.export_ab_btn.setEnabled(True)

                event.acceptProposedAction()
            else:
                event.ignore()

    def resizeEvent(self, event):
        """窗口大小改变事件"""
        super().resizeEvent(event)
        # 更新分割器大小
        total_width = self.width()
        self.findChild(QSplitter).setSizes([total_width // 2, total_width // 2])

    def on_search_text_changed(self, text):
        """处理搜索文本变化"""
        self.update_file_list()

    def on_sort_changed(self, logical_index, order):
        """处理排序变化"""
        if logical_index == 3:  # 大小列
            # 获取所有行
            for row in range(self.file_table.rowCount()):
                size_item = self.file_table.item(row, 3)
                if size_item:
                    # 获取原始大小值
                    size = size_item.data(Qt.ItemDataRole.UserRole)
                    # 更新显示文本
                    size_item.setText(self.format_file_size(size))
