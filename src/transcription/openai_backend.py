import numpy as np
import soundfile as sf
import os
import io
from typing import Dict, Any
from scipy import signal

from transcription.transcription_backend_base import TranscriptionBackendBase
from config_manager import ConfigManager


class OpenAIBackend(TranscriptionBackendBase):
    def __init__(self):
        self.OpenAI = None
        self.config = None
        self.client = None
        self._initialized = False

    def is_initialized(self) -> bool:
        return self._initialized

    def initialize(self, options: Dict[str, Any]):
        try:
            from openai import OpenAI
        except ImportError as e:
            raise RuntimeError(f"Failed to import required modules: {e}. "
                               f"Make sure OpenAI is installed.")

        self.OpenAI = OpenAI
        self.config = options
        api_key = self.config.get('api_key') or os.getenv('OPENAI_API_KEY')
        base_url = self.config.get('base_url') or 'https://api.openai.com/v1'

        if not api_key:
            raise RuntimeError("OpenAI API key not found. "
                               "Please set it in the configuration or as an environment variable.")

        try:
            self.client = self.OpenAI(api_key=api_key, base_url=base_url)
            ConfigManager.log_print("OpenAI client initialized successfully.")
            self._initialized = True
        except Exception as e:
            raise RuntimeError(f"Failed to initialize OpenAI client: {e}")

    def transcribe_complete(self, audio_data: np.ndarray, sample_rate: int = 16000,
                            channels: int = 1, language: str = 'auto') -> Dict[str, Any]:
        if not self.client:
            return {'raw_text': '', 'language': language, 'error': "OpenAI client not initialized"}

        # Prepare audio data
        try:
            audio_data = self._prepare_audio_data(audio_data, sample_rate, channels)
        except Exception as e:
            return {'raw_text': '', 'language': language,
                    'error': f"Error preparing audio data: {str(e)}"}

        # Convert numpy array to WAV file
        byte_io = io.BytesIO()
        sf.write(byte_io, audio_data, 16000, format='wav')
        byte_io.seek(0)

        try:
            response = self.client.audio.transcriptions.create(
                model=self.config.get('model', 'whisper-1'),
                file=('audio.wav', byte_io, 'audio/wav'),
                language=language if language != 'auto' else None,
                prompt=self.config.get('initial_prompt'),
                temperature=self.config.get('temperature', 0.0),
            )
            return {
                'raw_text': response.text,
                'language': language,  # OpenAI doesn't return detected language
                'error': '',
            }
        except Exception as e:
            return {
                'raw_text': '',
                'language': language,
                'error': f"OpenAI transcription failed: {str(e)}",
            }

    def _prepare_audio_data(self, audio_data: np.ndarray, sample_rate: int,
                            channels: int) -> np.ndarray:
        # OpenAI expects 16kHz mono audio
        if sample_rate != 16000 or channels != 1:
            # Resample to 16kHz
            if sample_rate != 16000:
                number_of_samples = round(len(audio_data) * 16000 / sample_rate)
                audio_data = signal.resample(audio_data, number_of_samples)

            # Convert to mono if necessary
            if channels > 1:
                audio_data = np.mean(audio_data, axis=1)

        # Ensure audio_data is in the correct format (float32, range [-1, 1])
        if audio_data.dtype == np.float32 and np.abs(audio_data).max() <= 1.0:
            # Data is already in the correct format
            pass
        elif audio_data.dtype == np.float32:
            # Data is float32 but may not be in [-1, 1] range
            audio_data = np.clip(audio_data, -1.0, 1.0)
        elif audio_data.dtype in [np.int16, np.int32]:
            # Convert integer PCM to float32
            audio_data = audio_data.astype(np.float32) / np.iinfo(audio_data.dtype).max
        else:
            raise ValueError(f"Unsupported audio format: {audio_data.dtype}")

        return audio_data

    def cleanup(self):
        self.client = None
        self._initialized = False
