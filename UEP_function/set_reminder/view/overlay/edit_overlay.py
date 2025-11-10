from PyQt5.QtGui import QCursor, QIcon
from PyQt5.QtWidgets import (
     QCheckBox, QComboBox, QDateTimeEdit, QFrame, QHBoxLayout, QLineEdit, QPlainTextEdit, QScrollArea, QSizePolicy, QTextEdit,
    QWidget, QVBoxLayout, QLabel, QPushButton
)
from PyQt5.QtCore import QDateTime, Qt, pyqtSignal, QEvent
from set_reminder.animate import delete_with_animation, gradually_enter_ani, gradually_exit_ani
from set_reminder.model.shared_task_state import SharedTaskState
from set_reminder.view.overlay.base_overlay import BaseOverlay
from set_reminder.view.widget.widget import create_scroll_area_edit, font_setting

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

class TaskFormWidget(QWidget):
    def __init__(self, parent=None, state: SharedTaskState = None, type_controller = None):
        super().__init__(parent)
        self._parent_widget = parent
        self._event_filter_parent = None
        self.state = state
        self.type_controller = type_controller

        self._build_ui() 
        self.connect_all_signals()

    def _build_ui(self):
        # 根 layout 減小 margins 與 spacing，避免預設造成大間距
        layout = QVBoxLayout(self)
        layout.setSpacing(1)
        
        self.title_label = QLabel("title:")
        self.title_label.setFont(font_setting(10))
        self.title_edit = QLineEdit()
        self.title_edit.setFont(font_setting(10))
        self.title_edit.setPlaceholderText("new title")
        # 減少輸入框高度
        self.title_edit.setStyleSheet("""
            QLineEdit {
                background-color: transparent;
                color:black;
                border: 1px solid #ccc;
                border-radius:6px;
                padding: 4px;
            }
        """)
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(6)
        title_layout.addWidget(self.title_label)
        title_layout.addWidget(self.title_edit)
        layout.addLayout(title_layout)

        self.type_label = QLabel("type:")
        self.type_label.setFont(font_setting(10))
        self.type_box = QComboBox()
        self.type_box.setFont(font_setting(10))

        type_layout = QHBoxLayout()
        type_layout.setContentsMargins(0,0,0,0)
        type_layout.setSpacing(6)
        type_layout.addWidget(self.type_label)
        type_layout.addWidget(self.type_box)
        layout.addLayout(type_layout)

        self.start_time_label = QLabel("start_time")
        self.start_time_label.setFont(font_setting(10))
        self.start_time = QDateTimeEdit()
        self.start_time.setFont(font_setting(10))
        self.start_time.setDisplayFormat("yyyy-MM-dd HH:mm")
        
        start_time_layout = QHBoxLayout()
        start_time_layout.setContentsMargins(0,0,0,0)
        start_time_layout.setSpacing(6)
        start_time_layout.addWidget(self.start_time_label)
        start_time_layout.addWidget(self.start_time)
        layout.addLayout(start_time_layout)

        self.end_time_label = QLabel("end_time")
        self.end_time_label.setFont(font_setting(10))
        self.end_time = QDateTimeEdit()
        self.end_time.setFont(font_setting(10))
        self.end_time.setDisplayFormat("yyyy-MM-dd HH:mm")

        end_time_layout = QHBoxLayout()
        end_time_layout.setContentsMargins(0,0,0,0)
        end_time_layout.setSpacing(6)
        end_time_layout.addWidget(self.end_time_label)
        end_time_layout.addWidget(self.end_time)
        layout.addLayout(end_time_layout)

        self.end_time.setMinimumDateTime(self.start_time.dateTime())
        self.start_time.dateTimeChanged.connect(
            lambda dt: self.end_time.setMinimumDateTime(dt)
        )

        self.desc_label = QLabel("describle")
        self.desc_label.setFont(font_setting(10))
        self.desc_label.setFixedHeight(40)

        self.desc_edit = QPlainTextEdit()
        self.desc_edit.setFont(font_setting(10))

        self.desc_edit.setFixedHeight(120)
        self.desc_edit.setStyleSheet("""
            QPlainTextEdit {
                border: 1px solid #ccc;
                border-radius:6px;
                padding: 6px;
            }
            QPlainTextEdit:focus {
                border: 1px solid #4A90E2;
            }
        """)

        layout.addWidget(self.desc_label)
        layout.addWidget(self.desc_edit)

        self.priority_label = QLabel("priority")
        self.priority_label.setFont(font_setting(10))
        self.priority_box = QComboBox()
        self.priority_box.setFont(font_setting(10))
        self.priority_box.addItems(["high", "medium", "low"])

        priority_layout = QHBoxLayout()
        priority_layout.setContentsMargins(0,0,0,0)
        priority_layout.setSpacing(6)
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

        alert_layout1 =QHBoxLayout()
        alert_layout1.setContentsMargins(0,0,0,0)
        alert_layout1.setSpacing(6)
        alert_layout1.addWidget(self.alert_label1)
        alert_layout1.addWidget(self.alert_combo1)
        layout.addLayout(alert_layout1)

        self.alert_label2 = QLabel("remind 2")
        self.alert_label2.setFont(font_setting(10))
        self.alert_combo2 = QComboBox()
        self.alert_combo2.setFont(font_setting(10))
        self.alert_combo2.addItems(remind_options)
        self.alert_combo2.setFixedHeight(40)

        alert_layout2 =QHBoxLayout()
        alert_layout2.setContentsMargins(0,0,0,0)
        alert_layout2.setSpacing(6)
        alert_layout2.addWidget(self.alert_label2)
        alert_layout2.addWidget(self.alert_combo2)
        layout.addLayout(alert_layout2)

        self.repeat_check = QCheckBox("是否重複")
        # 減小 checkbox 與上方元素間距
        layout.addWidget(self.repeat_check, stretch=0)


    def connect_all_signals(self):
        """連接所有 9 個 UI 元件到 state 的更新方法"""
        self.title_edit.textChanged.connect(self.on_title_changed)
        self.type_box.currentTextChanged.connect(self.on_type_changed)
        self.start_time.dateTimeChanged.connect(self.on_start_time_changed)
        self.end_time.dateTimeChanged.connect(self.on_end_time_changed)
        self.desc_edit.textChanged.connect(self.on_desc_changed)
        self.priority_box.currentTextChanged.connect(self.on_priority_changed)
        self.alert_combo1.currentTextChanged.connect(self.on_alert1_changed)
        self.alert_combo2.currentTextChanged.connect(self.on_alert2_changed)
        self.repeat_check.stateChanged.connect(self.on_repeat_changed)

    def on_title_changed(self, text):
        if self.state: self.state.title = text

    def on_type_changed(self, text):
        if self.state: self.state.type = text

    def on_start_time_changed(self, q_datetime):
        if self.state:
            self.state.start_time = q_datetime.toString("yyyy-MM-dd HH:mm")

    def on_end_time_changed(self, q_datetime):
        if self.state:
            self.state.end_time = q_datetime.toString("yyyy-MM-dd HH:mm")

    def on_desc_changed(self):
        # QPlainTextEdit 的 textChanged 訊號*沒有*參數
        if self.state:
            self.state.description = self.desc_edit.toPlainText()

    def on_priority_changed(self, text):
        if self.state:
            self.state.priority = text

    def on_alert1_changed(self, text):
        if self.state:
            self.state.alert1 = text

    def on_alert2_changed(self, text):
        if self.state:
            self.state.alert2 = text

    def on_repeat_changed(self, state_int):
        if self.state:
            self.state.repeat = (state_int == Qt.Checked)

    def sync_ui_from_state(self):
        """
        從 self.state 讀取資料來填滿 UI。
        這是為了在 View 顯示時，確保資料是最新的。
        """
        if not self.type_controller:
            print("TaskFormWidget: 沒有 type_controller，無法同步類型選單")
            return

        all_type_data = self.type_controller.load_types().get("type", [])
        existing_items = [self.type_box.itemText(i) for i in range(self.type_box.count())]

        for item in all_type_data:
            type_name = item["type_name"]
            if type_name not in existing_items:
                self.type_box.addItem(type_name)

        if not self.state:
            print("TaskFormWidget: 沒有 state 可同步")
            return

        # 關鍵！在填充 UI 時，暫時停止訊號
        self.blockSignals(True)
        
        self.title_edit.setText(self.state.title)
        self.type_box.setCurrentText(self.state.type)
        self.start_time.setDateTime(QDateTime.fromString(self.state.start_time, "yyyy-MM-dd HH:mm"))
        self.end_time.setDateTime(QDateTime.fromString(self.state.end_time, "yyyy-MM-dd HH:mm"))
        self.desc_edit.setPlainText(self.state.description)
        self.priority_box.setCurrentText(self.state.priority)
        self.alert_combo1.setCurrentText(self.state.alert1)
        self.alert_combo2.setCurrentText(self.state.alert2)
        self.repeat_check.setChecked(self.state.repeat)
        
        # 填充完畢，恢復訊號
        self.blockSignals(False)

    def change_parent_widget(self, new_parent):
        """更換用來監聽 Resize 事件的參考 widget，但不改變實際 parent

        為了避免把 widget 從原本的 layout 中移出（造成被覆蓋或佈局錯亂），
        我們不執行 setParent(new_parent)。改為把 new_parent 當作「尺寸參考」並
        在上面安裝 eventFilter（監聽 Resize），同時呼叫一次 _on_parent_resized() 做同步。
        """
        # 1. 移除舊的 eventFilter (如果你之前安裝過的話)
        if self._event_filter_parent is not None:
            try:
                self._event_filter_parent.removeEventFilter(self)
            except Exception:
                pass

        # 2. 決定實際要監聽的目標（若傳入的是 TypeTaskOverlay，使用其 content_area）
        resize_target = new_parent
        try:
            from set_reminder.view.overlay.gray_background_overlay import TypeTaskOverlay
            if isinstance(new_parent, TypeTaskOverlay):
                resize_target = getattr(new_parent, "content_area", new_parent)
        except Exception:
            pass

        # 3. 安裝新的 eventFilter 並做首次同步（但不改變 Qt 的 parent）
        self._event_filter_parent = resize_target
        if self._event_filter_parent is not None:
            try:
                self._event_filter_parent.installEventFilter(self)
                self._on_parent_resized()  # 初次同步大小
            except Exception:
                self._event_filter_parent = None

        # 4. 確保 Widget 知道它可能需要重繪/重新佈局
        self.updateGeometry()


    def eventFilter(self, obj, event):
        # 監聽參考父層的 Resize 事件
        from PyQt5.QtCore import QEvent
        if obj is getattr(self, '_event_filter_parent', None) and event.type() == QEvent.Resize:
            self._on_parent_resized()
        return super().eventFilter(obj, event)

    def set_state_and_sync(self, state: SharedTaskState, new_parent = None):
        """
        這是「公開 API」，讓容器 (EditTaskWidget) 
        可以注入 state 並觸發第一次 UI 同步。
        """
        self.state = state
        if new_parent:
            # 調整尺寸參考以適應新的父層（但不移動 widget 本身）
            from set_reminder.view.overlay.gray_background_overlay import TypeTaskOverlay
            if isinstance(new_parent, TypeTaskOverlay):
                # 如果父層是TypeTaskOverlay，設定合適的最小寬度（僅作為顯示建議）
                self.setMinimumWidth(400)  # 或其他適合的值
            else:
                # 重設最小寬度
                self.setMinimumWidth(0)

            self.change_parent_widget(new_parent)
        self.sync_ui_from_state()
        
    def _on_parent_resized(self):
        """根據參考父層尺寸調整自身尺寸（不再假設參考父層就是實際 parent）"""
        ref = getattr(self, '_event_filter_parent', None)
        if not ref:
            return
        try:
            margin = 24  # 保留左右內距

            # 若參考物件為 TypeTaskOverlay，嘗試使用其 content_area
            try:
                from set_reminder.view.overlay.gray_background_overlay import TypeTaskOverlay
                if isinstance(ref, TypeTaskOverlay):
                    if hasattr(ref, 'content_area'):
                        ref_width = ref.content_area.width()
                    else:
                        ref_width = ref.width()
                else:
                    ref_width = ref.width()
            except Exception:
                ref_width = ref.width()

            max_w = max(400, ref_width - margin)
            self.setMaximumWidth(max_w)
            self.updateGeometry()
        except Exception as e:
            print(f"Error in _on_parent_resized: {e}")

    def showEvent(self, event):
        """
        在 Widget 顯示時，也自動同步一次。
        這能確保在 Desktop/Mobile 切換時，資料永遠是新的。
        """
        self.sync_ui_from_state()
        super().showEvent(event)


