import datetime
import time
from PyQt5.QtGui import QCursor, QIcon
from PyQt5.QtWidgets import (
     QCheckBox, QComboBox, QDateTimeEdit, QHBoxLayout, QLineEdit, QSizePolicy, QTextEdit,
    QWidget, QVBoxLayout, QLabel, QPushButton
)
from PyQt5.QtCore import QDateTime, QEvent, QTimer, Qt, pyqtSignal
from set_reminder.animate import delete_with_animation, gradually_enter_ani, gradually_exit_ani
from set_reminder.view.overlay.base_overlay import BaseOverlay
from set_reminder.view.widget.widget import create_button_edit, create_scroll_area_edit, create_text_edit, font_setting

# TaskWidget 是每個任務的 widget
class TaskWidget(QWidget):

    edit_requested = pyqtSignal(str)   # 傳 task_id
    delete_requested = pyqtSignal(str)
    finish_toggled = pyqtSignal(str, bool)

    def __init__(self, degree, title, duration, finish_state, task_id, event_adapter = None, overlay_controller = None, parent=None):
        super().__init__(parent)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setAttribute(Qt.WA_StyledBackground, True)   # 讓背景顯示

        # 不以 parent 寬度在建構時硬設定最小寬度，改用彈性策略
        self.setMinimumHeight(80)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.task_id = task_id
        self.finish_state = finish_state
        self.event_adapter = event_adapter
        self.overlay_controller = overlay_controller

        # 只在直接 parent（container）上安裝 eventFilter，避免監聽到整個 window
        self._parent_widget = parent
        if self._parent_widget is not None:
            try:
                # 如果 parent 本身是頂層 window，則不要監聽（避免全域共變）
                if self._parent_widget is not self._parent_widget.window():
                    self._parent_widget.installEventFilter(self)
                    self._on_parent_resized()  # 初次同步
            except Exception:
                self._parent_widget = None

        self.background_color(degree)

        self.name = QLabel(title)
        self.name.setFont(font_setting(10))
        self.name.setStyleSheet("background: transparent;font-weight: bold;")
        self.name.setWordWrap(True)
        self.name.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.checkbox = QCheckBox()
        self.checkbox.stateChanged.connect(self.toggle_completed)
        if self.finish_state == True:
            self.checkbox.setCheckable(True)
            self.toggle_completed(True)

        cell_layout = QHBoxLayout()
        cell_layout.addWidget(self.checkbox)
        cell_layout.addWidget(self.name, alignment= Qt.AlignLeft)
        cell_layout.setStretch(0,1)
        cell_layout.setStretch(1,4)
        cell_layout.setContentsMargins(0,0,0,0)

        self.duration_text = QLabel(duration)
        self.duration_text.setFont(font_setting(8))
        self.duration_text.setStyleSheet("background: transparent;font-weight: bold;")
        self.duration_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.trash_button = QPushButton()
        self.trash_button.setFixedSize(24, 24)
        self.trash_button.setIcon(QIcon("set_reminder/image/delete.png"))
        self.trash_button.setIconSize(self.trash_button.size())
        self.trash_button.setStyleSheet("border: none; background: transparent;")
        self.trash_button.clicked.connect(lambda: self.delete_requested.emit(self.task_id))

        self.edit_button = QPushButton()
        self.edit_button.setFixedSize(24, 24)
        self.edit_button.setIcon(QIcon("set_reminder/image/edit.png"))
        self.edit_button.setIconSize(self.edit_button.size())
        self.edit_button.setStyleSheet("border: none; background: transparent;")
        self.edit_button.clicked.connect(lambda: self.edit_requested.emit(self.task_id))

        side_layout = QHBoxLayout()
        side_layout.addWidget(self.edit_button)
        side_layout.addWidget(self.trash_button)
        side_layout.setContentsMargins(10, 10, 10, 10)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(10, 10, 10, 10)
        text_layout.setSpacing(5)
        text_layout.addLayout(cell_layout)
        text_layout.addWidget(self.duration_text)

        layout = QHBoxLayout()
        layout.addLayout(text_layout)
        layout.addLayout(side_layout)
        layout.setContentsMargins(0,0,0,0)
        self.setLayout(layout)

    def eventFilter(self, obj, event):
        # 監聽直接 parent 的 Resize 事件，僅在 parent 不是 window 時處理
        if obj is self._parent_widget and event.type() == QEvent.Resize:
            self._on_parent_resized()
        return super().eventFilter(obj, event)

    def _on_parent_resized(self):
        # 根據直接 parent 寬度設定最大寬度（保留邊距），避免 TaskWidget 超出 container
        if not self._parent_widget:
            return
        try:
            margin = 24  # 保留左右內距
            max_w = max(200, self._parent_widget.width() - margin)
            self.setMaximumWidth(max_w)
            self.updateGeometry()
        except Exception:
            pass

    def sizeHint(self):
        # 根據內部 label 的 sizeHint 計算高度，避免內容被截斷
        hint = super().sizeHint()
        try:
            name_hint = self.name.sizeHint().height()
            dur_hint = self.duration_text.sizeHint().height()
            h = max(self.minimumHeight(), 12 + name_hint + dur_hint)
            hint.setHeight(h)
        except Exception:
            pass
        return hint

    def background_color(self, degree):
        if degree == "high":
            color = "#D5683D"
        elif degree == "medium":
            color ="#586C50"
        else:
            color = "#9CB3C5"
        
        self.setStyleSheet(f"""
            background-color: {color};
            border: none;
            border-radius: 10px;
        """)

    def mousePressEvent(self, event):
        # 以 signal 傳回 task_id
        self.edit_requested.emit(self.task_id)
        super().mousePressEvent(event)

    def toggle_completed(self, state):
        is_checked = (state == Qt.Checked)
        self.finish_state = is_checked
        font = self.name.font()
        font.setStrikeOut(is_checked)
        self.name.setFont(font)
        self.finish_toggled.emit(self.task_id, is_checked)

    def on_task_updated(self, task_id):
        # 可以在這裡 connect event_adapter signal 並更新 UI
        pass


