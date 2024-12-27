import subprocess
import os
import signal
import time
# import fcntl
import struct
from pynput.keyboard import Key, Controller as PynputController

from config_manager import ConfigManager
from event_bus import EventBus


class OutputManager:
    """A class to simulate keyboard output using various methods."""
    def __init__(self, profile_name: str, event_bus: EventBus):
        """Initialize the OutputManager with the specified configuration."""
        self.interval = ConfigManager.get_section('writing_key_press_delay', profile_name)
        self.keyboard = PynputController()

    def typewrite(self, text):
        """Simulate typing using pynput."""
        for char in text:
            self.keyboard.press(char)
            self.keyboard.release(char)
            time.sleep(self.interval)

    def backspace(self, count):
        """Simulate backspace using pynput."""
        for _ in range(count):
            self.keyboard.press(Key.backspace)
            self.keyboard.release(Key.backspace)
            time.sleep(0.05)

    def cleanup(self):
        pass
