Below is a step-by-step explanation of the **AudioManager** class, its flow, and its design decisions. The goal is to show *why* and *how* this code works as a whole. I’ll break it down into conceptual sections: initialization, public API methods, the audio-processing loop, and utility/helper methods.

---

## 1. Overview and Purpose

The **AudioManager** is responsible for:

1. Managing the microphone (or sound device) input.
2. Capturing audio in a separate worker thread.
3. Handling different recording modes (streaming vs. non-streaming).
4. Handling voice-activity detection (VAD) to stop recording automatically if silence is detected.
5. Passing audio frames or chunks to the rest of the application, typically via `Profile.audio_queue` and events on the `EventBus`.

It keeps track of audio states like **STOPPED**, **IDLE**, and **RECORDING** to coordinate when audio is flowing. It uses a queue (`recording_queue`) to signal when to start/stop recording or to gracefully shut down.

---

## 2. Constructor and Initialization

```python
def __init__(self, event_bus: EventBus):
    self.event_bus = event_bus
    self.state = AudioManagerState.STOPPED
    self.recording_queue = Queue()
    self.thread = None
    self.pyaudio = pyaudio.PyAudio()
    self.debug_recording_dir = 'debug_audio'
    os.makedirs(self.debug_recording_dir, exist_ok=True)
```

- **`event_bus`**: A central message/notification system used to notify other parts of the application about changes in recording status.
- **`state`**: Tracks whether audio is `STOPPED`, `IDLE` (ready to record), or `RECORDING`.
- **`recording_queue`**: A `Queue` to send commands or contexts to the worker thread. This is how `start_recording()` and `stop_recording()` communicate with the actual recording loop.
- **`thread`**: Will eventually hold the worker thread that captures audio.
- **`pyaudio`**: The PyAudio instance for interfacing with the hardware or default sound device.
- **`debug_recording_dir`**: A directory for saving raw `.wav` files if debugging is enabled.
- **`os.makedirs(self.debug_recording_dir, exist_ok=True)`**: Ensures the debug directory exists.

---

## 3. Starting and Stopping the Audio System

```python
def start(self):
    if self.state == AudioManagerState.STOPPED:
        self.state = AudioManagerState.IDLE
        self.thread = threading.Thread(target=self._audio_thread)
        self.thread.start()
```

- **start()**:  
  1. Checks if the audio is currently **STOPPED**.
  2. If stopped, sets the state to **IDLE**, meaning “ready to accept recording requests.”
  3. Spawns a new thread (`self.thread`) that runs `_audio_thread()`. This dedicated thread will do all the heavy lifting (opening the input device, capturing frames, applying VAD logic, etc.).

```python
def stop(self):
    if self.state != AudioManagerState.STOPPED:
        self.state = AudioManagerState.STOPPED
        self.recording_queue.put(None)  # Sentinel value to stop the thread
        if self.thread:
            self.thread.join(timeout=2)
            if self.thread.is_alive():
                ConfigManager.log_print("Warning: Audio thread did not terminate gracefully.")
    self.pyaudio.terminate()
```

- **stop()**:  
  1. Sets the state to **STOPPED** so that no further audio capturing occurs.
  2. Puts a sentinel value `None` in `recording_queue` to unblock the queue read in the worker thread.
  3. Joins the worker thread with a 2-second timeout.
     - If the thread is still alive, logs a warning. (In a robust system, you might need more fallback logic.)
  4. Terminates the PyAudio instance once the thread is done. No more audio I/O can occur afterward.

---

## 4. Recording Commands

```python
def start_recording(self, profile: Profile, session_id: str):
    self.recording_queue.put(RecordingContext(profile, session_id))
```

- **start_recording()**:  
  1. Creates a `RecordingContext` (a `namedtuple` of `app` and `session_id`, although your snippet shows `RecordingContext` as `[app, session_id]` but is used with `profile, session_id` — presumably `profile` has `app` or is an equivalent data structure).
  2. Pushes that context onto the `recording_queue`. This signals the worker thread to begin recording the given profile’s audio, with a unique session ID.