# ClickableWidget 上的按鈕事件
# 編輯事件頁清單
class EditTaskOverlay(BaseOverlay):

    comfirmed_requested = pyqtSignal(BaseOverlay)
    delete_requested = pyqtSignal(str)

    def __init__(self, parent=None, task_id="", event_adapter = None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 120);") 
        self.setGeometry(parent.rect())  
        self.task_id = task_id
        self.event_adapter = event_adapter

        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)

        scroll = create_scroll_area_edit()
        scroll.viewport().setStyleSheet("background: transparent;")
        main_layout.addWidget(scroll)

        container = QWidget()
        container.setStyleSheet("""
            background-color: #E4DCCF;
            border: none;
            padding:3px;
            border-radius: 25px;
        """)
        container.setMinimumWidth(450)

        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignTop)

        back_btn = QPushButton("◀️")   
        back_btn.setFont(font_setting(18))
        def on_back_clicked():
            gradually_exit_ani(self, duration=500, finished_callback=self.close)
        back_btn.clicked.connect(on_back_clicked)

        upper_layout = QHBoxLayout()
        upper_layout.addWidget(back_btn, alignment=Qt.AlignLeft)
        
        task_data = self.event_adapter.get_event_by_id(self.task_id)

        layout.addLayout(upper_layout)       
        
        self.title_label = QLabel("title:")
        self.title_label.setFont(font_setting(10))
        self.title_edit = QLineEdit(task_data["title"])
        self.title_edit.setFont(font_setting(10))
        self.title_edit.setPlaceholderText("new title")
        self.title_edit.setStyleSheet("""
            QTextEdit {
                background-color: transparent;
                color:black;
                border: 1px solid #ccc;
                border-radius:10px;
            }
        """)
        title_layout = QHBoxLayout()
        title_layout.addWidget(self.title_label)
        title_layout.addWidget(self.title_edit)
        layout.addLayout(title_layout)

        self.type_label = QLabel("type:")
        self.type_label.setFont(font_setting(10))
        self.type_box = QComboBox()
        self.type_box.setFont(font_setting(10))
        self.type_box.addItems(["work", "life", "finance", "other"])
        self.type_box.setCurrentText(task_data["type"])
        type_layout = QHBoxLayout()
        type_layout.addWidget(self.type_label)
        type_layout.addWidget(self.type_box)
        layout.addLayout(type_layout)

        self.start_time_label = QLabel("start_time")
        self.start_time_label.setFont(font_setting(10))
        self.start_time = QDateTimeEdit()
        self.start_time.setFont(font_setting(10))
        self.start_time.setDisplayFormat("yyyy-MM-dd hh:mm")
        if task_data["start_time"]:
            self.start_time.setDateTime(QDateTime.fromString(task_data["start_time"], "yyyy-MM-dd hh:mm"))
        self.start_time.setFont(font_setting(10))
        start_time_layout = QHBoxLayout()
        start_time_layout.addWidget(self.start_time_label)
        start_time_layout.addWidget(self.start_time)
        layout.addLayout(start_time_layout)

        self.end_time_label = QLabel("end_time")
        self.end_time_label.setFont(font_setting(10))
        self.end_time = QDateTimeEdit()
        self.end_time.setFont(font_setting(10))
        self.end_time.setDisplayFormat("yyyy-MM-dd hh:mm")

        if task_data["end_time"]:
            self.end_time.setDateTime(QDateTime.fromString(task_data["end_time"], "yyyy-MM-dd hh:mm"))
        end_time_layout = QHBoxLayout()
        end_time_layout.addWidget(self.end_time_label)
        end_time_layout.addWidget(self.end_time)
        layout.addLayout(end_time_layout)

        self.end_time.setMinimumDateTime(self.start_time.dateTime())
        self.start_time.dateTimeChanged.connect(
            lambda dt: self.end_time.setMinimumDateTime(dt)
        )

        self.desc_label = QLabel("describle")
        self.desc_label.setFont(font_setting(10))

        self.desc_edit = create_text_edit(self, task_data.get("description",""))
        self.desc_edit.setFont(font_setting(10))
        self.desc_edit.setPlaceholderText("輸入任務描述...")

        layout.addWidget(self.desc_label)
        layout.addWidget(self.desc_edit)

        self.priority_label = QLabel("priority")
        self.priority_label.setFont(font_setting(10))
        self.priority_box = QComboBox()
        self.priority_box.setFont(font_setting(10))
        self.priority_box.addItems(["high", "medium", "low"])
        self.priority_box.setCurrentText(task_data.get("priority","medium"))

        priority_layout = QHBoxLayout()
        priority_layout.addWidget(self.priority_label)
        priority_layout.addWidget(self.priority_box)
        layout.addLayout(priority_layout)

        remind_options = [
            "None",
            "At start time",
            "15 minutes before",
            "30 minutes before",
            "1 hour before",
            "2 hours before",
            "1 day before",
            "2 days before",
            "1 week before"
        ]

        self.alert_label1 = QLabel("remind 1")
        self.alert_label1.setFont(font_setting(10))
        self.alert_combo1 = QComboBox()
        self.alert_combo1.setFont(font_setting(10))
        self.alert_combo1.addItems(remind_options)
        self.alert_combo1.setCurrentText(task_data.get("alert1","None"))
        alert_layout1 =QHBoxLayout()
        alert_layout1.addWidget(self.alert_label1)
        alert_layout1.addWidget(self.alert_combo1)
        layout.addLayout(alert_layout1)

        self.alert_label2 = QLabel("remind 2")
        self.alert_label2.setFont(font_setting(10))
        self.alert_combo2 = QComboBox()
        self.alert_combo2.setFont(font_setting(10))
        self.alert_combo2.addItems(remind_options)
        self.alert_combo2.setCurrentText(task_data.get("alert2", "None"))
        alert_layout2 =QHBoxLayout()
        alert_layout2.addWidget(self.alert_label2)
        alert_layout2.addWidget(self.alert_combo2)
        layout.addLayout(alert_layout2)

        self.repeat_check = QCheckBox("是否重複")
        self.repeat_check.setChecked(task_data.get("repeat", False))
        layout.addWidget(self.repeat_check)

        save_btn = QPushButton("save")
        save_btn.setFont(font_setting(10))
        save_btn.setStyleSheet("background: #7D9D9C; color: white; padding: 8px; border-radius: 8px;")
        save_btn.clicked.connect(self.save_task)
        layout.addWidget(save_btn, alignment=Qt.AlignCenter)

        scroll.setWidget(container)
         
    def save_task(self):
        task = {
            "title": self.title_edit.text(),
            "id": self.task_id,
            "type": self.type_box.currentText(),
            "start_time": self.start_time.dateTime().toString("yyyy-MM-dd hh:mm"),
            "end_time": self.end_time.dateTime().toString("yyyy-MM-dd hh:mm"),
            "description": self.desc_edit.toPlainText(),
            "priority": self.priority_box.currentText(),
            "alert1": self.alert_combo1.currentText(),
            "alert2":self.alert_combo2.currentText(),
            "repeat": self.repeat_check.isChecked(),
        }
        if self.task_id !="":
            self.task_controller.edit_save_task(self.task_id, task)
            self.task_controller.move_expired_reminders()
            print("儲存的任務：", task)
            self.close()
        else:
            self.task_id = create_new_task_id(self.type_box.currentText())
            task["id"] = self.task_id
            self.task_controller.add_reminder(task)
            self.task_controller.move_expired_reminders()

    def showEvent(self, event):
        super().showEvent(event)

