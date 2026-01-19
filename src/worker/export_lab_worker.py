import logging
import os
import shutil
import tempfile

from PyQt6.QtCore import pyqtSignal, QThread

from src.core.asset_extractor import AssetExtractor
from src.utils.zip_utils import compress_to_zip
from src.utils.image_zip import ImageZip


class ExportLabWorker(QThread):
    """导出AB资源包工作线程"""
    progress = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, ab_name, source_file, zip_output_dir, preview_images, readme_txt, mod_type, replace_files,
                 compression_format="ZIP", use_image_zip=False, image_zip_path=None, password=None):
        super().__init__()
        self.temp_dir = None
        self.source_file = source_file
        # self.output_dir = output_dir
        self.replace_files = replace_files
        self.zip_output_dir = zip_output_dir
        self.preview_images = preview_images
        self.readme_txt = readme_txt
        self.mod_type = mod_type
        self.ab_name = ab_name
        self.compression_format = compression_format
        self.use_image_zip = use_image_zip
        self.image_zip_path = image_zip_path
        self.password = password
        # 配置日志
        self.logger = logging.getLogger(__name__)

    def run(self):
        try:
            self.temp_dir = tempfile.mkdtemp(prefix='arknight_export_lab_')
            self.logger.info(f"创建临时目录: {self.temp_dir}")
            #创建mod_type子目录
            mod_type_dir = os.path.join(self.temp_dir, self.mod_type)
            # shutil创建目录
            os.makedirs(mod_type_dir, exist_ok=True)
            #将preview_images和readme_txt添加到临时目录
            if self.preview_images:
                for image in self.preview_images:
                    self.progress.emit(f"正在添加预览图")
                    # 将图片复制到临时目录
                    shutil.copy(image, mod_type_dir)
            # 在mod_type_dir目录下创建readme.txt文件
            if self.readme_txt:
                self.progress.emit(f"正在添加说明文件")
                readme_path = os.path.join(mod_type_dir, "readme.md")
                with open(readme_path, "wb") as f:
                    f.write(self.readme_txt.encode("utf-8"))

            self.progress.emit(f"正在导出AB资源包: {self.source_file}")
            extractor = AssetExtractor()

            # 导出AB资源包
            success_ab = extractor.export_ab(
                self.source_file,
                mod_type_dir,
                self.replace_files
            )

            if success_ab:
                self.progress.emit("导出AB完成！")
                # 导出LAB压缩包
                success_lab = compress_to_zip(
                    mod_type_dir,
                    self.zip_output_dir,
                    compression_format=self.compression_format,
                    password=self.password
                )
                if success_lab:
                    # 如果启用了图种功能且压缩格式为ZIP
                    if self.use_image_zip and self.compression_format == "ZIP" and self.image_zip_path:
                        self.progress.emit("正在创建图种文件...")

                        # 创建图种文件
                        if ImageZip.create_image_zip(self.zip_output_dir, self.image_zip_path):
                            # 删除临时文件
                            self.progress.emit("图种文件创建成功！")
                        else:
                            self.error.emit("创建图种文件失败")
                            return
                    
                    # 删除临时目录
                    shutil.rmtree(self.temp_dir)
                    self.progress.emit(f"导出LAB压缩包完成！")
                    self.finished.emit()
                else:
                    self.error.emit("压缩失败，请查看日志")
            else:
                self.error.emit("导出失败，请查看日志")
        except Exception as e:
            # 输出日志
            self.logger.error(f"导出LAB资源包时出错: {str(e)}")
            self.error.emit(str(e))
        finally:
            # 删除临时目录
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                self.logger.info(f"删除临时目录: {self.temp_dir}")