```python
def stop_recording(self):
    self.recording_queue.put(None)  # Sentinel value to stop current recording
```

- **stop_recording()**:  
  1. Writes a `None` sentinel to the queue to tell the worker thread to stop capturing immediately.  
  2. If we’re in **RECORDING** state, this gracefully signals “stop the current recording.” Then, once the worker thread sees that `None`, it breaks out of the loop.

```python
def is_recording(self):
    return self.state == AudioManagerState.RECORDING
```

- **is_recording()**: Simple helper that returns `True` if the manager is actively in **RECORDING** state.

---

## 5. The Main Audio Thread Loop

```python
def _audio_thread(self):
    while self.state != AudioManagerState.STOPPED:
        try:
            context = self.recording_queue.get(timeout=0.2)
            if context is None:
                continue  # effectively stopping the current recording
            self.state = AudioManagerState.RECORDING
            self._record_audio(context)
            if self.state != AudioManagerState.STOPPED:
                self.state = AudioManagerState.IDLE
        except Empty:
            continue
```

- This is the **core** loop running in a separate thread. It runs until `self.state` becomes **STOPPED**.
- **`self.recording_queue.get(timeout=0.2)`**:
  1. Waits (up to 0.2s) for an item in the queue.
  2. If it times out, it hits the `Empty` exception and just `continue`s, which means “check the state again in the next iteration.”
- If the context is `None`, that is the sentinel meaning “stop current recording,” so the code just `continue`s the loop without calling `_record_audio()`.
- Otherwise:
  1. Sets state to **RECORDING**.
  2. Calls `_record_audio(context)` for actual capturing.
  3. After `_record_audio` completes, if we’re not **STOPPED** already, we go back to **IDLE**.

This design ensures you can queue up multiple start/stop commands and the audio thread will process them sequentially.

---

## 6. Recording Logic: `_record_audio()`

```python
def _record_audio(self, context: RecordingContext):
    recording_options = ConfigManager.get_section('recording_options', context.app.name)
    audio_config = self._prepare_audio_config(context, recording_options)

    stream = self._setup_audio_stream(audio_config)
    debug_wav_file = (self._setup_debug_file(context, audio_config) if
                      audio_config['save_debug_audio'] else None)

    try:
        recording, speech_detected = self._capture_audio(context, audio_config,
                                                         stream, debug_wav_file)
    finally:
        self._cleanup_audio_resources(stream, debug_wav_file)

    if not context.profile.is_streaming:
        self._process_non_streaming_audio(context, audio_config, recording, speech_detected)

    context.profile.audio_queue.put(None)  # Push sentinel value

    # Notify of auto-termination if VAD was used and we’re not stopped
    if audio_config['use_vad'] and self.state != AudioManagerState.STOPPED:
        self.event_bus.emit("recording_stopped", context.session_id)
```

Breaking it down:

1. **`recording_options`**: Reads recording settings from the `ConfigManager` (like sample rate, gain, silence thresholds, etc.).
2. **`audio_config`**: This dictionary (from `_prepare_audio_config`) bundles relevant audio settings (sample rate, chunk sizes, VAD usage, gain, etc.).
3. **`_setup_audio_stream()`**: Opens a PyAudio `Stream` for actual audio input using the chosen device, format, channels, etc.
4. **`_setup_debug_file()`** (conditional): Opens a `.wav` file for saving raw audio if debugging is turned on.
5. **`_capture_audio()`**: The heart of capturing audio frames, performing voice activity detection, streaming data in chunks if necessary, and building up a final “recording” array (list of frames).
6. **`finally: _cleanup_audio_resources()`**: Ensures the audio stream and debug file get closed properly, even if an exception arises.
7. For *non-streaming* audio, calls **`_process_non_streaming_audio()`** which finalizes and sends the entire captured audio buffer to the consumer.  
8. Places a sentinel `None` into `profile.audio_queue` to signal that the recording is finished.  
9. If VAD was used, emit a “recording_stopped” event on the `EventBus`—this can be used by other parts of the system to handle UI updates or further logic.

