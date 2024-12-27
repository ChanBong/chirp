Below is a **detailed walkthrough** of the `TranscriptionManager` class. This component is responsible for **managing the transcription process** in your application—choosing the correct backend, listening for audio data from a queue, transcribing it (streaming or non-streaming), and emitting results or errors via an event bus.

---

## 1. Purpose and High-Level Overview

1. **Orchestrates** the entire transcription lifecycle:
   - Chooses the correct backend (Faster Whisper, OpenAI, Vosk, etc.).
   - Initializes the backend with the right configuration.
   - Spawns a dedicated thread to continuously handle transcription tasks.
2. **Listens** for **audio data** in the `Profile`’s `audio_queue`—populated by the `AudioManager`.
3. **Processes** audio in either **streaming** or **batch** mode, based on configuration.
4. **Publishes** results or errors via the `EventBus`.

In essence, `TranscriptionManager` is the glue between raw audio and final text, mediated by your chosen transcription backend.

---

## 2. Constructor: `__init__`

```python
def __init__(self, profile, event_bus: EventBus):
    self.profile_name = profile.name
    self.event_bus = event_bus
    self.audio_queue = profile.audio_queue
    self.backend_type = ConfigManager.get_value('backend_type', self.profile_name)
    backend_class = self._get_backend_class()
    self.backend: TranscriptionBackendBase = backend_class()
    self.processing_thread = None
    self.current_session_id = None
    self.transcribe_event = threading.Event()
    self.stop_event = threading.Event()
```

1. **`profile_name`**: Stores the name of the profile (e.g., user configuration) that this manager belongs to.  
2. **`event_bus`**: Used to emit events like `"transcription_finished"`, `"raw_transcription_result"`, etc., so that the rest of the app can react.  
3. **`audio_queue`**: Points to the `Profile`’s queue of audio data (chunks or entire recordings). This is how the manager receives audio.  
4. **`backend_type`**: Retrieved from `ConfigManager`, e.g., `'faster_whisper'`, `'openai'`, or `'vosk'`.  
5. **`_get_backend_class()`**: Dynamically imports the right backend class, returning a subclass of `TranscriptionBackendBase`. The result is instantiated as `self.backend`.  
6. **Threading Controls**:
   - `self.processing_thread`: The background thread that runs `_transcription_thread()`.  
   - `self.current_session_id`: Tracks the active session ID (if any).  
   - `self.transcribe_event`: A threading `Event` used to signal “start transcribing.”  
   - `self.stop_event`: Another `Event` used to signal “stop the transcription thread.”

---

## 3. Selecting the Backend: `_get_backend_class()`

```python
def _get_backend_class(self):
    if self.backend_type == 'faster_whisper':
        from transcription_backend.faster_whisper_backend import FasterWhisperBackend
        return FasterWhisperBackend
    elif self.backend_type == 'openai':
        from transcription_backend.openai_backend import OpenAIBackend
        return OpenAIBackend
    elif self.backend_type == 'vosk':
        from transcription_backend.vosk_backend import VoskBackend
        return VoskBackend
    else:
        raise ValueError(f"Unsupported backend type: {self.backend_type}")
```

- This **dynamically** imports only the module needed based on `backend_type`.  
- Each imported class is a specific transcription backend (all presumably implement the same interface `TranscriptionBackendBase` for uniform usage).  
- If `backend_type` is unknown, raises an error.

---

## 4. Getting Chunk Size: `get_preferred_streaming_chunk_size()`

```python
def get_preferred_streaming_chunk_size(self):
    return self.backend.get_preferred_streaming_chunk_size()
```

- Simply **delegates** to the backend to find the ideal chunk size for streaming. This is used by the `AudioManager` to decide how many samples per chunk to capture if streaming is enabled.

---

## 5. Starting and Stopping the Manager

### 5.1 `start()`

```python
def start(self):
    if not self.backend.is_initialized():
        backend_options = ConfigManager.get_section('backend', self.profile_name)
        try:
            self.backend.initialize(backend_options)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize backend for profile "
                               f"{self.profile_name}.\n{e}")

    if not self.processing_thread:
        self.processing_thread = threading.Thread(target=self._transcription_thread)
        self.processing_thread.start()
```

