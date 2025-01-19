import sys
import os
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtWidgets import QApplication, QLabel, QHBoxLayout

from ui.BaseWindow import BaseWindow

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class StatusWindow(BaseWindow):
    def __init__(self, show_title=False):
        """
        Initialize the status window.
        """
        super().__init__('chirp :)', 200, 40, show_title)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
                            | Qt.WindowType.Tool | Qt.WindowType.WindowDoesNotAcceptFocus)

        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(0, 0, 0, 0)

        self.icon_label = QLabel()
        self.icon_label.setFixedSize(15, 15)
        microphone_path = os.path.join('assets', 'chirp-logo.png')
        pencil_path = os.path.join('assets', 'transcribing.png')
        thinking_path = os.path.join('assets', 'thinking.png')
        self.microphone_pixmap = QPixmap(
            microphone_path).scaled(15, 15, Qt.AspectRatioMode.KeepAspectRatio,
                                    Qt.TransformationMode.SmoothTransformation)
        self.pencil_pixmap = QPixmap(
            pencil_path).scaled(15, 15, Qt.AspectRatioMode.KeepAspectRatio,
                                Qt.TransformationMode.SmoothTransformation)
        self.thinking_pixmap = QPixmap(
            thinking_path).scaled(15, 15, Qt.AspectRatioMode.KeepAspectRatio,
                                Qt.TransformationMode.SmoothTransformation)
        self.icon_label.setPixmap(self.microphone_pixmap)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.status_label = QLabel('Recording...')
        self.status_label.setFont(QFont('Segoe UI', 10))
        self.status_label.setStyleSheet("color: #505050;")

        status_layout.addStretch(1)
        status_layout.addWidget(self.icon_label)
        status_layout.addWidget(self.status_label)
        status_layout.addStretch(1)

        self.main_layout.addLayout(status_layout)

    def show(self):
        """
        Position the window in the bottom center of the screen and show it.
        """
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()
        window_width = self.width()
        window_height = self.height()

        x = (screen_width - window_width) // 2
        y = screen_height - window_height - 100 

        self.move(x, y)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        super().show()

    def show_message(self, message):
        """
        Update the status window based on the given status.
        """
        if 'recording' in message or 'streaming' in message:
            self.icon_label.setPixmap(self.microphone_pixmap)

        elif 'Transcribing' in message:
            self.icon_label.setPixmap(self.pencil_pixmap)
        
        elif 'Inferring' in message:
            self.icon_label.setPixmap(self.thinking_pixmap)

        self.status_label.setText(message)
        self.show()

    def focusInEvent(self, event):
        self.clearFocus()
        event.ignore()
