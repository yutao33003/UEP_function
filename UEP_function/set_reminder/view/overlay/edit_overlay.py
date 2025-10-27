import datetime
import time
from PyQt5.QtGui import QCursor, QIcon
from PyQt5.QtWidgets import (
     QCheckBox, QComboBox, QDateTimeEdit, QFrame, QHBoxLayout, QLineEdit, QSizePolicy, QTextEdit,
    QWidget, QVBoxLayout, QLabel, QPushButton
)
from PyQt5.QtCore import QDateTime, QTimer, Qt, pyqtSignal, QEvent, QSize
from set_reminder.animate import delete_with_animation, gradually_enter_ani, gradually_exit_ani
from set_reminder.view.overlay.base_overlay import BaseOverlay
from set_reminder.view.widget.widget import create_button_edit, create_scroll_area_edit, create_text_edit, font_setting

# TaskWidget 是每個任務的 widget
class TaskWidget(QWidget):

    edit_requested = pyqtSignal(str)   # 傳 task_id
    delete_requested = pyqtSignal(str)
    finish_toggled = pyqtSignal(str, bool)

    def __init__(self, degree, title, duration, finish_state, task_id, event_adapter = None, parent=None):
        super().__init__(parent)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setAttribute(Qt.WA_StyledBackground, True)   # 讓背景顯示

        # 不以 parent 寬度在建構時硬設定最小寬度，改用彈性策略
        self.setMinimumHeight(80)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.task_id = task_id
        self.finish_state = finish_state
        self.event_adapter = event_adapter

        # 只在直接 parent（container）上安裝 eventFilter，避免監聽到整個 window
        self._parent_widget = parent
        if self._parent_widget is not None:
            try:
                self._parent_widget.installEventFilter(self)
                self._on_parent_resized()  # 初次同步
            except Exception:
                self._parent_widget = None

        self.background_color(degree)

        title = self.cal_title_length(title)

        self.name = QLabel(title)
        self.name.setFont(font_setting(10))
        self.name.setStyleSheet("background: transparent;font-weight: bold;")
        self.name.setWordWrap(True)
        self.name.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.finish_state)
        self.checkbox.stateChanged.connect(self.toggle_completed)
        print(self.finish_state)
        if self.finish_state == True:
            font = self.name.font()
            font.setStrikeOut(True)
            self.name.setFont(font)          

        cell_layout = QHBoxLayout()
        cell_layout.addWidget(self.checkbox)
        cell_layout.addWidget(self.name, alignment= Qt.AlignLeft)
        cell_layout.setStretch(0,1)
        cell_layout.setStretch(1,5)
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

    def cal_title_length(self, title: str, max_width=15):
        """
        中文算2個單位寬度，英文算1個單位寬度。
        超過 max_width 就截斷並加上 '...'
        """
        width = 0
        result = ""
        for ch in title:
            if '\u4e00' <= ch <= '\u9fff':
                width += 2
            else:
                width += 1
            if width > max_width:
                return result + "..."
            result += ch
        return result

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
        """根據回傳的 task dict 更新對應的 TaskWidget"""
        task = self.event_adapter.get_event_by_id(task_id)
        if task:
            self.update_content(task)

    def update_content(self, task):
        """更新 TaskWidget 顯示的內容"""
        self.name.setText(task["title"])
        duration = task["start_time"].split(" ")[0]
        self.duration_text.setText(duration)

        self.background_color(task.get("priority", "medium"))
 
        self.update()


