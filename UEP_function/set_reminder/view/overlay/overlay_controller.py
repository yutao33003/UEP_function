# overlay_controller.py
from PyQt5.QtCore import QObject
from set_reminder.view.overlay.overlay_factory import OverlayFactory

class OverlayController(QObject):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.active_overlay = None

        self.main_window.installEventFilter(self)

    def show(self, overlay_name: str, **kwargs):
        
        if self.active_overlay and self.active_overlay.isVisible():
            self.active_overlay.close()
        overlay = OverlayFactory.create(overlay_name, **kwargs)
        overlay.show()
        self.active_overlay = overlay
        return overlay

    def eventFilter(self, obj, event):
        from PyQt5.QtCore import QEvent
        embedded = getattr(self, "embedded", False)  # 若沒有 embedded 屬性，預設 False

        if (
            not embedded
            and obj == self.parent()
            and event.type() == QEvent.Resize
        ):
            self.setGeometry(self.parent().rect())

        return False