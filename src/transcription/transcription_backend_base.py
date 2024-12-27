import numpy as np
import threading
import queue
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Generator


class TranscriptionBackendBase(ABC):
    @abstractmethod
    def is_initialized(self) -> bool:
        pass

    @abstractmethod
    def initialize(self, options: Dict[str, Any]):
        pass

    @abstractmethod
    def transcribe_complete(self, audio_data: np.ndarray, sample_rate: int = 16000,
                            channels: int = 1, language: str = 'auto') -> Dict[str, Any]:
        pass

    @abstractmethod
    def cleanup(self):
        pass

    def get_preferred_streaming_chunk_size(self) -> Optional[int]:
        return None

    def process_stream(self, audio_queue: queue.Queue,
                       stop_event: threading.Event) -> Generator[Dict[str, Any], None, None]:
        yield {
            'raw_text': '',
            'language': 'en',
            'error': 'Streaming transcription is not supported by this backend.',
            'is_utterance_end': True
        }
        # Consume the queue to prevent it from filling up
        while not stop_event.is_set():
            try:
                audio_chunk = audio_queue.get(timeout=0.1)
                if audio_chunk is None:
                    break
            except queue.Empty:
                continue
