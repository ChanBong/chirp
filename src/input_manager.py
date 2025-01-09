from typing import Set, Dict, Type, Optional
import time
from pynput import keyboard, mouse
import platform
import ctypes

from event_bus import EventBus
from enums import InputEvent, KeyCode
from config_manager import ConfigManager


class PynputBackend():
    """
    Pynput backend implementation using the pynput library.
    """
    def __init__(self):
        """Initialize PynputBackend."""
        self.keyboard_listener = None
        self.mouse_listener = None
        self.keyboard = None
        self.mouse = None
        self.key_map = None

    def start(self):
        """Start listening for keyboard and mouse events."""
        if self.keyboard is None or self.mouse is None:
            self.keyboard = keyboard
            self.keyboard_controller = keyboard.Controller() # for simulating key presses
            self.mouse = mouse
            self.key_map = self._create_key_map()

        self.keyboard_listener = self.keyboard.Listener(
            on_press=self._on_keyboard_press,
            on_release=self._on_keyboard_release
        )
        self.mouse_listener = self.mouse.Listener(
            on_click=self._on_mouse_click
        )
        self.keyboard_listener.start()
        self.mouse_listener.start()

    def stop(self):
        """Stop listening for keyboard and mouse events."""
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None
        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None

    def _translate_key_event(self, native_event) -> tuple[KeyCode, InputEvent]:
        """Translate a pynput event to our internal event representation."""
        pynput_key, is_press = native_event
        key_code = self.key_map.get(pynput_key, KeyCode.SPACE)
        event_type = InputEvent.KEY_PRESS if is_press else InputEvent.KEY_RELEASE
        return key_code, event_type

    def _on_keyboard_press(self, key):
        """Handle keyboard press events."""
        translated_event = self._translate_key_event((key, True))
        self.on_input_event(translated_event)

    def _on_keyboard_release(self, key):
        """Handle keyboard release events."""
        translated_event = self._translate_key_event((key, False))
        self.on_input_event(translated_event)

    def _on_mouse_click(self, x, y, button, pressed):
        """Handle mouse click events."""
        translated_event = self._translate_key_event((button, pressed))
        self.on_input_event(translated_event)

    def _create_key_map(self):
        """Create a mapping from pynput keys to our internal KeyCode enum."""
        return {
            # Modifier keys
            self.keyboard.Key.ctrl_l: KeyCode.CTRL_LEFT,
            self.keyboard.Key.ctrl_r: KeyCode.CTRL_RIGHT,
            self.keyboard.Key.shift_l: KeyCode.SHIFT_LEFT,
            self.keyboard.Key.shift_r: KeyCode.SHIFT_RIGHT,
            self.keyboard.Key.alt_l: KeyCode.ALT_LEFT,
            self.keyboard.Key.alt_r: KeyCode.ALT_RIGHT,
            self.keyboard.Key.cmd_l: KeyCode.META_LEFT,
            self.keyboard.Key.cmd_r: KeyCode.META_RIGHT,

            # Function keys
            self.keyboard.Key.f1: KeyCode.F1,
            self.keyboard.Key.f2: KeyCode.F2,
            self.keyboard.Key.f3: KeyCode.F3,
            self.keyboard.Key.f4: KeyCode.F4,
            self.keyboard.Key.f5: KeyCode.F5,
            self.keyboard.Key.f6: KeyCode.F6,
            self.keyboard.Key.f7: KeyCode.F7,
            self.keyboard.Key.f8: KeyCode.F8,
            self.keyboard.Key.f9: KeyCode.F9,
            self.keyboard.Key.f10: KeyCode.F10,
            self.keyboard.Key.f11: KeyCode.F11,
            self.keyboard.Key.f12: KeyCode.F12,
            self.keyboard.Key.f13: KeyCode.F13,
            self.keyboard.Key.f14: KeyCode.F14,
            self.keyboard.Key.f15: KeyCode.F15,
            self.keyboard.Key.f16: KeyCode.F16,
            self.keyboard.Key.f17: KeyCode.F17,
            self.keyboard.Key.f18: KeyCode.F18,
            self.keyboard.Key.f19: KeyCode.F19,
            self.keyboard.Key.f20: KeyCode.F20,

            # Number keys
            self.keyboard.KeyCode.from_char('1'): KeyCode.ONE,
            self.keyboard.KeyCode.from_char('2'): KeyCode.TWO,
            self.keyboard.KeyCode.from_char('3'): KeyCode.THREE,
            self.keyboard.KeyCode.from_char('4'): KeyCode.FOUR,
            self.keyboard.KeyCode.from_char('5'): KeyCode.FIVE,
            self.keyboard.KeyCode.from_char('6'): KeyCode.SIX,
            self.keyboard.KeyCode.from_char('7'): KeyCode.SEVEN,
            self.keyboard.KeyCode.from_char('8'): KeyCode.EIGHT,
            self.keyboard.KeyCode.from_char('9'): KeyCode.NINE,
            self.keyboard.KeyCode.from_char('0'): KeyCode.ZERO,

            # Letter keys
            self.keyboard.KeyCode.from_char('a'): KeyCode.A,
            self.keyboard.KeyCode.from_char('b'): KeyCode.B,
            self.keyboard.KeyCode.from_char('c'): KeyCode.C,
            self.keyboard.KeyCode.from_char('d'): KeyCode.D,
            self.keyboard.KeyCode.from_char('e'): KeyCode.E,
            self.keyboard.KeyCode.from_char('f'): KeyCode.F,
            self.keyboard.KeyCode.from_char('g'): KeyCode.G,
            self.keyboard.KeyCode.from_char('h'): KeyCode.H,
            self.keyboard.KeyCode.from_char('i'): KeyCode.I,
            self.keyboard.KeyCode.from_char('j'): KeyCode.J,
            self.keyboard.KeyCode.from_char('k'): KeyCode.K,
            self.keyboard.KeyCode.from_char('l'): KeyCode.L,
            self.keyboard.KeyCode.from_char('m'): KeyCode.M,
            self.keyboard.KeyCode.from_char('n'): KeyCode.N,
            self.keyboard.KeyCode.from_char('o'): KeyCode.O,
            self.keyboard.KeyCode.from_char('p'): KeyCode.P,
            self.keyboard.KeyCode.from_char('q'): KeyCode.Q,
            self.keyboard.KeyCode.from_char('r'): KeyCode.R,
            self.keyboard.KeyCode.from_char('s'): KeyCode.S,
            self.keyboard.KeyCode.from_char('t'): KeyCode.T,
            self.keyboard.KeyCode.from_char('u'): KeyCode.U,
            self.keyboard.KeyCode.from_char('v'): KeyCode.V,
            self.keyboard.KeyCode.from_char('w'): KeyCode.W,
            self.keyboard.KeyCode.from_char('x'): KeyCode.X,
            self.keyboard.KeyCode.from_char('y'): KeyCode.Y,
            self.keyboard.KeyCode.from_char('z'): KeyCode.Z,

            # Special keys
            self.keyboard.Key.space: KeyCode.SPACE,
            self.keyboard.Key.enter: KeyCode.ENTER,
            self.keyboard.Key.tab: KeyCode.TAB,
            self.keyboard.Key.backspace: KeyCode.BACKSPACE,
            self.keyboard.Key.esc: KeyCode.ESC,
            self.keyboard.Key.insert: KeyCode.INSERT,
            self.keyboard.Key.delete: KeyCode.DELETE,
            self.keyboard.Key.home: KeyCode.HOME,
            self.keyboard.Key.end: KeyCode.END,
            self.keyboard.Key.page_up: KeyCode.PAGE_UP,
            self.keyboard.Key.page_down: KeyCode.PAGE_DOWN,
            self.keyboard.Key.caps_lock: KeyCode.CAPS_LOCK,
            self.keyboard.Key.num_lock: KeyCode.NUM_LOCK,
            self.keyboard.Key.scroll_lock: KeyCode.SCROLL_LOCK,
            self.keyboard.Key.pause: KeyCode.PAUSE,
            self.keyboard.Key.print_screen: KeyCode.PRINT_SCREEN,

            # Arrow keys
            self.keyboard.Key.up: KeyCode.UP,
            self.keyboard.Key.down: KeyCode.DOWN,
            self.keyboard.Key.left: KeyCode.LEFT,
            self.keyboard.Key.right: KeyCode.RIGHT,

            # Numpad keys
            self.keyboard.Key.num_lock: KeyCode.NUM_LOCK,
            self.keyboard.KeyCode.from_vk(96): KeyCode.NUMPAD_0,
            self.keyboard.KeyCode.from_vk(97): KeyCode.NUMPAD_1,
            self.keyboard.KeyCode.from_vk(98): KeyCode.NUMPAD_2,
            self.keyboard.KeyCode.from_vk(99): KeyCode.NUMPAD_3,
            self.keyboard.KeyCode.from_vk(100): KeyCode.NUMPAD_4,
            self.keyboard.KeyCode.from_vk(101): KeyCode.NUMPAD_5,
            self.keyboard.KeyCode.from_vk(102): KeyCode.NUMPAD_6,
            self.keyboard.KeyCode.from_vk(103): KeyCode.NUMPAD_7,
            self.keyboard.KeyCode.from_vk(104): KeyCode.NUMPAD_8,
            self.keyboard.KeyCode.from_vk(105): KeyCode.NUMPAD_9,
            self.keyboard.KeyCode.from_vk(107): KeyCode.NUMPAD_ADD,
            self.keyboard.KeyCode.from_vk(109): KeyCode.NUMPAD_SUBTRACT,
            self.keyboard.KeyCode.from_vk(106): KeyCode.NUMPAD_MULTIPLY,
            self.keyboard.KeyCode.from_vk(111): KeyCode.NUMPAD_DIVIDE,
            self.keyboard.KeyCode.from_vk(110): KeyCode.NUMPAD_DECIMAL,

            # Additional special characters
            self.keyboard.KeyCode.from_char('-'): KeyCode.MINUS,
            self.keyboard.KeyCode.from_char('='): KeyCode.EQUALS,
            self.keyboard.KeyCode.from_char('['): KeyCode.LEFT_BRACKET,
            self.keyboard.KeyCode.from_char(']'): KeyCode.RIGHT_BRACKET,
            self.keyboard.KeyCode.from_char(';'): KeyCode.SEMICOLON,
            self.keyboard.KeyCode.from_char("'"): KeyCode.QUOTE,
            self.keyboard.KeyCode.from_char('`'): KeyCode.BACKQUOTE,
            self.keyboard.KeyCode.from_char('\\'): KeyCode.BACKSLASH,
            self.keyboard.KeyCode.from_char(','): KeyCode.COMMA,
            self.keyboard.KeyCode.from_char('.'): KeyCode.PERIOD,
            self.keyboard.KeyCode.from_char('/'): KeyCode.SLASH,

            # Media keys
            self.keyboard.Key.media_volume_mute: KeyCode.AUDIO_MUTE,
            self.keyboard.Key.media_volume_down: KeyCode.AUDIO_VOLUME_DOWN,
            self.keyboard.Key.media_volume_up: KeyCode.AUDIO_VOLUME_UP,
            self.keyboard.Key.media_play_pause: KeyCode.MEDIA_PLAY_PAUSE,
            self.keyboard.Key.media_next: KeyCode.MEDIA_NEXT,
            self.keyboard.Key.media_previous: KeyCode.MEDIA_PREVIOUS,

            # Mouse buttons
            self.mouse.Button.left: KeyCode.MOUSE_LEFT,
            self.mouse.Button.right: KeyCode.MOUSE_RIGHT,
            self.mouse.Button.middle: KeyCode.MOUSE_MIDDLE,
        }

    def on_input_event(self, event):
        """
        Callback method to be set by the InputManager.
        This method is called for each processed input event.
        """
        pass


    def simulate_key_event(self, key: str, event_type: InputEvent):
        """Simulate a key event."""
        if event_type == InputEvent.KEY_PRESS:
            if key == "CAPS_LOCK":
                self.keyboard_controller.press(self.keyboard.Key.caps_lock)
            elif key == "BACKSPACE":
                self.keyboard_controller.press(self.keyboard.Key.backspace)
            else:
                self.keyboard_controller.press(self.keyboard.KeyCode.from_char(key))
        else:
            if key == "CAPS_LOCK":
                self.keyboard_controller.release(self.keyboard.Key.caps_lock)
            elif key == "BACKSPACE":
                self.keyboard_controller.release(self.keyboard.Key.backspace)
            else:
                self.keyboard_controller.release(self.keyboard.KeyCode.from_char(key))

    def is_caps_lock_on(self) -> bool:
        """Check if Caps Lock is on."""
        if platform.system() == "Windows":
            return ctypes.WinDLL("User32.dll").GetKeyState(0x14) & 1
        elif platform.system() == "Linux":
            import subprocess
            xset_output = subprocess.run(["xset", "q"], capture_output=True, text=True)
            return "Caps Lock:   on" in xset_output.stdout
        else:
            raise NotImplementedError("Caps Lock detection is not implemented for this OS.")



