import threading
import time
import queue
from typing import Dict, Any

from config_manager import ConfigManager
from event_bus import EventBus
from transcription.transcription_backend_base import TranscriptionBackendBase


class TranscriptionManager:
    def __init__(self, app, event_bus: EventBus):
        self.app_name = app.name
        self.event_bus = event_bus
        self.audio_queue = app.audio_queue
        self.backend_type = ConfigManager.get_value('transcription_backend_type', self.app_name)
        backend_class = self._get_backend_class()
        self.backend: TranscriptionBackendBase = backend_class()
        self.processing_thread = None
        self.current_session_id = None
        self.transcribe_event = threading.Event()
        self.stop_event = threading.Event()

    def _get_backend_class(self):
        if self.backend_type == 'faster_whisper':
            from transcription.faster_whisper_backend import FasterWhisperBackend
            return FasterWhisperBackend
        elif self.backend_type == 'openai':
            from transcription.openai_backend import OpenAIBackend
            return OpenAIBackend
        elif self.backend_type == 'vosk':
            from transcription.vosk_backend import VoskBackend
            return VoskBackend
        else:
            raise ValueError(f"Unsupported backend type: {self.backend_type}")

    def get_preferred_streaming_chunk_size(self):
        return self.backend.get_preferred_streaming_chunk_size()

    def start(self):
        if not self.backend.is_initialized():
            backend_options = ConfigManager.get_section('backend', self.app_name)
            try:
                self.backend.initialize(backend_options)
            except Exception as e:
                raise RuntimeError(f"Failed to initialize backend for app "
                                   f"{self.app_name}.\n{e}")

        if not self.processing_thread:
            self.processing_thread = threading.Thread(target=self._transcription_thread)
            self.processing_thread.start()

    def stop(self):
        self.stop_event.set()
        self.transcribe_event.set()  # Wake up the thread to exit
        if self.processing_thread:
            self.processing_thread.join()
            self.processing_thread = None

    def start_transcription(self, session_id: str):
        self.current_session_id = session_id
        self.stop_event.clear()
        self.transcribe_event.set()

    def _transcription_thread(self):
        while not self.stop_event.is_set():
            self.transcribe_event.wait()
            self.transcribe_event.clear()

            if self.stop_event.is_set():
                break

            self._process_audio()

    def _process_audio(self):
        if not self.backend:
            ConfigManager.log_print("Backend not initialized. Transcription cannot start.")
            return

        # TODO: get from config
        is_streaming = False

        try:
            if is_streaming:
                for result in self.backend.process_stream(self.audio_queue, self.stop_event):
                    if self.stop_event.is_set():
                        break
                    self._emit_result(result)
            else:
                while not self.stop_event.is_set():
                    try:
                        print(f"Audio queue contents: {list(self.audio_queue.queue)}")
                        audio_data = self.audio_queue.get(timeout=0.2)
                        if audio_data is None:  # Sentinel value
                            break
                        start_time = time.time()
                        result = self.backend.transcribe_complete(
                            audio_data['audio_chunk'],
                            audio_data['sample_rate'],
                            audio_data['channels'],
                            audio_data['language']
                        )
                        end_time = time.time()
                        transcription_time = end_time - start_time
                        ConfigManager.log_print(
                            f'Transcription completed in {transcription_time:.2f} seconds.\n'
                            f"Raw transcription: {result['raw_text']}")
                        result['is_utterance_end'] = True
                        self._emit_result(result)
                    except queue.Empty:
                        continue
        finally:
            self.current_session_id = None
            self.event_bus.emit("transcription_finished", self.app_name)

    def _emit_result(self, result: Dict[str, Any]):
        if result['error']:
            self.event_bus.emit("transcription_error", result['error'])
        self.event_bus.emit("raw_transcription_result", result, self.current_session_id)

    def cleanup(self):
        self.stop()
        if self.backend:
            self.backend.cleanup()
            self.backend = None
