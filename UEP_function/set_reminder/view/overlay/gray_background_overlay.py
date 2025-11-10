import datetime
from tarfile import data_filter
from PyQt5.QtCore import QTimer, Qt, QRectF, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QBrush, QColor, QIcon, QPainter, QPainterPath, QPixmap, QRegion
from PyQt5.QtWidgets import QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSizePolicy, QStyledItemDelegate, QVBoxLayout, QWidget
from set_reminder.animate import delete_with_animation,gradually_enter_ani, gradually_exit_ani
from set_reminder.view.overlay.base_overlay import BaseOverlay
from set_reminder.view.widget.widget import create_button_edit, create_scroll_area_edit, font_setting
from set_reminder.view.overlay.edit_overlay import TaskWidget

# 類別卡頁的事件編輯列表
class TypeTaskOverlay(BaseOverlay):
    edit_task_requested = pyqtSignal(str)

    def __init__(self, mode: str, task_type: str, date_filter = None, event_adapter = None, type_controller = None, task_service = None, is_overlay = False, embedded = False, parent=None):
        super().__init__(parent)
        # 1. 確保不會跑到視窗外
        self.setWindowFlags(Qt.Widget)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        
        # 2. 設置透明背景，內層才放半透明遮罩
        self.setStyleSheet("background-color: transparent;")
        
        # 3. 建立半透明背景層
        self.overlay_bg = QFrame(self)
        self.overlay_bg.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 120);
                border-radius: 10px;
            }
        """)
        
        # 4. 主佈局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.overlay_bg)

        # 5. 內容區域
        self.content_area = QFrame(self.overlay_bg)
        self.content_area.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border-radius: 10px;
            }
        """)
        content_layout = QVBoxLayout(self.overlay_bg)
        content_layout.addWidget(self.content_area)

        # 基本屬性設置
        self.type_controller =type_controller
        self.event_adapter = event_adapter
        self.task_service = task_service
        self.is_overlay = is_overlay
        self.embedded = embedded
        self.task_type = task_type
        self.date_filter = date_filter or datetime.date.today().isoformat()
        self.mode = mode
        self.task_widget_set = []
        self.all_past_task_id = []

        # 6. 滾動區域設置
        self.scroll = create_scroll_area_edit()
        self.scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self.scroll.viewport().setStyleSheet("background: transparent;")

        # 7. 容器設置
        self.container = QFrame()
        self.container.setStyleSheet("background-color: transparent; border-radius: 10px;")
        self.scroll_layout = QVBoxLayout(self.container)
        self.scroll_layout.setAlignment(Qt.AlignTop)
        
        # 9. 設置佈局
        content_layout = QVBoxLayout(self.content_area)
        content_layout.addWidget(self.scroll)
        
        self.scroll.setWidget(self.container)
        self.refresh_data()

        # 10. 尺寸策略
        if embedded:
            # 嵌入式 → 讓 layout 控制大小，不強制填滿
            self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
            if parent:
                self.setGeometry(parent.rect())

        else:
            # 非嵌入式 → 仍然覆蓋整個視窗
            window = self.window()
            if window:
                self.setGeometry(window.rect())
            else:
                self.resize(600, 500)

    def add_task_widget(self, task):
        # 傳入 parent 為 container（不是 window），讓 TaskWidget 以 container 為尺寸參考
        task_widget = TaskWidget(
            degree=task["priority"],
            title=task["title"],
            duration=task["start_time"].split(" ")[0],
            finish_state=task["finish"],
            task_id=task["id"],
            event_adapter=self.event_adapter,
            parent=self.container
        )

        task_widget.edit_requested.connect(self._on_edit_task_requested)

        task_widget.delete_requested.connect(
            lambda task_id: self.open_child_overlay(
                "confirm_overlay",
                message="Are you sure you want to delete this?",
                dialog_type="confirm",
                confirm_callback=lambda tid=task_id: self.delete_task(tid),
                parent=self
            )
        )

        self.task_widget_set.append(task_widget)

        task_widget.finish_toggled.connect(self.on_finish_toggled)
        # 加入時以 AlignTop（或不帶 alignment）讓 widget 能橫向伸展填滿 container
        self.scroll_layout.addWidget(task_widget, alignment=Qt.AlignTop)

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
        self.task_service.open_task_editor(task_id=task_id, is_overlay = self.is_overlay, parent = self)

    def refresh_data(self, task_type=None, date_filter=None, mode=None):

        if task_type:
            self.task_type = task_type
        if date_filter:
            self.date_filter = date_filter
        if mode:
            self.mode = mode

        # 清除舊內容
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        gradually_enter_ani(self, duration=500)

        if self.embedded == False:
            back_btn = QPushButton("◀")   
            back_btn.setStyleSheet("border: none; background: transparent;")
            back_btn.setFont(font_setting(18))
            def on_back_clicked():
                gradually_exit_ani(self, duration=500, finished_callback=self.close)

            back_btn.clicked.connect(on_back_clicked)
            self.scroll_layout.addWidget(back_btn, alignment=Qt.AlignLeft)

        if self.mode == "past":
            del_all_trash_button = QPushButton()
            del_all_trash_button.setFixedSize(24, 24) 
            del_all_trash_button.setIcon(QIcon("set_reminder/image/delete.png"))      
            del_all_trash_button.setIconSize(del_all_trash_button.size())   
            del_all_trash_button.setStyleSheet("border: none; background: transparent;")
            del_all_trash_button.clicked.connect(lambda: self.delete_all_past_task())
            self.scroll_layout.addWidget(del_all_trash_button, alignment=Qt.AlignRight )

        if self.mode == "feature":
            if task_type == "":
                task_data = self.event_adapter.get_future_events(self.date_filter)
            else:
                tasks = self.event_adapter.get_future_events(self.date_filter)
                task_data = [
                            task for task in tasks
                            if task.get("type", "").split(" ")[0] == self.task_type
                        ]
        elif self.mode == "past":
            task_data = self.event_adapter.get_past_events(self.date_filter)

            for task in task_data:
                self.all_past_task_id.append(task["id"])
        else:
            if self.date_filter:
                  task_data = self.event_adapter.get_events(self.date_filter)
        
        priority_order = {"high": 0, "medium": 1, "low": 2}
        task_data.sort(key=lambda t: priority_order.get(t.get("priority", "low"), 3))

        tasks_added = False
        for task in task_data:
            self.add_task_widget(task)
            tasks_added = True

        if not tasks_added:
            no_task_label = QLabel(f"No {self.task_type} tasks.")
            no_task_label.setStyleSheet("background: transparent; color: #555;")
            no_task_label.setFont(font_setting(16))
            no_task_label.setAlignment(Qt.AlignCenter)
            self.scroll_layout.addStretch()  
            self.scroll_layout.addWidget(no_task_label, alignment= Qt.AlignVCenter)
            self.scroll_layout.addStretch()  

    def delete_task(self, task_id):
        # 找到對應 TaskWidget
        task_widget_to_delete = None
        for widget in list(self.task_widget_set):
            if getattr(widget, "task_id", None) == task_id:
                task_widget_to_delete = widget
                break

        if not task_widget_to_delete:
            # 未找到對應 widget，直接移除資料並刷新
            try:
                self.event_adapter.remove_event(task_id)
            except Exception:
                pass
            QTimer.singleShot(0, lambda: self.refresh_data(mode=self.mode))
            return

        # 先從集合移除（避免重複處理）
        try:
            self.task_widget_set.remove(task_widget_to_delete)
        except ValueError:
            pass

        # 在動畫完成後再移除資料並刷新列表，避免與動畫同時操作 layout 導致競態
        def _after_delete():
            try:
                self.event_adapter.remove_event(task_id)
            except Exception:
                pass
            # 小延遲再 refresh，確保動畫 cleanup 完成
            QTimer.singleShot(50, lambda: self.refresh_data(mode=self.mode))

        delete_with_animation(task_widget_to_delete, on_deleted=_after_delete)


    def delete_all_past_task(self):
        """刪除所有過期任務，但不關閉 overlay"""
        # 防呆：如果 scroll_layout 還沒建立，就直接返回
        if not hasattr(self, "scroll_layout") or self.scroll_layout is None:
            return

        # 若沒有任何可刪除任務，直接返回
        if not self.task_widget_set:
            return

        for t_id in self.all_past_task_id:
            self.event_adapter.remove_event(t_id)

        for widget in self.task_widget_set:
            delete_with_animation(widget)

        self.task_widget_set.clear()
        self.all_past_task_id.clear()

        QTimer.singleShot(500, lambda: self.refresh_data(mode="past"))


    def on_finish_toggled(self, task_id, state):
        self.event_adapter.mark_finished(task_id, state)

    def update_font_scale(self):
        """根據 parent 尺寸動態縮放整個 scroll layout 內文字"""
        if not self.embedded:
            return

        base_width = 600
        parent = self.parent()

        scale = parent.width() / base_width
        print(scale)
        scale = max(0.5, min(scale, 3.0))  # 避免太小或太大

        for i in range(self.scroll_layout.count()):
            item = self.scroll_layout.itemAt(i)
            widget = item.widget()
            if widget is None:
                continue

            for target in widget.findChildren((QLabel, QPushButton)) + [widget]:
                if hasattr(target, "font"):
                    font = target.font()

                    if not hasattr(target, "_base_font_size"):
                        base_size = font.pointSize() or 12
                        target._base_font_size = base_size
                    else:
                        base_size = target._base_font_size

                    new_size = base_size * scale
                    if new_size < 8:
                        new_size = 8
                    elif new_size>10:
                        new_size = 10
                    font.setPointSizeF(new_size)
                    target.setFont(font)

                    print(f"{target} | base={base_size}, scale={scale}, new={new_size}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        QTimer.singleShot(0, self.update_font_scale)

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self.update_font_scale)


