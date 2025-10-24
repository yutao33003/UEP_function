# overlay_controller.py
from set_reminder.view.overlay.overlay_factory import OverlayFactory

class OverlayController:
    def __init__(self, main_window):
        self.main_window = main_window
        self.active_overlay = None

    def show(self, overlay_name: str, **kwargs):
        if self.active_overlay and self.active_overlay.isVisible():
            self.active_overlay.close()
        overlay = OverlayFactory.create(overlay_name, **kwargs)
        overlay.show()
        self.active_overlay = overlay
        return overlay