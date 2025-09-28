import time
from PyQt5.QtGui import QCursor, QIcon
from PyQt5.QtWidgets import (
     QCheckBox, QComboBox, QDateTimeEdit, QHBoxLayout, QLineEdit, QTextEdit,
    QWidget, QVBoxLayout, QLabel, QPushButton, QScrollArea
)
from PyQt5.QtCore import QDateTime, QEasingCurve, QParallelAnimationGroup, QPropertyAnimation, Qt, pyqtSignal
from set_reminder.animate import delete_with_animation, gradually_enter_ani
from set_reminder.record_controller import TaskController
from set_reminder.widget import create_button_edit, create_text_edit, font_setting

# TaskWidget 是每個任務的 widget
class TaskWidget(QWidget):

    clicked = pyqtSignal()
    def __init__(self, degree, title, duration, finish_state, task_id, section_key = "reminders", parent=None):
        super().__init__(parent)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setAttribute(Qt.WA_StyledBackground, True)   # 讓背景顯示
        self.setFixedSize(300,100)
        self.task_id = task_id
        self.finish_state = finish_state
        self.section_key = section_key
        self.task_controller = TaskController(section_key)
        self.task_controller.data_changed.connect(self.on_task_updated)

        self.background_color(degree)

        self.name = QLabel(title)
        self.name.setFont(font_setting(10))
        self.name.setStyleSheet("background: transparent;font-weight: bold;")

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

        self.duration_text = QLabel(duration)
        self.duration_text.setFont(font_setting(8))
        self.duration_text.setStyleSheet("background: transparent;font-weight: bold;")

        self.trash_button = QPushButton()
        self.trash_button.setFixedSize(24, 24) 
        self.trash_button.setIcon(QIcon("set_reminder/image/delete.png"))      # 設定圖片
        self.trash_button.setIconSize(self.trash_button.size())   # 圖片大小跟隨按鈕
        self.trash_button.setStyleSheet("border: none; background: transparent;")
        self.trash_button.clicked.connect(lambda: self.deletePressEvent(task_id))

        self.edit_button = QPushButton()
        self.edit_button.setFixedSize(24, 24) 
        self.edit_button.setIcon(QIcon("set_reminder/image/edit.png"))
        self.edit_button.setIconSize(self.edit_button.size())
        self.edit_button.setStyleSheet("border: none; background: transparent;")
        self.edit_button.clicked.connect(lambda: self.open_edit_overlay(task_id))

        side_layout = QHBoxLayout()
        side_layout.addWidget(self.edit_button)
        side_layout.addWidget(self.trash_button)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(10, 10, 10, 10)
        text_layout.setSpacing(5)
        text_layout.addLayout(cell_layout)
        text_layout.addWidget(self.duration_text)

        layout = QHBoxLayout()
        layout.addLayout(text_layout)
        layout.addLayout(side_layout)
        self.setLayout(layout)
        self.setMinimumHeight(60)  # 確保 widget 高度足夠顯示背景

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
            border-radius: 20px;
        """)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)

    def open_edit_overlay(self, task_id):
        main_window = self.window()   # 抓最上層的 MainWindow
        overlay = EditTaskOverlay(main_window, task_id, self.section_key, self.task_controller)
        overlay.show()

    def toggle_completed(self, state):
        is_checked = (state == Qt.Checked)   # True/False
        self.finish_state = is_checked
        self.task_controller.update_finish(self.task_id, is_checked)
        self.task_controller.move_expired_reminders()

        font = self.name.font()
        font.setStrikeOut(is_checked)
        self.name.setFont(font)

    # 刪除事件
    def deletePressEvent(self, task_id):
        def really_delete():
            self.task_controller.delete_task(task_id)
            delete_with_animation(self)

        dialog = ConfirmDialog(self.window() ,message="Are you certain you want to delete this?", dialog_type="confirm", confirm_callback=really_delete)
        dialog.show()

    def on_task_updated(self, task_id):
        if task_id == self.task_id:
            task_data = next((t for t in self.task_controller.load_reminders()[self.section_key] if t["id"] == task_id), {})
            self.name.setText(task_data.get("title", self.name.text()))
            self.duration_text.setText(task_data.get("start_time", self.duration_text.text()))
            self.background_color(task_data.get("priority", ""))


# ClickableWidget 上的按鈕事件
# 編輯事件頁清單
class EditTaskOverlay(QWidget):
    def __init__(self, parent=None, task_id="", section_key = "reminders", task_controller = None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 120);") 
        self.setGeometry(parent.rect())  
        self.task_controller = task_controller
        self.section_key = section_key

        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background-color: transparent; border: none")
        scroll.viewport().setStyleSheet("background: transparent;")
        scroll.setFixedSize(350, 400)
        main_layout.addWidget(scroll)

        container = QWidget()
        container.setStyleSheet("""
            background-color: #E4DCCF;
            border: none;
            padding:3px;
            border-radius: 25px;
        """)
        container.setMinimumWidth(450)

        gradually_enter_ani(self, container)

        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignTop)

        back_btn = QPushButton("◀️")   
        back_btn.setFont(font_setting(18))
        back_btn.clicked.connect(self.close)

        upper_layout = QHBoxLayout()
        upper_layout.addWidget(back_btn, alignment=Qt.AlignLeft)

        if self.section_key == "expired_reminders":
            print(self.section_key)
            trash_button = QPushButton()
            trash_button.setFixedSize(24, 24) 
            trash_button.setIcon(QIcon("set_reminder/image/delete.png"))      
            trash_button.setIconSize(trash_button.size())   
            trash_button.setStyleSheet("border: none; background: transparent;")
            trash_button.clicked.connect(lambda: self.deleteAllPressEvent())
            upper_layout.addWidget(trash_button, alignment=Qt.AlignRight )

        layout.addLayout(upper_layout)

        reminders = self.task_controller.load_reminders()
        task_data = next((task for task in reminders[self.section_key] 
                         if task.get("id") == task_id), {})
        self.task_id = task_data.get("id", "")
        
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

        self.type_label = QLabel("type:")
        self.type_label.setFont(font_setting(10))
        self.type_box = QComboBox()
        self.type_box.setFont(font_setting(10))
        self.type_box.addItems(["work", "life", "finance", "other"])
        self.type_box.setCurrentText(task_data.get("type", ""))
        type_layout = QHBoxLayout()
        type_layout.addWidget(self.type_label)
        type_layout.addWidget(self.type_box)
        layout.addLayout(type_layout)

        self.start_time_label = QLabel("start_time")
        self.start_time_label.setFont(font_setting(10))
        self.start_time = QDateTimeEdit()
        self.start_time.setFont(font_setting(10))
        self.start_time.setDisplayFormat("yyyy-MM-dd hh:mm")
        if task_data.get("start_time"):
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

        if task_data.get("end_time"):
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

        self.desc_edit = create_text_edit(self, task_data.get("description", ""))
        self.desc_edit.setFont(font_setting(10))
        self.desc_edit.setPlaceholderText("輸入任務描述...")

        layout.addWidget(self.desc_label)
        layout.addWidget(self.desc_edit)

        self.priority_label = QLabel("priority")
        self.priority_label.setFont(font_setting(10))
        self.priority_box = QComboBox()
        self.priority_box.setFont(font_setting(10))
        self.priority_box.addItems(["high", "medium", "low"])
        self.priority_box.setCurrentText(task_data.get("priority", "medium"))

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
        self.alert_combo1.setCurrentText(task_data.get("alert1", ""))

        alert_layout1 =QHBoxLayout()
        alert_layout1.addWidget(self.alert_label1)
        alert_layout1.addWidget(self.alert_combo1)
        layout.addLayout(alert_layout1)

        self.alert_label2 = QLabel("remind 2")
        self.alert_label2.setFont(font_setting(10))
        self.alert_combo2 = QComboBox()
        self.alert_combo2.setFont(font_setting(10))
        self.alert_combo2.addItems(remind_options)
        self.alert_combo2.setCurrentText(task_data.get("alert2", ""))
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

    def deleteAllPressEvent(self):

        def really_delete():

            self.task_controller.delete_all_tasks()

            parent_layout = self.parentWidget().layout()
            if parent_layout is not None:
                # 遍歷 layout 裡所有 widget
                for i in reversed(range(parent_layout.count())):
                    widget = parent_layout.itemAt(i).widget()
                    if widget is None:
                        continue

                    delete_with_animation(widget)

        dialog = ConfirmDialog(
            self.window(),
            message="Are you certain you want to delete ALL tasks?",
            dialog_type="confirm",
            confirm_callback=really_delete
        )
        dialog.show()

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