---

## 7. Preparing Audio Config: `_prepare_audio_config()`

```python
def _prepare_audio_config(self, context: RecordingContext, recording_options):
    sample_rate = recording_options.get('sample_rate', 16000)
    streaming_chunk_size = context.profile.streaming_chunk_size or 4096
    frame_size = self._calculate_frame_size(sample_rate, streaming_chunk_size,
                                            context.app.is_streaming)
    silence_duration_ms = recording_options.get('silence_duration', 900)
    recording_mode = RecordingMode[recording_options.get('recording_mode',
                                                         'PRESS_TO_TOGGLE').upper()]

    return {
        'sample_rate': sample_rate,
        'gain': recording_options.get('gain', 1.0),
        'channels': 1,
        'streaming_chunk_size': streaming_chunk_size,
        'frame_size': frame_size,
        'silence_frames': int(silence_duration_ms / (frame_size / sample_rate * 1000)),
        'sound_device': self._get_sound_device(recording_options.get('sound_device')),
        'save_debug_audio': recording_options.get('save_debug_audio', False),
        'use_vad': recording_mode in (RecordingMode.VOICE_ACTIVITY_DETECTION,
                                      RecordingMode.CONTINUOUS)
    }
```

- **sample_rate**: By default 16kHz.  
- **streaming_chunk_size**: The size of each chunk that will be processed if streaming. Defaults to 4096 if not provided.
- **frame_size**: Calculated by `_calculate_frame_size`. This often corresponds to the VAD-friendly frames (like 10ms, 20ms, or 30ms).
- **silence_duration_ms**: The threshold of silence that VAD uses to consider ending the recording (e.g., 900 ms).
- **silence_frames**: How many frames equate to that silence duration at the chosen frame_size / sample_rate.
- **use_vad**: Tied to the user-chosen “recording_mode.” In `VOICE_ACTIVITY_DETECTION` or `CONTINUOUS` mode, we automatically detect speech presence.

---

## 8. Setting up the PyAudio Stream: `_setup_audio_stream()`

```python
def _setup_audio_stream(self, audio_config):
    return self.pyaudio.open(format=pyaudio.paFloat32,
                             channels=audio_config['channels'],
                             rate=audio_config['sample_rate'],
                             input=True,
                             input_device_index=audio_config['sound_device'],
                             frames_per_buffer=audio_config['frame_size'])
```

This simply creates and opens a PyAudio stream:
- **format** = `paFloat32` means each sample is a 32-bit float in range [-1.0, 1.0].
- **channels** = 1 for mono (typical for voice).
- **rate** = sample rate from the config.
- **frames_per_buffer** = how many samples to read each time we call `stream.read()`.

---

## 9. Debug File Setup: `_setup_debug_file()`

```python
def _setup_debug_file(self, context, audio_config):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{context.profile.name}_{timestamp}.wav"
    debug_wav_file = wave.open(os.path.join(self.debug_recording_dir, filename), 'wb')
    debug_wav_file.setnchannels(audio_config['channels'])
    debug_wav_file.setsampwidth(2)  # 16-bit audio
    debug_wav_file.setframerate(audio_config['sample_rate'])
    return debug_wav_file
```

- Creates a `.wav` file (16-bit, 1 channel) in the `debug_audio` directory, with a timestamp.  
- Even though PyAudio is using Float32 internally, the debug file is saved as Int16.

---

## 10. Capturing Audio: `_capture_audio()`

