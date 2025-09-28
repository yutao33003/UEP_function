from PyQt5.QtWidgets import QApplication, QLabel, QScrollArea, QWidget
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
import threading
import sys
import os
import PyQt5
from dialog_box.typerwrite_effect import TypewriterLabel

os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = os.path.join(
    os.path.dirname(PyQt5.__file__),
    "Qt5",  # 注意你目前 DLL 在 Qt5
    "plugins",
    "platforms"
)

class DialogBoxWindow(QWidget):
    next_text_label = pyqtSignal(str)
    def __init__(self, parent = None):
        super().__init__()
        self.setWindowTitle("對話框視窗")
        self.setFixedSize(150, 160)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setMouseTracking(True)
        self._drag_active = False
        self._drag_position = None

        # 對話框動畫
        self.dialog_label = QLabel(self)
        self.dialog_label.setGeometry(0, 0, 150, 160)

        self.text_label = TypewriterLabel(self)
        self.text_label.setGeometry(63, 40, 70, 55)
        self.text_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        scroll = QScrollArea(self)
        scroll.setGeometry(65, 40, 70, 55)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")  # 保持透明
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)      # 只要垂直捲動
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)        # 也可以關掉卷軸 UI
        scroll.setWidget(self.text_label)
        self.text_label.scroll_area = scroll

        self.current_frame = 0
        base_path = os.path.join(os.path.dirname(__file__), "dialog_ani")
        self.dialog_frames = []
        for i in range(70):
            path = os.path.join(base_path, f"dialog_box_{i}.png")
            pixmap = QPixmap(path)
            scaled_pixmap = pixmap.scaled(150, 160, Qt.KeepAspectRatio)
            if pixmap.isNull():
                print(f"找不到圖片: {path}")
            self.dialog_frames.append(scaled_pixmap)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(50)  

        self.next_text_label.connect(self.text_label.start)
        # 背景執行緒讀輸入
        threading.Thread(target=self.update_text_thread, daemon=True).start()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_active = True
            self._drag_position = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._drag_active and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_position)

    def mouseReleaseEvent(self, event):
        self._drag_active = False

    def update_frame(self):
        self.dialog_label.setPixmap(self.dialog_frames[self.current_frame])
        self.current_frame = (self.current_frame + 1) % len(self.dialog_frames)

    def update_text_thread(self):
        while True:
            text = input("輸入文字：")
            # 自動每 10 字元插入換行
            wrapped_text = self.wrap_text(text)
            self.next_text_label.emit(wrapped_text)

    def wrap_text(self,text, width = 10):
        words = text.split(' ')
        lines = []
        current_line = ""
        for word in words:
            if (len(word) > width):
                if current_line:
                    lines.append(current_line)
                for i in range(0, len(word), width):
                    lines.append(word[i:i+width])

            else:
                if not current_line:
                    current_line = word
                elif len(current_line) + 1 + len(word)  <= width:
                    current_line += " " + word 
                else:
                    lines.append(current_line)
                    current_line = word

        if current_line:
            lines.append(current_line)
        return "\n".join(lines)

def start_dialog_box():
    app = QApplication(sys.argv)
    window = DialogBoxWindow()
    window.show()
    sys.exit(app.exec_())