# 編輯事件頁清單
class EditTaskWidget(BaseOverlay):

    confirmed_requested = pyqtSignal()
    back_requested = pyqtSignal()

    def __init__(self, parent=None, state: SharedTaskState = None, type_controller = None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Widget)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setGeometry(parent.rect())

        self.setStyleSheet("background-color: rgba(0, 0, 0, 120);") 
        
        self.state = state
        self.task_id = self.state.id if self.state else ""
        self.type_controller = type_controller

        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)

        scroll = create_scroll_area_edit()
        scroll.setWidgetResizable(True)
        scroll.viewport().setStyleSheet("background: transparent;")
        main_layout.addWidget(scroll)

        container = QWidget()
        container.setStyleSheet("""
            background-color: #E4DCCF;
            border: none;
            padding:3px;
            border-radius: 25px;
        """)

        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignCenter)

        back_btn = QPushButton("◀️")   
        back_btn.setFont(font_setting(18))
        back_btn.clicked.connect(self.back_requested)

        upper_layout = QHBoxLayout()
        upper_layout.addWidget(back_btn, alignment=Qt.AlignLeft)
        layout.addLayout(upper_layout)

        self.form = TaskFormWidget(parent=parent, state = self.state , type_controller = self.type_controller)
        layout.addWidget(self.form)

        save_btn = QPushButton("save")
        save_btn.setFont(font_setting(10))
        save_btn.setStyleSheet("background: #7D9D9C; color: white; padding: 8px; border-radius: 8px;")
        save_btn.clicked.connect(self.confirmed_requested)
        layout.addWidget(save_btn, alignment=Qt.AlignCenter)

        scroll.setWidget(container)      

    def reparent_to(self, state=None, new_parent=None):
        """
        動態更換父層，確保以「浮層」方式嵌入，不干擾父層 layout。
        """
        if new_parent is None or state is None:
            return

        # 更新父層與狀態
        self.setParent(new_parent)
        self.state = state
        self.setGeometry(new_parent.rect())
        self.raise_()
        self.show()

        # 同步表單內容
        if hasattr(self, "form"):
            self.form.set_state_and_sync(self.state, new_parent)

        print(f"[reparent_to] EditTaskWidget 以浮層形式嵌入 {type(new_parent).__name__}")


    def showEvent(self, event):
        super().showEvent(event)
        parent = self.parent()
        if parent:
            parent.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj == self.parent() and event.type() == QEvent.Resize:
            self.setGeometry(obj.rect())
        return super().eventFilter(obj, event)