```python
def _capture_audio(self, context, audio_config, stream, debug_wav_file):
    recording = []
    silent_frame_count = 0
    speech_detected = False
    sample_rate = audio_config['sample_rate']
    initial_frames_to_skip = int(0.15 * sample_rate / audio_config['frame_size'])
    vad = webrtcvad.Vad(2) if audio_config['use_vad'] else None

    while self.state != AudioManagerState.STOPPED and self.recording_queue.empty():
        frame = stream.read(audio_config['frame_size'])
        frame_array = self._process_audio_frame(frame, audio_config['gain'])
        recording.extend(frame_array)

        if debug_wav_file:
            int16_frame = (frame_array * 32767).astype(np.int16)
            debug_wav_file.writeframes(int16_frame.tobytes())

        if context.profile.is_streaming:
            self._handle_streaming(context, audio_config, recording)

        if vad:
            if initial_frames_to_skip > 0:
                initial_frames_to_skip -= 1
                continue
            # Convert to int16 for VAD
            int16_frame = (frame_array * 32767).astype(np.int16)
            if vad.is_speech(int16_frame.tobytes(), sample_rate):
                silent_frame_count = 0
                if not speech_detected:
                    ConfigManager.log_print("Speech detected.")
                    speech_detected = True
            else:
                silent_frame_count += 1

            if speech_detected and silent_frame_count > audio_config['silence_frames']:
                break

    return recording, speech_detected
```

Key points:
1. **`recording = []`**: A list that accumulates all the float32 samples.
2. **`silent_frame_count`**: Tracks how many frames have no speech (for VAD).
3. **`initial_frames_to_skip`**: Skips VAD for the initial 150ms to avoid false positives from keyboard/microphone noise.
4. **`stream.read()`**: Reads `frame_size` samples from PyAudio.
5. **`_process_audio_frame()`** applies gain and ensures the data is clamped to [-1, 1].
6. **Write to debug file** if enabled (converted to int16).
7. **If streaming**: `_handle_streaming()` sends audio chunks in real time to wherever `Profile.audio_queue` is consumed.
8. **If VAD** is active, calls `vad.is_speech()` on the int16 data:
   - If speech is detected, resets `silent_frame_count` to 0 and marks `speech_detected = True`.
   - If no speech, increments `silent_frame_count`.
   - If `speech_detected` is already true and we exceed the allowed silence frames, break from the loop (ending the recording).

The loop runs until:
- The state becomes **STOPPED**, or
- A `None` is placed on the `recording_queue` (which is checked by `self.recording_queue.empty()` to know if a new command arrived), or
- VAD triggers a break due to extended silence.

---

## 11. Streaming vs. Non-streaming: `_handle_streaming()` and `_process_non_streaming_audio()`

### Streaming (`_handle_streaming()`)

```python
def _handle_streaming(self, context, audio_config, recording):
    chunk_size = audio_config['streaming_chunk_size']
    sample_rate = audio_config['sample_rate']
    while len(recording) >= chunk_size:
        chunk = np.array(recording[:chunk_size], dtype=np.float32)
        self._push_audio_chunk(context, chunk, sample_rate, audio_config['channels'])
        del recording[:chunk_size]
```

- Continuously checks if the `recording` buffer has enough samples (`chunk_size` or more).
- Extracts that chunk and calls `_push_audio_chunk()` to immediately send it to `context.profile.audio_queue`.
- Removes those samples from the `recording` buffer.
- Leaves leftover samples in `recording` for the next iteration.

### Non-streaming (`_process_non_streaming_audio()`)

```python
def _process_non_streaming_audio(self, context, audio_config, recording, speech_detected):
    audio_data = np.array(recording, dtype=np.float32)
    duration = len(audio_data) / audio_config['sample_rate']

    ...
    if audio_config['use_vad'] and not speech_detected:
        ...
    elif (duration * 1000) >= min_duration_ms:
        self._push_audio_chunk(context, audio_data, audio_config['sample_rate'], audio_config['channels'])
    else:
        ...
```

- Once recording ends, we convert the entire list of float samples into a NumPy array, measure the duration.
- If no speech was detected and VAD was used, we discard the audio and emit an `"audio_discarded"` event.
- Else if the duration meets a minimum threshold, we send the entire final audio chunk in one go.
- Otherwise, it’s considered too short, so we discard it.

---

## 12. Cleanup and Utility Methods

