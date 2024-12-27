Below is a **step-by-step** explanation of the `ApplicationController` class and its design. The key objective is to illustrate how the controller organizes different parts of the application—particularly audio recording, transcription, input events, and UI—to create a coherent workflow.

---

## 1. Purpose and High-Level Overview

The `ApplicationController` acts as the **central coordinator** for the application. Its responsibilities include:

1. **Initializing** and **managing** application components, such as:
   - The `AudioManager` (handles microphone input and recording)
   - The `InputManager` (handles keyboard shortcuts or other input events)
   - The `Profile` objects (one per user configuration)
2. **Orchestrating** the flow of events, such as:
   - Starting/stopping recordings
   - Handling user shortcuts (press/release events)
   - Dealing with automatic stopping via VAD (Voice Activity Detection)
3. **Maintaining** a mapping between *session IDs* and the *profiles* that spawned them.  
4. **Handling** the UI event loop lifecycle and cleaning up resources on exit.

In short, everything flows through the `ApplicationController`, which ties together multiple managers and watchers, bridging them with an event bus system.

---

## 2. Constructor: `__init__`

```python
def __init__(self, ui_manager, event_bus):
    self.ui_manager = ui_manager
    self.event_bus = event_bus
    self.audio_queue = Queue()
    self.listening = False
    self.audio_manager = None
    self.input_manager = None
    self.manually_stopped_profiles = set()  # For tracking continuous mode profiles

    self.active_profiles: Dict[str, Profile] = {}
    self.session_profile_map: Dict[str, str] = {}

    self.load_active_profiles()
    self.setup_connections()
```

- **UI Manager** (`ui_manager`): Manages the graphical user interface, typically a Qt or similar framework.  
- **Event Bus** (`event_bus`): A publish-subscribe system used for inter-component communication.  
- **`audio_queue`**: A queue for audio data or events if needed (though the snippet doesn’t heavily use it).  
- **`listening`**: A boolean flag that indicates whether the app is in a “listening” or “started” state.  
- **`audio_manager` / `input_manager`**: Will be instantiated later. They start/stop along with the application.  
- **`manually_stopped_profiles`**: Used to handle logic around *continuous recording* profiles that the user has explicitly stopped, so the app doesn’t auto-restart them.  
- **`active_profiles`**: A dictionary from profile name → `Profile` instance.  
- **`session_profile_map`**: A dictionary from session_id → profile name. This helps the controller figure out which profile an ongoing recording belongs to.  

Finally, the constructor calls:
1. **`load_active_profiles()`**: Reads configuration and initializes `Profile` objects.  
2. **`setup_connections()`**: Subscribes to events on the `event_bus`.

---

## 3. Loading Profiles: `load_active_profiles()`

```python
def load_active_profiles(self):
    active_profiles = ConfigManager.get_profiles(active_only=True)
    for profile in active_profiles:
        profile_name = profile['name']
        profile_obj = Profile(profile_name, self.event_bus)
        self.active_profiles[profile_name] = profile_obj
```

- Uses the `ConfigManager` to get all “active” profiles from some configuration.
- For each profile definition, instantiates a `Profile` object.
- Stores it in `self.active_profiles` for later access.  

This design decouples reading from a config file (handled by `ConfigManager`) from actually setting up the `Profile` objects.

---

## 4. Event Subscriptions: `setup_connections()`

```python
def setup_connections(self):
    self.event_bus.subscribe("start_listening", self.handle_start_listening)
    self.event_bus.subscribe("shortcut_triggered", self.handle_shortcut)
    self.event_bus.subscribe("audio_discarded", self.handle_audio_discarded)
    self.event_bus.subscribe("recording_stopped", self.handle_recording_stopped)
    self.event_bus.subscribe("transcription_complete", self.handle_transcription_complete)
    self.event_bus.subscribe("config_changed", self.handle_config_change)
    self.event_bus.subscribe("close_app", self.close_application)
```

This method **wires up** the controller to various application-wide events, allowing the controller to react:

1. **`start_listening`** → `handle_start_listening`  
2. **`shortcut_triggered`** → `handle_shortcut`  
3. **`audio_discarded`** → `handle_audio_discarded`  
4. **`recording_stopped`** → `handle_recording_stopped`  
5. **`transcription_complete`** → `handle_transcription_complete`  
6. **`config_changed`** → `handle_config_change`  
7. **`close_app`** → `close_application`  

Each subscription ties an event name to a handler method.

---

## 5. Handling User Shortcuts: `handle_shortcut()`

```python
def handle_shortcut(self, profile_name: str, event_type: str):
    profile = self.active_profiles.get(profile_name)
    if profile:
        if event_type == "press":
            if profile.should_start_on_press():
                self.start_recording(profile)
            elif profile.should_stop_on_press():
                self.stop_recording(profile)
                if profile.recording_mode == RecordingMode.CONTINUOUS:
                    self.manually_stopped_profiles.add(profile.name)
        elif event_type == "release":
            if profile.should_stop_on_release():
                self.stop_recording(profile)
```

