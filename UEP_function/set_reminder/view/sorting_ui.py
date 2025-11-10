import math
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtWidgets import (
    QHBoxLayout, QVBoxLayout, QWidget, QGridLayout, 
    QSizePolicy
)
from set_reminder.animate import gradually_enter_ani
from set_reminder.view.widget.widget import (
    create_picture_button_edit, create_title_label_edit, create_tag_button_edit, create_button_edit, create_type_button_edit
)


class SortingUI(QWidget):
    switch_page = pyqtSignal(int)
    
    def __init__(self, event_adapter=None, overlay_ctrl=None, type_ctrl=None, task_service = None, min_cell_width=140):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 存儲基礎參數
        self.event_adapter = event_adapter
        self.type_controller = type_ctrl
        self.overlay_controller = overlay_ctrl
        self.task_service = task_service
        self.min_cell_width = min_cell_width
        self.buttons = []
        self.square_buttons = True

        self._setup_ui()
        self._connect_signals()
        
        # 延遲重新布局的計時器
        self._relayout_timer = QTimer()
        self._relayout_timer.setSingleShot(True)
        self._relayout_timer.timeout.connect(self._relayout)

    def _setup_ui(self):
        # 標題區域
        self.title_text = create_title_label_edit(self, "Reminders")
        self.title_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        # 導航按鈕
        self.today_button = create_tag_button_edit(self, "today")
        self.sorting_button = create_tag_button_edit(self, "sorting")
        self.calendar_button = create_tag_button_edit(self, "calendar")
        self.sorting_button.setStyleSheet("background: transparent; color:black;")
        
        # 新增按鈕
        self.add_button = create_picture_button_edit(
            self, 
            "set_reminder/image/add.png",
            "set_reminder/image/add_hover.png",
            60
        )

        # 布局設置
        self._setup_layouts()
        self.reload_type_buttons()

    def _setup_layouts(self):
        # 標題布局
        title_layout = QHBoxLayout()
        title_layout.addWidget(self.title_text)
        title_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        # 導航按鈕布局
        nav_layout = QHBoxLayout()
        nav_layout.addWidget(self.today_button)
        nav_layout.addWidget(self.sorting_button)
        nav_layout.addWidget(self.calendar_button)
        nav_layout.setAlignment(Qt.AlignHCenter)
        nav_layout.setSpacing(10)

        # 上方布局組合
        self.upper_layout = QVBoxLayout()
        self.upper_layout.addLayout(title_layout)
        self.upper_layout.addLayout(nav_layout)

        # 網格布局（用於類型按鈕）
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(20)

        # 右下方布局（新增按鈕）
        self.right_lower = QVBoxLayout()
        self.right_lower.addWidget(self.add_button)
        self.right_lower.setAlignment(Qt.AlignBottom)

        # 下方布局組合
        lower_layout = QHBoxLayout()
        lower_layout.addLayout(self.grid_layout)
        lower_layout.addLayout(self.right_lower)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.addLayout(self.upper_layout)
        main_layout.addLayout(lower_layout)

    def _connect_signals(self):
        self.today_button.clicked.connect(lambda: self.switch_page.emit(0))
        self.sorting_button.clicked.connect(lambda: self.switch_page.emit(1))
        self.calendar_button.clicked.connect(lambda: self.switch_page.emit(2))
        self.add_button.clicked.connect(
            lambda checked: self.exit_edit_type_page("", "")
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 使用計時器延遲執行重新布局，避免過於頻繁刷新
        self._relayout_timer.start(100)

    def _relayout(self):
        """根據可用空間自動計算最合適的 rows/cols 並讓按鈕填滿畫面，
        同時盡量維持按鈕寬高比在 1.2~1.8 範圍內。
        """
        if not self.buttons:
            return

        spacing = self.grid_layout.spacing()
        # 保守地預留右側新增按鈕寬度與一些外邊距
        right_w = self.right_lower.sizeHint().width() + 20
        available_width = max(200, self.width() - right_w - 40)
        available_height = max(200, self.height() - self.upper_layout.sizeHint().height() - 20)

        n = len(self.buttons)
        min_ratio = 1.2
        max_ratio = 1.8

        # 限制最多的 cols 為不超過按鈕數，且不超過 available_width/min_cell_width
        max_possible_cols = min(n, max(1, int(available_width / self.min_cell_width)))
        best = None  # (score, cols, rows, cell_w, cell_h)

        for cols in range(1, max_possible_cols + 1):
            rows = math.ceil(n / cols)
            cell_w = (available_width - (cols - 1) * spacing) / cols
            cell_h = (available_height - (rows - 1) * spacing) / rows
            if cell_w <= 0 or cell_h <= 0:
                continue
            ratio = cell_w / cell_h

            # penalty：越在目標 ratio 內越好，且寬度低於最小寬度會被懲罰
            penalty = 0.0
            if ratio < min_ratio:
                penalty += (min_ratio - ratio) * 100.0
            elif ratio > max_ratio:
                penalty += (ratio - max_ratio) * 100.0

            if cell_w < self.min_cell_width:
                penalty += (self.min_cell_width - cell_w) * 50.0

            # tie-breaker: prefer larger area (負值讓 area 大的更好)
            area = cell_w * cell_h
            score = penalty - area * 1e-3

            if best is None or score < best[0]:
                best = (score, cols, rows, cell_w, cell_h, ratio)

        if best is None:
            cols = 1
            rows = n
            cell_w = max(self.min_cell_width, available_width)
            cell_h = max(40, (available_height - (rows - 1) * spacing) / rows)
        else:
            _, cols, rows, cell_w, cell_h, _ = best

        # 清除 grid_layout 目前的項目（只移除，不刪除 widget）
        for i in reversed(range(self.grid_layout.count())):
            item = self.grid_layout.takeAt(i)
            w = item.widget()
            if w:
                self.grid_layout.removeWidget(w)

        # 計算按鈕最終寬高，嘗試將 ratio 鎖在目標範圍
        btn_w = cell_w
        btn_h = cell_h
        cur_ratio = btn_w / max(1.0, btn_h)

        if cur_ratio < min_ratio:
            # 以寬為主，增加高度以接近 min_ratio
            btn_h = max(40, btn_w / min_ratio)
        elif cur_ratio > max_ratio:
            # 以高為主，減少寬度以接近 max_ratio
            btn_w = max(self.min_cell_width, btn_h * max_ratio)

        # 護欄
        btn_w = max(self.min_cell_width, btn_w)
        btn_h = max(40, btn_h)

        # 把按鈕加入 grid，並設定固定大小，讓按鈕填滿格子
        for idx, btn in enumerate(self.buttons):
            r = idx // cols
            c = idx % cols
            self.grid_layout.addWidget(btn, r, c)
            # 讓每個 column 有相同伸展性
            self.grid_layout.setColumnStretch(c, 1)
            btn.setFixedSize(int(btn_w), int(btn_h))

    def reload_type_buttons(self):
        # 清除現有按鈕（從 layout 移除）
        for btn in self.buttons:
            btn.setParent(None)
        self.buttons.clear()

        # 載入類型數據
        type_data = self.type_controller.load_types()
        for type_info in type_data["type"]:
            type_name = type_info.get("type_name") or type_info.get("title_name") or ""
            color = type_info.get("color", "")
            
            button = create_type_button_edit(type_name, color, parent = self)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            
            # 連接信號
            button.clicked.connect(
                lambda checked, t=type_name: self.overlay_controller.show(
                    "task_overlay",
                    parent=self,
                    mode="feature",
                    task_type=t,
                    event_adapter=self.event_adapter,
                    type_controller = self.type_controller,
                    task_service = self.task_service,
                    is_overlay = True
                )
            )
            button.rightClicked.connect(
                lambda t=type_name, c=color: self.exit_edit_type_page(t, c)
            )
            
            self.buttons.append(button)

        self._relayout()

    def exit_edit_type_page(self, type_name, type_color):
        main_window = self.window()
        add_type_overlay = self.overlay_controller.show(
            "type_edit_overlay",
            parent=main_window,
            title=type_name,
            color=type_color,
            type_controller = self.type_controller
        )
        add_type_overlay.refresh_signal.connect(lambda : self.reload_type_buttons())