**Steps**:

1. **Check** if the backend is initialized. If not, read `backend_options` from config and call `self.backend.initialize(backend_options)`.  
2. **Start** the background transcription thread if it isn’t already running. This ensures that once we signal “transcribe” with `transcribe_event`, the thread is ready to process audio.

### 5.2 `stop()`

```python
def stop(self):
    self.stop_event.set()
    self.transcribe_event.set()  # Wake up the thread to exit
    if self.processing_thread:
        self.processing_thread.join()
        self.processing_thread = None
```

- Sets the `stop_event`, telling the transcription thread to break out of its loop.  
- Sets `transcribe_event` to **wake** the thread if it’s waiting. This ensures we don’t leave the thread blocked.  
- Joins the thread and sets it to `None` so we can cleanly shut down or start again later if needed.

---

## 6. Starting a New Transcription Session

```python
def start_transcription(self, session_id: str):
    self.current_session_id = session_id
    self.stop_event.clear()
    self.transcribe_event.set()
```

- Assigns a new `session_id`. Usually called by the application controller when a new recording session starts.  
- Clears any previous stop signal (`stop_event.clear()`) so the thread can run again.  
- Sets `transcribe_event`, which **unblocks** the transcription thread so it starts `_process_audio()`.

---

## 7. The Transcription Thread: `_transcription_thread()`

```python
def _transcription_thread(self):
    while not self.stop_event.is_set():
        self.transcribe_event.wait()
        self.transcribe_event.clear()

        if self.stop_event.is_set():
            break

        self._process_audio()
```

- **Infinite loop** that runs until `stop_event` is set.  
- **Waits** on `transcribe_event`. This is crucial so the thread only proceeds when there's a transcription job to do.  
- Once triggered, it **clears** the event (so we don’t re-run it immediately in the next iteration) and checks if we were told to stop.  
- Calls `_process_audio()` to handle all the data in the queue.  
- After `_process_audio()` finishes, it goes back to waiting for the next event or until `stop_event` is triggered.

**Design Choice**: 
- Using two events (`stop_event` and `transcribe_event`) allows the thread to idle without busy-waiting, and to exit gracefully.

---

## 8. Processing Audio: `_process_audio()`

```python
def _process_audio(self):
    if not self.backend:
        ConfigManager.log_print("Backend not initialized. Transcription cannot start.")
        return

    is_streaming = ConfigManager.get_value('backend.use_streaming', self.profile_name)

    try:
        if is_streaming:
            for result in self.backend.process_stream(self.audio_queue, self.stop_event):
                if self.stop_event.is_set():
                    break
                self._emit_result(result)
        else:
            while not self.stop_event.is_set():
                try:
                    audio_data = self.audio_queue.get(timeout=0.2)
                    if audio_data is None:  # Sentinel value
                        break
                    ...
                    result = self.backend.transcribe_complete(
                        audio_data['audio_chunk'],
                        audio_data['sample_rate'],
                        audio_data['channels'],
                        audio_data['language']
                    )
                    ...
                    result['is_utterance_end'] = True
                    self._emit_result(result)
                except queue.Empty:
                    continue
    finally:
        self.current_session_id = None
        self.event_bus.emit("transcription_finished", self.profile_name)
```

**Steps**:

1. **Checks** if `self.backend` is present. If not, logs a warning and returns.
2. **Determines** if the user wants streaming (`is_streaming = True`) from the config.
3. Two main flows:
   1. **Streaming**:  
      - Calls `self.backend.process_stream(self.audio_queue, self.stop_event)` which presumably yields partial results in real time.  
      - For each partial `result`, checks if `stop_event` is set (to bail out). Otherwise, calls `_emit_result(result)`.  
   2. **Non-streaming**:
      - Continually `get()` blocks from `self.audio_queue` with a 0.2s timeout.  
      - If it obtains a `None`, that’s a sentinel meaning “no more audio.” Break the loop.  
      - Otherwise, calls `self.backend.transcribe_complete(...)` on the entire chunk.  
      - Logs the raw transcription time, sets an additional flag `is_utterance_end`, then `_emit_result(result)`.  
      - If the queue is empty, a `queue.Empty` exception is caught, and the code just loops again.
