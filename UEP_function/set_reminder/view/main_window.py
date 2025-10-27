import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget
from set_reminder.adapters.event_adapter import EventAdapter
from set_reminder.animate import gradually_enter_ani, slide_stack
from set_reminder.view import sorting_ui, today_list_ui
from set_reminder.calendar import calendar_ui
from set_reminder.json_repository.record_controller import TaskController, TypeController
from set_reminder.view.overlay.edit_overlay import ConfirmDialog, EditTaskOverlay
from set_reminder.view.overlay.gray_background_overlay import AddTypeCard, TypeTaskOverlay
from set_reminder.view.overlay.overlay_controller import OverlayController
from set_reminder.view.overlay.overlay_factory import OverlayFactory


class ReminderMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(600, 500)
        self.setWindowTitle("Reminder")

        self.task_controller = TaskController()
        self.type_controller = TypeController()
        self.event_adapter = EventAdapter(self.task_controller)
        self.overlay_controller = OverlayController(self)
        self.overlay_factory = OverlayFactory

        self.overlay_factory.register("task_overlay", TypeTaskOverlay)
        self.overlay_factory.register("edit_overlay", EditTaskOverlay)
        self.overlay_factory.register("confirm_overlay", ConfirmDialog)
        self.overlay_factory.register("type_edit_overlay", AddTypeCard)

        self.stack = QStackedWidget()
        self.sorting_widget = sorting_ui.SortingUI(self.event_adapter, self.overlay_controller, self.type_controller)
        self.today_list_widget = today_list_ui.TodayListUI(self.event_adapter, self.overlay_controller, self.type_controller)
        self.calendar_widget = calendar_ui.CalendarUI(self.event_adapter, self.overlay_controller, self.type_controller)
        self.stack.addWidget(self.today_list_widget)
        self.stack.addWidget(self.sorting_widget)
        self.stack.addWidget(self.calendar_widget)
        self.stack.setCurrentIndex(0)

        pixmap_path = os.path.join(os.path.dirname(__file__), "image","background.png")
        self.stack.setStyleSheet(f"""
            QMainWindow {{
                border-image: url({pixmap_path}) 0 0 0 0 stretch stretch;
            }}
        """)
        self.today_list_widget.switch_page.connect(self.switch_page)
        self.sorting_widget.switch_page.connect(self.switch_page)
        self.calendar_widget.switch_page.connect(self.switch_page)

        self.setCentralWidget(self.stack)

    def switch_page(self, index):
        cur = self.stack.currentIndex()
        # 決定方向： index > cur -> 左滑（新頁由右入），否則右滑
        direction = 'left' if index > cur else 'right'
        try:
            slide_stack(self.stack, index, direction=direction)
        except Exception:
            # fallback
            self.stack.setCurrentIndex(index)

        # 保留原本的特例行為（回到 TodayList 顯示 list frame 的漸入）
        if index == 0:
            frame = self.today_list_widget.list_frame
            if hasattr(frame, "_fade_in_animation"):
                gradually_enter_ani(frame)

def main():
    app = QApplication([])
    w = ReminderMainWindow()
    w.show()
    app.exec_()
