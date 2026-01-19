"""
预览管理器
"""
import os
import logging
import json
from PyQt6.QtWidgets import (QLabel, QTextEdit, QPushButton, QFrame, QHBoxLayout, 
                            QVBoxLayout, QSlider, QApplication)
from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtGui import QPixmap, QImage, QIcon, QFont
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

class PreviewManager:
    """预览管理器"""
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.is_loading = False
        self.current_preview_path = None
        self.last_position = 0
        self.is_dragging = False

        # 初始化音频播放器
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.positionChanged.connect(self.update_audio_progress)
        self.media_player.durationChanged.connect(self.update_audio_duration)
        self.media_player.playbackStateChanged.connect(self.update_play_button)
        self.media_player.errorOccurred.connect(self.handle_media_error)

        # 创建定时器来更新位置
        self.position_update_timer = QTimer()
        self.position_update_timer.setInterval(200)  # 增加更新间隔到200ms
        self.position_update_timer.timeout.connect(self.update_position)

    def setup_audio_ui(self, widget):
        """设置音频UI控件"""
        self.audio_preview = widget.audio_preview
        self.audio_info = widget.audio_info
        self.play_button = widget.play_button
        self.audio_progress = widget.audio_progress
        self.current_time = widget.current_time
        self.total_time = widget.total_time

        # 连接信号
        self.play_button.clicked.connect(self.toggle_audio_playback)
        self.audio_progress.sliderPressed.connect(self.on_progress_slider_pressed)
        self.audio_progress.sliderReleased.connect(self.on_progress_slider_released)
        self.audio_progress.valueChanged.connect(self.on_progress_changed)

    def update_preview(self, name, file_type, path, widget):
        """更新预览内容"""
        try:
            # 如果正在加载其他文件，取消当前加载
            if self.is_loading and self.current_preview_path != path:
                self.is_loading = False
                widget.preview_text.clear()
                QApplication.processEvents()

            # 设置当前预览文件路径
            self.current_preview_path = path

            # 默认隐藏所有预览组件
            widget.image_preview.setVisible(False)
            widget.preview_text.setVisible(False)
            widget.audio_preview.setVisible(False)
            widget.edit_buttons_container.setVisible(False)
            widget.image_info_label.setVisible(False)

            # 获取文件信息
            file_size = os.path.getsize(path) if os.path.exists(path) else 0
            size_str = self.format_file_size(file_size)

            if not widget.preview_text.isReadOnly():
                self.toggle_edit_mode(widget)

            if file_type == "Texture2D":
                self._preview_image(name, path, size_str, widget)
            elif file_type == "TextAsset":
                self._preview_text(name, path, size_str, widget)
            elif file_type == "AudioClip":
                self._preview_audio(name, path, size_str, widget)
            elif file_type == "MonoBehaviour":
                self._preview_mono_behaviour(name, path, size_str, widget)
            else:
                self._preview_other(name, file_type, size_str, widget)

        except Exception as e:
            self.logger.error(f"更新预览时出错: {str(e)}")
            widget.image_preview.setText(f"预览出错: {str(e)}")
            widget.image_info_label.setVisible(False)
            self.is_loading = False

    def _preview_image(self, name, path, size_str, widget):
        """预览图片"""
        widget.image_preview.setVisible(True)
        widget.image_info_label.setVisible(True)

        # 加载图片
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            # 获取图片信息
            image = QImage(path)
            width = image.width()
            height = image.height()
            format = image.format()
            depth = image.depth()

            # 获取色彩空间信息
            color_space = "RGB" if format in [QImage.Format.Format_RGB32, QImage.Format.Format_ARGB32] else "RGBA"

            # 设置图片信息文本
            info_text = f"文件名: {name}\n"
            info_text += f"分辨率: {width}x{height}\n"
            info_text += f"文件大小: {size_str}\n"
            info_text += f"色彩深度: {depth}位\n"
            info_text += f"色彩空间: {color_space}\n"
            info_text += f"格式: {format}"

            widget.image_info_label.setText(info_text)
            widget.image_info_label.setFixedHeight(125)

            # 缩放图片以适应预览区域
            scaled_pixmap = pixmap.scaled(
                widget.image_preview.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            widget.image_preview.setPixmap(scaled_pixmap)
        else:
            widget.image_preview.setText("无法加载图片")
            widget.image_info_label.setVisible(False)

    def _preview_text(self, name, path, size_str, widget):
        """预览文本"""
        if path.lower().endswith('.json'):
            self._preview_json(name, path, size_str, widget)
        else:
            self._preview_plain_text(name, path, size_str, widget)

    def _preview_json(self, name, path, size_str, widget):
        """预览JSON文件"""
        widget.preview_text.setVisible(True)
        widget.preview_text.clear()
        widget.edit_buttons_container.setVisible(True)
        widget.image_info_label.setVisible(True)

        try:
            # 使用分块读取方式处理大文件
            content = ""
            chunk_size = 1024 * 10  # 1MB的块大小
            self.is_loading = True
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                while self.is_loading:  # 检查是否应该继续加载
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    content += chunk
                    QApplication.processEvents()  # 允许UI更新

            # 对于大JSON文件，使用流式处理
            try:
                # 尝试格式化JSON
                json_obj = json.loads(content)
                formatted_json = json.dumps(json_obj, indent=2, ensure_ascii=False)

                # 分块设置文本内容
                widget.preview_text.clear()
                chunk_size = 1024 * 10  # 1MB的块大小
                for i in range(0, len(formatted_json), chunk_size):
                    if not self.is_loading:  # 检查是否应该继续加载
                        break
                    chunk = formatted_json[i:i + chunk_size]
                    widget.preview_text.append(chunk)
                    QApplication.processEvents()  # 允许UI更新

                widget.preview_text.setReadOnly(True)
            except json.JSONDecodeError:
                # 如果JSON解析失败，直接显示原始内容
                widget.preview_text.setText(content)

            # 设置文件信息
            info_text = f"文件名: {name}\n"
            info_text += f"类型: TextAsset (JSON)\n"
            info_text += f"文件大小: {size_str}\n"
            info_text += f"编码: UTF-8"

            widget.image_info_label.setText(info_text)
            widget.image_info_label.setFixedHeight(90)

        except Exception as e:
            widget.preview_text.setText(f"读取JSON文件失败: {str(e)}")
        finally:
            self.is_loading = False

    def _preview_plain_text(self, name, path, size_str, widget):
        """预览普通文本文件"""
        widget.preview_text.setVisible(True)
        widget.image_info_label.setVisible(True)

        if os.path.isfile(path):
            # 使用分块读取方式处理大文件
            widget.preview_text.clear()
            chunk_size = 1024 * 10  # 1MB的块大小
            self.is_loading = True
            with open(path, 'rb') as f:
                while self.is_loading:  # 检查是否应该继续加载
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    try:
                        # 尝试使用UTF-8解码
                        text = chunk.decode('utf-8', errors='replace')
                    except UnicodeDecodeError:
                        # 如果UTF-8解码失败，尝试其他编码
                        try:
                            text = chunk.decode('gbk', errors='replace')
                        except UnicodeDecodeError:
                            text = chunk.decode('latin1', errors='replace')

                    widget.preview_text.append(text)
                    QApplication.processEvents()  # 允许UI更新
        else:
            widget.preview_text.setText(path)

        # 设置文件信息
        info_text = f"文件名: {name}\n"
        info_text += f"类型: TextAsset\n"
        info_text += f"文件大小: {size_str}\n"
        info_text += f"编码: UTF-8"

        widget.image_info_label.setText(info_text)
        widget.image_info_label.setFixedHeight(90)
        self.is_loading = False

    def _preview_audio(self, name, path, size_str, widget):
        """预览音频文件"""
        self.setup_audio_ui(widget)  # 设置音频UI控件
        widget.audio_preview.setVisible(True)
        widget.image_info_label.setVisible(True)

        # 设置文件信息
        info_text = f"文件名: {name}\n"
        info_text += f"类型: AudioClip\n"
        info_text += f"文件大小: {size_str}"

        widget.image_info_label.setText(info_text)
        widget.image_info_label.setFixedHeight(90)
        widget.audio_info.setText(f"音频文件: {name}")
        self.media_player.setSource(QUrl.fromLocalFile(path))
        widget.audio_progress.setValue(0)
        self.update_play_button(QMediaPlayer.PlaybackState.StoppedState)
        self.position_update_timer.start()

    def _preview_mono_behaviour(self, name, path, size_str, widget):
        """预览MonoBehaviour文件"""
        if path.lower().endswith('.json'):
            widget.preview_text.setVisible(True)
            widget.edit_buttons_container.setVisible(True)
            widget.image_info_label.setVisible(True)
            widget.edit_btn.setVisible(True)

            try:
                # 使用分块读取方式处理大文件
                content = ""
                chunk_size = 1024 * 10  # 1MB的块大小
                self.is_loading = True
                with open(path, 'r', encoding='utf-8', errors='replace') as f:
                    while self.is_loading:  # 检查是否应该继续加载
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        content += chunk
                        QApplication.processEvents()  # 允许UI更新

                # 对于大JSON文件，使用流式处理
                try:
                    # 尝试格式化JSON
                    json_obj = json.loads(content)
                    formatted_json = json.dumps(json_obj, indent=2, ensure_ascii=False)

                    # 分块设置文本内容
                    widget.preview_text.clear()
                    chunk_size = 1024 * 10  # 1MB的块大小
                    for i in range(0, len(formatted_json), chunk_size):
                        if not self.is_loading:  # 检查是否应该继续加载
                            break
                        chunk = formatted_json[i:i + chunk_size]
                        widget.preview_text.append(chunk)
                        QApplication.processEvents()  # 允许UI更新
                except json.JSONDecodeError:
                    # 如果JSON解析失败，直接显示原始内容
                    widget.preview_text.setText(content)

                # 设置文件信息
                info_text = f"文件名: {name}\n"
                info_text += f"类型: TextAsset (JSON)\n"
                info_text += f"文件大小: {size_str}\n"
                info_text += f"编码: UTF-8"

                widget.image_info_label.setText(info_text)
                widget.image_info_label.setFixedHeight(90)

            except Exception as e:
                widget.preview_text.setText(f"读取JSON文件失败: {str(e)}")
            finally:
                self.is_loading = False

    def _preview_other(self, name, file_type, size_str, widget):
        """预览其他类型文件"""
        widget.image_preview.setVisible(True)
        widget.image_info_label.setVisible(True)

        # 设置文件信息
        info_text = f"文件名: {name}\n"
        info_text += f"类型: {file_type}\n"
        info_text += f"文件大小: {size_str}"

        widget.image_info_label.setText(info_text)
        widget.image_info_label.setFixedHeight(90)
        widget.image_preview.setText(f"文件: {name}\n类型: {file_type}")

    def toggle_edit_mode(self, widget):
        """切换编辑模式"""
        is_readonly = widget.preview_text.isReadOnly()
        widget.preview_text.setReadOnly(not is_readonly)
        widget.edit_btn.setText("退出编辑" if is_readonly else "编辑")
        widget.save_btn.setVisible(is_readonly)

    def toggle_audio_playback(self):
        """切换音频播放状态"""
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
            self.position_update_timer.stop()
        else:
            self.media_player.play()
            self.position_update_timer.start()

    def update_audio_progress(self, position):
        """更新音频进度条"""
        if not self.is_dragging and self.media_player.duration() > 0:
            self.last_position = position
            progress = int((position / self.media_player.duration()) * 100)
            self.audio_progress.setValue(progress)
            self.current_time.setText(self.format_time(position))

    def update_audio_duration(self, duration):
        """更新音频总时长"""
        self.audio_progress.setMaximum(100)
        # 更新总时长
        self.total_time.setText(self.format_time(duration))

    def update_play_button(self, state):
        """更新播放按钮状态"""
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_button.setIcon(QIcon.fromTheme("media-playback-pause"))
            self.position_update_timer.start()
        else:
            self.play_button.setIcon(QIcon.fromTheme("media-playback-start"))
            self.position_update_timer.stop()

    def handle_media_error(self, error, error_string):
        """处理媒体错误"""
        self.logger.error(f"媒体播放错误: {error_string}")
        self.image_preview.setText(f"音频播放错误: {error_string}")

    def update_position(self):
        """定时更新位置"""
        if not self.is_dragging and self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.update_audio_progress(self.media_player.position())

    def on_progress_changed(self, value):
        """处理进度条值改变"""
        if self.media_player.duration() > 0 and self.is_dragging:
            position = int((value / 100) * self.media_player.duration())
            self.media_player.setPosition(position)
            self.current_time.setText(self.format_time(position))

    def on_progress_slider_pressed(self):
        """进度条按下时"""
        self.is_dragging = True
        self.position_update_timer.stop()

    def on_progress_slider_released(self):
        """进度条释放时"""
        self.is_dragging = False
        position = int((self.audio_progress.value() / 100) * self.media_player.duration())
        self.media_player.setPosition(position)
        self.position_update_timer.start()

    def format_time(self, milliseconds):
        """格式化时间显示"""
        seconds = int(milliseconds / 1000)
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    def format_file_size(self, size_in_bytes):
        """格式化文件大小显示"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_in_bytes < 1024.0:
                return f"{size_in_bytes:.2f} {unit}"
            size_in_bytes /= 1024.0
        return f"{size_in_bytes:.2f} TB"

    def cleanup(self):
        """清理资源"""
        try:
            # 停止音频播放并释放资源
            self.position_update_timer.stop()  # 停止定时器
            if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                self.media_player.stop()
            self.media_player.setSource(QUrl())  # 清除音频源
            self.media_player.setAudioOutput(None)  # 断开音频输出
            self.audio_output = None  # 释放音频输出
            self.media_player = None  # 释放媒体播放器
        except Exception as e:
            self.logger.error(f"清理预览资源时出错: {str(e)}") 