4. **finally** block:
   - Always resets `current_session_id` to `None`.  
   - Emits `"transcription_finished"` to signal the entire process ended for the current profile.

---

## 9. Emitting Results: `_emit_result()`

```python
def _emit_result(self, result: Dict[str, Any]):
    if result['error']:
        self.event_bus.emit("transcription_error", result['error'])
    self.event_bus.emit("raw_transcription_result", result, self.current_session_id)
```

- If the backend sets `result['error']`, we emit a separate `"transcription_error"` event.  
- In either case, we also emit a `"raw_transcription_result"` event, passing along the transcription data and the `current_session_id`.  
- The rest of the application can listen to these events for updates (e.g., to display text in the UI, or post-process the text further).

---

## 10. Cleanup

```python
def cleanup(self):
    self.stop()
    if self.backend:
        self.backend.cleanup()
        self.backend = None
```

1. **Stops** the thread by calling `stop()`.  
2. **Calls** `self.backend.cleanup()` to release any backend resources (e.g., GPU models, file handles, network connections).  
3. Sets `self.backend` to `None`.

This ensures a clean shutdown and that the transcription manager can be restarted (if needed) with a fresh backend initialization.

---

## 11. Key Design Decisions

1. **Threaded Approach**  
   - The class runs its own **transcription thread** that waits on `transcribe_event`. This is safer than transcribing on the main thread, which might freeze the UI or block other tasks.  
   - The `stop_event` allows graceful interruption of the loop.

2. **Two Operation Modes**: **Streaming** vs. **Non-Streaming**  
   - **Streaming**: The backend can yield partial transcriptions for each chunk. The code uses `process_stream()` for real-time updates.  
   - **Non-Streaming**: The code waits for entire audio chunks (or entire recordings), transcribes them in one go, and emits a result once each chunk is fully processed.

3. **Config-driven**  
   - The backend type, streaming preferences, and other details come from `ConfigManager`. This makes it easy to switch transcription engines or toggle streaming with minimal code changes.

4. **Event-Driven**  
   - The manager communicates results via the `EventBus`, decoupling the transcription logic from whoever consumes the text.  
   - The rest of the system can subscribe to `raw_transcription_result` or `transcription_finished` events to handle UI updates, post-processing, or logging.

5. **Session Management**  
   - Each new recording has a unique `session_id`. This helps the rest of the system track which utterance or conversation snippet the transcriptions belong to.  
   - Once done, `current_session_id` is cleared, and `transcription_finished` is emitted for that profile.

---

## 12. Summary of the Flow

1. **Initialization**: The manager is created with a reference to a `Profile`’s audio queue and an event bus.
2. **Selecting a Backend**: Decides which transcription engine to use based on config (e.g., FasterWhisper, OpenAI, Vosk).
3. **Start**: Ensures backend is initialized and spawns `_transcription_thread()`.
4. **start_transcription(session_id)**: Clears any stop request, sets the new session ID, and signals the thread (`transcribe_event.set()`).
5. **Thread**: Waits for `transcribe_event`; once signaled, calls `_process_audio()`:
   - If **streaming** is on, uses `process_stream()` in a loop.
   - If **non-streaming**, repeatedly reads chunks from the audio queue and calls `transcribe_complete()`.
   - For each result, calls `_emit_result()` to broadcast via the event bus.
   - Ends by resetting `current_session_id` and emitting `"transcription_finished"`.
6. **Stop**: Sets `stop_event`, signals the thread to wake up and exit, and joins it.
7. **Cleanup**: Calls the backend’s own cleanup routines and clears references.

By structuring the manager this way, you get a **modular**, **scalable**, and **maintainable** system for transcription that can switch backends easily and handle real-time or batch transcription scenarios seamlessly.