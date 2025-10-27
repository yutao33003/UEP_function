# calendar_widget.py
from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QVBoxLayout, QHBoxLayout
from PyQt5.QtCore import pyqtSignal
from set_reminder.view.widget.widget import create_date_button_edit, font_setting

class CalendarWidget(QWidget):
    date_selected = pyqtSignal(str)       # emit 'YYYY-MM-DD'
    month_changed = pyqtSignal(int,int)   # emit year, month

    def __init__(self, model, styles=None):
        super().__init__()
        self.model = model
        self.styles = styles
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 50, 10, 50) # 左、上、右、下
        header = QHBoxLayout()
        self.lbl_title = QLabel()
        self.lbl_title.setFont(font_setting(12))
        btn_prev = create_date_button_edit()
        btn_prev.setText("◀")
        btn_next = create_date_button_edit()
        btn_next.setText("▶")
        btn_prev.clicked.connect(self.on_prev)
        btn_next.clicked.connect(self.on_next)

        header.addWidget(self.lbl_title)
        header.addStretch()
        header.addWidget(btn_prev)
        header.addWidget(btn_next)
        layout.addLayout(header)

        self.grid = QGridLayout()
        self.day_buttons = []
        for r in range(6):
            row = []
            for c in range(7):
                b = create_date_button_edit()
                b.clicked.connect(self._on_day_clicked)
                b.setProperty("iso", None)
                row.append(b)
                self.grid.addWidget(b, r, c)
            self.day_buttons.append(row)
        layout.addLayout(self.grid)
        layout.setStretch(0,1)
        layout.setStretch(1,7)
        self.setLayout(layout)
        self.refresh()

    def refresh(self):
        self.lbl_title.setText(f"{self.model.year}-{self.model.month:02d}")
        matrix = self.model.get_month_matrix()
        for r in range(6):
            for c in range(7):
                cell = matrix[r][c]
                btn = self.day_buttons[r][c]
                if cell.date:
                    btn.setText(str(cell.date.day))
                    btn.setEnabled(cell.in_month)
                    btn.setProperty("iso", cell.date.isoformat())
                else:
                    btn.setText("")
                    btn.setEnabled(False)
                    btn.setProperty("iso", None)

    def _on_day_clicked(self):
        btn = self.sender()
        iso = btn.property("iso")
        if iso:
            self.date_selected.emit(iso)

    def on_prev(self):
        self.model.go_prev()
        self.refresh()
        self.month_changed.emit(self.model.year, self.model.month)

    def on_next(self):
        self.model.go_next()
        self.refresh()
        self.month_changed.emit(self.model.year, self.model.month)