class KeyChord:
    """Represents either a combination of keys or a tap sequence."""

    def __init__(self, keys: Set[KeyCode | frozenset[KeyCode]], is_tap_sequence: bool = False):
        """Initialize the KeyChord."""
        self.keys = keys
        self.pressed_keys: Set[KeyCode] = set()
        self.is_tap_sequence = is_tap_sequence

        # For tap sequence
        self.sequence_start_time: Optional[float] = None
        self.TAP_SEQUENCE_TIMEOUT = 0.5  # 500ms window

    def update(self, key: KeyCode, event_type: InputEvent) -> bool:
        """
        Update the state of pressed keys and check if the chord is active.

        For normal chords (is_tap_sequence == False), we want all keys pressed simultaneously.
        For tap sequences (e.g., 'TAP:CAPS_LOCK>S'), we want them pressed in order, within TAP_SEQUENCE_TIMEOUT.
        """
        # ----- Normal chord behavior -----
        if not self.is_tap_sequence:
            if event_type == InputEvent.KEY_PRESS:
                self.pressed_keys.add(key)
            elif event_type == InputEvent.KEY_RELEASE:
                self.pressed_keys.discard(key)
            return self.is_valid_chord()

        # ----- Tap sequence behavior -----
        # Expect exactly 2 keys, e.g. {KeyCode.CAPS_LOCK, KeyCode.S}
        if len(self.keys) != 2:
            return False

        # Unpack our two keys
        first_key, second_key = list(self.keys)  # ordering them
        # If you'd like to ensure 'first_key' is always Caps Lock, you could do a check here

        if event_type == InputEvent.KEY_PRESS:
            if key == first_key:
                # Start or restart the timer whenever first key is pressed
                self.sequence_start_time = time.time()

            elif key == second_key:
                # If user presses the second key within the time limit, we have a match
                if (self.sequence_start_time is not None and
                    (time.time() - self.sequence_start_time) <= self.TAP_SEQUENCE_TIMEOUT):
                    # Successful chord
                    self.reset_sequence()
                    return True
                else:
                    # Too late or no valid start time, reset
                    self.reset_sequence()

        elif event_type == InputEvent.KEY_RELEASE:
            # If you want to invalidate the chord on first-key release (depending on your use case),
            # you could do so here. For now, let's keep it simple and just rely on the timer.
            #
            # Also, if time is up by the time we release anything, reset.
            if (self.sequence_start_time is not None and
               (time.time() - self.sequence_start_time) > self.TAP_SEQUENCE_TIMEOUT):
                self.reset_sequence()

        return False

    def reset_sequence(self):
        """Reset the tap sequence state."""
        self.sequence_start_time = None

    def is_valid_chord(self) -> bool:
        """Check if all keys in the chord are currently pressed."""
        if self.is_tap_sequence:
            # Tap sequences use update() to detect activation, not simultaneous press
            return False

        # For normal chord usage (e.g. SHIFT+S, etc.)
        for key in self.keys:
            if isinstance(key, frozenset):
                if not any(k in self.pressed_keys for k in key):
                    return False
            elif key not in self.pressed_keys:
                return False
        return True


