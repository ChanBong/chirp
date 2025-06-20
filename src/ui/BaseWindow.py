from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QBrush, QColor, QFont, QPainterPath, QGuiApplication
from PyQt6.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QMainWindow


class BaseWindow(QMainWindow):
    def __init__(self, title, width, height, show_title=True):
        """
        Initialize the base window.
        """
        super().__init__()
        self.initUI(title, width, height, show_title)
        self.setWindowPosition()
        self.is_dragging = False

    def initUI(self, title, width, height, show_title):
        """
        Initialize the user interface.
        """
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(width, height)

        self.main_widget = QWidget(self)
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        title_bar_layout = None
        if show_title:
            # Create a widget for the title bar
            title_bar = QWidget()
            title_bar_layout = QHBoxLayout(title_bar)
            title_bar_layout.setContentsMargins(0, 0, 0, 0)
            # Add the title label
            title_label = QLabel('Chirp 🐤')
            title_label.setFont(QFont('Segoe UI', 12))
            title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            title_label.setStyleSheet("color: #404040;")
            title_bar_layout.addWidget(QWidget(), 1)  # Left spacer
            title_bar_layout.addWidget(title_label, 3)  # Title (with more width)
        # else:
            # title_bar_layout.addWidget(QWidget(), 4)  # Full-width spacer when no title

        # Create a widget for the close button
        close_button_widget = QWidget()
        close_button_layout = QHBoxLayout(close_button_widget)
        close_button_layout.setContentsMargins(0, 0, 0, 0)

        close_button = QPushButton('×')
        close_button.setFixedSize(25, 25)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #404040;
            }
            QPushButton:hover {
                color: #000000;
            }
        """)
        close_button.clicked.connect(self.handleCloseButton)

        close_button_layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignRight)

        # Add widgets to the title bar layout
        if show_title:
            title_bar_layout.addWidget(close_button_widget, 1)  # Close button
            self.main_layout.addWidget(title_bar)

        self.setCentralWidget(self.main_widget)

    def setWindowPosition(self):
        """
        Set the window position to the 1/2 of the screen width and 3/4th of the screen height.
        """
        screen_geometry = QGuiApplication.primaryScreen().availableGeometry()
        frame_geometry = self.frameGeometry()
        
        # Calculate position at 1/2 screen width and 3/4 screen height
        x = (screen_geometry.width() - frame_geometry.width()) // 2
        y = int((screen_geometry.height() - frame_geometry.height()) * 0.9)
        
        # Move window to calculated position
        self.move(x, y)

    def handleCloseButton(self):
        """
        Close the window.
        """
        self.close()

    def mousePressEvent(self, event):
        """
        Allow the window to be moved by clicking and dragging anywhere on the window.
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.start_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """
        Move the window when dragging.
        """
        if Qt.MouseButton.LeftButton and self.is_dragging:
            self.move(event.globalPosition().toPoint() - self.start_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        """
        Stop dragging the window.
        """
        self.is_dragging = False

    def paintEvent(self, event):
        """
        Create a rounded rectangle with a semi-transparent white background.
        """
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 20, 20)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(QColor(255, 255, 255, 220)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPath(path)
