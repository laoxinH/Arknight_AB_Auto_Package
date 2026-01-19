"""
主题管理类
"""
import os
from PyQt6.QtWidgets import QMessageBox
from src.config.config_manager import ConfigManager

class ThemeManager:
    """主题管理类"""
    def __init__(self, main_window):
        self.main_window = main_window
        self.config = ConfigManager()
        
        # 从配置加载主题模式
        self.theme_mode = self.config.get('theme_mode', 'auto')
        self.last_theme_is_dark = self._get_current_theme_state()

    def _get_current_theme_state(self):
        """获取当前主题状态"""
        if self.theme_mode == 'light':
            return False
        elif self.theme_mode == 'dark':
            return True
        else:  # auto
            return self._is_system_dark_mode()

    def _is_system_dark_mode(self):
        """检测系统是否处于深色模式"""
        palette = self.main_window.palette()
        return palette.window().color().lightness() < 128

    def check_theme_change(self):
        """检查系统主题是否发生变化（仅在auto模式下生效）"""
        if self.theme_mode != 'auto':
            return
            
        current_is_dark = self._is_system_dark_mode()
        if current_is_dark != self.last_theme_is_dark:
            self.last_theme_is_dark = current_is_dark
            self.update_theme()

    def is_dark_mode(self):
        """检测当前是否应该使用深色模式"""
        return self.last_theme_is_dark

    def get_theme_display_name(self):
        """获取主题模式的显示名称"""
        if self.theme_mode == 'auto':
            return "自动"
        elif self.theme_mode == 'light':
            return "浅色"
        else:  # dark
            return "深色"

    def toggle_theme(self):
        """切换主题"""
        # 循环切换: auto -> light -> dark -> auto
        if self.theme_mode == 'auto':
            self.theme_mode = 'light'
        elif self.theme_mode == 'light':
            self.theme_mode = 'dark'
        else:  # dark
            self.theme_mode = 'auto'
        
        # 保存配置
        self.config.set('theme_mode', self.theme_mode)
        
        # 更新主题状态
        self.last_theme_is_dark = self._get_current_theme_state()
        
        # 应用主题
        if self.last_theme_is_dark:
            self.apply_dark_theme()
        else:
            self.apply_light_theme()
        
        self.update_theme_icon()

    def update_theme_icon(self):
        """更新主题切换按钮图标和标签（使用emoji）"""
        # 根据主题模式设置不同的emoji和提示
        if self.theme_mode == 'auto':
            # 自动模式：显示自动图标
            emoji = "🌙" if self.last_theme_is_dark else "☀️"
            self.main_window.theme_btn.setText(emoji)
            self.main_window.theme_btn.setToolTip(f"当前: 自动模式 ({('深色' if self.last_theme_is_dark else '浅色')})\n点击切换到浅色模式")
        elif self.theme_mode == 'light':
            # 浅色模式：显示太阳图标
            self.main_window.theme_btn.setText("☀️")
            self.main_window.theme_btn.setToolTip("当前: 浅色模式\n点击切换到深色模式")
        else:  # dark
            # 深色模式：显示月亮图标
            self.main_window.theme_btn.setText("🌙")
            self.main_window.theme_btn.setToolTip("当前: 深色模式\n点击切换到自动模式")
        
        # 更新主题标签文本
        if hasattr(self.main_window, 'theme_label'):
            self.main_window.theme_label.setText(self.get_theme_display_name())

    def update_theme(self):
        """更新主题样式"""
        is_dark = self.is_dark_mode()
        if is_dark:
            self.apply_dark_theme()
        else:
            self.apply_light_theme()
        self.update_theme_icon()

    def apply_dark_theme(self):
        """应用深色主题"""
        try:
            # 更新日志框样式
            if hasattr(self.main_window, 'log_text'):
                self.main_window.log_text.setStyleSheet("""
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
            self.main_window.github_label.setStyleSheet("color: #4a86e8;")
            self.main_window.alipay_label.setStyleSheet("color: #4a86e8;")
            self.main_window.about_text.setStyleSheet("""
                color: #cccccc;
                font-size: 12px;
                padding: 10px;
                background-color: #2d2d2d;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
            """)
            self.main_window.stats_label.setStyleSheet("""
                color: #cccccc;
                font-size: 12px;
                padding: 5px;
                background-color: #2d2d2d;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
            """)

            # 更新按钮样式
            self.main_window.single_import_btn.setStyleSheet("""
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

            # 更新移除按钮样式
            self.main_window.close_selected_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2d2d2d;
                    color: #ff6b6b;
                    border: 1px solid #ff6b6b;
                    padding: 8px 15px;
                    border-radius: 4px;
                    min-width: 100px;
                }
                QPushButton:hover {
                    background-color: #3d2d2d;
                    border: 1px solid #ff8b8b;
                }
                QPushButton:pressed {
                    background-color: #2d2d2d;
                    border: 1px solid #ff6b6b;
                }
                QPushButton:disabled {
                    background-color: #1a1a1a;
                    color: #ff6b6b;
                    border: 1px solid #ff6b6b;
                }
            """)

            self.main_window.close_all_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2d2d2d;
                    color: #ff4444;
                    border: 1px solid #ff4444;
                    padding: 8px 15px;
                    border-radius: 4px;
                    min-width: 100px;
                }
                QPushButton:hover {
                    background-color: #3d2d2d;
                    border: 1px solid #ff6666;
                }
                QPushButton:pressed {
                    background-color: #2d2d2d;
                    border: 1px solid #ff4444;
                }
                QPushButton:disabled {
                    background-color: #1a1a1a;
                    color: #ff4444;
                    border: 1px solid #ff4444;
                }
            """)

            self.main_window.batch_import_btn.setStyleSheet("""
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

            self.main_window.update_mod_btn.setStyleSheet("""
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

            self.main_window.batch_decrypt_btn.setStyleSheet("""
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
            self.main_window.window_list.setStyleSheet("""
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
            self.main_window.setStyleSheet("""
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
            self.main_window.logger.error(f"应用深色主题时出错: {str(e)}")
            QMessageBox.critical(self.main_window, "错误", f"应用深色主题时出错: {str(e)}")

    def apply_light_theme(self):
        """应用浅色主题"""
        try:
            # 更新日志框样式
            if hasattr(self.main_window, 'log_text'):
                self.main_window.log_text.setStyleSheet("""
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
            self.main_window.github_label.setStyleSheet("color: #0066cc;")
            self.main_window.alipay_label.setStyleSheet("color: #0066cc;")
            self.main_window.about_text.setStyleSheet("""
                color: #666666;
                font-size: 12px;
                padding: 10px;
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 4px;
            """)
            self.main_window.stats_label.setStyleSheet("""
                color: #666666;
                font-size: 12px;
                padding: 5px;
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 4px;
            """)

            # 更新按钮样式
            self.main_window.single_import_btn.setStyleSheet("""
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

            # 更新移除按钮样式
            self.main_window.close_selected_btn.setStyleSheet("""
                QPushButton {
                    background-color: #fff5f5;
                    color: #dc3545;
                    border: 1px solid #dc3545;
                    padding: 8px 15px;
                    border-radius: 4px;
                    min-width: 100px;
                }
                QPushButton:hover {
                    background-color: #ffe5e5;
                    border: 1px solid #dc3545;
                }
                QPushButton:pressed {
                    background-color: #fff5f5;
                    border: 1px solid #dc3545;
                }
                QPushButton:disabled {
                    background-color: #fff5f5;
                    color: #dc3545;
                    border: 1px solid #dc3545;
                }
            """)

            self.main_window.close_all_btn.setStyleSheet("""
                QPushButton {
                    background-color: #fff5f5;
                    color: #dc3545;
                    border: 1px solid #dc3545;
                    padding: 8px 15px;
                    border-radius: 4px;
                    min-width: 100px;
                }
                QPushButton:hover {
                    background-color: #ffe5e5;
                    border: 1px solid #dc3545;
                }
                QPushButton:pressed {
                    background-color: #fff5f5;
                    border: 1px solid #dc3545;
                }
                QPushButton:disabled {
                    background-color: #fff5f5;
                    color: #dc3545;
                    border: 1px solid #dc3545;
                }
            """)

            self.main_window.batch_import_btn.setStyleSheet("""
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

            self.main_window.update_mod_btn.setStyleSheet("""
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

            self.main_window.batch_decrypt_btn.setStyleSheet("""
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

            # 更新表格样式
            self.main_window.window_list.setStyleSheet("""
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
            self.main_window.setStyleSheet("""
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
            self.main_window.logger.error(f"应用浅色主题时出错: {str(e)}")
            QMessageBox.critical(self.main_window, "错误", f"应用浅色主题时出错: {str(e)}") 