# 新增或刪除事件的類別
class AddTypeCard(BaseOverlay):
    refresh_signal = pyqtSignal()

    def __init__(self, title : str, color : str, type_controller = None, parent = None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Widget)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setStyleSheet("background-color: transparent;") 
        self.setGeometry(parent.rect()) 

        self.color = color
        self.type_controller = type_controller

        # 背景層
        self.overlay_bg = QFrame(self)
        self.overlay_bg.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 120);
                border-radius: 10px;
            }
        """)
        self.overlay_bg.setGeometry(self.rect())
        
        container = QFrame(self.overlay_bg)
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
        
        self.save_button = create_button_edit("save", "#7D9D9C", parent=self.overlay_bg)
        self.save_button.setFixedWidth(100)
        self.save_button.setFont(font_setting(10))
        self.save_button.clicked.connect(self.save_type)
        self.button_layout = QHBoxLayout()
        self.button_layout.setSpacing(20)
        self.button_layout.addWidget(self.save_button)
        self.button_layout.setAlignment(Qt.AlignCenter)

        if title != "":
            self.delete_button = create_button_edit("delete", "#df6262", parent=self)
            self.delete_button.setFixedWidth(100)
            self.delete_button.setFont(font_setting(10))
            self.button_layout.addWidget(self.delete_button)
            self.delete_button.clicked.connect(lambda _title :self.delete_type(title))

        main_layout = QVBoxLayout(self.overlay_bg)
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
            self.refresh_signal.emit()
            self.close()
        else:
            if self.type_name_line_edit.text() == "" :
                self.open_child_overlay(
                    "confirm_overlay",
                    parent=self.window(),
                    message = "Title cannot be empty.",
                    dialog_type = "notify"
                    )
            elif self.type_controller.has_same_id (new_type):
                self.open_child_overlay(
                    "confirm_overlay",
                    parent=self.window(),
                    message = "A card with the same category already exists. Please rename it.",
                    dialog_type = "notify"
                    )
            else:
                self.type_controller.add_type(new_type)
                self.refresh_signal.emit()
                self.close()

    def delete_type(self, type_id):
        delete_type = {
            "id" : type_id,
            "type_name": type_id,
            "color": self.color_combo.currentText()
            }
        if self.type_controller.has_same_id(delete_type) :
            self.type_controller.delete_type(type_id)
            self.refresh_signal.emit()
            self.close()
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