**Workflow**:

1. Looks up the `Profile` by name from `active_profiles`.
2. Depending on whether the event was a **press** or **release**:
   - **Press**:
     - If the profile says “start on press,” call `start_recording(profile)`.
     - Else if it says “stop on press,” call `stop_recording(profile)` and note if it’s a continuous recording that the user manually stopped (by adding to `manually_stopped_profiles`).
   - **Release**:
     - If the profile says “stop on release,” call `stop_recording(profile)`.

This design allows flexible control: some profiles might start recording on press, others on release, etc. It’s all determined by the `Profile` logic (e.g., `profile.should_start_on_press()`).

---

## 6. Starting and Stopping Recordings

### `start_recording()`

```python
def start_recording(self, profile: Profile):
    if profile.is_idle() and not self.audio_manager.is_recording():
        session_id = str(uuid.uuid4())
        self.session_profile_map[session_id] = profile.name
        self.audio_manager.start_recording(profile, session_id)
        profile.start_transcription(session_id)
        self.manually_stopped_profiles.discard(profile.name)
    else:
        ConfigManager.log_print("Profile or audio thread is busy.")
```

Steps:

1. Checks if the profile is idle (i.e., not currently recording) **and** if the `AudioManager` is not already recording.
2. Creates a unique `session_id` (using `uuid.uuid4()`).
3. Stores the mapping `session_id` → `profile.name` in `session_profile_map`.
4. Instructs the `AudioManager` to start recording with `(profile, session_id)`.
5. Tells the profile to start its transcription process (`profile.start_transcription(session_id)`).  
6. Removes the profile name from `manually_stopped_profiles` to reset the “manually stopped” state if it was previously there.

If the profile is not idle or the `AudioManager` is busy, logs a message.

### `stop_recording()`

```python
def stop_recording(self, profile: Profile):
    if profile.is_recording():
        self.audio_manager.stop_recording()
        profile.recording_stopped()
```

- If the profile is currently in a recording state, calls `audio_manager.stop_recording()`—which sends a sentinel to the audio thread to stop.  
- Then calls `profile.recording_stopped()`, so the profile knows the audio capture has ended on purpose.

---

## 7. Handling Events After Recording

### `handle_recording_stopped()`

```python
def handle_recording_stopped(self, session_id: str):
    profile = self._get_profile_for_session(session_id)
    if profile:
        self.stop_recording(profile)
```

- This is triggered when **VAD** or **CONTINUOUS** logic in the `AudioManager` automatically stops a recording.  
- Looks up the relevant `profile` based on `session_id` and then calls `stop_recording(profile)` to do the official teardown (i.e., call `profile.recording_stopped()`).

### `handle_audio_discarded()`

```python
def handle_audio_discarded(self, session_id: str):
    profile = self._get_profile_for_session(session_id)
    if profile:
        profile.finish_transcription()  # This will emit "transcription_complete" event
```

- If recorded audio was discarded (e.g., no speech detected, or too short):
  - The `Profile` is told to “finish” the transcription, which presumably notifies the rest of the system that transcription ended with no result.

### `handle_transcription_complete()`

```python
def handle_transcription_complete(self, session_id: str):
    profile = self._get_profile_for_session(session_id)
    if profile:
        del self.session_profile_map[session_id]
        # Play beep sound if configured
        if ConfigManager.get_value('global_options.noise_on_completion', False):
            beep_file = os.path.join('assets', 'beep.wav')
            play_wav(beep_file)

        if (profile.recording_mode == RecordingMode.CONTINUOUS and
                profile.name not in self.manually_stopped_profiles):
            self.start_recording(profile)
        else:
            self.manually_stopped_profiles.discard(profile.name)
```

- Finds the `Profile` via `session_id`, then removes that session from `session_profile_map`.
- Optionally plays a beep when transcription is complete (`noise_on_completion` setting).
- **Continuous mode** logic:
  - If the `Profile` is in `CONTINUOUS` mode and the user **did not** manually stop it, automatically re-start recording. This ensures that in continuous mode, once a session completes, a new one begins.
  - If the user manually stopped it, do nothing further.

---

## 8. Handling “Start Listening” and Config Changes

### `handle_start_listening()`

```python
def handle_start_listening(self):
    self.listening = True
    self.start_core_components()
```

- When the system receives a “start_listening” event, set `listening = True` and call `start_core_components()` to initialize everything.

### `handle_config_change()`

```python
def handle_config_change(self):
    self.cleanup()
    self.load_active_profiles()
    if self.listening:
        self.start_core_components()
```

