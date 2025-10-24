# event_list_widget.py
import datetime
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PyQt5.QtCore import pyqtSignal
from set_reminder.animate import gradually_enter_ani
from set_reminder.view.widget.widget import font_setting

class EventListWidget(QWidget):
    add_requested = pyqtSignal(str)   # iso date
    remove_requested = pyqtSignal(str, str)  # iso, event_id

    def __init__(self, event_adapter, overlay_controller):
        super().__init__()
        self.event_adapter = event_adapter
        self.overlay_controller = overlay_controller
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        self.lbl = QLabel("Events")
        cust_font = font_setting(10)
        self.lbl.setFont(cust_font)
        self.lst = self.overlay_controller.show("task_overlay", scope = "calendar", cache = True, mode = "day", task_type = "", date_filter = datetime.date.today().isoformat(), event_adapter = self.event_adapter, embedded = True, parent = self)

        h = QHBoxLayout()
        self.btn_add = QPushButton("+")
        self.btn_remove = QPushButton("Remove")
        self.btn_add.clicked.connect(self._on_add)
        self.btn_remove.clicked.connect(self._on_remove)
        h.addWidget(self.btn_add); h.addWidget(self.btn_remove)
        layout.addWidget(self.lbl)
        layout.addWidget(self.lst)
        gradually_enter_ani(container=self.lst, duration=500)
        layout.addLayout(h)
        self.setLayout(layout)

    def show_events(self, iso_date):
        self.current_date = iso_date
        self.lst.refresh_data(date_filter=iso_date, mode = "day")

    def _on_add(self):
        if hasattr(self, "current_date"):
            self.add_requested.emit(self.current_date)
            self.overlay_controller.show_type_task(task_type="", section_key="reminders", parent=self.parent())

    def _on_remove(self):
        cur = self.lst.currentItem()
        if not cur:
            return
        text = cur.text()
        # 解析出 id（demo 用簡單 split）
        evt_id = text.split(":",1)[0]
        self.remove_requested.emit(self.current_date, evt_id)



