from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QScrollArea, QWidget, QTextEdit
from PyQt6.QtCore import Qt

class ScrollableMessageDialog(QDialog):
    def __init__(self, message, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Full Message")

        layout = QVBoxLayout()
        self.setLayout(layout)

        # A read-only QTextEdit is often easier than a QScrollArea+QLabel for big text
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setPlainText(message)

        layout.addWidget(text_edit)

        self.resize(500, 400)  # A default size (adjust as you like)
