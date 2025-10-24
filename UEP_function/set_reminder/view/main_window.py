import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget
from set_reminder.adapters.event_adapter import EventAdapter
from set_reminder.animate import gradually_enter_ani
from set_reminder.view import sorting_ui, today_list_ui
from set_reminder.calendar import calendar_ui
from set_reminder.json_repository.record_controller import TaskController, TypeController
from set_reminder.view.overlay.edit_overlay import ConfirmDialog, EditTaskOverlay
from set_reminder.view.overlay.gray_background_overlay import TypeTaskOverlay
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

        self.stack = QStackedWidget()
        self.sorting_widget = sorting_ui.SortingUI(self.event_adapter, self.overlay_controller, self.type_controller)
        self.today_list_widget = today_list_ui.TodayListUI(self.event_adapter, self.overlay_controller)
        self.calendar_widget = calendar_ui.CalendarUI(self.event_adapter, self.overlay_controller)
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
        self.stack.setCurrentIndex(index)
        if index == 0:  # ¦^¨ì TodayListUI
            frame = self.today_list_widget.list_frame
            if hasattr(frame, "_fade_in_animation"):
                gradually_enter_ani(frame)

def main():
    app = QApplication([])
    w = ReminderMainWindow()
    w.show()
    app.exec_()
