"""
设置对话框
"""
import os
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                             QWidget, QLabel, QPushButton, QComboBox, QCheckBox,
                             QLineEdit, QTextEdit, QFileDialog, QGroupBox,
                             QFormLayout, QMessageBox, QScrollArea)
from src.config.config_manager import ConfigManager


class SettingsDialog(QDialog):
    """设置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.config = ConfigManager()
        self.setWindowTitle("设置")
        self.setMinimumSize(700, 600)
        self.init_ui()
        self.load_settings()
        
        # 应用主题
        if hasattr(parent, 'theme_manager'):
            if parent.theme_manager.is_dark_mode():
                self.apply_dark_theme()
            else:
                self.apply_light_theme()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # 创建选项卡
        self.tab_widget = QTabWidget()
        
        # 外观设置标签页
        appearance_tab = self.create_appearance_tab()
        self.tab_widget.addTab(appearance_tab, "🎨 外观")
        
        # 日志设置标签页
        log_tab = self.create_log_tab()
        self.tab_widget.addTab(log_tab, "📝 日志")
        
        # 资源编辑设置标签页
        ab_export_tab = self.create_ab_export_tab()
        self.tab_widget.addTab(ab_export_tab, "📦 资源编辑")
        
        # 实验室MOD设置标签页
        lab_mod_tab = self.create_lab_mod_tab()
        self.tab_widget.addTab(lab_mod_tab, "🧪 实验室MOD")
        
        layout.addWidget(self.tab_widget)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.reset_btn = QPushButton("恢复默认")
        self.reset_btn.setMinimumSize(100, 35)
        self.reset_btn.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(self.reset_btn)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setMinimumSize(100, 35)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.save_btn = QPushButton("保存")
        self.save_btn.setMinimumSize(100, 35)
        self.save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
    
    def create_appearance_tab(self):
        """创建外观设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 主题设置组
        theme_group = QGroupBox("主题设置")
        theme_layout = QFormLayout()
        theme_layout.setSpacing(15)
        
        # 主题模式选择
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["自动", "浅色", "深色"])
        self.theme_combo.setMinimumHeight(30)
        theme_layout.addRow("主题模式:", self.theme_combo)
        
        # 说明文字
        theme_desc = QLabel("• 自动: 跟随系统主题\n• 浅色: 始终使用浅色主题\n• 深色: 始终使用深色主题")
        theme_desc.setStyleSheet("color: #666666; font-size: 12px;")
        theme_layout.addRow("", theme_desc)
        
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        
        layout.addStretch()
        return widget
    
    def create_log_tab(self):
        """创建日志设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 日志文件设置组
        log_group = QGroupBox("日志文件设置")
        log_layout = QFormLayout()
        log_layout.setSpacing(15)
        
        # 启用日志文件
        self.log_enabled_cb = QCheckBox("启用日志文件记录")
        self.log_enabled_cb.setMinimumHeight(30)
        log_layout.addRow("", self.log_enabled_cb)
        
        # 日志等级
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.log_level_combo.setMinimumHeight(30)
        log_layout.addRow("日志等级:", self.log_level_combo)
        
        # 说明文字
        log_desc = QLabel(
            "• DEBUG: 记录所有详细信息（调试用）\n"
            "• INFO: 记录一般信息和重要操作\n"
            "• WARNING: 仅记录警告和错误\n"
            "• ERROR: 仅记录错误信息\n"
            "• CRITICAL: 仅记录严重错误\n\n"
            "日志文件保存位置: logs 文件夹"
        )
        log_desc.setStyleSheet("color: #666666; font-size: 12px;")
        log_desc.setWordWrap(True)
        log_layout.addRow("", log_desc)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        layout.addStretch()
        return widget
    
    def create_ab_export_tab(self):
        """创建资源编辑设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 导出设置组
        export_group = QGroupBox("导出AB资源包设置")
        export_layout = QVBoxLayout()
        export_layout.setSpacing(15)
        
        # 默认保存目录
        dir_layout = QHBoxLayout()
        dir_label = QLabel("默认保存目录:")
        dir_label.setMinimumWidth(120)
        dir_layout.addWidget(dir_label)
        
        self.ab_export_dir_edit = QLineEdit()
        self.ab_export_dir_edit.setPlaceholderText("未设置（使用上次选择的目录）")
        self.ab_export_dir_edit.setMinimumHeight(30)
        dir_layout.addWidget(self.ab_export_dir_edit)
        
        self.ab_export_dir_btn = QPushButton("浏览...")
        self.ab_export_dir_btn.setMinimumSize(80, 30)
        self.ab_export_dir_btn.clicked.connect(self.browse_ab_export_dir)
        dir_layout.addWidget(self.ab_export_dir_btn)
        
        export_layout.addLayout(dir_layout)
        
        # 清除按钮
        clear_layout = QHBoxLayout()
        clear_layout.addStretch()
        self.ab_export_clear_btn = QPushButton("清除默认目录")
        self.ab_export_clear_btn.setMinimumSize(120, 30)
        self.ab_export_clear_btn.clicked.connect(lambda: self.ab_export_dir_edit.clear())
        clear_layout.addWidget(self.ab_export_clear_btn)
        export_layout.addLayout(clear_layout)
        
        # 说明文字
        export_desc = QLabel(
            "设置后，在资源编辑界面导出AB资源包时，\n"
            "文件对话框将默认打开此目录。\n"
            "留空则使用上次选择的目录。"
        )
        export_desc.setStyleSheet("color: #666666; font-size: 12px;")
        export_layout.addWidget(export_desc)
        
        export_group.setLayout(export_layout)
        layout.addWidget(export_group)
        
        layout.addStretch()
        return widget
    
    def create_lab_mod_tab(self):
        """创建实验室MOD设置标签页"""
        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 压缩设置组
        compress_group = QGroupBox("压缩设置")
        compress_layout = QFormLayout()
        compress_layout.setSpacing(15)
        
        # 默认压缩密码
        self.lab_password_edit = QLineEdit()
        self.lab_password_edit.setPlaceholderText("留空表示不使用密码")
        self.lab_password_edit.setMinimumHeight(30)
        self.lab_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        compress_layout.addRow("默认压缩密码:", self.lab_password_edit)
        
        # 显示密码按钮
        show_pwd_layout = QHBoxLayout()
        self.lab_show_password_cb = QCheckBox("显示密码")
        self.lab_show_password_cb.stateChanged.connect(self.toggle_password_visibility)
        show_pwd_layout.addWidget(self.lab_show_password_cb)
        show_pwd_layout.addStretch()
        compress_layout.addRow("", show_pwd_layout)
        
        compress_group.setLayout(compress_layout)
        layout.addWidget(compress_group)
        
        # 图种设置组
        image_group = QGroupBox("图种设置")
        image_layout = QVBoxLayout()
        image_layout.setSpacing(10)
        
        self.lab_image_steg_cb = QCheckBox("默认启用图种功能")
        self.lab_image_steg_cb.setMinimumHeight(30)
        image_layout.addWidget(self.lab_image_steg_cb)
        
        image_desc = QLabel("图种功能可将压缩包隐藏在图片中，更具趣味性。")
        image_desc.setStyleSheet("color: #666666; font-size: 12px;")
        image_layout.addWidget(image_desc)
        
        image_group.setLayout(image_layout)
        layout.addWidget(image_group)
        
        # MOD描述设置组
        desc_group = QGroupBox("MOD描述")
        desc_layout = QVBoxLayout()
        desc_layout.setSpacing(10)
        
        desc_label = QLabel("默认MOD描述内容:")
        desc_layout.addWidget(desc_label)
        
        self.lab_description_edit = QTextEdit()
        self.lab_description_edit.setPlaceholderText("在此输入默认的MOD描述信息...")
        self.lab_description_edit.setMinimumHeight(120)
        desc_layout.addWidget(self.lab_description_edit)
        
        desc_tip = QLabel("此描述将作为导出实验室MOD时的默认内容。")
        desc_tip.setStyleSheet("color: #666666; font-size: 12px;")
        desc_layout.addWidget(desc_tip)
        
        desc_group.setLayout(desc_layout)
        layout.addWidget(desc_group)
        
        # 导出目录设置组
        export_group = QGroupBox("导出设置")
        export_layout = QVBoxLayout()
        export_layout.setSpacing(15)
        
        # 默认保存目录
        dir_layout = QHBoxLayout()
        dir_label = QLabel("默认保存目录:")
        dir_label.setMinimumWidth(120)
        dir_layout.addWidget(dir_label)
        
        self.lab_export_dir_edit = QLineEdit()
        self.lab_export_dir_edit.setPlaceholderText("未设置（使用上次选择的目录）")
        self.lab_export_dir_edit.setMinimumHeight(30)
        dir_layout.addWidget(self.lab_export_dir_edit)
        
        self.lab_export_dir_btn = QPushButton("浏览...")
        self.lab_export_dir_btn.setMinimumSize(80, 30)
        self.lab_export_dir_btn.clicked.connect(self.browse_lab_export_dir)
        dir_layout.addWidget(self.lab_export_dir_btn)
        
        export_layout.addLayout(dir_layout)
        
        # 清除按钮
        clear_layout = QHBoxLayout()
        clear_layout.addStretch()
        self.lab_export_clear_btn = QPushButton("清除默认目录")
        self.lab_export_clear_btn.setMinimumSize(120, 30)
        self.lab_export_clear_btn.clicked.connect(lambda: self.lab_export_dir_edit.clear())
        clear_layout.addWidget(self.lab_export_clear_btn)
        export_layout.addLayout(clear_layout)
        
        # 说明文字
        export_desc = QLabel(
            "设置后，导出实验室MOD时，\n"
            "文件对话框将默认打开此目录。\n"
            "留空则使用上次选择的目录。"
        )
        export_desc.setStyleSheet("color: #666666; font-size: 12px;")
        export_layout.addWidget(export_desc)
        
        export_group.setLayout(export_layout)
        layout.addWidget(export_group)
        
        layout.addStretch()
        
        scroll.setWidget(widget)
        return scroll
    
    def toggle_password_visibility(self, state):
        """切换密码可见性"""
        if state == Qt.CheckState.Checked.value:
            self.lab_password_edit.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.lab_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
    
    def browse_ab_export_dir(self):
        """浏览AB导出目录"""
        current_dir = self.ab_export_dir_edit.text() or os.path.expanduser("~")
        directory = QFileDialog.getExistingDirectory(
            self,
            "选择AB资源包默认保存目录",
            current_dir
        )
        if directory:
            self.ab_export_dir_edit.setText(directory)
    
    def browse_lab_export_dir(self):
        """浏览实验室MOD导出目录"""
        current_dir = self.lab_export_dir_edit.text() or os.path.expanduser("~")
        directory = QFileDialog.getExistingDirectory(
            self,
            "选择实验室MOD默认保存目录",
            current_dir
        )
        if directory:
            self.lab_export_dir_edit.setText(directory)
    
    def load_settings(self):
        """加载设置"""
        # 主题设置
        theme_mode = self.config.get('theme_mode', 'auto')
        theme_index = {'auto': 0, 'light': 1, 'dark': 2}.get(theme_mode, 0)
        self.theme_combo.setCurrentIndex(theme_index)
        
        # 日志设置
        self.log_enabled_cb.setChecked(self.config.get('log_enabled', True))
        log_level = self.config.get('log_level', 'INFO')
        log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if log_level in log_levels:
            self.log_level_combo.setCurrentIndex(log_levels.index(log_level))
        
        # AB导出设置
        ab_export_dir = self.config.get('ab_export_default_dir', '')
        self.ab_export_dir_edit.setText(ab_export_dir or '')
        
        # 实验室MOD设置
        self.lab_password_edit.setText(self.config.get('lab_mod_default_password', ''))
        self.lab_image_steg_cb.setChecked(self.config.get('lab_mod_enable_image_steganography', False))
        self.lab_description_edit.setPlainText(self.config.get('lab_mod_default_description', ''))
        lab_export_dir = self.config.get('lab_mod_export_default_dir', '')
        self.lab_export_dir_edit.setText(lab_export_dir or '')
    
    def save_settings(self):
        """保存设置"""
        try:
            # 主题设置
            theme_modes = ['auto', 'light', 'dark']
            theme_mode = theme_modes[self.theme_combo.currentIndex()]
            old_theme_mode = self.config.get('theme_mode', 'auto')
            self.config.set('theme_mode', theme_mode)
            
            # 日志设置
            self.config.set('log_enabled', self.log_enabled_cb.isChecked())
            log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            self.config.set('log_level', log_levels[self.log_level_combo.currentIndex()])
            
            # AB导出设置
            ab_export_dir = self.ab_export_dir_edit.text().strip()
            self.config.set('ab_export_default_dir', ab_export_dir if ab_export_dir else None)
            
            # 实验室MOD设置
            self.config.set('lab_mod_default_password', self.lab_password_edit.text())
            self.config.set('lab_mod_enable_image_steganography', self.lab_image_steg_cb.isChecked())
            self.config.set('lab_mod_default_description', self.lab_description_edit.toPlainText())
            lab_export_dir = self.lab_export_dir_edit.text().strip()
            self.config.set('lab_mod_export_default_dir', lab_export_dir if lab_export_dir else None)
            
            # 如果主题改变，更新主窗口主题
            if theme_mode != old_theme_mode and self.parent_window:
                if hasattr(self.parent_window, 'theme_manager'):
                    self.parent_window.theme_manager.theme_mode = theme_mode
                    self.parent_window.theme_manager.last_theme_is_dark = self.parent_window.theme_manager._get_current_theme_state()
                    self.parent_window.theme_manager.update_theme()
            
            QMessageBox.information(self, "成功", "设置已保存！")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存设置失败：{str(e)}")
    
    def reset_to_defaults(self):
        """恢复默认设置"""
        reply = QMessageBox.question(
            self,
            "确认",
            "确定要恢复所有设置为默认值吗？\n此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 恢复默认值
            self.theme_combo.setCurrentIndex(0)  # auto
            self.log_enabled_cb.setChecked(True)
            self.log_level_combo.setCurrentIndex(1)  # INFO
            self.ab_export_dir_edit.clear()
            self.lab_password_edit.clear()
            self.lab_image_steg_cb.setChecked(False)
            self.lab_description_edit.clear()
            self.lab_export_dir_edit.clear()
            
            QMessageBox.information(self, "成功", "已恢复默认设置！\n点击\"保存\"以应用更改。")
    
    def apply_light_theme(self):
        """应用浅色主题"""
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                color: #000000;
            }
            QGroupBox {
                border: 1px solid #cccccc;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 5px 15px;
                color: #000000;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
            QLineEdit, QTextEdit, QComboBox {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 5px;
                color: #000000;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                border: 1px solid #0078d4;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: #ffffff;
            }
            QTabBar::tab {
                background-color: #f0f0f0;
                border: 1px solid #cccccc;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 8px 20px;
                margin-right: 2px;
                color: #000000;
            }
            QTabBar::tab:selected {
                background-color: #ffffff;
                border-bottom: 1px solid #ffffff;
            }
            QTabBar::tab:hover {
                background-color: #e0e0e0;
            }
            QCheckBox {
                color: #000000;
            }
        """)
    
    def apply_dark_theme(self):
        """应用深色主题"""
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QGroupBox {
                border: 1px solid #3f3f3f;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
                color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #2d2d2d;
                border: 1px solid #3f3f3f;
                border-radius: 4px;
                padding: 5px 15px;
                color: #ffffff;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
            }
            QPushButton:pressed {
                background-color: #4d4d4d;
            }
            QLineEdit, QTextEdit, QComboBox {
                background-color: #2d2d2d;
                border: 1px solid #3f3f3f;
                border-radius: 4px;
                padding: 5px;
                color: #ffffff;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                border: 1px solid #0078d4;
            }
            QTabWidget::pane {
                border: 1px solid #3f3f3f;
                border-radius: 4px;
                background-color: #1e1e1e;
            }
            QTabBar::tab {
                background-color: #2d2d2d;
                border: 1px solid #3f3f3f;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 8px 20px;
                margin-right: 2px;
                color: #ffffff;
            }
            QTabBar::tab:selected {
                background-color: #1e1e1e;
                border-bottom: 1px solid #1e1e1e;
            }
            QTabBar::tab:hover {
                background-color: #3d3d3d;
            }
            QCheckBox, QLabel {
                color: #ffffff;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                color: #ffffff;
                selection-background-color: #0078d4;
            }
            QComboBox::drop-down {
                border: none;
            }
            QScrollArea {
                border: none;
            }
        """)
