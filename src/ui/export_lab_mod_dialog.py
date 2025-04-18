"""
导出实验室MOD对话框
"""
import logging
import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QTextEdit, QFileDialog,
                             QScrollArea, QWidget, QGridLayout, QMessageBox,
                             QComboBox, QCheckBox)
from PyQt6.QtCore import Qt, QTimer, QMimeData
from PyQt6.QtGui import QPixmap, QImage, QDragEnterEvent, QDropEvent

from src.worker.export_lab_worker import ExportLabWorker


class ExportLabModDialog(QDialog):
    """导出实验室MOD对话框"""

    def __init__(self, current_ab_name: str,source_file:str,replace_files:list, parent=None):
        super().__init__(parent)
        self.export_worker = None
        self.setWindowTitle("导出实验室MOD")
        self.setMinimumSize(600, 500)

        # 存储当前AB资源名称
        self.current_ab_name = current_ab_name
        self.source_file = source_file
        self.replace_files = replace_files

        # 初始化UI
        self.setup_ui()

        # 初始化主题
        self.last_theme_is_dark = self.is_dark_mode()
        self.update_theme()

        # 创建定时器来检查系统主题变化
        self.theme_check_timer = QTimer(self)
        self.theme_check_timer.timeout.connect(self.check_theme_change)
        self.theme_check_timer.start(10)  # 每秒检查一次

        # 存储预览图路径
        self.preview_images = []

        self.logger = logging.getLogger(__name__)

    def is_dark_mode(self):
        """检测系统是否处于深色模式"""
        try:
            # print(self.parent().theme)
            # return self.parent().theme
            palette = self.parent().palette()
            # print("当前调色板:", palette.window().color().lightness())
            return palette.window().color().lightness() < 128
        except Exception as e:
            self.logger.error(f"检测主题模式时出错: {str(e)}")
            return False

    def check_theme_change(self):
        # print("检查主题变化")
        """检查系统主题是否发生变化"""
        try:
            current_is_dark = self.is_dark_mode()
            if current_is_dark != self.last_theme_is_dark:
                self.last_theme_is_dark = current_is_dark
                self.update_theme()
        except Exception as e:
            self.logger.error(f"检查主题变化时出错: {str(e)}")

    def update_theme(self):
        # print("更新主题样式")
        """更新主题样式"""
        try:
            is_dark = self.is_dark_mode()
            if is_dark:
                self.apply_dark_theme()
            else:
                self.apply_light_theme()
        except Exception as e:
            self.logger.error(f"更新主题样式时出错: {str(e)}")

    def apply_dark_theme(self):
        """应用深色主题"""
        # 设置窗口背景色
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
            }
            QLineEdit {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3c3c3c;
                padding: 8px;
                border-radius: 4px;
            }
            QLineEdit:focus {
                border: 1px solid #4a86e8;
            }
            QTextEdit {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3c3c3c;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3c3c3c;
                padding: 8px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
                border: 1px solid #4c4c4c;
            }
            QPushButton:pressed {
                background-color: #2d2d2d;
                border: 1px solid #3c3c3c;
            }
            QScrollArea {
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                background-color: #2d2d2d;
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
            QComboBox {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3c3c3c;
                padding: 8px;
                border-radius: 4px;
                min-width: 120px;
            }
            QComboBox:hover {
                border: 1px solid #4c4c4c;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: url(icons/down_arrow_white.png);
                width: 12px;
                height: 12px;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3c3c3c;
                selection-background-color: #3d3d3d;
                selection-color: #ffffff;
            }
            QComboBox QAbstractItemView::item {
                padding: 8px;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #3d3d3d;
            }
            QWidget#preview_container {
                background-color: #2d2d2d;
            }
            QLabel#preview_label {
                border: 1px solid #3c3c3c;
            }
            QCheckBox {
                color: #ffffff;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #3c3c3c;
                background-color: #2d2d2d;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #4a86e8;
                border: 1px solid #4a86e8;
            }
            QCheckBox::indicator:disabled {
                border: 1px solid #2c2c2c;
                background-color: #1a1a1a;
            }
        """)

        # 更新预览图容器样式
        if hasattr(self, 'preview_container'):
            self.preview_container.setStyleSheet("""
                QWidget {
                    background-color: #2d2d2d;
                }
            """)

        # 更新预览图标签样式
        if hasattr(self, 'preview_grid'):
            for i in range(self.preview_grid.count()):
                widget = self.preview_grid.itemAt(i).widget()
                if widget:
                    for child in widget.findChildren(QLabel):
                        child.setStyleSheet("border: 1px solid #3c3c3c;")

    def apply_light_theme(self):
        """应用浅色主题"""
        # 设置窗口背景色
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                color: #333333;
            }
            QLabel {
                color: #333333;
            }
            QLineEdit {
                background-color: white;
                color: #333333;
                border: 1px solid #cccccc;
                padding: 8px;
                border-radius: 4px;
            }
            QLineEdit:focus {
                border: 1px solid #4a86e8;
            }
            QTextEdit {
                background-color: white;
                color: #333333;
                border: 1px solid #cccccc;
                padding: 8px;
                border-radius: 4px;
            }
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
            QPushButton:pressed {
                background-color: #1e7e34;
            }
            QScrollArea {
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: white;
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
            QComboBox {
                background-color: white;
                color: #333333;
                border: 1px solid #cccccc;
                padding: 8px;
                border-radius: 4px;
                min-width: 120px;
            }
            QComboBox:hover {
                border: 1px solid #4a86e8;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: url(icons/down_arrow_black.png);
                width: 12px;
                height: 12px;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                color: #333333;
                border: 1px solid #cccccc;
                selection-background-color: #e9ecef;
                selection-color: #333333;
            }
            QComboBox QAbstractItemView::item {
                padding: 8px;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #e9ecef;
            }
            QWidget#preview_container {
                background-color: white;
            }
            QLabel#preview_label {
                border: 1px solid #cccccc;
            }
            QCheckBox {
                color: #333333;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #cccccc;
                background-color: white;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #28a745;
                border: 1px solid #28a745;
            }
            QCheckBox::indicator:disabled {
                border: 1px solid #cccccc;
                background-color: #f8f9fa;
            }
        """)

        # 更新预览图容器样式
        if hasattr(self, 'preview_container'):
            self.preview_container.setStyleSheet("""
                QWidget {
                    background-color: white;
                }
            """)

        # 更新预览图标签样式
        if hasattr(self, 'preview_grid'):
            for i in range(self.preview_grid.count()):
                widget = self.preview_grid.itemAt(i).widget()
                if widget:
                    for child in widget.findChildren(QLabel):
                        child.setStyleSheet("border: 1px solid #cccccc;")

    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        # 显示当前AB资源名称
        ab_name_layout = QHBoxLayout()
        ab_name_label = QLabel("当前AB资源:")
        self.ab_name_display = QLabel(self.current_ab_name)
        self.ab_name_display.setStyleSheet("font-weight: bold;")
        ab_name_layout.addWidget(ab_name_label)
        ab_name_layout.addWidget(self.ab_name_display)
        ab_name_layout.addStretch()
        layout.addLayout(ab_name_layout)

        # 名称输入框
        name_layout = QHBoxLayout()
        name_label = QLabel("名称:")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("请输入MOD名称")
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        # MOD类型选择
        type_layout = QHBoxLayout()
        type_label = QLabel("MOD类型:")
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "普通立绘",
            "静态皮肤",
            "动态皮肤",
            "剧情立绘",
            "剧情CG",
            "肉鸽道具贴图",
            "界面UI素材",
            "肉鸽主题背景",
            "个人名片背景",
            "敌人修改",
            "特效修改"
        ])
        self.type_combo.setCurrentIndex(0)  # 默认选择第一个选项
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_combo)
        layout.addLayout(type_layout)

        # 预览图选择
        preview_layout = QVBoxLayout()
        preview_label = QLabel("预览图 (可直接拖拽文件添加):")

        # 创建滚动区域用于显示预览图
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setMinimumHeight(150)
        self.scroll_area.setAcceptDrops(True)
        self.scroll_area.dragEnterEvent = self.dragEnterEvent
        self.scroll_area.dropEvent = self.scroll_area_drop_event

        # 创建预览图容器
        self.preview_container = QWidget()
        self.preview_grid = QGridLayout(self.preview_container)
        self.preview_grid.setSpacing(10)

        # 添加选择图片按钮
        self.add_image_btn = QPushButton("添加预览图")
        self.add_image_btn.clicked.connect(self.add_preview_image)

        preview_layout.addWidget(preview_label)
        preview_layout.addWidget(self.scroll_area)
        preview_layout.addWidget(self.add_image_btn)
        layout.addLayout(preview_layout)

        # 压缩选项
        compression_layout = QHBoxLayout()
        compression_label = QLabel("压缩格式:")
        self.compression_combo = QComboBox()
        self.compression_combo.addItems(["ZIP", "7Z"])
        self.compression_combo.currentTextChanged.connect(self.on_compression_changed)
        compression_layout.addWidget(compression_label)
        compression_layout.addWidget(self.compression_combo)
        
        # 图种选项
        self.image_zip_checkbox = QCheckBox("启用图种")
        # self.image_zip_checkbox.setEnabled()  # 初始禁用
        self.image_zip_checkbox.stateChanged.connect(self.on_image_zip_changed)
        compression_layout.addWidget(self.image_zip_checkbox)
        
        # 图种图片选择
        self.image_zip_combo = QComboBox()
        self.image_zip_combo.setEnabled(False)  # 初始禁用
        compression_layout.addWidget(self.image_zip_combo)
        
        layout.addLayout(compression_layout)

        # 密码输入框
        password_layout = QHBoxLayout()
        password_label = QLabel("压缩密码:")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("请输入压缩密码（可选）")
        self.password_input.setEchoMode(QLineEdit.EchoMode.PasswordEchoOnEdit)  # 密码模式
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)
        layout.addLayout(password_layout)

        # README文本编辑框
        readme_layout = QVBoxLayout()
        readme_label = QLabel("MOD描述:")
        self.readme_edit = QTextEdit()
        self.readme_edit.setPlaceholderText("请输入MOD说明(可拖拽TXT/MD文本文件直接导入, 支持Markdown语法)")
        self.readme_edit.setMinimumHeight(180)
        self.readme_edit.setAcceptDrops(True)
        self.readme_edit.dragEnterEvent = self.dragEnterEvent
        self.readme_edit.dropEvent = self.readme_drop_event
        readme_layout.addWidget(readme_label)
        readme_layout.addWidget(self.readme_edit)
        layout.addLayout(readme_layout)

        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.confirm_btn = QPushButton("确认")
        self.confirm_btn.clicked.connect(self.on_confirm)
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(self.confirm_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)

    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def scroll_area_drop_event(self, event: QDropEvent):
        """预览图区域拖拽释放事件"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            for url in urls:
                file_path = url.toLocalFile()
                if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                    if file_path not in self.preview_images:
                        self.preview_images.append(file_path)
                        self.update_preview_grid()
            event.acceptProposedAction()

    def readme_drop_event(self, event: QDropEvent):
        """README区域拖拽释放事件"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            for url in urls:
                file_path = url.toLocalFile()
                if file_path.lower().endswith(('.txt', '.md')):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            self.readme_edit.setText(content)
                    except Exception as e:
                        QMessageBox.warning(self, "警告", f"读取文件失败: {str(e)}")
            event.acceptProposedAction()

    def add_preview_image(self):
        """添加预览图"""
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        file_dialog.setNameFilter("图片文件 (*.png *.jpg *.jpeg)")

        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            for file_path in selected_files:
                if file_path not in self.preview_images:
                    self.preview_images.append(file_path)
                    self.update_preview_grid()

    def update_preview_grid(self):
        """更新预览图网格"""
        # 清空现有预览图
        for i in reversed(range(self.preview_grid.count())):
            self.preview_grid.itemAt(i).widget().deleteLater()

        # 清空图种图片选择下拉框
        self.image_zip_combo.clear()

        # 添加预览图
        row = 0
        col = 0
        for image_path in self.preview_images:
            # 创建预览图标签
            preview_label = QLabel()
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                # 缩放图片以适应预览区域
                scaled_pixmap = pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio)
                preview_label.setPixmap(scaled_pixmap)
                preview_label.setFixedSize(100, 100)
                preview_label.setStyleSheet("border: 1px solid #cccccc;")

                # 添加图片到图种选择下拉框
                self.image_zip_combo.addItem(os.path.basename(image_path), image_path)

                # 创建删除按钮
                delete_btn = QPushButton("删除")
                delete_btn.setFixedSize(60, 25)  # 增加按钮宽度
                delete_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #dc3545;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        font-size: 12px;
                        padding: 2px 8px;
                    }
                    QPushButton:hover {
                        background-color: #c82333;
                    }
                    QPushButton:pressed {
                        background-color: #bd2130;
                    }
                """)
                delete_btn.clicked.connect(lambda checked, path=image_path: self.remove_preview_image(path))

                # 创建容器
                container = QWidget()
                container_layout = QVBoxLayout(container)
                container_layout.addWidget(preview_label)
                container_layout.addWidget(delete_btn)
                container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

                # 添加到网格
                self.preview_grid.addWidget(container, row, col)

                col += 1
                if col > 2:  # 每行最多显示3个预览图
                    col = 0
                    row += 1

        # 设置预览容器
        self.scroll_area.setWidget(self.preview_container)

        # 如果有预览图，设置默认选择的图种图片
        if self.preview_images:
            self.image_zip_combo.setCurrentIndex(0)

    def remove_preview_image(self, image_path):
        """删除预览图"""
        if image_path in self.preview_images:
            self.preview_images.remove(image_path)
            self.update_preview_grid()

    def on_compression_changed(self, text):
        """压缩格式改变事件"""
        # 只有在选择ZIP格式时才启用图种选项
        self.image_zip_checkbox.setEnabled(text == "ZIP")
        if text != "ZIP":
            self.image_zip_checkbox.setChecked(False)
            self.image_zip_combo.setEnabled(False)

    def on_image_zip_changed(self, state):
        """图种选项改变事件"""
        # 启用或禁用图种图片选择下拉框
        self.image_zip_combo.setEnabled(state == Qt.CheckState.Checked.value)

    def on_confirm(self):
        """确认按钮点击事件"""
        # 获取输入内容
        name = self.name_input.text().strip()
        readme = self.readme_edit.toPlainText().strip()
        mod_type = self.type_combo.currentText()
        compression_format = self.compression_combo.currentText()
        use_image_zip = self.image_zip_checkbox.isChecked()
        image_zip_path = self.image_zip_combo.currentData() if use_image_zip else None
        password = self.password_input.text().strip()

        # 验证输入
        if not name:
            QMessageBox.warning(self, "警告", "请输入MOD名称")
            return

        if not self.preview_images:
            QMessageBox.warning(self, "警告", "请至少添加一张预览图")
            return

        if not readme:
            QMessageBox.warning(self, "警告", "请输入MOD说明")
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

        type_mapping = {
            "普通立绘": "chararts",
            "静态皮肤": "skinpack",
            "动态皮肤": "dynchars",
            "剧情立绘": "characters",
            "剧情CG": "imgs",
            "肉鸽道具贴图": "spritepack",
            "界面UI素材": "refs",
            "肉鸽主题背景": "rglktopic",
            "个人名片背景": "namecardskin",
            "敌人修改": "enemies",
            "特效修改": "effects"
        }
        mod_type_value = type_mapping.get(mod_type, "chararts")
        
        # 根据压缩格式设置输出文件扩展名
        output_ext = ".zip" if compression_format == "ZIP" else ".7z"
        output_path = os.path.join(save_dir, f"{name}{output_ext}")
        
        self.export_worker = ExportLabWorker(
            ab_name=self.current_ab_name,
            source_file=self.source_file,
            zip_output_dir=output_path,
            preview_images=self.preview_images,
            readme_txt=readme,
            mod_type=mod_type_value,
            replace_files=self.replace_files,
            compression_format=compression_format,
            use_image_zip=use_image_zip,
            image_zip_path=image_zip_path,
            password=password
        )
        self.export_worker.finished.connect(self.on_export_finished)
        self.export_worker.error.connect(self.on_export_error)
        self.export_worker.start()

        self.accept()

    def on_export_finished(self):
        QMessageBox.information(self, "完成", "实验室MOD导出完成！")

    def on_export_error(self,message):
        QMessageBox.critical(self, "错误", message)