class EditTaskOverlay(BaseOverlay):
    confirmed_requested = pyqtSignal()
    back_requested = pyqtSignal()

    def __init__(self, parent, state: SharedTaskState = None, type_controller=None):
        super().__init__(parent)

        # === Overlay 層設定 ===
        self.setWindowFlags(Qt.Widget)
        self.setGeometry(parent.rect())
        self.setStyleSheet("background-color: transparent;")

        # 半透明背景
        self.overlay_bg = QFrame(self)
        self.overlay_bg.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 120);
                border-radius: 15px;
            }
        """)
        self.overlay_bg.setGeometry(self.rect())

        # 狀態設定
        self.state = state
        self.task_id = self.state.id if self.state else ""
        self.type_controller = type_controller

        # === 主 layout ===
        main_layout = QVBoxLayout(self.overlay_bg)
        # 減小 overlay 內部 margin/spacing
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)
        main_layout.setAlignment(Qt.AlignCenter)

        # === Scroll 區域 ===
        scroll = create_scroll_area_edit()
        scroll.setWidgetResizable(True)
        scroll.setAlignment(Qt.AlignCenter)
        scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical, QScrollBar:horizontal {
                background: transparent;
            }
        """)
        main_layout.addWidget(scroll)

        # === Container ===
        self.container = QWidget()
        self.container.setStyleSheet("""
            QWidget {
                background-color: #E4DCCF;
                border-radius: 12px;
                padding: 10px;
            }
        """)

        self.container.setFixedWidth(520)
        self.container.setMaximumHeight(720)
        self.container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)

        scroll.setWidget(self.container)

        # === 內容布局 ===
        layout = QVBoxLayout(self.container)
        # 減少內部 layout 間距
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignTop)

        # 返回按鈕
        back_btn = QPushButton("◀️")
        back_btn.setFont(font_setting(18))
        back_btn.setStyleSheet("border: none; background: transparent;")
        back_btn.clicked.connect(self.back_requested)

        upper_layout = QHBoxLayout()
        upper_layout.setContentsMargins(0,0,0,0)
        upper_layout.addWidget(back_btn, alignment=Qt.AlignLeft)
        layout.addLayout(upper_layout)

        # 表單內容：把 parent 指向 container，讓 layout 管理
        self.form = TaskFormWidget(
            parent=self.container,
            state=self.state,
            type_controller=self.type_controller
        )
        layout.addWidget(self.form)

        # 儲存按鈕 (縮小 padding)
        save_btn = QPushButton("Save")
        save_btn.setFont(font_setting(11))
        save_btn.setFixedWidth(90)
        save_btn.setStyleSheet("""
            QPushButton {
                background: #7D9D9C;
                color: white;
                padding: 8px 16px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: #576F72;
            }
        """)
        save_btn.clicked.connect(self.confirmed_requested)
        layout.addWidget(save_btn, alignment=Qt.AlignCenter)

    # === ✅ 讓 container 隨畫面大小自動置中 ===
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.overlay_bg.setGeometry(self.rect())

        # 當 overlay 足夠大時，讓 scroll 自動隱藏滾動條，容器置中顯示
        available_w = self.width()
        available_h = self.height()
        container_h = self.container.sizeHint().height()

        # 若畫面足夠高，則取消滾動並垂直置中
        scroll = self.overlay_bg.findChild(QScrollArea)
        if container_h + 120 < available_h:
            if scroll:
                scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                scroll.setAlignment(Qt.AlignCenter)
        else:
            if scroll:
                scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
                scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)