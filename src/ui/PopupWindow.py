import sys
import time
import threading

from PyQt6.QtCore import (
    Qt, QTimer, QObject, pyqtSignal, QEvent
)
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QLabel
)


class EventBus(QObject):
    """
    A simple event bus with PyQt signals to demonstrate streaming text.
    """
    start_popup = pyqtSignal(str)   # Signal to show a popup with a given title
    append_text = pyqtSignal(str)   # Signal to append partial text to the popup
    end_of_stream = pyqtSignal()    # Signal indicating the stream has ended


class TimedPopup(QDialog):
    """
    A timed pop-up that:
      - Appears in the top-right corner
      - Appends streamed text incrementally
      - Closes automatically 5s after the last text arrived, unless hovered
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        # Window flags: frameless, on top, translucent
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setWindowOpacity(0.8)  # 80% transparent

        # 5-second auto-close timer
        self._timer = QTimer(self)
        self._timer.setInterval(5000)  # 5 seconds
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.close)

        # Keep track of the current message text
        self._current_message = ""

        # Prepare layout
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(layout)

        self.title_label = QLabel("", self)
        self.message_label = QLabel("", self)
        self.message_label.setWordWrap(True)       # Wrap text
        self.message_label.setMaximumWidth(300)    # Fixed max width

        font = self.message_label.font()
        font.setPointSize(12)
        self.message_label.setFont(font)

        layout.addWidget(self.title_label)
        layout.addWidget(self.message_label)

        # Hover detection
        self.setMouseTracking(True)

    def subscribe_to_event_bus(self, event_bus: EventBus):
        """
        Connect this pop-up’s methods to the event bus signals.
        """
        event_bus.start_popup.connect(self.show_popup)
        event_bus.append_text.connect(self.append_text)
        event_bus.end_of_stream.connect(self.on_end_of_stream)


    def show_full_message_dialog(self, title: str, message: str):
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


    def show_popup(self, title: str):
        """
        Show the pop-up with an initial title. Message starts empty or minimal.
        """
        self.title_label.setText(f"<b>{title}</b>")
        self._current_message = ""
        self.message_label.setText("")
        
        # Size to fit (initially)
        self.adjustSize()

        # Position in the top-right corner of the primary screen
        screen_geom = QGuiApplication.primaryScreen().geometry()
        x = screen_geom.right() - self.width() - 10
        y = screen_geom.top() + 10
        self.move(x, y)

        # (Re)start the timer so it closes if no text arrives after 5s
        # - You can decide if you want it to close if no text is arriving
        #   or if you'd prefer to wait until end_of_stream is called.
        self._timer.start()

        self.show()

    def append_text(self, text_chunk: str):
        """
        Add new text to the message label, keep the pop-up open.
        """
        # Stop the timer if it's running, because new text arrived
        self._timer.stop()

        # Append the text to the current message
        self._current_message += text_chunk
        self.message_label.setText(self._current_message)

        # Adjust the size again if the text has grown
        self.adjustSize()

        # Reposition if needed (since size might have changed)
        screen_geom = QGuiApplication.primaryScreen().geometry()
        x = screen_geom.right() - self.width() - 10
        y = screen_geom.top() + 10
        self.move(x, y)

    def on_end_of_stream(self):
        """
        Once the stream has ended, we know no more text is coming.
        So we can start the auto-close countdown.
        """
        self._timer.start()

    def enterEvent(self, event: QEvent):
        """
        Stop the auto-close timer when the mouse enters the pop-up.
        """
        self._timer.stop()
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent):
        """
        Restart the auto-close timer when the mouse leaves the pop-up.
        """
        # Only restart if the stream is already ended or the pop-up is in final state.
        # Otherwise, you could keep stopping it upon each text chunk. 
        self._timer.start()
        super().leaveEvent(event)


def simulate_stream(event_bus: EventBus):
    """
    A mock function that simulates streaming of text.
    For a real application, this might be some async generator or
    data read from a socket, etc.
    """
    # Signal to show popup first
    event_bus.start_popup.emit("Streaming Title")

    # Send partial text in chunks
    chunks = [
        "Hello, this is the first part. ",
        "Now adding the second part. ",
        "And here's more text coming in... ",
        "Final line. "
    ]
    
    for c in chunks:
        time.sleep(1)  # simulate delay between chunks
        event_bus.append_text.emit(c)

    # Indicate end of stream
    event_bus.end_of_stream.emit()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Create our event bus
    bus = EventBus()

    # Create the TimedPopup and subscribe it to the bus
    popup = TimedPopup()
    popup.subscribe_to_event_bus(bus)

    # Start a background thread to simulate streaming
    thread = threading.Thread(target=simulate_stream, args=(bus,), daemon=True)
    thread.start()

    sys.exit(app.exec())
