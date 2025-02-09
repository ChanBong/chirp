from typing import Set, Dict, Type, Optional, Union, Tuple
import time
from pynput import keyboard, mouse
import platform
import ctypes
from rich import print as rprint

from event_bus import EventBus
from enums import InputEvent, KeyCode
from config_manager import ConfigManager
from console_manager import console

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

    def __init__(self, 
                 keys: Union[Set[Union[KeyCode, frozenset]], Tuple[KeyCode, KeyCode]], 
                 is_tap_sequence: bool = False):
        """
        Initialize the KeyChord.

        For tap sequences, supply keys as an ordered tuple: (primary, secondary).
        For normal chords, keys can be a set.
        """
        self.is_tap_sequence = is_tap_sequence

        if self.is_tap_sequence:
            if not isinstance(keys, (tuple, list)) or len(keys) != 2:
                raise ValueError("For tap sequences, keys must be an ordered pair (primary, secondary)")
            self.primary_key, self.secondary_key = keys
        else:
            self.keys = keys
            self.pressed_keys: Set[KeyCode] = set()

        # For tap sequence mode
        self.sequence_start_time: Optional[float] = None
        self.TAP_SEQUENCE_TIMEOUT = 0.5
        self.tap_state = 0  # 0 = waiting for primary, 1 = primary pressed waiting for secondary


    def update(self, key: KeyCode, event_type: InputEvent) -> bool:
        """
        Update the state of pressed keys and check if the chord is active.

        For normal chords (is_tap_sequence == False), we require all keys pressed simultaneously.
        For tap sequences (e.g., 'TAP:CAPS_LOCK>S'), we require the primary key first, then the secondary
        within TAP_SEQUENCE_TIMEOUT.
        """
        if not self.is_tap_sequence:
            # ----- Normal chord behavior -----
            if event_type == InputEvent.KEY_PRESS:
                self.pressed_keys.add(key)
            elif event_type == InputEvent.KEY_RELEASE:
                self.pressed_keys.discard(key)
            return self.is_valid_chord()

        # ----- Tap sequence behavior -----
        # We'll use an explicit state machine:
        # State 0: Waiting for primary key press.
        # State 1: Primary key was pressed; waiting for secondary key within timeout.
        if event_type == InputEvent.KEY_PRESS:
            if self.tap_state == 0:
                if key == self.primary_key:
                    # Primary key pressed: start waiting for secondary key.
                    self.sequence_start_time = time.time()
                    self.tap_state = 1
                # If secondary is pressed in idle state, ignore it.
            elif self.tap_state == 1:
                if key == self.secondary_key:
                    # Secondary key pressed while waiting.
                    if (time.time() - self.sequence_start_time) <= self.TAP_SEQUENCE_TIMEOUT:
                        self.reset_sequence()
                        return True  # Successful tap sequence.
                    else:
                        # Timeout exceeded.
                        self.reset_sequence()
                elif key == self.primary_key:
                    # If the primary is pressed again, restart the timer.
                    self.sequence_start_time = time.time()
                # You might also decide to ignore any other keys.
        elif event_type == InputEvent.KEY_RELEASE:
            # Optionally: If you want to cancel the sequence on primary key release,
            # you could reset the state here. For this example, we'll leave it as is.
            pass

        # Check for timeout: if we're waiting for the secondary key too long, reset.
        if self.tap_state == 1 and (time.time() - self.sequence_start_time) > self.TAP_SEQUENCE_TIMEOUT:
            self.reset_sequence()

        return False

    def reset_sequence(self):
        """Reset the tap sequence state."""
        self.sequence_start_time = None
        self.tap_state = 0

    def is_valid_chord(self) -> bool:
        """
        Check if all keys in the chord are currently pressed (for normal chords).

        For tap sequences, activation is detected in update() so this always returns False.
        """
        if self.is_tap_sequence:
            return False

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
        active_apps = ConfigManager.get_apps(active_only=True)
        for app in active_apps:
            app_name = app['name']
            activation_backend_type = ConfigManager.get_value('activation_backend_type', app_name)
            activation_backend = ConfigManager.get_value('activation_backend', app_name)
            if activation_backend_type == 'press_together':
                shortcut = activation_backend['hotkey']
            elif activation_backend_type == 'rapid_tap':
                shortcut = f"TAP:{activation_backend['trigger_key']}>{activation_backend['secondary_key']}"
            else:
                raise ValueError(f"Unsupported activation backend type: {activation_backend_type}")
            keys = self.parse_key_combination(shortcut)
            is_tap_sequence = isinstance(shortcut, str) and shortcut.upper().startswith('TAP:')
            self.shortcuts[app_name] = KeyChord(keys, is_tap_sequence=is_tap_sequence)
            if is_tap_sequence:
                rprint(f"[dim]Loaded tap sequence:[/dim] {shortcut.split(':')[1]} for [green]{app_name}[/green]")
            else:
                rprint(f"[dim]Loaded hotkey:[/dim] {shortcut} for [green]{app_name}[/green]")
        
        # Leave a line for better readability
        print("")
    
    def start(self):
        try:
            self.backend.start()
            console.success("Started input manager\n")
        except Exception as e:
            console.error(f"Failed to start input manager: {e}")

    def stop(self):
        self.backend.stop()


    def parse_key_combination(
        self, combination_string: str
    ) -> Union[Set[Union[KeyCode, frozenset[KeyCode]]], Tuple[KeyCode, KeyCode]]:
        """
        Parse a string representation of a key combination.
        
        For tap sequences (e.g., "TAP:CAPS_LOCK>S"), return an ordered tuple:
        (primary_key, secondary_key)
        
        For normal chords (e.g., "CTRL+SHIFT+S"), return a set of KeyCodes or key groups.
        """
        key_map = {
            'CTRL': frozenset({KeyCode.CTRL_LEFT, KeyCode.CTRL_RIGHT}),
            'SHIFT': frozenset({KeyCode.SHIFT_LEFT, KeyCode.SHIFT_RIGHT}),
            'ALT': frozenset({KeyCode.ALT_LEFT, KeyCode.ALT_RIGHT}),
            'META': frozenset({KeyCode.META_LEFT, KeyCode.META_RIGHT}),
        }
        
        # ----- TAP SEQUENCE PARSING -----
        # Check if this is a tap sequence in the format "TAP:PRIMARY>SECONDARY"
        if combination_string.upper().startswith('TAP:'):
            sequence_str = combination_string[4:].strip()  # remove "TAP:" prefix
            sequence_keys = [k.strip() for k in sequence_str.split('>')]
            if len(sequence_keys) != 2:
                rprint("[red]Invalid tap sequence format. Expected TAP:KEY1>KEY2[/red]")
                return tuple()  # or raise an exception if that fits your error handling
            
            try:
                primary = KeyCode[sequence_keys[0].upper()]
            except KeyError:
                rprint(f"[red]Unknown primary key in tap sequence:[/red] {sequence_keys[0]}")
                return tuple()
            try:
                secondary = KeyCode[sequence_keys[1].upper()]
            except KeyError:
                rprint(f"[red]Unknown secondary key in tap sequence:[/red] {sequence_keys[1]}")
                return tuple()
            
            # Return an ordered tuple so the state machine knows which is primary vs secondary.
            return (primary, secondary)
        
        # ----- NORMAL CHORD PARSING -----
        keys: Set[Union[KeyCode, frozenset[KeyCode]]] = set()
        for key_str in combination_string.upper().split('+'):
            key_str = key_str.strip()
            if key_str in key_map:
                keys.add(key_map[key_str])
            else:
                try:
                    keycode = KeyCode[key_str]
                    keys.add(keycode)
                except KeyError:
                    rprint(f"[red]Unknown key:[/red] {key_str}")
        return keys


    def on_input_event(self, event):
        """Handle input events and trigger callbacks if the key chord becomes active."""
        key, event_type = event

        for app_name, key_chord in self.shortcuts.items():
            was_active = key_chord.is_valid_chord()   # only relevant for normal chords
            is_valid_chord = key_chord.update(key, event_type)

            if is_valid_chord:
                self.event_bus.emit("shortcut_triggered", app_name, "press")

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
