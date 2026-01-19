"""
JSON语法高亮器
"""
from PyQt6.QtCore import QRegularExpression
from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont

class JsonHighlighter(QSyntaxHighlighter):
    """JSON语法高亮器"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []

        # 字符串格式
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#008000"))  # 绿色
        self.highlighting_rules.append((
            QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"'), string_format
        ))

        # 数字格式
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#0000FF"))  # 蓝色
        self.highlighting_rules.append((
            QRegularExpression(r'\b[0-9]+\b'), number_format
        ))

        # 关键字格式
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#FF0000"))  # 红色
        keyword_format.setFontWeight(QFont.Weight.Bold)
        keywords = ["true", "false", "null"]
        for word in keywords:
            pattern = QRegularExpression(f"\\b{word}\\b")
            self.highlighting_rules.append((pattern, keyword_format))

    def highlightBlock(self, text):
        """应用高亮规则"""
        for pattern, format in self.highlighting_rules:
            expression = pattern
            match = expression.match(text)
            while match.hasMatch():
                start = match.capturedStart()
                length = match.capturedLength()
                self.setFormat(start, length, format)
                match = expression.match(text, start + length) 