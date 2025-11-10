# calendar_widget.py
from PyQt5 import QtCore
import datetime
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PyQt5.QtCore import pyqtSignal
from set_reminder.animate import gradually_enter_ani
from set_reminder.calendar.calendar_model import CalendarModel
from set_reminder.calendar.calendar_widget import CalendarWidget
from set_reminder.calendar.event_list_widget import EventListWidget
from set_reminder.calendar.calendar_controller import CalendarController
from set_reminder.view.widget.widget import create_tag_button_edit, create_title_label_edit


class CalendarUI(QWidget):
    switch_page = pyqtSignal(int)

    def __init__(self, event_adapter = None, overlay_ctrl = None, type_controller = None, task_service = None):
        super().__init__()
        self._init_models_and_controllers(event_adapter, overlay_ctrl, type_controller, task_service)
        self._build_ui()
        self._connect_signals()
        self.current_date = None
    
    def _init_models_and_controllers(self, event_adapter, overlay_ctrl, type_controller, task_service):
        self.model = CalendarModel()
        self.event_adapter = event_adapter
        self.overlay_controller = overlay_ctrl
        self.type_controller = type_controller
        self.task_service = task_service
  
        self.calendar_widget = CalendarWidget(self.model)
        self.event_list_widget = EventListWidget(self.event_adapter, self.overlay_controller, self.type_controller, self.task_service)
        self.controller = CalendarController(
            self.model, self.calendar_widget, self.event_adapter, self.event_list_widget)

    def _build_ui(self):
        self.title_text = create_title_label_edit(self,"Calendar")
        self.title_text.setAlignment(QtCore.Qt.AlignLeft)
        self.today_button = create_tag_button_edit(self,"today")
        self.today_button.clicked.connect(lambda: self.switch_page.emit(0))
        self.sorting_button = create_tag_button_edit(self, "sorting")
        self.sorting_button.clicked.connect(lambda: self.switch_page.emit(1))
        self.calendar_button = create_tag_button_edit(self, "calendar")
        self.calendar_button.clicked.connect(lambda: self.switch_page.emit(2))
        self.calendar_button.setStyleSheet("background: transparent; color:black;")

        title_layout2 = QHBoxLayout()
        title_layout2.addWidget(self.today_button)
        title_layout2.addWidget(self.sorting_button)
        title_layout2.addWidget(self.calendar_button)
        title_layout2.setAlignment(QtCore.Qt.AlignHCenter)
        calendar_layout = QVBoxLayout()
        calendar_layout.addLayout(title_layout2)
        calendar_layout.addWidget(self.calendar_widget)
        event_list_layout = QVBoxLayout()
        event_list_layout.addWidget(self.event_list_widget)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.title_text)
        widget_layout = QHBoxLayout()
        widget_layout.addLayout(calendar_layout)
        widget_layout.addLayout(event_list_layout)
        widget_layout.setStretch(0, 1)
        widget_layout.setStretch(1, 1)
        main_layout.addLayout(widget_layout)
        self.setLayout(main_layout)

    def _connect_signals(self):
        self.calendar_widget.date_selected.connect(self.on_date_selected)
        self.event_list_widget.add_requested.connect(self.on_add_event)

    def on_date_selected(self, iso_date):
        """當使用者點選某日時，顯示該日的事件"""
        self.current_date = iso_date
        self.event_list_widget.show_events(iso_date)

    def on_add_event(self, iso_date, overlay=None):
        """
        當使用者要求新增事件時，我們「委派」這個請求給 TaskService。
        Service 會處理業務邏輯，並發射訊號給 MainWindow 的「決策中心」。
        """
        if not self.task_service:
            print("錯誤：CalendarUI 沒有 TaskService")
            return

        print(f"CalendarUI: 委派新增請求 ({iso_date}) 給 TaskService")
        self.task_service.open_task_editor(iso_date = iso_date)

    def showEvent(self, event):
        super().showEvent(event)
        self.calendar_widget.date_selected.emit(datetime.date.today().isoformat())