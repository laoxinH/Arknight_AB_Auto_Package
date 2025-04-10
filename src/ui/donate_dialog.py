"""
捐赠窗口
"""
import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

class DonateDialog(QDialog):
    """捐赠窗口类"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("支持作者")
        self.setMinimumSize(800, 500)  # 调整窗口大小以适应更大的图片
        self.setup_ui()
        
    def setup_ui(self):
        """设置用户界面"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 创建标题
        title_label = QLabel("感谢您的支持！")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #333333;
                margin-bottom: 10px;
            }
        """)
        main_layout.addWidget(title_label)
        
        # 创建说明文字
        desc_label = QLabel("您的支持是我持续开发的动力")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 14px;
            }
        """)
        main_layout.addWidget(desc_label)
        
        # 创建付款码布局
        qr_layout = QHBoxLayout()
        qr_layout.setSpacing(30)
        qr_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 支付宝付款码
        alipay_layout = QVBoxLayout()
        alipay_layout.setSpacing(10)
        alipay_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        alipay_label = QLabel("支付宝")
        alipay_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        alipay_label.setStyleSheet("color: #333333;")
        alipay_layout.addWidget(alipay_label)
        
        alipay_qr = QLabel()
        alipay_pixmap = QPixmap(os.path.join(os.path.dirname(os.path.dirname(__file__)), "resource", "payme", "alipay.jpg"))
        # 调整图片大小
        alipay_pixmap = alipay_pixmap.scaled(400, 400, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        alipay_qr.setPixmap(alipay_pixmap)
        alipay_qr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        alipay_layout.addWidget(alipay_qr)
        
        qr_layout.addLayout(alipay_layout)
        
        # 微信付款码
        wechat_layout = QVBoxLayout()
        wechat_layout.setSpacing(10)
        wechat_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        wechat_label = QLabel("微信")
        wechat_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        wechat_label.setStyleSheet("color: #333333;")
        wechat_layout.addWidget(wechat_label)
        
        wechat_qr = QLabel()
        wechat_pixmap = QPixmap(os.path.join(os.path.dirname(os.path.dirname(__file__)), "resource", "payme", "wxpay.jpg"))
        # 调整图片大小
        wechat_pixmap = wechat_pixmap.scaled(400, 400, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        wechat_qr.setPixmap(wechat_pixmap)
        wechat_qr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        wechat_layout.addWidget(wechat_qr)
        
        qr_layout.addLayout(wechat_layout)
        
        main_layout.addLayout(qr_layout)
        
        # 添加底部说明
        bottom_label = QLabel("扫码支持作者，感谢您的慷慨！")
        bottom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bottom_label.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 12px;
                margin-top: 20px;
            }
        """)
        main_layout.addWidget(bottom_label)
        
        self.setLayout(main_layout)
        
        # 设置窗口样式
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QLabel {
                font-family: "Microsoft YaHei", "微软雅黑";
            }
        """) 