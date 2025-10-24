from PyQt5.QtWidgets import QPushButton,QMessageBox
from PyQt5.QtCore import Qt, pyqtSignal

class RightClickButton(QPushButton):
    rightClicked = pyqtSignal()

    def __init__(self, parent = None, text = ""):
        super().__init__(text, parent)

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.rightClicked.emit()
        elif event.button() == Qt.LeftButton:
            self.clicked.emit()
        
        super().mousePressEvent(event)