from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QIcon

from ui.MainWindow import MainWindow
from ui.SettingsWindow import SettingsWindow
from ui.StatusWindow import StatusWindow
from ui.TrayIcon import TrayIcon
from ui.ScrollWindow import ScrollableMessageDialog
from ui.PopupWindow import TimedPopup
from config_manager import ConfigManager
from console_manager import console
from rich import print as rprint

class UIManager:
    """
    The UIManager class is responsible for managing all user interface components of
    the application. It handles the creation and interaction of various windows (main, settings,
    status) and the system tray icon. This class serves as the central point for UI-related
    operations and events.
    """
    def __init__(self, event_bus):
        """Initialize the UIManager with the event bus."""
        self.event_bus = event_bus
        self.is_closing = False
        self.status_update_mode = "Window"

        self.main_window = MainWindow()
        self.settings_window = SettingsWindow()
        self.status_window = StatusWindow(show_title=False)
        self.tray_icon = TrayIcon()
        self.popup_window = TimedPopup()
        self.long_message_cache = None

        self.setup_connections()

    def setup_connections(self):
        """Establish connections between UI components and their corresponding actions."""
        self.main_window.open_settings.connect(self.settings_window.show)
        self.main_window.start_listening.connect(self.handle_start_listening)
        self.main_window.close_app.connect(self.initiate_close)
        self.tray_icon.open_settings.connect(self.settings_window.show)
        self.tray_icon.close_app.connect(self.initiate_close)
        self.tray_icon.message_clicked.connect(self.handle_tray_message_clicked)
        self.event_bus.subscribe("quit_application", self.quit_application)
        self.event_bus.subscribe("app_state_change", self.handle_app_state_change)
        self.event_bus.subscribe("transcription_error", self.show_error_message)
        self.event_bus.subscribe("initialization_successful", self.hide_main_window)
        self.event_bus.subscribe("show_balloon", self.show_notification)
        self.event_bus.subscribe("start_of_stream", self.start_of_stream)
        self.event_bus.subscribe("add_text_to_popup", self.append_text_to_popup)
        self.event_bus.subscribe("end_of_stream", self.end_of_stream)
        self.event_bus.subscribe("show_popup", self.show_full_popup)

    def show_main_window(self):
        """Display the main application window and show the system tray icon."""
        self.main_window.show()
        self.tray_icon.show()

    def handle_start_listening(self):
        """Handle the start listening event."""
        self.event_bus.emit("start_listening")

    def hide_main_window(self):
        """Hide the main window after successful initialization."""
        self.main_window.hide_main_window()

    def handle_app_state_change(self, message):
        """Handle changes in app states, updating status based on the chosen mode."""
        print("")
        if message == "":
            self.show_status_window(message)

        status_update_mode = ConfigManager.get_value('global_options.status_update_mode')
        if status_update_mode is None:
            status_update_mode = "Window"

        rprint("⌛", message)
        if status_update_mode == "Window":
            self.show_status_window(message)
        elif status_update_mode == "Notification":
            self.show_notification(message, "Chirp")

    def show_status_window(self, message):
        """Display a status message in the status window."""
        if message:
            self.status_window.show_message(message)
        else:
            self.status_window.hide()

    def show_notification(self, message, app_name):
        """Display a desktop notification."""
        if not message:
            message = "Finished."

        words = message.split()
        if len(words) > 100:
            short_message = " ".join(words[:100]) + "..."
            self.long_message_cache = message

            self.tray_icon.tray_icon.showMessage(
                f"{app_name}",
                short_message + "\n(click to read more)",
                QIcon(),
                5000
            )
        else:
            self.long_message_cache = message
            self.tray_icon.tray_icon.showMessage(
                f"{app_name}",
                message,
                QIcon(),
                5000
            )

    def show_full_popup(self, text, app_name):
        """Display a popup message."""
        self.popup_window.show_full_message_dialog(title=app_name, message=text)

    def start_of_stream(self, app_name):
        """Display a popup message."""
        self.popup_window.show_popup(title=app_name)

    def append_text_to_popup(self, text):
        """Append text to the popup message."""
        if not text:
            return

        self.popup_window.append_text(text)

    def end_of_stream(self, app_name):
        """Hide the popup window."""
        self.popup_window.on_end_of_stream()

    def handle_tray_message_clicked(self):
        """
        Called when user clicks the tray balloon notification.
        Check if we had a truncated message. If so, show the full text.
        """
        if self.long_message_cache:
            # Show a dialog with scrollable text
            self.show_full_message_dialog(self.long_message_cache)
        else:
            # No long message stored, so do nothing or show a small pop-up, etc.
            pass

    def show_full_message_dialog(self, long_text):
        dialog = ScrollableMessageDialog(long_text)
        dialog.exec()


    def show_error_message(self, message):
        """Display an error message in a QMessageBox."""
        ConfigManager.log_print(f"Transcription error: {message}")
        QMessageBox.critical(None, "Transcription Error", message)

    def show_settings_with_error(self, error_message: str):
        """Show the settings window with a detailed error message."""
        QMessageBox.critical(self.main_window, "Initialization Error", error_message)
        self.settings_window.show()
        self.main_window.show()

    def initiate_close(self):
        """Initiate the application closing process, ensuring it only happens once."""
        if not self.is_closing:
            self.is_closing = True
            self.event_bus.emit("close_app")

    def quit_application(self):
        """Quit the QApplication instance, effectively closing the application."""
        # Close all windows first
        self.main_window.close()
        self.settings_window.close()
        self.status_window.close()
        self.tray_icon.hide()
        QApplication.instance().quit()

    def run_event_loop(self):
        """Start and run the Qt event loop, returning the exit code when finished."""
        return QApplication.instance().exec()