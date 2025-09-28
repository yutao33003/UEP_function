import os
import time
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QSlider, QLabel, QLineEdit, QMessageBox, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QIcon, QPixmap
from music_controller.music_control import MusicPlayer

class MusicControlUI(QWidget):
    def __init__(self, file_path):
        super().__init__()
        self.setWindowTitle("Music Controller")
        self.setMinimumSize(400, 300)
        self.setStyleSheet("""
            QWidget {
                background: #f5f5f7;
                border-radius: 16px;
            }
            QPushButton {
                background: #e0e0e0;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #d1d1d6;
            }
            QLineEdit, QSlider {
                border-radius: 8px;
                background: #fff;
            }
        """)
        self.player = MusicPlayer(file_path)
        self.is_playing = False

        icon_dir = os.path.join(os.path.dirname(__file__), "image")
        self.play_icon = QIcon(os.path.join(icon_dir, "play.png"))
        self.pause_icon = QIcon(os.path.join(icon_dir, "pause.png"))
        self.next_icon = QIcon(os.path.join(icon_dir, "next.png"))
        self.back_icon = QIcon(os.path.join(icon_dir, "back.png"))
        self.loop_icon = QIcon(os.path.join(icon_dir, "loop.png"))
        self.search_icon = QIcon(os.path.join(icon_dir, "search.png"))
        self.music_notes_path = os.path.join(icon_dir, "music-notes.png")

        self.init_ui()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(200)  # 更即時

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        # 音樂圖示
        self.music_image = QLabel()
        self.music_image.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        pixmap = QPixmap(self.music_notes_path)
        if pixmap.isNull():
            self.music_image.setText("圖片載入失敗")
        else:
            self.music_image.setPixmap(pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.music_image.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.music_image)

        # 檔案路徑顯示
        self.song_path_label = QLabel(self.player.playlist[self.player.current_index])
        self.song_path_label.setStyleSheet("font-size: 12px; color: #333;")
        self.song_path_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.song_path_label)

        self.user_dragging = False

        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setMinimum(0)
        self.progress_slider.setMaximum(len(self.player.song))
        self.progress_slider.sliderPressed.connect(self.on_slider_pressed)
        self.progress_slider.sliderReleased.connect(self.on_slider_released)
        layout.addWidget(self.progress_slider)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.setAlignment(Qt.AlignCenter)

        # Back (前一首)
        self.back_btn = QPushButton()
        self.back_btn.setIcon(self.back_icon)
        self.back_btn.setFixedSize(QSize(25, 25))
        self.back_btn.clicked.connect(self.previous_song)
        btn_layout.addWidget(self.back_btn)

        # Play/Pause 最大
        self.play_pause_btn = QPushButton()
        self.play_pause_btn.setIcon(self.play_icon)
        self.play_pause_btn.setFixedSize(QSize(48, 48))
        self.play_pause_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.play_pause_btn.clicked.connect(self.toggle_play_pause)
        btn_layout.addWidget(self.play_pause_btn)

        # Next
        self.next_btn = QPushButton()
        self.next_btn.setIcon(self.next_icon)
        self.next_btn.setFixedSize(QSize(25, 25))
        self.next_btn.clicked.connect(self.next_song)
        btn_layout.addWidget(self.next_btn)

        # Loop 按鈕
        self.loop_btn = QPushButton()
        self.loop_btn.setCheckable(True)
        self.loop_btn.setIcon(self.loop_icon)
        self.loop_btn.setFixedSize(QSize(25, 25))
        self.loop_btn.clicked.connect(self.toggle_loop)
        btn_layout.addWidget(self.loop_btn)

        layout.addLayout(btn_layout)
        layout.setAlignment(Qt.AlignCenter)

        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜尋音樂...")
        search_layout.addWidget(self.search_input)
        self.search_btn = QPushButton()
        self.search_btn.setIcon(self.search_icon)
        self.search_btn.setFixedSize(QSize(25, 25))
        self.search_btn.clicked.connect(self.search_song)
        search_layout.addWidget(self.search_btn)
        layout.addLayout(search_layout)

        self.setLayout(layout)

    def on_slider_pressed(self):
        self.user_dragging = True

    def on_slider_released(self):
        self.user_dragging = False
        self.seek_position()

    def update_progress(self):
        if not self.user_dragging:
            self.progress_slider.setMaximum(int(len(self.player.song) / 1000))

            if self.player.play_start_time is not None and not self.player.paused:
                elapsed_time = int((time.time() - self.player.play_start_time))
                current_position = int(self.player.position/ 1000) + elapsed_time
            else:
                current_position = int(self.player.position / 1000)

            self.progress_slider.setValue(current_position)

            # 只有在 index 有效時才更新歌名
            if 0 <= self.player.current_index < len(self.player.playlist):
                self.song_path_label.setText(self.player.playlist[self.player.current_index])

            # 自動播放下一首
            if current_position >= len(self.player.song) and not self.player.paused:
                self.next_song()


    def seek_position(self):
        pos = self.progress_slider.value()
        self.player.jump(pos)

    def toggle_play_pause(self):
        if self.is_playing:
            self.player.pause()
            self.play_pause_btn.setIcon(self.play_icon)
            self.is_playing = False
        else:
            self.player.play()
            self.play_pause_btn.setIcon(self.pause_icon)
            self.is_playing = True

    def next_song(self):
        self.player.next_song()
        self.is_playing = True
        self.play_pause_btn.setIcon(self.pause_icon)

        self.progress_slider.setMaximum(int(len(self.player.song)/1000))
        self.progress_slider.setValue(0)
        self.song_path_label.setText(self.player.playlist[self.player.current_index])

    def previous_song(self):
        self.player.previous_song()
        self.is_playing = True
        self.play_pause_btn.setIcon(self.pause_icon)

        self.progress_slider.setMaximum(int(len(self.player.song)/1000))
        self.progress_slider.setValue(0)
        self.song_path_label.setText(self.player.playlist[self.player.current_index])

    def toggle_loop(self):
        self.player.toggle_loop()
        if self.loop_btn.isChecked():
            self.loop_btn.setStyleSheet("background: #b2f2a5;")
        else:
            self.loop_btn.setStyleSheet("")

    def search_song(self):
        keyword = self.search_input.text()
        if keyword:
            self.player.change_song(keyword)
            self.is_playing = True
            self.play_pause_btn.setIcon(self.pause_icon)

            self.progress_slider.setMaximum(int(len(self.player.song)/1000))
            self.progress_slider.setValue(0)
            self.song_path_label.setText(self.player.playlist[self.player.current_index])
        else:
            QMessageBox.warning(self, "提示", "請輸入搜尋關鍵字")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        btn_size = self.play_pause_btn.size()
        self.play_pause_btn.setIconSize(btn_size)
        pixmap = QPixmap(self.music_notes_path)
        if not pixmap.isNull():
            size = min(self.music_image.width(), self.music_image.height())
            self.music_image.setPixmap(pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation))



