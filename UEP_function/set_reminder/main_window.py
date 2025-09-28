import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget
from set_reminder import sorting_ui, today_list_ui

class ReminderMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setFixedSize(600, 500)
        self.setWindowTitle("Reminder")
        self.stack = QStackedWidget()
        self.sorting_widget = sorting_ui.SortingUI()
        self.today_list_widget = today_list_ui.TodayListUI()
        self.stack.addWidget(self.today_list_widget)
        self.stack.addWidget(self.sorting_widget)
        self.stack.setCurrentIndex(0)

        pixmap_path = os.path.join(os.path.dirname(__file__), "image","background.png")
        self.stack.setStyleSheet(f"""
            QMainWindow {{
                border-image: url({pixmap_path}) 0 0 0 0 stretch stretch;
            }}
        """)
        self.today_list_widget.switch_page.connect(self.switch_page)
        self.sorting_widget.switch_page.connect(self.switch_page)

        self.setCentralWidget(self.stack)

    def switch_page(self, index):
        self.stack.setCurrentIndex(index)
        if index == 0:  # ¦^¨ì TodayListUI
            self.today_list_widget.fade_in_animation.stop()
            self.today_list_widget.opacity_effect.setOpacity(0.0)
            self.today_list_widget.fade_in_animation.start()

def main():
    app = QApplication([])
    w = ReminderMainWindow()
    w.show()
    app.exec_()

if __name__ == "__main__":
    main()