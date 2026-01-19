"""
主题管理器
"""
import logging

from PyQt6.QtGui import QColor, QBrush
from PyQt6.QtWidgets import QWidget

class ThemeManager:
    """主题管理器"""
    def __init__(self):
        self.last_theme_is_dark = False
        self.logger = logging.getLogger(__name__)

    def is_dark_mode(self, widget: QWidget) -> bool:
        """检测系统是否处于深色模式"""
        try:
            palette = widget.main_window.palette()
            return palette.window().color().lightness() < 128
        except Exception as e:
            self.logger.error(f"检测主题模式时出错: {str(e)}")
            return False

    def apply_dark_theme(self, widget: QWidget):
        """应用深色主题"""
        try:
            # 设置全局深色主题样式
            widget.setStyleSheet("""
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
            """)

            # 更新搜索框样式
            if hasattr(widget, 'search_input'):
                widget.search_input.setStyleSheet("""
                    QLineEdit {
                        padding: 5px;
                        border: 1px solid #3c3c3c;
                        border-radius: 4px;
                        background-color: #2d2d2d;
                        color: #ffffff;
                    }
                    QLineEdit:focus {
                        border: 1px solid #4a86e8;
                    }
                """)

            # 更新音频预览区域样式
            if hasattr(widget, 'audio_preview'):
                widget.audio_preview.setStyleSheet("""
                    QFrame {
                        background-color: #2d2d2d;
                        border: 1px solid #3c3c3c;
                        border-radius: 4px;
                    }
                    QLabel {
                        color: #cccccc;
                        font-size: 14px;
                        padding: 10px;
                    }
                    QPushButton {
                        background-color: #2d2d2d;
                        color: #ffffff;
                        border: 1px solid #3c3c3c;
                        border-radius: 30px;
                        padding: 0;
                    }
                    QPushButton:hover {
                        background-color: #3d3d3d;
                        border: 1px solid #4c4c4c;
                    }
                    QPushButton:pressed {
                        background-color: #2d2d2d;
                        border: 1px solid #3c3c3c;
                    }
                    QSlider::groove:horizontal {
                        border: 1px solid #3c3c3c;
                        height: 8px;
                        background: #2d2d2d;
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

            # 更新编辑按钮容器样式
            if hasattr(widget, 'edit_buttons_container'):
                widget.edit_buttons_container.setStyleSheet("""
                    QWidget {
                        background-color: transparent;
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
                    QPushButton:disabled {
                        background-color: #1a1a1a;
                        color: #666666;
                        border: 1px solid #2c2c2c;
                    }
                """)

            # 更新提示区域样式
            if hasattr(widget, 'tips_label'):
                widget.tips_label.setStyleSheet("""
                    QLabel {
                        color: #cccccc;
                        font-size: 12px;
                        padding: 5px;
                        background-color: #2d2d2d;
                        border: 1px solid #3c3c3c;
                        border-radius: 4px;
                    }
                """)

            # 更新表格样式
            if hasattr(widget, 'file_table'):
                widget.file_table.setStyleSheet("""
                    QTableWidget {
                        background-color: #1e1e1e;
                        border: 1px solid #3c3c3c;
                        border-radius: 4px;
                        gridline-color: #3c3c3c;
                        color: #ffffff;
                    }
                    QTableWidget::item {
                        padding: 5px;
                        border-bottom: 1px solid #3c3c3c;
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

            # 更新预览区域样式
            if hasattr(widget, 'image_preview'):
                widget.image_preview.setStyleSheet("""
                    QLabel {
                        background-color: #2d2d2d;
                        border: 1px solid #3c3c3c;
                        border-radius: 4px;
                        font-size: 14px;
                        color: #cccccc;
                    }
                """)

            # 更新滚动区域样式
            if hasattr(widget, 'scroll_area'):
                widget.scroll_area.setStyleSheet("""
                    QScrollArea {
                        border: none;
                        background-color: #1e1e1e;
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

            # 更新图片信息标签样式
            if hasattr(widget, 'image_info_label'):
                widget.image_info_label.setStyleSheet("""
                    QLabel {
                        background-color: #2d2d2d;
                        color: #f8f9fa;
                        border: 1px solid #3c3c3c;
                        padding: 8px;
                        margin-bottom: 8px;
                        border-radius: 4px;
                        font-size: 12px;
                    }
                """)

            # 更新按钮样式
            if hasattr(widget, 'select_all_btn'):
                widget.select_all_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #2d2d2d;
                        color: #ffffff;
                        border: 1px solid #3c3c3c;
                        padding: 5px 10px;
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
                """)

            if hasattr(widget, 'deselect_all_btn'):
                widget.deselect_all_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #2d2d2d;
                        color: #ffffff;
                        border: 1px solid #3c3c3c;
                        padding: 5px 10px;
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
                """)

            if hasattr(widget, 'export_ab_btn'):
                widget.export_ab_btn.setStyleSheet("""
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
                    QPushButton:disabled {
                        background-color: #1a1a1a;
                        color: #666666;
                        border: 1px solid #2c2c2c;
                    }
                """)

            if hasattr(widget, 'export_lab_btn'):
                widget.export_lab_btn.setStyleSheet("""
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
                    QPushButton:disabled {
                        background-color: #1a1a1a;
                        color: #666666;
                        border: 1px solid #2c2c2c;
                    }
                """)

            if hasattr(widget, 'confirm_btn'):
                widget.confirm_btn.setStyleSheet("""
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
                    QPushButton:disabled {
                        background-color: #1a1a1a;
                        color: #666666;
                        border: 1px solid #2c2c2c;
                    }
                """)

            # 更新文本预览样式
            if hasattr(widget, 'preview_text'):
                widget.preview_text.setStyleSheet("""
                    QTextEdit {
                        background-color: #2d2d2d;
                        color: #ffffff;
                        border: 1px solid #3c3c3c;
                        border-radius: 4px;
                        padding: 8px;
                    }
                """)

        except Exception as e:
            logging.getLogger(__name__).error(f"应用深色主题时出错: {str(e)}")

    def apply_light_theme(self, widget: QWidget):
        """应用浅色主题"""
        try:
            # 设置全局浅色主题样式
            widget.setStyleSheet("""
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
            """)

            # 更新音频预览区域样式
            if hasattr(widget, 'audio_preview'):
                widget.audio_preview.setStyleSheet("""
                    QFrame {
                        background-color: #f8f8f8;
                        border: 1px solid #dddddd;
                        border-radius: 4px;
                    }
                    QLabel {
                        color: #666666;
                        font-size: 14px;
                        padding: 10px;
                    }
                    QPushButton {
                        background-color: #4a86e8;
                        color: white;
                        border: none;
                        border-radius: 30px;
                        padding: 0;
                    }
                    QPushButton:hover {
                        background-color: #3a76d8;
                    }
                    QPushButton:pressed {
                        background-color: #2a66c8;
                    }
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

            # 更新编辑按钮容器样式
            if hasattr(widget, 'edit_buttons_container'):
                widget.edit_buttons_container.setStyleSheet("""
                    QWidget {
                        background-color: transparent;
                    }
                    QPushButton {
                        background-color: #4a86e8;
                        color: white;
                        border: none;
                        padding: 8px 15px;
                        border-radius: 4px;
                    }
                    QPushButton:hover {
                        background-color: #3a76d8;
                    }
                    QPushButton:pressed {
                        background-color: #2a66c8;
                    }
                    QPushButton:disabled {
                        background-color: #cccccc;
                    }
                """)

            # 更新搜索框样式
            if hasattr(widget, 'search_input'):
                widget.search_input.setStyleSheet("""
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

            # 更新提示区域样式
            if hasattr(widget, 'tips_label'):
                widget.tips_label.setStyleSheet("""
                    QLabel {
                        color: #666666;
                        font-size: 12px;
                        padding: 5px;
                        background-color: #f8f9fa;
                        border: 1px solid #e9ecef;
                        border-radius: 4px;
                    }
                """)

            # 更新表格样式
            if hasattr(widget, 'file_table'):
                widget.file_table.setStyleSheet("""
                    QTableWidget {
                        border: 1px solid #cccccc;
                        border-radius: 4px;
                        background-color: white;
                        color: #000000;
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
                        color: #000000;
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

            # 更新预览区域样式
            if hasattr(widget, 'image_preview'):
                widget.image_preview.setStyleSheet("""
                    QLabel {
                        background-color: #f8f8f8;
                        border: 1px solid #dddddd;
                        border-radius: 4px;
                        font-size: 14px;
                        color: #666666;
                    }
                """)

            # 更新滚动区域样式
            if hasattr(widget, 'scroll_area'):
                widget.scroll_area.setStyleSheet("""
                    QScrollArea {
                        border: none;
                        background-color: #f8f8f8;
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

            # 更新图片信息标签样式
            if hasattr(widget, 'image_info_label'):
                widget.image_info_label.setStyleSheet("""
                    QLabel {
                        background-color: #f8f8f8;
                        color: #666666;
                        padding: 8px;
                        margin-bottom: 8px;
                        border: 1px solid #dddddd;
                        border-radius: 4px;
                        font-size: 12px;
                    }
                """)

            # 更新按钮样式
            if hasattr(widget, 'select_all_btn'):
                widget.select_all_btn.setStyleSheet("""
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

            if hasattr(widget, 'deselect_all_btn'):
                widget.deselect_all_btn.setStyleSheet("""
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

            if hasattr(widget, 'export_ab_btn'):
                widget.export_ab_btn.setStyleSheet("""
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
                    QPushButton:disabled {
                        background-color: #cccccc;
                    }
                """)

            if hasattr(widget, 'export_lab_btn'):
                widget.export_lab_btn.setStyleSheet("""
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
                    QPushButton:disabled {
                        background-color: #cccccc;
                    }
                """)

            if hasattr(widget, 'confirm_btn'):
                widget.confirm_btn.setStyleSheet("""
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
                    QPushButton:disabled {
                        background-color: #cccccc;
                    }
                """)

            # 更新文本预览样式
            if hasattr(widget, 'preview_text'):
                widget.preview_text.setStyleSheet("""
                    QTextEdit {
                        background-color: #f8f9fa;
                        color: #333333;
                        border: 1px solid #cccccc;
                        border-radius: 4px;
                        padding: 8px;
                    }
                """)

        except Exception as e:
            self.logger.error(f"应用浅色主题时出错: {str(e)}")

    def get_replaced_file_style(self, is_dark: bool) -> tuple:
        """获取替换文件的样式"""
        if is_dark:
            return QBrush(QColor("#1a3a1a")), QBrush(QColor("#4caf50"))  # 深色主题下的深绿色背景和亮绿色文本
        else:
            return QBrush(QColor("#e8f5e9")), QBrush(QColor("#2e7d32"))  # 浅色主题下的浅绿色背景和深绿色文本 