import numpy as np
from typing import Dict, Any, Generator
import json
import queue
import threading

from transcription.transcription_backend_base import TranscriptionBackendBase
from config_manager import ConfigManager


class VoskBackend(TranscriptionBackendBase):
    def __init__(self):
        self.vosk = None
        self.model = None
        self.recognizer = None
        self.config = None
        self._initialized = False

    def is_initialized(self) -> bool:
        return self._initialized

    def initialize(self, options: Dict[str, Any]):
        self.config = options
        try:
            import vosk
            self.vosk = vosk
        except ImportError:
            raise RuntimeError("Failed to import vosk. Make sure it's installed.")

        try:
            model_path = self.config.get('model_path', "model")
            self.model = self.vosk.Model(model_path)
            sample_rate = self.config.get('sample_rate', 16000)
            self.recognizer = self.vosk.KaldiRecognizer(self.model, sample_rate)
            ConfigManager.log_print("Vosk model initialized successfully.")
            self._initialized = True
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Vosk model: {e}")

    def transcribe_complete(self, audio_data: np.ndarray, sample_rate: int = 16000,
                            channels: int = 1, language: str = 'auto') -> Dict[str, Any]:
        if not self.recognizer:
            return {
                'raw_text': '',
                'language': 'en',
                'error': 'Recognizer not initialized',
                'is_utterance_end': True
            }

        # Ensure audio_data is in the correct format (16-bit PCM)
        if audio_data.dtype != np.int16:
            audio_data = (audio_data * 32767).astype(np.int16)

        try:
            self.recognizer.AcceptWaveform(audio_data.tobytes())
            result = json.loads(self.recognizer.FinalResult())

            return {
                'raw_text': result.get('text', ''),
                'language': 'en',
                'error': '',
                'is_utterance_end': True
            }
        except Exception as e:
            return {
                'raw_text': '',
                'language': 'en',
                'error': f'Unexpected error during transcription: {e}',
                'is_utterance_end': True
            }

    def process_stream(self, audio_queue: queue.Queue,
                       stop_event: threading.Event) -> Generator[Dict[str, Any], None, None]:
        if not self.recognizer:
            yield {
                'raw_text': '',
                'language': 'en',
                'error': 'Recognizer not initialized',
                'is_utterance_end': True
            }
            return

        error_reported = False
        try:
            while not stop_event.is_set():
                try:
                    audio_data = audio_queue.get(timeout=0.1)
                    if audio_data is None:  # Sentinel value
                        break

                    audio_chunk = audio_data['audio_chunk']
                    # Ensure audio_chunk is in the correct format (16-bit PCM)
                    if audio_chunk.dtype != np.int16:
                        audio_chunk = (audio_chunk * 32767).astype(np.int16)

                    is_utterance_end = self.recognizer.AcceptWaveform(audio_chunk.tobytes())
                    if is_utterance_end:
                        result = json.loads(self.recognizer.Result())
                    else:
                        result = json.loads(self.recognizer.PartialResult())
                    yield {
                        'raw_text': (result.get('partial', '')
                                     if not is_utterance_end
                                     else result.get('text', '')),
                        'language': 'en',
                        'error': '',
                        'is_utterance_end': is_utterance_end
                    }

                except queue.Empty:
                    continue

        except Exception as e:
            if not error_reported:
                yield {
                    'raw_text': '',
                    'language': 'en',
                    'error': f'Unexpected error during streaming transcription: {e}',
                    'is_utterance_end': True
                }
                error_reported = True

        # Final result after the stream ends
        try:
            final_result = json.loads(self.recognizer.FinalResult())
            yield {
                'raw_text': final_result.get('text', ''),
                'language': 'en',
                'error': '',
                'is_utterance_end': True
            }
        except Exception as e:
            if not error_reported:
                yield {
                    'raw_text': '',
                    'language': 'en',
                    'error': f'Unexpected error during stream finalization: {e}',
                    'is_utterance_end': True
                }

    def get_preferred_streaming_chunk_size(self):
        return 4096

    def cleanup(self):
        self.recognizer = None
        self.model = None
        self.vosk = None
        self._initialized = False
