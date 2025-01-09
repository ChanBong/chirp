import sys
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QLabel
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QGuiApplication


class TimedPopup(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Make the window frameless, always on top, and allow setting opacity
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint 
            | Qt.WindowType.WindowStaysOnTopHint
        )
        
        # Set 50% window opacity
        self.setWindowOpacity(0.8)

        # Use a 5-second timer to auto-close
        self._timer = QTimer(self)
        # TODO: get from config
        self._timer.setInterval(5000)     # 5 seconds
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.close)

        # Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)  # A bit of padding
        self.setLayout(layout)

        # Title and message labels
        self.title_label = QLabel("Title", self)
        self.message_label = QLabel("Message", self)

        # Enable word wrap and set a max width on the message
        self.message_label.setWordWrap(True)
        # TODO: get from config
        self.message_label.setMaximumWidth(300)

        # Set font size
        font = self.message_label.font()
        font.setPointSize(12)
        self.message_label.setFont(font)

        layout.addWidget(self.title_label)
        layout.addWidget(self.message_label)

        # Enable mouse tracking to detect enter/leave events
        self.setMouseTracking(True)

    def show_popup(self, title: str, message: str):
        """
        Show the pop-up with the given title and message.
        Positions it in the top-right corner of the primary screen.
        """
        self.title_label.setText(f"<b>{title}</b>")
        self.message_label.setText(message)

        # Resize to fit content before moving to top right
        self.adjustSize()

        # Move the pop-up to the top-right corner of the primary screen
        screen_geom = QGuiApplication.primaryScreen().geometry()
        x = screen_geom.right() - self.width() - 10
        y = screen_geom.top() + 10
        self.move(x, y)

        # Start or restart the timer for auto-close
        self._timer.start()
        self.show()

    def enterEvent(self, event):
        """
        Stop the auto-close timer when the mouse enters the pop-up.
        """
        self._timer.stop()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """
        Restart the auto-close timer when the mouse leaves the pop-up.
        """
        self._timer.start()
        super().leaveEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    popup = TimedPopup()

    lorem_ipsum = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."

    popup.show_popup(
        title="vanilla", 
        message=lorem_ipsum
    )

    sys.exit(app.exec())