# 編輯事件頁清單
class EditTaskOverlay(BaseOverlay):

    confirmed_requested = pyqtSignal(str)

    def __init__(self, parent=None, task_id="", iso_date = "", event_adapter = None, type_controller = None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Widget)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)

        self.setStyleSheet("background-color: rgba(0, 0, 0, 120);") 
        window = self.parent()
        if window:
            self.setGeometry(window.rect())
        else:
            self.resize(600, 500)

        self.task_id = task_id
        self.iso_date = iso_date
        self.event_adapter = event_adapter
        self.type_controller = type_controller

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
        back_btn.clicked.connect(self.close)

        upper_layout = QHBoxLayout()
        upper_layout.addWidget(back_btn, alignment=Qt.AlignLeft)

        if self.task_id!="":
            task_data = self.event_adapter.get_event_by_id(self.task_id)
        else:
            if iso_date!="":
                print(iso_date)
                start_time = f"{iso_date} 09:00"
                end_time = f"{iso_date} 10:00"
            else:
                now = datetime.datetime.now()
                # 例如現在是 14:23，預設可以從現在算起 1 小時
                start_time = now.strftime("%Y-%m-%d %H:%M")
                end_time = (now + datetime.timedelta(hours=1)).strftime("%Y-%m-%d %H:%M")


            task_data ={
                        "title": "",
                        "id": "",
                        "type": "",
                        "start_time": start_time,
                        "end_time": end_time,
                        "description": "",
                        "priority": "",
                        "alert1": "",
                        "alert2": "",
                        "finish": False,
                        "repeat": False
                         }

        layout.addLayout(upper_layout)       
        
        self.title_label = QLabel("title:")
        self.title_label.setFont(font_setting(10))
        self.title_edit = QLineEdit(task_data.get("title", ""))
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

        all_type_data = self.type_controller.load_types().get("type", [])
        type_data = [item["type_name"] for item in all_type_data]

        self.type_label = QLabel("type:")
        self.type_label.setFont(font_setting(10))
        self.type_box = QComboBox()
        self.type_box.setFont(font_setting(10))
        self.type_box.addItems(type_data)
        self.type_box.setCurrentText(task_data.get("type", "work"))
        type_layout = QHBoxLayout()

        type_layout.addWidget(self.type_label)
        type_layout.addWidget(self.type_box)
        layout.addLayout(type_layout)

        self.start_time_label = QLabel("start_time")
        self.start_time_label.setFont(font_setting(10))
        self.start_time = QDateTimeEdit()
        self.start_time.setFont(font_setting(10))
        self.start_time.setDisplayFormat("yyyy-MM-dd HH:mm")
        if task_data["start_time"]:
            self.start_time.setDateTime(QDateTime.fromString(task_data["start_time"], "yyyy-MM-dd HH:mm"))
        self.start_time.setFont(font_setting(10))
        start_time_layout = QHBoxLayout()
        start_time_layout.addWidget(self.start_time_label)
        start_time_layout.addWidget(self.start_time)
        layout.addLayout(start_time_layout)

        self.end_time_label = QLabel("end_time")
        self.end_time_label.setFont(font_setting(10))
        self.end_time = QDateTimeEdit()
        self.end_time.setFont(font_setting(10))
        self.end_time.setDisplayFormat("yyyy-MM-dd HH:mm")

        if task_data["end_time"]:
            self.end_time.setDateTime(QDateTime.fromString(task_data["end_time"], "yyyy-MM-dd HH:mm"))
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
        print(task_data.get("description",""))
        self.desc_edit = create_text_edit(self, task_data.get("description",""), "輸入任務描述...")
        self.desc_edit.setFont(font_setting(10))

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
        self.alert_combo1.setCurrentText(task_data.get("alert1",""))
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
            self.event_adapter.update_event(self.task_id, task)
            print("儲存的任務：", task)
            
        else:
            self.task_id = create_new_task_id(self.type_box.currentText())
            task["id"] = self.task_id
            self.event_adapter.add_event(task)

        self.confirmed_requested.emit(self.task_id)
            
        gradually_exit_ani(self, duration=500, finished_callback=self.close)

    def showEvent(self, event):
        super().showEvent(event)
        
    def resizeEvent(self, event):
        """自動讓 overlay 跟隨父層視窗尺寸調整"""
        super().resizeEvent(event)

        parent = self.parent()
        if parent is not None:
            self.setGeometry(parent.rect())

def create_new_task_id(task_type:str):
    timestamp = int(time.time() * 1000)  # 毫秒級時間戳
    return f"{task_type}_{timestamp}"

# 確認視窗
class ConfirmDialog(BaseOverlay):

    def __init__(self, parent, message="", dialog_type = "", confirm_callback=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Widget)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        
        self.setStyleSheet("background-color: transparent;")
        self.setGeometry(parent.rect()) 
        
        self.confirm_callback = confirm_callback

        # 背景層
        self.overlay_bg = QFrame(self)
        self.overlay_bg.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 120);
                border-radius: 10px;
            }
        """)
        self.overlay_bg.setGeometry(self.rect())

        # 主 layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.overlay_bg)

        main_layout = QVBoxLayout(self.overlay_bg)
        main_layout.setAlignment(Qt.AlignCenter)  # ✅ 讓內容置中

        # 中央框
        box = QWidget(self.overlay_bg)
        box.setStyleSheet("background-color: #E4DCCF; border-radius: 12px;")
        box.setMinimumSize(250, 180)  # ✅ 避免被壓扁
        main_layout.addWidget(box, alignment=Qt.AlignCenter)

        box_layout = QVBoxLayout(box)
        box_layout.setContentsMargins(20, 20, 20, 20)
        box_layout.setSpacing(15)

        label = QLabel(message)
        label.setFont(font_setting(10))
        label.setAlignment(Qt.AlignCenter)
        box_layout.addWidget(label)

        button_layout = QHBoxLayout(box)
        button_layout.setAlignment(Qt.AlignCenter)
        box_layout.addLayout(button_layout)   

        if dialog_type == "confirm":
            print("comfirm")
            confirm_btn = create_button_edit("confirm", "#7D9D9C", parent=box)
            confirm_btn.setFont(font_setting(10))
            cancel_btn = create_button_edit("cancel", "#aaa", parent=box)
            cancel_btn.setFont(font_setting(10))
            button_layout.addWidget(confirm_btn)
            button_layout.addWidget(cancel_btn)
            confirm_btn.clicked.connect(self.on_confirm)
            cancel_btn.clicked.connect(self.close)
        else:
            ok_btn = create_button_edit("ok", "#7D9D9C", parent=box)
            ok_btn.setFont(font_setting(10))
            button_layout.addWidget(ok_btn)
            ok_btn.clicked.connect(self.close)
            
        button_layout.setAlignment(Qt.AlignCenter)
        

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.overlay_bg.setGeometry(self.rect())  # ✅ 讓背景層填滿

    def on_confirm(self):
        if self.confirm_callback:
            self.confirm_callback()
        self.close()
