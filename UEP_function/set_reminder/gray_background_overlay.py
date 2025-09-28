from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QBrush, QColor, QPainter, QPainterPath, QPixmap, QRegion
from PyQt5.QtWidgets import QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea, QStyledItemDelegate, QVBoxLayout, QWidget
from PyQt5.sip import delete
from set_reminder.animate import gradually_enter_ani
from set_reminder.widget import create_button_edit, font_setting
from set_reminder.edit_overlay import ConfirmDialog, TaskWidget
from set_reminder.record_controller import TaskController

# 類別卡頁的事件列表
class TypeTaskOverlay(QWidget):

    def __init__(self, parent=None, task_type="", section_key = "reminders"):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 120);") 
        self.setGeometry(parent.rect())  
        self.task_type = task_type
        self.section_key = section_key
        self.task_controller = TaskController(self.section_key)
        reminder = self.task_controller.load_reminders()

        back_btn = QPushButton("◀️")   
        back_btn.setStyleSheet("border: none; background: transparent;")
        back_btn.setFont(font_setting(18))
        back_btn.clicked.connect(self.close)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border: none; background: transparent;")
        self.scroll.viewport().setStyleSheet("background: transparent;")
        self.scroll.setFixedSize(350, 400)

        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #9c9892;
                border-radius: 10px;
            }
        """)

        gradually_enter_ani(self, container)

        self.scroll_layout = QVBoxLayout(container)
        self.scroll_layout.setAlignment(Qt.AlignTop)
        self.scroll_layout.addWidget(back_btn, alignment=Qt.AlignLeft)

        if task_type == "":
            task_type_data = reminder[self.section_key]
        else:
            task_type_data = [
                        task for task in reminder[self.section_key]
                        if task.get("type", "").split(" ")[0] == self.task_type
                    ]
        priority_order = {"high": 0, "medium": 1, "low": 2}
        
        task_type_data.sort(key=lambda t: priority_order.get(t.get("priority", "low"), 3))

        tasks_added = False
        for task in task_type_data:
            title = task.get("title")
            degree = task.get("priority")
            duration = task.get("start_time").split(" ")[0]
            finish_state = task.get("finish")
            task_id = task.get("id")
            task_widget = TaskWidget(degree, title, duration, finish_state, task_id, section_key,self)
            self.scroll_layout.addWidget(task_widget, alignment=Qt.AlignCenter)
            tasks_added = True

        if not tasks_added:
            no_task_label = QLabel(f"No {self.task_type} tasks.")
            no_task_label.setStyleSheet("background: transparent; color: #555;")
            no_task_label.setFont(font_setting(16))
            no_task_label.setAlignment(Qt.AlignCenter)
            self.scroll_layout.addWidget(no_task_label)

        self.scroll.setWidget(container)

        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.scroll)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        rect = QRectF(self.scroll.viewport().rect())
        path = QPainterPath()
        path.addRoundedRect(rect, 10, 10)
        region = QRegion(path.toFillPolygon().toPolygon())
        self.scroll.viewport().setMask(region)

# 新增或刪除事件的類別
class AddTypeCard(QWidget):
    def __init__(self, parent = None, title = "", color = "", type_controller = None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 120);") 
        self.setGeometry(parent.rect()) 
        self.color = color
        self.type_controller = type_controller
        
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #E4DCCF; 
                border-radius: 12px;
                padding : 10px;
                }
        """)
        container.setMinimumWidth(300)

        back_btn = QPushButton("◀️")   
        back_btn.setStyleSheet("border: none; background: transparent;")
        back_btn.setFont(font_setting(18))
        back_btn.clicked.connect(self.close)

        self.type_name_label = QLabel("title")
        self.type_name_label.setFont(font_setting(10))
        self.type_name_line_edit = QLineEdit(title)
        self.type_name_line_edit.setFont(font_setting(10))
        self.type_name_line_edit.setStyleSheet(
            """ QLineEdit {
                background-color: transparent;
                color:black;
                border: 1px solid #ccc;
                border-radius:10px;
            }""")

        self.type_name_layout = QHBoxLayout()
        self.type_name_layout.addWidget(self.type_name_label)
        self.type_name_layout.addWidget(self.type_name_line_edit)

        if self.color =="" :
            self.color ="#8D91AA"

        self.color_label = QLabel("color")
        self.color_label.setFont(font_setting(10))
        self.color_combo = QComboBox()
        self.color_combo.setMinimumWidth(150)
        self.color_combo.setStyleSheet("""
            QComboBox {
                border-radius: 10px;   
                padding: 5px;
            }
        """)
        self.color_combo.setFont(font_setting(10))
        self.color_combo.setItemDelegate(ColorDelegate())
        self.color_add()

        self.color_layout = QHBoxLayout()
        self.color_layout.addWidget(self.color_label)
        self.color_layout.addWidget(self.color_combo)
        
        self.save_button = create_button_edit(self, "save", "#7D9D9C")
        self.save_button.setFixedWidth(100)
        self.save_button.clicked.connect(self.save_type)
        self.button_layout = QHBoxLayout()
        self.button_layout.setSpacing(20)
        self.button_layout.addWidget(self.save_button)
        self.button_layout.setAlignment(Qt.AlignCenter)

        if title != "":
            self.delete_button = create_button_edit(self, "delete", "#df6262")
            self.delete_button.setFixedWidth(100)
            self.button_layout.addWidget(self.delete_button)
            self.delete_button.clicked.connect(lambda _title :self.delete_type(title))

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(container, alignment=Qt.AlignCenter)
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignTop)
        layout.addWidget(back_btn, alignment=Qt.AlignLeft)
        layout.addLayout(self.type_name_layout)
        layout.addLayout(self.color_layout)
        layout.addLayout(self.button_layout)

    
    def color_add(self):
        colors =["#8D91AA", "#6F7D5C", "#BE7F54", "#DFAB4D", "#7A989A", "#849271", "#C1AE8D", "#CF9546", "#C67052", "#695B8F", "#B26C61", "#C2AF46", "#4D5E30", "#8B1F1D"]

        for color_code in colors:
            color = QColor(color_code)
            text = color_code
            self.color_combo.addItem(text)
            idx = self.color_combo.count() - 1
            self.color_combo.setItemData(idx, color, Qt.UserRole)

        if self.color:
            index = self.color_combo.findText(self.color)
            if index != -1:  # 有找到
                self.color_combo.setCurrentIndex(index)
        else:
            color = QColor(self.color)
            self.color_combo.addItem(self.color)
            idx = self.color_combo.count() - 1
            self.color_combo.setItemData(idx, color, Qt.UserRole)
            self.color_combo.setCurrentIndex(idx)

    def save_type(self):
        new_type = {
            "id" : self.type_name_line_edit.text(),
            "type_name": self.type_name_line_edit.text(),
            "color": self.color_combo.currentText()
            }

        if hasattr(self, "delete_button") and self.delete_button is not None:
            self.type_controller.update_type(new_type)
            self.close()
        else:
            if self.type_name_line_edit.text() == "" :
                dialog = ConfirmDialog(self.window(), message = "Title cannot be empty.", dialog_type = "notify")
                dialog.show()
            elif self.type_controller.has_same_id (new_type):
                dialog = ConfirmDialog(self.window(), message = "A card with the same category already exists. Please rename it.", dialog_type = "notify")
                dialog.show()
            else:
                self.type_controller.add_type(new_type)
                self.close()

    def delete_type(self, type_id):
        delete_type = {
            "id" : type_id,
            "type_name": type_id,
            "color": self.color_combo.currentText()
            }
        if self.type_controller.has_same_id(delete_type) :
            self.type_controller.delete_type(type_id)
        else:
            print("can't find the type")


class ColorDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        painter.save()
        rect = option.rect

        # 取出顏色與文字
        color = index.data(Qt.UserRole)
        text = index.data(Qt.DisplayRole)

        # 畫顏色小圓圈
        circle_radius = 8
        circle_x = rect.x() + 10
        circle_y = rect.y() + rect.height() // 2

        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(circle_x, circle_y - circle_radius, circle_radius * 2, circle_radius * 2)

        # 畫文字（顏色名稱/色號）
        text_x = circle_x + circle_radius * 2 + 8
        painter.setPen(Qt.black)
        painter.drawText(text_x, rect.y(), rect.width(), rect.height(),
                         Qt.AlignVCenter, text)

        painter.restore()

