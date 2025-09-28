from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QGraphicsOpacityEffect, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget
from set_reminder.animate import gradually_enter_ani
from set_reminder.edit_overlay import TaskWidget
from set_reminder.gray_background_overlay import TypeTaskOverlay
from set_reminder.widget import create_picture_button_edit, create_tag_button_edit, create_title_label_edit, font_setting
from set_reminder.record_controller import TaskController
import datetime

class TodayListUI(QWidget):
    switch_page = QtCore.pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.title_text = create_title_label_edit(self,"Today List")
        self.expired_button  = create_picture_button_edit(self, "set_reminder/image/expired.png", "set_reminder/image/expired_hover.png", 40)
        self.expired_button.clicked.connect(self.expired_page)
        self.date_subtitle = QLabel(self)   

        self.today_button = create_tag_button_edit(self,"today")
        self.today_button.clicked.connect(lambda: self.switch_page.emit(0))
        self.today_button.setStyleSheet("background: transparent; color:black;")
        self.sorting_button = create_tag_button_edit(self, "sorting")
        self.sorting_button.clicked.connect(lambda: self.switch_page.emit(1))
        self.calendar_button = create_tag_button_edit(self, "calendar")
        
        self.list_frame = QFrame()        
        self.list_frame.setFrameShape(QFrame.NoFrame)
        self.list_frame.setStyleSheet("""
            QFrame {
                background-color: #9c9892;
                border: none;
                border-radius: 10px;
            }
        """)
        self.title_layout = QHBoxLayout()
        self.title_layout.addWidget(self.title_text, alignment=Qt.AlignLeft | Qt.AlignTop)
        self.title_layout.addWidget(self.expired_button, alignment=Qt.AlignRight | Qt.AlignCenter)

        self.title_layout2 = QHBoxLayout()
        self.title_layout2.addWidget(self.today_button)
        self.title_layout2.addWidget(self.sorting_button)
        self.title_layout2.addWidget(self.calendar_button)
        self.title_layout2.setAlignment(Qt.AlignHCenter)
        self.title_layout2.setSpacing(20)
        self.list_layout = QVBoxLayout()
        self.list_layout.setAlignment(Qt.AlignTop | Qt.AlignCenter )

        reminder = TaskController().load_reminders()
        today = datetime.date.today().strftime("%Y-%m-%d")
        tasks_added = False
        priority_order = {"high": 0, "medium": 1, "low": 2}

        today_tasks = [
            task for task in reminder["reminders"]
            if task.get("start_time", "").split(" ")[0] == today
        ]

        today_tasks.sort(key=lambda t: priority_order.get(t.get("priority", "low"), 3))

        for task in today_tasks:
            title = task.get("title")
            finish_state = task.get("finish")
            start_time = task.get("start_time").split(" ")[0]
            degree = task.get("priority")
            task_id = task.get("id")

            self.task_button = TaskWidget(degree, title, start_time, finish_state, task_id, "reminders", self)
            self.list_layout.addWidget(self.task_button)
            tasks_added = True
        
        if not tasks_added:
            no_task_label = QLabel("No tasks for today.", self.list_frame)
            no_task_label.setStyleSheet("""
                QLabel {
                    background-color: transparent;  
                    color: #555555;                  
                }
            """)
            cust_font = font_setting(16)
            no_task_label.setFont(cust_font)
            no_task_label.setAlignment(Qt.AlignCenter)
            self.list_layout.addWidget(no_task_label)

        gradually_enter_ani(self, self.list_frame)

        # 預設載入時啟動動畫
        self.fade_in_animation.start()
               
        self.scroll_area = QScrollArea()
        self.scroll_area.setStyleSheet("background: transparent; border: none;")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(20, 10, 10, 20)
        self.main_layout.setSpacing(10)      
        self.main_layout.addLayout(self.title_layout)
        self.main_layout.addLayout(self.title_layout2)
        self.main_layout.addWidget(self.scroll_area)
        
        self.scroll_area.setWidget(self.list_frame)
        self.list_frame.setLayout(self.list_layout)
        self.setLayout(self.main_layout)
    
    def expired_page(self):
        overlay = TypeTaskOverlay(self, "", "expired_reminders")
        overlay.show()