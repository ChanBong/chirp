from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                            QPushButton, QLabel, QMenuBar, QTabWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from .GeneralTab import GeneralTab
from .apps.SlackTab import SlackTab

class SettingsWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chirp")
        self.setGeometry(1175, 25, 400, 200) # x, y, width, height

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Initialize tabs with their respective classes
        self.general_tab = GeneralTab()
        self.slack_tab = SlackTab()
        
        # Add the tabs to the tab widget
        self.tab_widget.addTab(self.general_tab, "General")
        self.tab_widget.addTab(self.slack_tab, "Apps")

    def button_clicked(self):
        print("Button was clicked!") 