def create_new_task_id(task_type:str):
    timestamp = int(time.time() * 1000)  # 毫秒級時間戳
    return f"{task_type}_{timestamp}"

# 確認視窗
class ConfirmDialog(QWidget):
    def __init__(self, parent, message="", dialog_type = "", confirm_callback=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 120);") 
        self.setGeometry(parent.rect())  
        self.confirm_callback = confirm_callback

        main_layout = QVBoxLayout(self)
        # 中央框
        box = QWidget(self)
        box.setStyleSheet("background-color: #E4DCCF; border-radius: 12px;")
        box.setMinimumHeight(180)
        main_layout.addWidget(box, alignment=Qt.AlignCenter)

        layout = QVBoxLayout(box)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 提示文字
        label = QLabel(message)
        label.setFont(font_setting(10))
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        # 按鈕區 
        button_layout = QHBoxLayout()

        if dialog_type =="confirm":
            confirm_btn = create_button_edit(self, "confirm", "#7D9D9C")
            confirm_btn.setFont(font_setting(10))
            cancel_btn = create_button_edit(self, "cancel", "#aaa")
            cancel_btn.setFont(font_setting(10))

            button_layout.addWidget(confirm_btn)
            button_layout.addWidget(cancel_btn)
            confirm_btn.clicked.connect(self.on_confirm)
            cancel_btn.clicked.connect(self.close)
        else:
            ok_btn = create_button_edit(self, "ok", "#7D9D9C")
            ok_btn.setFont(font_setting(10))
            button_layout.addWidget(ok_btn)
            ok_btn.clicked.connect(self.close)
            
        button_layout.setAlignment(Qt.AlignCenter)
        layout.addLayout(button_layout)    

    def on_confirm(self):
        if self.confirm_callback:
            self.confirm_callback()
        self.close()
