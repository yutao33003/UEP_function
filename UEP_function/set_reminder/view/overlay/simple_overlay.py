from PyQt5.QtWidgets import (
    QFrame, QHBoxLayout, QWidget, QVBoxLayout, QLabel
)
from PyQt5.QtCore import Qt
from set_reminder.view.overlay.base_overlay import BaseOverlay
from set_reminder.view.widget.widget import create_button_edit, font_setting


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
