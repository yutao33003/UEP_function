from PyQt5.QtCore import QObject, Qt
from set_reminder.view.overlay.overlay_factory import OverlayFactory

class OverlayController(QObject):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.active_overlay = None
        self.active_overlays = {}  # key=id, value=instance

    def show(self, overlay_name: str, close_previous: bool = True, embedded_con: bool = False, **kwargs):
        """顯示 overlay。"""

        from set_reminder.view.overlay.edit_overlay import EditTaskOverlay
        from set_reminder.view.overlay.gray_background_overlay import TypeTaskOverlay

        # ✅ 若已存在 edit_overlay，禁止再開一個
        if overlay_name == "edit_overlay":
            for ov in self.active_overlays.values():
                if ov and ov.isVisible() and ov.objectName() == "edit_overlay":
                    print("⚠️ 已存在一個 edit_overlay，禁止重複開啟。")
                    return ov  # 直接返回已存在 overlay

        # ✅ 若設定要關閉前一個 overlay
        if close_previous and self.active_overlay and self.active_overlay.isVisible():
            should_close = True

            # 🚫 若「新開的是 EditTaskOverlay」，而前一個是 TypeTaskOverlay，則不關閉父層
            if overlay_name == "edit_overlay" and isinstance(self.active_overlay, TypeTaskOverlay):
                should_close = False
                print("🔸 偵測到父層 TypeTaskOverlay，不關閉，只開 EditTaskOverlay")

            # 🚫 若「新開的是嵌入模式」，也不關閉任何父層
            if embedded_con:
                should_close = False

            if should_close:
                try:
                    self.active_overlay.close()
                except Exception:
                    pass

        # ✅ 建立新 overlay
        overlay = OverlayFactory.create(overlay_name, **kwargs)
        overlay.setObjectName(overlay_name)
        overlay.show()

        # ✅ 記錄 overlay
        self.active_overlays[id(overlay)] = overlay

        # 🔥 關閉時自動清理紀錄
        def _on_destroyed():
            self.active_overlays.pop(id(overlay), None)
            if self.active_overlay is overlay:
                self.active_overlay = None

        overlay.destroyed.connect(_on_destroyed)

        # ✅ 嵌入式 overlay 不影響 active_overlay（維持原邏輯）
        if not embedded_con:
            self.active_overlay = overlay

        return overlay

    # ✅ 對外提供一個乾淨屬性
    @property
    def current_overlay(self):
        return self.active_overlay