- On a “config_changed” event, the controller fully **cleans up** (stops all managers, clears out data) and **reloads** profiles from the (new or updated) config.  
- If the application is still in a “listening” state, it re-initializes the core components so the new config settings take effect immediately.

---

## 9. Main Run Loop: `run()`

```python
def run(self):
    self.ui_manager.show_main_window()
    exit_code = self.ui_manager.run_event_loop()
    self.cleanup()
    return exit_code
```

- Shows the main window in the UI and enters the UI’s event loop (e.g., Qt or similar).
- When the UI loop finishes (the user closes the window or triggers exit), it calls `cleanup()` to stop everything.
- Returns an exit code (common in desktop apps for success/failure, etc.).

---

## 10. Starting Core Components: `start_core_components()`

```python
def start_core_components(self):
    if self.ui_manager:
        self.ui_manager.status_update_mode = ConfigManager.get_value(
            'global_options.status_update_mode')
    
    self.input_manager = InputManager(self.event_bus)
    self.audio_manager = AudioManager(self.event_bus)
    self.input_manager.start()
    self.audio_manager.start()

    initialization_error = None
    for profile in self.active_profiles.values():
        try:
            profile.transcription_manager.start()
        except RuntimeError as e:
            initialization_error = str(e)
            ConfigManager.log_print(f"Failed to start transcription manager for "
                                    f"profile {profile.name}.\n{initialization_error}")
            break

    if initialization_error:
        # if there's a failure, stop everything
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
```

Sequence:

1. Optionally updates the UI manager’s status update mode based on config.
2. Instantiates the `InputManager` and `AudioManager` and **starts** them.  
   - `InputManager.start()` typically sets up keyboard hooks or other watchers for user triggers.  
   - `AudioManager.start()` spins up an audio-capturing thread.
3. Starts each `Profile`’s transcription manager. If any fail, logs the error and shuts down everything (`self.cleanup()`), then notifies the user or raises an exception.
4. If all goes well, emits `initialization_successful` over the event bus.

---

## 11. Application Closing: `close_application()` and `cleanup()`

### `close_application()`

```python
def close_application(self):
    self.event_bus.emit("quit_application")
```

- Emits the event that presumably instructs the UI or other watchers to quit the application.

### `cleanup()`

```python
def cleanup(self):
    if self.audio_manager:
        self.audio_manager.stop_recording()
        self.audio_manager.cleanup()
        self.audio_manager = None

    for session_id in list(self.session_profile_map.keys()):
        self.handle_transcription_complete(session_id)

    for profile in self.active_profiles.values():
        profile.cleanup()

    self.active_profiles.clear()
    self.session_profile_map.clear()

    if self.input_manager:
        self.input_manager.cleanup()
        self.input_manager = None
```

**Steps**:

1. Stops any ongoing recording and calls `audio_manager.cleanup()` to terminate audio threads/resources.
2. Ensures all pending sessions are marked as complete (calls `handle_transcription_complete` for any leftover session_ids).
3. Cleans each profile (stop transcription, release resources, etc.).
4. Clears `active_profiles` and `session_profile_map`.
5. Cleans up (stops) the input manager as well.

By the end, all references to managers and session data are cleared, ensuring a clean exit or a clean state to re-initialize if needed.

---

## 12. Getting the Right Profile for a Session: `\_get_profile_for_session()`

```python
def _get_profile_for_session(self, session_id: str) -> Optional[Profile]:
    if session_id in self.session_profile_map:
        profile_name = self.session_profile_map[session_id]
        return self.active_profiles.get(profile_name)
    return None
```

- A helper method that looks up a `session_id` in `session_profile_map` to find the corresponding profile name, then returns that profile from `active_profiles`.

---

## 13. Design Decisions

1. **Event Bus**: A central publish-subscribe model that decouples the controller from other components (UI, input events, audio manager, etc.).  
2. **Profiles**: Each “profile” encapsulates app-specific settings (mic/recording settings, transcription manager, etc.). The controller can manage multiple profiles simultaneously.  
3. **Session-based Recording**: Each recording is assigned a unique `session_id`. That session is mapped to a profile, so we know which profile to notify once the transcription is done.  
4. **Continuous Mode Handling**: If a profile is in `CONTINUOUS` mode, the system automatically restarts recording once the previous session ends—*unless* the user manually stopped it.  
5. **Separation of Concerns**: 
   - **`AudioManager`** strictly handles audio input.  
   - **`Profile`** manages logic for each “application profile” (transcription, etc.).  
   - **`ApplicationController`** orchestrates them, deciding *when* to start/stop, how to handle events, and how to route them.  

Thus, `ApplicationController` is the glue that ensures that everything runs smoothly and in the correct order, while also reacting to user input and system events in real time.