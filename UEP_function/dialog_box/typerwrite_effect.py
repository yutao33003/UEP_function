from PyQt5.QtWidgets import  QLabel
from PyQt5.QtCore import QTimer

class TypewriterLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWordWrap(True)          # 讓長度超過會自動換行
        self.setStyleSheet("background: transparent; color: black; font-size: 12px; font-weight: bold; font-family: 'Courier New', monospace;")
        self._full_text = ""
        self._index = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._interval = 50             # 每個字的間隔（毫秒）
        self._running = False
        self.scroll_area = None

    def set_speed(self, ms_per_char: int):
        self._interval = max(1, ms_per_char)
        if self._running:
            self._timer.setInterval(self._interval)

    def set_speed_by_wpm(self, wpm: int = 141):
        """根據文章和 WPM 自動計算速度"""
        total_letter = len(self._full_text)
        word = self._full_text.split()
        avg_letters = total_letter / len(word) if word else 1
        ms_per_char = int(60000 / (wpm * avg_letters))
        self.set_speed(ms_per_char)

    def start(self, text: str):
        """開始打字；會從頭重新來。"""
        self._full_text = text
        self._index = 0
        self.setText("")
        self._running = True
        self._timer.start(self._interval)

    def skip_to_end(self):
        """直接跳到全文結尾。"""
        if not self._full_text:
            return
        self._timer.stop()
        self._running = False
        self._index = len(self._full_text)
        self.setText(self._full_text)

    def _tick(self):
        if self._index < len(self._full_text):
            self._index += 1
            self.setText(self._full_text[:self._index])

            if self.scroll_area:
                bar = self.scroll_area.verticalScrollBar()
                bar.setValue(bar.maximum())
        else:
            self._timer.stop()
            self._running = False