class InputManager:
    """Manages input backends and listens for specific key combinations."""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.backend = PynputBackend()
        self.backend.on_input_event = self.on_input_event
        self.shortcuts: Dict[str, KeyChord] = {}
        self.load_shortcuts()

    def load_shortcuts(self):
        """Load shortcuts from config, supporting both traditional shortcuts and tap sequences."""
        active_profiles = ConfigManager.get_apps(active_only=True)
        for profile in active_profiles:
            profile_name = profile['name']
            activation_backend_type = ConfigManager.get_value('activation_backend_type', profile_name)
            activation_backend = ConfigManager.get_value('activation_backend', profile_name)
            if activation_backend_type == 'press_together':
                shortcut = activation_backend['hotkey']
            elif activation_backend_type == 'rapid_tap':
                shortcut = f"TAP:{activation_backend['trigger_key']}>{activation_backend['secondary_key']}"
            else:
                raise ValueError(f"Unsupported activation backend type: {activation_backend_type}")
            keys = self.parse_key_combination(shortcut)
            is_tap_sequence = isinstance(shortcut, str) and shortcut.upper().startswith('TAP:')
            self.shortcuts[profile_name] = KeyChord(keys, is_tap_sequence=is_tap_sequence)

    def start(self):
        self.backend.start()

    def stop(self):
        self.backend.stop()

    def parse_key_combination(self, combination_string: str) -> Set[KeyCode | frozenset[KeyCode]]:
        """Parse a string representation of key combination into a set of KeyCodes."""
        keys = set()
        key_map = {
            'CTRL': frozenset({KeyCode.CTRL_LEFT, KeyCode.CTRL_RIGHT}),
            'SHIFT': frozenset({KeyCode.SHIFT_LEFT, KeyCode.SHIFT_RIGHT}),
            'ALT': frozenset({KeyCode.ALT_LEFT, KeyCode.ALT_RIGHT}),
            'META': frozenset({KeyCode.META_LEFT, KeyCode.META_RIGHT}),
        }
        print(combination_string)
        # Check if this is a tap sequence (format: "TAP:CAPS_LOCK>S")
        if combination_string.upper().startswith('TAP:'):
            sequence = combination_string[4:].upper().split('>')
            if len(sequence) == 2:
                for key in sequence:
                    key = key.strip()
                    try:
                        keycode = KeyCode[key]
                        keys.add(keycode)
                    except KeyError:
                        print(f"Unknown key in tap sequence: {key}")
                print(keys)
                return keys

        # Original chord parsing (e.g. "CTRL+SHIFT+S")
        for key in combination_string.upper().split('+'):
            key = key.strip()
            if key in key_map:
                keys.add(key_map[key])
            else:
                try:
                    keycode = KeyCode[key]
                    keys.add(keycode)
                except KeyError:
                    print(f"Unknown key: {key}")
        return keys

    def on_input_event(self, event):
        """Handle input events and trigger callbacks if the key chord becomes active."""
        key, event_type = event

        for app_name, key_chord in self.shortcuts.items():
            was_active = key_chord.is_valid_chord()   # only relevant for normal chords
            is_valid_chord = key_chord.update(key, event_type)

            if is_valid_chord:
                self.event_bus.emit("shortcut_triggered", app_name, "press")
                print(f"Shortcut triggered: {app_name}")

                if self.backend.is_caps_lock_on() and key_chord.is_tap_sequence:
                    # Toggle the primary key if it's Caps Lock and remove the secondary key that was typed
                    self.backend.simulate_key_event("CAPS_LOCK", InputEvent.KEY_PRESS)
                    self.backend.simulate_key_event("CAPS_LOCK", InputEvent.KEY_RELEASE)
                    self.backend.simulate_key_event("BACKSPACE", InputEvent.KEY_PRESS)
                    self.backend.simulate_key_event("BACKSPACE", InputEvent.KEY_RELEASE)
                    #

            # For normal chord combos, we check if we just lost activation:
            elif was_active and not key_chord.is_valid_chord():
                self.event_bus.emit("shortcut_triggered", app_name, "release")

    def update_shortcuts(self):
        self.load_shortcuts()

    def cleanup(self):
        self.stop()
        self.backend = None
        self.shortcuts = None
