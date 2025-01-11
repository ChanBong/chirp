import uuid
import os
from queue import Queue
from typing import Dict, Optional

from audio_manager import AudioManager
from input_manager import InputManager
from enums import RecordingMode
from apps import App
from config_manager import ConfigManager
from play_wav import play_wav


class ApplicationController:
    """
    Central coordinator for the application, managing core components and orchestrating
    the overall workflow.

    Responsible for initializing and managing apps, coordinating audio recording and
    transcription processes, handling user input events, and managing application state
    transitions. Acts as a bridge between various components, handles session management,
    and ensures proper cleanup of resources. Manages the lifecycle of recording sessions
    across different apps and modes of operation.
    """
    def __init__(self, ui_manager, event_bus):
        """Initialize the ApplicationController with UI manager and event bus."""
        self.ui_manager = ui_manager
        self.event_bus = event_bus
        self.audio_queue = Queue()
        self.listening = False
        self.audio_manager = None
        self.input_manager = None
        self.manually_stopped_apps = set()  # For tracking continuous mode apps

        self.active_apps: Dict[str, App] = {}
        self.session_app_map: Dict[str, str] = {}

        self.load_active_apps()
        self.setup_connections()

    def load_active_apps(self):
        """Load and initialize active apps from configuration."""
        active_apps = ConfigManager.get_apps(active_only=True)
        for app in active_apps:
            app_name = app['name']
            app_obj = App(app_name, self.event_bus)
            self.active_apps[app_name] = app_obj

    def setup_connections(self):
        """Set up event subscriptions for various application events."""
        self.event_bus.subscribe("start_listening", self.handle_start_listening)
        self.event_bus.subscribe("shortcut_triggered", self.handle_shortcut)
        self.event_bus.subscribe("audio_discarded", self.handle_audio_discarded)
        self.event_bus.subscribe("recording_stopped", self.handle_recording_stopped)
        self.event_bus.subscribe("inferencing_finished", self.handle_transcription_complete)
        self.event_bus.subscribe("inferencing_skipped", self.handle_transcription_complete)
        self.event_bus.subscribe("config_changed", self.handle_config_change)
        self.event_bus.subscribe("close_app", self.close_application)

    def handle_shortcut(self, app_name: str, event_type: str):
        """Handle shortcut events for starting or stopping recording."""
        app = self.active_apps.get(app_name)
        if app:
            if event_type == "press":
                if app.should_start_on_press():
                    self.start_recording(app)
                elif app.should_stop_on_press():
                    self.stop_recording(app)
                    if app.recording_mode == RecordingMode.CONTINUOUS:
                        self.manually_stopped_apps.add(app.name)
            elif event_type == "release":
                if app.should_stop_on_release():
                    self.stop_recording(app)

    def start_recording(self, app: App):
        """Start recording for a given app."""
        if app.is_idle() and not self.audio_manager.is_recording():
            session_id = str(uuid.uuid4())
            self.session_app_map[session_id] = app.name
            self.audio_manager.start_recording(app, session_id)
            app.start_transcription(session_id)
            self.manually_stopped_apps.discard(app.name)
        else:
            ConfigManager.log_print("App or audio thread is busy.")

    def stop_recording(self, app: App):
        """Stop recording for a given app."""
        if app.is_recording():
            self.audio_manager.stop_recording()
            app.recording_stopped()

    def handle_recording_stopped(self, session_id: str):
        """Handle cases when audio stopped automatically in VAD and CONTINUOUS modes"""
        app = self._get_app_for_session(session_id)
        if app:
            self.stop_recording(app)

    def handle_audio_discarded(self, session_id: str):
        """Handle cases where recorded audio is discarded."""
        app = self._get_app_for_session(session_id)
        if app:
            app.finish_inferencing()  # This will emit "inferencing_complete" event

    def handle_transcription_complete(self, session_id: str):
        """Handle the completion of a transcription session."""
        app = self._get_app_for_session(session_id)
        if app:
            del self.session_app_map[session_id]
            # Play beep sound
            if ConfigManager.get_value('global_options.noise_on_completion', False):
                beep_file = os.path.join('assets', 'beep.wav')
                play_wav(beep_file)

            if (app.recording_mode == RecordingMode.CONTINUOUS and
                    app.name not in self.manually_stopped_apps):
                self.start_recording(app)
            else:
                self.manually_stopped_apps.discard(app.name)

    def handle_start_listening(self):
        """Initialize core components when the application starts listening."""
        self.listening = True
        self.start_core_components()

    def handle_config_change(self):
        """Handle configuration changes by reloading apps and restarting components."""
        self.cleanup()
        self.load_active_apps()
        if self.listening:
            self.start_core_components()

    def run(self):
        """Run the main application loop and return the exit code."""
        start_minimized = ConfigManager.get_value('misc.start_minimized')
        if start_minimized:
            self.event_bus.emit("start_listening")
        else:
            self.ui_manager.show_main_window()
        exit_code = self.ui_manager.run_event_loop()  # Run QT event loop
        self.cleanup()
        return exit_code

    def start_core_components(self):
        """Initialize and start core components."""
        if self.ui_manager:
            self.ui_manager.status_update_mode = ConfigManager.get_value(
                'global_options.status_update_mode')
        
        self.input_manager = InputManager(self.event_bus)
        self.audio_manager = AudioManager(self.event_bus)
        self.input_manager.start()
        self.audio_manager.start()

        initialization_error = None
        for app in self.active_apps.values():
            try:
                app.transcription_manager.start()
            except RuntimeError as e:
                initialization_error = str(e)
                ConfigManager.log_print(f"Failed to start transcription manager for "
                                      f"app {app.name}.\n{initialization_error}")
                break

            # Only try to start LLM manager if it exists
            if app.llm_manager:
                try:
                    app.llm_manager.start()
                except RuntimeError as e:
                    initialization_error = str(e)
                    ConfigManager.log_print(f"Failed to start LLM manager for "
                                          f"app {app.name}.\n{initialization_error}")
                    break

        if initialization_error:
            self.cleanup()
            self.listening = False
            error_message = (f"Failed to initialize transcription backend.\n"
                           f"{initialization_error}\nPlease check your settings.")
            if self.ui_manager:
                self.ui_manager.show_settings_with_error(error_message)
            else:
                raise RuntimeError(error_message)
        else:
            self.event_bus.emit("initialization_successful")

    def close_application(self):
        """Initiate the application closing process."""
        self.cleanup()  # Add cleanup before emitting quit
        self.event_bus.emit("quit_application")

    def cleanup(self):
        """Clean up resources and stop all components before application exit."""
        # Stop and cleanup audio-related components
        if self.audio_manager:
            self.audio_manager.stop_recording()
            self.audio_manager.cleanup()
            self.audio_manager = None

        # Ensure all active sessions are properly closed
        for session_id in list(self.session_app_map.keys()):
            self.handle_transcription_complete(session_id)

        # Stop and cleanup all active apps
        for app in self.active_apps.values():
            app.cleanup()

        # Clear the active apps and session app map
        self.active_apps.clear()
        self.session_app_map.clear()

        # Stop and cleanup input manager
        if self.input_manager:
            self.input_manager.cleanup()
            self.input_manager = None

    def _get_app_for_session(self, session_id: str) -> Optional[App]:
        """Get the app associated with a given session ID."""
        if session_id in self.session_app_map:
            app_name = self.session_app_map[session_id]
            return self.active_apps.get(app_name)
        return None
