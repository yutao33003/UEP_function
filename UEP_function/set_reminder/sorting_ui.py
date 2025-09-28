import math
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget, QGridLayout
from set_reminder.widget import create_button_edit, create_picture_button_edit, create_title_label_edit, create_tag_button_edit
from set_reminder.record_controller import TypeController
from set_reminder.gray_background_overlay import AddTypeCard, TypeTaskOverlay


class SortingUI(QWidget):

    switch_page = pyqtSignal(int)
    def __init__(self, min_cell_width=140):
        super().__init__()
        self.title_text = create_title_label_edit(self, "Reminders") 
        self.min_cell_width = min_cell_width
        self.square_buttons = True
        self.today_button = create_tag_button_edit(self,"today")
        self.today_button.clicked.connect(lambda: self.switch_page.emit(0))
        self.sorting_button = create_tag_button_edit(self, "sorting")
        self.sorting_button.clicked.connect(lambda: self.switch_page.emit(1))
        self.sorting_button.setStyleSheet("background: transparent; color:black;")
        self.calendar_button = create_tag_button_edit(self, "calendar")
        
        self.type_controller = TypeController()
        self.type_controller.data_change.connect(self.on_type_data_changed)

        self.add_button = create_picture_button_edit(self, "set_reminder/image/add.png", "set_reminder/image/add_hover.png", 60)
        self.add_button.clicked.connect(lambda checked : self.exit_edit_type_page("", ""))

        self.title_layout = QHBoxLayout()
        self.title_layout.addWidget(self.title_text)
        self.title_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        self.title_layout2 = QHBoxLayout()
        self.title_layout2.addWidget(self.today_button)
        self.title_layout2.addWidget(self.sorting_button)
        self.title_layout2.addWidget(self.calendar_button)
        self.title_layout2.setAlignment(Qt.AlignHCenter)
        self.title_layout2.setSpacing(20)

        self.upper_layout = QVBoxLayout()
        self.upper_layout.addLayout(self.title_layout)
        self.upper_layout.addLayout(self.title_layout2)

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(20, 10, 10, 20)
        self.main_layout.setSpacing(10)

        self.right_lower_layout = QVBoxLayout()
        self.right_lower_layout.addWidget(self.add_button)
        self.right_lower_layout.setAlignment(Qt.AlignBottom)
       
        self.grid_layout = QGridLayout()
        self.grid_layout.setContentsMargins(0, 10, 0, 0)
        self.grid_layout.setSpacing(20) 
        self.buttons = []
        self.reload_type_buttons()

        self.lower_layout = QHBoxLayout()
        self.lower_layout.addLayout(self.grid_layout)
        self.lower_layout.addLayout(self.right_lower_layout)
        
        self.main_layout.addLayout(self.upper_layout)
        self.main_layout.addLayout(self.lower_layout)      
        self.setLayout(self.main_layout)

    def reload_type_buttons(self):
        # 先清空原本的按鈕
        for btn in self.buttons:
            btn.setParent(None)
        self.buttons.clear()

        type_data = self.type_controller.load_types()
        for type_info in type_data["type"]:
            type_name = type_info.get("type_name") or type_info.get("title_name") or ""
            color = type_info.get("color", "")
            button = create_button_edit(self, type_name, color)
            button.clicked.connect(lambda _, t=type_name: self.exit_type_task(t, self))
            print(type_name)
            button.rightClicked.connect(lambda t= type_name, c = color: self.exit_edit_type_page(t, c))
            self.buttons.append(button)

        self._relayout()

    def on_type_data_changed(self, changed_id: str):
        self.reload_type_buttons()

    def _relayout(self):
        # 先清掉格子
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)

        n = len(self.buttons)
        if n == 0:
            return
        approx = int(math.sqrt(n))
        cols = max(1, approx)
        rows = math.ceil(n / cols)

        # 如果太扁，就調整 cols
        if rows * cols < n:
            cols += 1
            rows = math.ceil(n / cols)

        # 取得 layout 可用寬度
        margins = self.main_layout.contentsMargins()
        title_space = self.upper_layout.sizeHint().height() + self.main_layout.spacing() + margins.top()
        side_space = self.right_lower_layout.sizeHint().width() + self.main_layout.spacing() + margins.right()
        spacing = self.grid_layout.spacing()
        available_w = max(0, self.width() - margins.left() - side_space - approx*spacing)
        available_h = max(0, self.height() - title_space - margins.bottom())

        # 計算每格實際大小
        if cols > 0:
            cell_w = (available_w - spacing * (cols - 1)) / cols
        else:
            cell_w = self.min_cell_width

        if rows > 0:
            cell_h = (available_h - spacing * (rows - 1)) / rows
        else:
            cell_h = 40

        # 依序放入格子
        for idx, btn in enumerate(self.buttons):
            r = idx // cols
            c = idx % cols
            self.grid_layout.addWidget(btn, r, c)

      # 設定按鈕大小
        if self.square_buttons:
            size = int(min(cell_w, cell_h))
            size = max(40, size)
            for btn in self.buttons:
                btn.setFixedSize(int(cell_w) , int(cell_h))

        else:
            for btn in self.buttons:
                btn.setMinimumHeight(40)
                btn.setMaximumHeight(16777215)

    def exit_type_task(self, type_name = "",parent = None):
        overlay = TypeTaskOverlay(parent, type_name, "reminders")
        overlay.show()

    def exit_edit_type_page(self, type_name, type_color):
        main_window = self.window()
        overlay = AddTypeCard(main_window, type_name, type_color, self.type_controller)
        overlay.show()