### `_cleanup_audio_resources()`

```python
def _cleanup_audio_resources(self, stream, debug_wav_file):
    stream.stop_stream()
    stream.close()
    if debug_wav_file:
        debug_wav_file.close()
```

- Safely stops/closes the PyAudio stream and the debug file.

### `_calculate_frame_size()`
```python
def _calculate_frame_size(self, sample_rate: int, streaming_chunk_size: int, is_streaming: bool) -> int:
    ...
```
- For streaming, tries to find a frame duration (in ms) that is evenly divisible by the streaming chunk size (10, 20, 30 ms are typical for WebRTC VAD).
- For non-streaming, defaults to 30 ms.

### `_get_sound_device()`
```python
def _get_sound_device(self, device):
    ...
```
- Checks if a specific device index is given.  
- If invalid or not given, falls back to PyAudio’s default input device.  
- Logs the chosen device via `ConfigManager.log_print()`.

### `_process_audio_frame()`
```python
def _process_audio_frame(self, frame: bytes, gain: float) -> np.ndarray:
    frame_array = np.frombuffer(frame, dtype=np.float32).copy()
    frame_array *= gain
    np.clip(frame_array, -1.0, 1.0, out=frame_array)
    return frame_array
```
- Converts raw bytes → float32 array.
- Applies a user-configured `gain`.
- Clamps samples to [-1.0, 1.0] to avoid overflow.

### `_push_audio_chunk()`
```python
def _push_audio_chunk(self, context: RecordingContext, audio_data: np.ndarray,
                      sample_rate: int, channels: int):
    context.profile.audio_queue.put({
        'session_id': context.session_id,
        'sample_rate': sample_rate,
        'channels': channels,
        'language': 'auto',
        'audio_chunk': audio_data
    })
```
- Puts a dictionary of audio metadata + the actual NumPy audio data onto the `Profile`’s `audio_queue`. 
- Other parts of the app will presumably process it (transcription, sending over network, etc.).

### `cleanup()`
```python
def cleanup(self):
    self.stop()
    self.thread = None
    self.pyaudio = None
    self.recording_queue = None
```
- Gracefully stops and frees references. Often used at application shutdown.

---

## 13. Design Choices and Flow Summary

1. **Thread-Based Audio Capture**:  
   - Audio capturing is done in a single dedicated thread (`_audio_thread`) that *blocks* on reading from the microphone. This prevents blocking the main UI or other logic.

2. **Queue-based Commands**:  
   - Start/stop recording requests are placed onto `recording_queue`. This is a thread-safe way for the main thread to tell the audio thread what to do without concurrency issues.

3. **Sentinel Values**:  
   - Using `None` as a sentinel indicates a request to stop the current recording (or to shut down entirely, depending on context). This is a common pattern in producer/consumer or queue-based threading.

4. **Voice Activity Detection**:  
   - `webrtcvad.Vad(2)` is used for speech detection. Level 2 is typically a good balance between sensitivity and false-positives. Once silence is detected for a certain duration, recording stops automatically.

5. **Streaming vs. Non-Streaming**:
   - If streaming, audio is chunked into smaller pieces and pushed in near-real-time.
   - If not streaming, the entire audio is accumulated in an array and then processed after capture ends. 
   - This is determined by `context.profile.is_streaming`.

6. **Debugging**:
   - Optionally writes `.wav` files to `debug_audio/` for analysis of captured audio.  
   - The debug files are stored in 16-bit format, which is typical for wave files, even though the internal stream is 32-bit float.

7. **Cleanup**:
   - Ensures that resources are always properly released (`stop_stream()`, `close()`, `terminate()`) to avoid device lock-ups or leftover threads.

Overall, the **AudioManager** cleanly encapsulates audio capture, device configuration, optional debug logging, and VAD-based or manual stop logic. It uses a consistent state machine (`STOPPED` -> `IDLE` -> `RECORDING` -> back to `IDLE`), with a queue-based approach that makes threading and concurrency easier to manage.