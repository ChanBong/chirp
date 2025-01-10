from queue import Queue
from typing import Dict

from output_manager import OutputManager
from transcription_manager import TranscriptionManager
from llm_manager import LLMManager
from enums import ProfileState, RecordingMode
from event_bus import EventBus
from config_manager import ConfigManager
from utils import to_clipboard, read_clipboard, is_bad_transcription


class App:
    """
    Encapsulates the configuration, state, and behavior of a specific transcription profile.

    Manages the lifecycle of transcription sessions, including recording, processing,
    and output of transcribed text. Coordinates interactions between TranscriptionManager,
    PostProcessingManager, and OutputManager. Handles both streaming and non-streaming
    transcription modes, and manages its own state transitions based on user input and
    transcription events.
    """
    def __init__(self, name: str, event_bus: EventBus):
        """Initialize the Profile with name, configuration, and necessary components."""
        self.name = name
        self.config = ConfigManager.get_section('apps', name)
        self.read_from_clipboard = self.config.get('recording_options', {}).get('read_from_clipboard', False)
        self.save_output_to_clipboard = self.config.get('output_options', {}).get('save_output_to_clipboard', False)
        self.output_mode = self.config.get('output_options', {}).get('output_mode', 'text')
        self.event_bus = event_bus
        self.audio_queue = Queue()
        self.inference_queue = Queue()
        self.output_manager = OutputManager(name, event_bus)
        self.recording_mode = RecordingMode.PRESS_TO_TOGGLE
        self.state = ProfileState.IDLE
        self.transcription_manager = TranscriptionManager(self, event_bus)
        self.llm_manager = LLMManager(self, event_bus)
        self.is_llm_streaming = self.config.get('output_options', {}).get('is_streaming', False)
        self.is_streaming = False
        self.streaming_chunk_size = self.transcription_manager.get_preferred_streaming_chunk_size()
        self.result_handler = (StreamingResultHandler(self.name, self.event_bus) if self.is_llm_streaming else None)
        self.current_session_id = None

        self.event_bus.subscribe("raw_transcription_result", self.handle_raw_transcription)
        self.event_bus.subscribe("transcription_finished", self.handle_transcription_finished)
        self.event_bus.subscribe("inferencing_result", self.handle_inferencing_result)
        self.event_bus.subscribe("inferencing_finished", self.handle_inferencing_finished)

    def start_transcription(self, session_id: str):
        """Start the transcription process for this profile."""
        self.current_session_id = session_id
        self.state = ProfileState.RECORDING
        self.event_bus.emit("profile_state_change", f"({self.name}) "
                            f"{'Streaming' if self.is_streaming else 'Recording'}...")
        print(f"Starting transcription for session {self.current_session_id}")
        self.transcription_manager.start_transcription(session_id)

    def recording_stopped(self):
        """Transition to transcribing state since recording has stopped."""
        if self.state == ProfileState.RECORDING:
            self.event_bus.emit("profile_state_change", f"({self.name}) Transcribing...")
            self.state = ProfileState.TRANSCRIBING
            print(f"Recording stopped for session {self.current_session_id}")
        else:
            print(f"Recording stopped for session {self.current_session_id}")

    def is_recording(self) -> bool:
        return self.state == ProfileState.RECORDING

    def is_idle(self) -> bool:
        return self.state == ProfileState.IDLE

    def finish_transcription(self):
        """Finish the transcription process and return to idle state."""
        pass

    def handle_raw_transcription(self, result: Dict, session_id: str):
        """
        Handle raw transcription results.

        The 'result' dictionary typically contains:
        - 'raw_text': The unprocessed transcription text.
        - 'processed': The post-processed transcription text. (created by the post_processor)
        - 'is_utterance_end': Boolean indicating if this is the end of an utterance.
        - 'language': Detected or specified language of the audio.
        - 'error': Any error message (None if no error occurred).
        """
        # print(f"Session id: {session_id}")
        # print(f"Current session id: {self.current_session_id}")

        if session_id != self.current_session_id:
            return

        if result['error']:
            self.event_bus.emit("inferencing_skipped", self.name)
            return
        
        is_bad, reason = is_bad_transcription(result['raw_text'])
        if is_bad:
            print(f"Skipping transcription because it is bad: {reason}")
            self.event_bus.emit("inferencing_skipped", self.name)
            return

        self.current_session_id = session_id
        self.state = ProfileState.INFERENCING
        self.event_bus.emit("profile_state_change", f"({self.name}) Inferring...")

        clipboard = read_clipboard()
        clipboard_content = ""
        if clipboard and self.read_from_clipboard:
            clipboard_content = clipboard['content']

        user_message = {
            "transcription": result['raw_text'],
            "clipboard_content": clipboard_content
        }
        
        self.llm_manager.inference_queue.put(user_message)
        self.llm_manager.inference_queue.put(None)
        self.llm_manager.start_inference(session_id)

    def handle_transcription_finished(self, profile_name: str):
        if profile_name == self.name:
            self.finish_transcription()

    def handle_inferencing_result(self, result: Dict, session_id: str):
        # print(f"Session id: {session_id}")
        # print(f"Current session id: {self.current_session_id}")
        if session_id != self.current_session_id:
            return
        
        self.current_session_id = session_id

        if self.is_llm_streaming:
            self.result_handler.handle_result(result, self.output_mode)
        else:
            self.output(result['assistant'])

    def handle_inferencing_finished(self, profile_name: str):
        if profile_name == self.name:
            self.finish_inferencing()

    def finish_inferencing(self):
        previous_state = self.state
        self.state = ProfileState.IDLE
        self.event_bus.emit("profile_state_change", '')

        old_sid = self.current_session_id
        self.current_session_id = None
        if previous_state in [ProfileState.INFERENCING, ProfileState.RECORDING, ProfileState.TRANSCRIBING]:
            self.event_bus.emit("inferencing_complete", old_sid)

    def output(self, text: str):
        """Output the processed text using the output manager."""
        print(f"Outputting: {text}")
        if not text:
            return

        if self.output_mode == 'clipboard':
            to_clipboard(text)
        elif self.output_mode == 'notification':
            self.event_bus.emit("show_balloon", text, self.name)
        elif self.output_mode == 'pop-up':
            self.event_bus.emit("show_popup", text, self.name)
        elif self.output_mode == 'text':
            self.output_manager.typewrite(text)
        elif self.output_mode == 'voice':
            print("Support for voice output is not implemented yet. Output mode set to notification")
            self.event_bus.emit("show_balloon", text, self.name)

        if self.save_output_to_clipboard:
            to_clipboard(text)

    def should_start_on_press(self) -> bool:
        """Determine if recording should start on key press."""
        return self.state == ProfileState.IDLE

    def should_stop_on_press(self) -> bool:
        """Determine if recording should stop on key press."""
        return (self.state == ProfileState.RECORDING and
                self.recording_mode in [
                    RecordingMode.PRESS_TO_TOGGLE,
                    RecordingMode.CONTINUOUS,
                    RecordingMode.VOICE_ACTIVITY_DETECTION
                ])

    def should_stop_on_release(self) -> bool:
        """Determine if recording should stop on key release."""
        return (self.state == ProfileState.RECORDING and
                self.recording_mode == RecordingMode.HOLD_TO_RECORD)

    def cleanup(self):
        """Clean up resources and reset attributes for garbage collection."""
        self.recording_stopped()
        self.finish_transcription()
        self.finish_inferencing()
        if self.transcription_manager:
            self.transcription_manager.cleanup()
        if self.llm_manager:
            self.llm_manager.cleanup()
        if self.output_manager:
            self.output_manager.cleanup()
        if self.event_bus:
            self.event_bus.unsubscribe("raw_transcription_result",
                                       self.handle_raw_transcription)
            self.event_bus.unsubscribe("transcription_finished",
                                       self.handle_transcription_finished)

        # Reset all attributes to enforce garbage collection
        self.config = None
        self.audio_queue = None
        self.output_manager = None
        self.recording_mode = None
        self.state = None
        self.is_streaming = None
        # self.post_processor = None
        self.transcription_manager = None
        self.result_handler = None


class StreamingResultHandler:
    def __init__(self, name, event_bus: EventBus):
        self.name = name
        self.buffer = ""
        self.full_message = ""
        self.event_bus = event_bus
    
    def handle_result(self, result: Dict, output_mode: str):
        new_text = result['assistant']

        if not new_text:
            return
        
        if new_text == "<end_of_stream>":
            if output_mode == 'clipboard':
                to_clipboard(self.full_message)
            elif output_mode == 'notification':
                self.event_bus.emit("show_balloon", self.full_message, self.name)

            self.full_message = ""
            self.buffer = ""
            self.event_bus.emit("end_of_stream", self.name)
            return

        full_message = self.full_message + new_text
        if output_mode == 'pop-up':
            self.event_bus.emit("add_text_to_popup", new_text)
        elif output_mode == 'text':
            self.output_manager.typewrite(new_text)
        elif output_mode == 'voice':
            print("Support for voice output is not implemented yet. Output mode set to notification")
            self.event_bus.emit("show_balloon", new_text, self.name)

        self.buffer = new_text
        self.full_message = full_message
