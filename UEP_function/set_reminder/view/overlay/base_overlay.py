# base_overlay.py
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt

from set_reminder.animate import gradually_exit_ani

class BaseOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._child_overlays = []
        # 常用 window flags（視情況調整）
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        # 你可以在此加入共用背景、動畫等
    def open_child_overlay(self, overlay_name, parent = None, **kwargs):
        """使用工廠在自己上面開一層 overlay，parent 設為 self（疊層）"""
        from set_reminder.view.overlay.overlay_factory import OverlayFactory  # 避免循環 import
        child = OverlayFactory.create(overlay_name, parent=parent or self, **kwargs)
        self._child_overlays.append(child)
        child.setParent(self)
        child.setWindowFlags(Qt.Widget)
        child.show()
        return child
    def closeEvent(self, event):
        # 關閉時確保子層也關閉
        for c in list(self._child_overlays):
            try:
                c.close()
            except Exception:
                pass
        self._child_overlays.clear()
        super().closeEvent(event)