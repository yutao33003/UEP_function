from turtle import tilt
from PyQt5 import QtCore
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import QFrame, QGraphicsOpacityEffect, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget
from set_reminder.animate import gradually_enter_ani

from set_reminder.view.overlay.edit_overlay import TaskWidget
from set_reminder.view.widget.widget import create_picture_button_edit, create_tag_button_edit, create_title_label_edit, font_setting
import datetime

class TodayListUI(QWidget):
    switch_page = QtCore.pyqtSignal(int)

    def __init__(self, event_adapter = None, overlay_ctrl = None, type_controller = None, task_service = None):
        super().__init__()
        self.event_adapter = event_adapter
        self.overlay_controller = overlay_ctrl
        self.type_controller = type_controller
        self.task_service = task_service

        self.title_text = create_title_label_edit(self,"Today List")
        self.expired_button  = create_picture_button_edit(self, "set_reminder/image/expired.png", "set_reminder/image/expired_hover.png", 40)
        self.expired_button.clicked.connect(lambda: self.overlay_controller.show(
            "task_overlay",
            embedded = False,
            parent = self,
            mode = "past", 
            task_type = None,
            date_filter = None,
            event_adapter = self.event_adapter,
            type_controller = self.type_controller,
            task_service = self.task_service,
            is_overlay = True
           ))
        self.date_subtitle = QLabel(self)   

        self.today_button = create_tag_button_edit(self,"today")
        self.today_button.clicked.connect(lambda: self.switch_page.emit(0))
        self.today_button.setStyleSheet("background: transparent; color:black;")
        self.sorting_button = create_tag_button_edit(self, "sorting")
        self.sorting_button.clicked.connect(lambda: self.switch_page.emit(1))
        self.calendar_button = create_tag_button_edit(self, "calendar")
        self.calendar_button.clicked.connect(lambda: self.switch_page.emit(2))
        
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
    

    def _clear_layout(self, layout):
        """ 輔助函式：安全地清空一個 layout 裡的所有 widgets """
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def refresh_list(self):
        """ 這是新的刷新方法 """
        
        # 1. 清空舊的列表
        self._clear_layout(self.list_layout)

        # 2. 重新獲取資料並排序
        today_tasks = self.event_adapter.get_events(datetime.date.today().isoformat())
        tasks_added = False
        priority_order = {"high": 0, "medium": 1, "low": 2}
        today_tasks.sort(key=lambda t: priority_order.get(t.get("priority", "low"), 3))

        # 3. 重新建立 Widgets
        for task in today_tasks:
            title = task.get("title")
            finish_state = task.get("finish")
            start_time = task.get("start_time").split(" ")[0]
            degree = task.get("priority")
            task_id = task.get("id")

            task_button = TaskWidget(
                degree = degree,
                title = title, 
                duration = start_time,
                finish_state = finish_state,
                task_id = task_id, 
                event_adapter = self.event_adapter, 
                parent=self
                )

            task_button.edit_requested.connect(self._on_edit_task_requested)

            task_button.delete_requested.connect(
                lambda tid=task_id: self.overlay_controller.show(
                    "confirm_overlay",
                    message="Are you sure you want to delete this?",
                    dialog_type="confirm",
                    confirm_callback=lambda: self.delete_task_and_refresh(tid), # 改用新方法
                    parent=self
                )
            )
            
            self.list_layout.addWidget(task_button)
            tasks_added = True
        
        # 4. 處理沒有任務的狀況
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

    @pyqtSlot(str)
    def _on_edit_task_requested(self, task_id):
        """
        這就是「指令」！
        當 TaskWidget 請求編輯時，我們呼叫 TaskService。
        """
        if not self.task_service:
            print("TypeTaskOverlay 錯誤：TaskService 未被傳入！")
            return

        # 呼叫 TaskService，這會觸發 MainWindow 的「決策中心」
        self.task_service.open_task_editor(task_id=task_id)

    def delete_task_and_refresh(self, task_id):
        """ 
        這是一個範例：當刪除回呼(callback)被執行時，
        它會刪除任務，*然後*立即刷新列表。
        """

        print(f"假裝刪除 Task ID: {task_id}")
        
        # 立即刷新
        self.refresh_list()
        
        # (可選) 關閉 confirm_overlay，如果它沒有自動關閉的話
        self.overlay_controller.hide()


    def showEvent(self, event):
        """ 
        覆寫 showEvent，這個方法在 Widget 變為可見時自動觸發
        """
        # 1. 呼叫父類別的 showEvent
        super().showEvent(event)
        
        # 2. 執行刷新
        self.refresh_list()
        
        # 3. 執行動畫 (你原本在 __init__ 和 switch_page 中的邏輯)
        gradually_enter_ani(self.list_frame)