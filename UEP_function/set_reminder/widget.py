from PyQt5.QtGui import QColor, QFont, QFontDatabase
from PyQt5.QtWidgets import QGraphicsDropShadowEffect, QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget
from PyQt5.QtWidgets import QPushButton
from set_reminder.right_click_btn import RightClickButton


def create_button_edit(parent, text, color):
    button = RightClickButton(parent)
    button.setText(text)
    hover_color = adjust_color(color)
    button.setStyleSheet(f"""
        QPushButton {{
            background-color: {color};
            color: white;
            border-radius: 10px;
            padding: 8px;
        }}
        QPushButton:hover {{
            background-color: {hover_color};
        }}
    """)
    
    cust_font = font_setting(16)
    button.setFont(cust_font)
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(20)
    shadow.setOffset(3, 3)
    shadow.setColor(QColor(0, 0, 0, 120))
    button.setGraphicsEffect(shadow)
    return button

def adjust_color(color_code, factor = 0.8):
    color = QColor(color_code)
    h, s, l, a = color.getHsl()
    l = min(255, int(l * factor))
    adjusted_color = QColor.fromHsl(h, s, l, a)
    return adjusted_color.name()

def create_tag_button_edit(parent, text):
    tag_button = QPushButton(parent)
    tag_button.setText(text)
    tag_button.setStyleSheet("""
        QPushButton {
            background: transparent;
            color: #8c8a88;
            padding: 5px 10px;
        }
        QPushButton:hover {
            color: #363432;
        }
    """)
    cust_font = font_setting(12)
    tag_button.setFont(cust_font)
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(15)
    shadow.setOffset(2, 2)
    shadow.setColor(QColor(0, 0, 0, 100))
    tag_button.setGraphicsEffect(shadow)
    return tag_button

def create_picture_button_edit(parent, icon_path, icon_hover_path, size):
    pic_button = QPushButton(parent)
    pic_button.setFixedSize(size, size)
    pic_button.setStyleSheet(f"""
        QPushButton {{
            background: transparent;
            border-image: url({icon_path});
            background-repeat: no-repeat;
            background-position: center;
            border-radius: {size//2}px;
        }}
        QPushButton:hover {{
            border-image: url({icon_hover_path});
        }}
    """)
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(15)
    shadow.setOffset(2, 2)
    shadow.setColor(QColor(0, 0, 0, 100))
    pic_button.setGraphicsEffect(shadow)
    return pic_button

def create_title_label_edit(parent, text):
    title_edit = QLabel(parent) 
    title_edit.setFixedSize(400, 50)
    title_edit.setText(text)
    cust_font = font_setting(20)
    title_edit.setFont(cust_font)
    return title_edit
    
def font_setting(font_size):
    font_id = QFontDatabase.addApplicationFont(r"set_reminder\CaviarDreams-Bold-2.ttf")
    font_families = QFontDatabase.applicationFontFamilies(font_id)
    if font_families:
        cust_font = QFont(font_families[0], font_size)
    return cust_font

def create_text_edit(parent, placeholder):
    line_edit = QTextEdit(placeholder)
    line_edit.setStyleSheet("""
        QTextEdit {
            border: 1px solid #ccc;
            border-radius: 5px;
            padding: 5px;
        }
        QTextEdit:focus {
            border: 1px solid #4A90E2;
        }
    """)
    cust_font = font_setting(10)
    line_edit.setFont(cust_font)
    return line_edit
