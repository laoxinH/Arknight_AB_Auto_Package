"""
捐赠窗口
"""
import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap

class DonateDialog(QDialog):
    """捐赠窗口类"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("支持开发者")
        self.setMinimumSize(700, 350)
        
        # 设置为非模态对话框
        self.setModal(False)
        
        self.setup_ui()
        
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
        self.theme_check_timer.start(100)  # 每秒检查一次
        
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
        
    def setup_ui(self):
        """设置用户界面"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 创建标题
        self.title_label = QLabel("感谢您的支持！")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                margin-bottom: 10px;
            }
        """)
        main_layout.addWidget(self.title_label)
        
        # 创建说明文字
        self.desc_label = QLabel("您的支持是我持续开发的动力")
        self.desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.desc_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
            }
        """)
        main_layout.addWidget(self.desc_label)
        
        # 创建付款码布局
        qr_layout = QHBoxLayout()
        qr_layout.setSpacing(30)
        qr_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 支付宝付款码
        alipay_layout = QVBoxLayout()
        alipay_layout.setSpacing(10)
        alipay_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.alipay_label = QLabel("支付宝")
        self.alipay_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        alipay_layout.addWidget(self.alipay_label)
        
        alipay_qr = QLabel()
        alipay_pixmap = QPixmap(os.path.join(os.path.dirname(os.path.dirname(__file__)), "resource", "payme", "alipay.jpg"))
        alipay_pixmap = alipay_pixmap.scaled(400, 400, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        alipay_qr.setPixmap(alipay_pixmap)
        alipay_qr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        alipay_layout.addWidget(alipay_qr)
        
        qr_layout.addLayout(alipay_layout)
        
        # 微信付款码
        wechat_layout = QVBoxLayout()
        wechat_layout.setSpacing(10)
        wechat_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.wechat_label = QLabel("微信")
        self.wechat_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        wechat_layout.addWidget(self.wechat_label)
        
        wechat_qr = QLabel()
        wechat_pixmap = QPixmap(os.path.join(os.path.dirname(os.path.dirname(__file__)), "resource", "payme", "wxpay.jpg"))
        wechat_pixmap = wechat_pixmap.scaled(400, 400, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        wechat_qr.setPixmap(wechat_pixmap)
        wechat_qr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        wechat_layout.addWidget(wechat_qr)
        
        qr_layout.addLayout(wechat_layout)
        
        main_layout.addLayout(qr_layout)
        
        # 添加底部说明
        self.bottom_label = QLabel("扫码支持作者，感谢您的慷慨！")
        self.bottom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bottom_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                margin-top: 20px;
            }
        """)
        main_layout.addWidget(self.bottom_label)
        
        self.setLayout(main_layout)
        
        # 设置窗口样式
        self.setStyleSheet("""
            QDialog {
                font-family: "Microsoft YaHei", "微软雅黑";
            }
        """) 