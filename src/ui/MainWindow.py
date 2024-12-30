import os
import sys
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QPushButton, QHBoxLayout, QVBoxLayout
from PyQt6.QtCore import pyqtSignal

from ui.BaseWindow import BaseWindow

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class MainWindow(BaseWindow):
    open_settings = pyqtSignal()
    start_listening = pyqtSignal()
    close_app = pyqtSignal()

    def __init__(self):
        """
        Initialize the main window.
        """
        # Make the window a bit smaller to achieve a sleek rectangle shape
        super().__init__('chirp', 250, 70)
        self.initMainUI()
        # self.set_custom_styles()

    def initMainUI(self):
        """
        Initialize the main user interface.
        """
        # Create smaller buttons
        start_btn = QPushButton('Start')
        start_btn.setFont(QFont('Segoe UI', 9))
        start_btn.setFixedSize(80, 30)
        start_btn.clicked.connect(self.start_pressed)

        settings_btn = QPushButton('Settings')
        settings_btn.setFont(QFont('Segoe UI', 9))
        settings_btn.setFixedSize(80, 30)
        settings_btn.clicked.connect(self.open_settings.emit)

        # Create an HBox layout to hold the buttons side by side
        button_layout = QHBoxLayout()
        # You can tweak spacing and margins to taste
        button_layout.setSpacing(10)
        button_layout.addStretch(1)
        button_layout.addWidget(start_btn)
        button_layout.addWidget(settings_btn)
        button_layout.addStretch(1)

        # You likely have a main_layout from BaseWindow; 
        # ensure it’s a QVBoxLayout so we have vertical stacking
        # We remove (or reduce) vertical stretches to tighten the layout
        self.main_layout.addLayout(button_layout)

    def set_custom_styles(self):
        """
        Apply custom styles to achieve a light-blue background and a modern button style.
        """
        # Light blue background for the main window
        self.setStyleSheet("""
            QMainWindow {
                background-color: #D0EFFF; /* light-ish blue */
            }
            QPushButton {
                background-color: #E7F5FE;
                border: 1px solid #A0CFFF;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #C9E9FF;
            }
            QPushButton:pressed {
                background-color: #B5DFFA;
            }
        """)

    def closeEvent(self, event):
        """
        Close the application when the main window is closed.
        """
        self.close_app.emit()
        event.ignore()

    def start_pressed(self):
        """
        Emit the start_listening signal when the start button is pressed.
        """
        self.start_listening.emit()

    def hide_main_window(self):
        """
        Hide the main window.
        """
        self.hide()
