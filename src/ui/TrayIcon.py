import os
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QPixmap


class TrayIcon(QObject):
    open_settings = pyqtSignal()
    close_app = pyqtSignal()
    message_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.tray_icon = None
        self.create_tray_icon()

    def create_tray_icon(self):
        app = QApplication.instance()
        icon_path = os.path.join('assets', 'chirp-logo.png')

        self.tray_icon = QSystemTrayIcon(QIcon(icon_path), app)

        tray_menu = QMenu()

        settings_action = QAction('Open Settings', app)
        settings_action.triggered.connect(self.open_settings.emit)
        tray_menu.addAction(settings_action)

        exit_action = QAction('Exit', app)
        exit_action.triggered.connect(self.close_app.emit)
        tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(tray_menu)

    def on_message_clicked(self):
        # Re-emit so UIManager can pick it up
        self.message_clicked.emit()

    def show(self):
        if self.tray_icon:
            self.tray_icon.show()

    def hide(self):
        if self.tray_icon:
            self.tray_icon.hide()
