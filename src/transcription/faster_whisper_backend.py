import queue
import time
import threading
import numpy as np
from typing import Dict, Any, Generator, List

from transcription.transcription_backend_base import TranscriptionBackendBase
from config_manager import ConfigManager


class FasterWhisperBackend(TranscriptionBackendBase):
    def __init__(self):
        self.WhisperModel = None
        self.config = None
        self.model = None
        self._initialized = False
        self.current_utterance_buffer: List[np.ndarray] = []
        self.last_vad_duration = 0.0
        self.last_duration = 0.0

    def is_initialized(self) -> bool:
        return self._initialized

    def initialize(self, options: Dict[str, Any]):
        try:
            from faster_whisper import WhisperModel
            self.WhisperModel = WhisperModel
        except ImportError:
            raise RuntimeError("Failed to import faster_whisper. Make sure it's installed.")

        self.config = options
        self._load_model()
        if not self.model:
            raise RuntimeError("Failed to initialize any Whisper model.")
        self._initialized = True

    def _load_model(self):
        ConfigManager.log_print('Creating Faster Whisper model...')
        compute_type = self.config.get('compute_type', 'default')
        model_path = self.config.get('model_path', '')
        device = self.config.get('device', 'auto')
        model_name = self.config.get('model', 'base')

        if model_path:
            try:
                ConfigManager.log_print(f'Loading model from: {model_path}')
                self.model = self.WhisperModel(model_path,
                                               device=device,
                                               compute_type=compute_type,
                                               download_root=None)
                ConfigManager.log_print('Model loaded successfully from specified path.')
                return
            except Exception as e:
                ConfigManager.log_print(f'Error loading model from path: {e}')
                ConfigManager.log_print('Falling back to online models...')

        # If model_path is empty or failed to load, use online models
        try:
            ConfigManager.log_print(f'Attempting to load {model_name} model...')
            self.model = self.WhisperModel(model_name,
                                           device=device,
                                           compute_type=compute_type)
            ConfigManager.log_print(f'{model_name.capitalize()} model loaded successfully.')
        except Exception as e:
            ConfigManager.log_print(f'Error loading {model_name} model: {e}')
            ConfigManager.log_print('Falling back to base model on CPU...')
            try:
                self.model = self.WhisperModel('base',
                                               device='cpu',
                                               compute_type='default')
                ConfigManager.log_print('Base model loaded successfully on CPU.')
            except Exception as e:
                raise RuntimeError(f"Failed to load any Whisper model. Last error: {e}")

    def transcribe_complete(self, audio_data: np.ndarray, sample_rate: int = 16000,
                            channels: int = 1, language: str = 'auto') -> Dict[str, Any]:
        if not self.model:
            return {
                'raw_text': '',
                'language': 'en',
                'error': 'Model not initialized.'
            }

        try:
            audio_data = self._normalize_audio(audio_data)
            segments, info = self.model.transcribe(
                audio=audio_data,
                language=language if language != 'auto' else None,
                initial_prompt=self.config.get('initial_prompt'),
                condition_on_previous_text=self.config.get('condition_on_previous_text', True),
                temperature=self.config.get('temperature', 0.0),
                vad_filter=self.config.get('vad_filter', False),
            )

            transcription = ''.join([segment.text for segment in segments])

            return {
                'raw_text': transcription,
                'language': info.language,
                'error': '',
            }
        except Exception as e:
            return {
                'raw_text': '',
                'language': 'en',
                'error': f'Unexpected error during transcription: {e}'
            }

    def process_stream(self, audio_queue: queue.Queue,
                       stop_event: threading.Event) -> Generator[Dict[str, Any], None, None]:
        """
        This method orchestrates the streaming transcription process. It continuously collects
        audio chunks from an input queue and processes them at regular intervals, as defined by
        min_transcription_interval. The method ensures that transcription only occurs after
        a sufficient amount of time has passed since the last transcription, allowing for
        a reasonable accumulation of audio data. When a sentinel value (None) is encountered in
        the queue, it triggers the final transcription of any remaining audio. The method also
        initializes the sample rate from the first chunk and uses a short sleep to prevent
        busy-waiting, ensuring efficient CPU usage.
        """
        self.current_utterance_buffer = []
        accumulated_chunks: List[np.ndarray] = []
        last_transcription_time = None
        sample_rate = None
        min_transcription_interval = self.config.get('min_transcription_interval', 0.5)
        if min_transcription_interval < 0.2:
            min_transcription_interval = 0.2

        while not stop_event.is_set():
            # Collect all available chunks
            while True:
                try:
                    audio_data = audio_queue.get_nowait()
                    if audio_data is None:  # Sentinel value
                        if accumulated_chunks or self.current_utterance_buffer:
                            yield from self._process_chunks(accumulated_chunks,
                                                            sample_rate, is_final=True)
                        return
                    accumulated_chunks.append(audio_data['audio_chunk'])
                    if sample_rate is None:
                        sample_rate = audio_data['sample_rate']
                        last_transcription_time = time.time()  # Initialize the time for chunk #1
                except queue.Empty:
                    break

            if sample_rate is None:
                continue  # No audio data received yet

            current_time = time.time()

            # Process accumulated chunks if enough time has passed
            if current_time - last_transcription_time >= min_transcription_interval:
                if accumulated_chunks:
                    yield from self._process_chunks(accumulated_chunks, sample_rate)
                    accumulated_chunks = []
                    last_transcription_time = current_time

            # Short sleep to prevent busy-waiting
            time.sleep(0.1)

    def _process_chunks(self, new_chunks: List[np.ndarray], sample_rate: int,
                        is_final: bool = False) -> Generator[Dict[str, Any], None, None]:
        """
        This method is responsible for processing a list of accumulated audio chunks. It extends
        the current utterance buffer with new chunks, normalizes the audio data, and then
        transcribes it using the Whisper model. The method handles two special cases: resetting
        the buffer when prolonged silence is detected and handling silence detected by Whisper's
        built-in voice activity detection (VAD). If neither case applies, the method proceeds
        to check for punctuation-based endpoints in the transcription. It yields the transcription
        results, marking utterances as complete or ongoing based on the presence of punctuation
        and the finality of the audio data.
        """
        try:
            self.current_utterance_buffer.extend(new_chunks)
            audio_data = np.concatenate(self.current_utterance_buffer)
            audio_data = self._normalize_audio(audio_data)

            segments, info = self.model.transcribe(
                audio=audio_data,
                language=self.config.get('language', None),
                initial_prompt=self.config.get('initial_prompt'),
                condition_on_previous_text=self.config.get('condition_on_previous_text', True),
                temperature=self.config.get('temperature', 0.0),
                vad_filter=self.config.get('vad_filter', True),
            )

            # Reset silent buffer
            if info.duration > 10.0 and info.duration_after_vad == 0.0:
                # Prune 8 seconds of silence
                self._update_buffer(audio_data, 8.0, sample_rate)
                return

            # Convert generator to list
            segments_list = list(segments)

            # Handle VAD-based silence detection
            vad_silence_result = self._handle_vad_silence(info, segments_list)
            if vad_silence_result:
                yield vad_silence_result
                return

            # Handle punctuation-based endpoint detection
            yield from self._handle_punctuation_endpoint(info, segments_list, audio_data,
                                                         sample_rate, is_final)

        except Exception as e:
            yield {
                'raw_text': '',
                'language': 'en',
                'error': f'Unexpected error during streaming transcription: {e}',
                'is_utterance_end': True
            }

    def _handle_vad_silence(self, info, segments_list):
        """
        This method detects silence in the audio stream using the duration information provided
        by Whisper's VAD. If a significant duration of silence (defined in vad_silence_duration)
        is detected after an utterance, it yields the transcription as a complete utterance and
        resets the internal state to prepare for the next utterance.
        """
        if info.duration_after_vad > 0.0:
            if info.duration_after_vad != self.last_vad_duration:
                self.last_vad_duration = info.duration_after_vad
                self.last_duration = info.duration
            if info.duration - self.last_duration >= self.config.get('vad_silence_duration', 2.0):
                # Yield completed utterance due to silence
                completed_text = ' '.join([seg.text for seg in segments_list])
                # Reset buffer and VAD update time
                self.current_utterance_buffer = []
                self.last_vad_duration = 0.0
                self.last_duration = 0.0
                return {
                    'raw_text': completed_text,
                    'language': info.language,
                    'error': '',
                    'is_utterance_end': True
                }
        return None

    def _handle_punctuation_endpoint(self, info, segments_list, audio_data, sample_rate, is_final):
        """
        This method analyzes the transcription segments to find natural endpoints based on
        punctuation and Whisper segmentation. It identifies the last segment that ends with
        punctuation and considers it the end of a complete utterance. The method then yields
        the complete utterance and updates the buffer to only include audio data beyond this
        endpoint. If no punctuation-based endpoint is found, it yields the entire transcription
        as ongoing.
        """
        # Find the last segment with ending punctuation
        endpoint_index = self._find_utterance_endpoint(segments_list)

        if endpoint_index is not None and endpoint_index < len(segments_list) - 1:
            # Yield completed utterance
            completed_text = ' '.join([seg.text for seg in segments_list[:endpoint_index+1]])
            yield {
                'raw_text': completed_text,
                'language': info.language,
                'error': '',
                'is_utterance_end': True
            }

            # Update buffer
            self._update_buffer(audio_data, segments_list[endpoint_index+1].start, sample_rate)

            # Yield ongoing utterance
            ongoing_utterance = ' '.join([seg.text for seg in segments_list[endpoint_index+1:]])
        else:
            # No clear endpoint, yield entire transcription as ongoing
            ongoing_utterance = ' '.join([seg.text for seg in segments_list])

        yield {
            'raw_text': ongoing_utterance,
            'language': info.language,
            'error': '',
            'is_utterance_end': is_final
        }

    def _find_utterance_endpoint(self, segments_list):
        for i in range(len(segments_list) - 2, -1, -1):
            if segments_list[i].text.strip().endswith(('.', '!', '?')):
                return i
        return None

    def _update_buffer(self, audio_data, start_time, sample_rate):
        start_sample = int(start_time * sample_rate)
        self.current_utterance_buffer = [audio_data[start_sample:]]

    def _normalize_audio(self, audio_data: np.ndarray) -> np.ndarray:
        if audio_data.dtype == np.float32 and np.abs(audio_data).max() <= 1.0:
            return audio_data
        elif audio_data.dtype == np.float32:
            return np.clip(audio_data, -1.0, 1.0)
        elif audio_data.dtype in [np.int16, np.int32]:
            return audio_data.astype(np.float32) / np.iinfo(audio_data.dtype).max
        else:
            raise ValueError(f"Unsupported audio format: {audio_data.dtype}")

    def get_preferred_streaming_chunk_size(self):
        return 3200  # 200ms at 16kHz

    def cleanup(self):
        self.model = None
        self._initialized = False
