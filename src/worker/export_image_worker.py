"""
导出图片的worker线程
"""
import shutil

import numpy as np
from PIL import Image
from PyQt6.QtCore import QThread, pyqtSignal

class ExportImageWorker(QThread):
    """导出图片的worker线程"""
    progress = pyqtSignal(int)  # 进度信号
    finished = pyqtSignal()  # 完成信号
    error = pyqtSignal(str)  # 错误信号

    def __init__(self, source_path, target_path):
        super().__init__()
        self.source_path = source_path
        self.target_path = target_path

    def run(self):
        try:
            # 打开源图片
            img = Image.open(self.source_path).convert("RGBA")
            
            # 应用 straight_alpha 转换
            processed_img = self.straight_alpha(img)
            
            # 保存处理后的图片
            processed_img.save(self.target_path)
            
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

    def straight_alpha(self,img):
        """
        将预乘透明转换为直通透明

        Args:
            img: PIL图像对象

        Returns:
            PIL.Image: 处理后的图像
        """
        matrix = np.array(img)
        for row in matrix:
            for pixel in row:
                rgb = pixel[:-1]
                alpha = pixel[-1]
                if alpha != 0 and alpha != 255:
                    maxrgb = max(rgb)
                    if maxrgb > alpha:
                        for i in range(3):
                            pixel[i] = rgb[i] * 255 // maxrgb
                    else:
                        for i in range(3):
                            pixel[i] = rgb[i] * 255 // alpha
        return Image.fromarray(matrix)