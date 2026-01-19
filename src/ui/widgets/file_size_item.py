"""
文件大小排序项
"""
from PyQt6.QtWidgets import QTableWidgetItem

class FileSizeItem(QTableWidgetItem):
    """自定义文件大小排序项"""
    def __init__(self, text, size):
        super().__init__(text)
        self.size = size

    def __lt__(self, other):
        return self.size < other.size

    def __gt__(self, other):
        return self.size > other.size

    def __eq__(self, other):
        return self.size == other.size

    def __le__(self, other):
        return self.size <= other.size

    def __ge__(self, other):
        return self.size >= other.size

    def __ne__(self, other):
        return self.size != other.size 