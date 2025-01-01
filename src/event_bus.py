from PyQt6.QtCore import QObject, pyqtSignal
from collections import defaultdict
from typing import Callable

class EventEmitter(QObject):
    signal = pyqtSignal(str, tuple, dict)


class EventBus(QObject):
    def __init__(self):
        super().__init__()
        self._subscribers = defaultdict(list)
        self._emitter = EventEmitter()
        self._emitter.signal.connect(self._process_event)
        self.debug = False # Get debug setting from config

    def subscribe(self, event_type: str, callback: Callable):
        if self.debug:
            # Log the subscription
            print(f"EVENT SUBSCRIBE: {event_type} -> {callback.__qualname__}")
        self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable):
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                cb for cb in self._subscribers[event_type] if cb != callback
            ]

    def emit(self, event_type: str, *args, **kwargs):
        if self.debug:
            # Log the emission of the event
            arg_str = ', '.join([str(arg) for arg in args])
            kwarg_str = ', '.join([f"{k}={v}" for k, v in kwargs.items()])
            params = f"{arg_str}{', ' if arg_str and kwarg_str else ''}{kwarg_str}"
            print(f"EVENT EMIT: {event_type} ({params})")
        
        # Emit the signal, which will be processed on the main thread
        self._emitter.signal.emit(event_type, args, kwargs)

    def _process_event(self, event_type: str, args: tuple, kwargs: dict):
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                if self.debug:
                    # Log when the callback is actually called
                    arg_str = ', '.join([str(arg) for arg in args])
                    kwarg_str = ', '.join([f"{k}={v}" for k, v in kwargs.items()])
                    params = f"{arg_str}{', ' if arg_str and kwarg_str else ''}{kwarg_str}"
                    print(f"EVENT PROCESS: {event_type} -> {callback.__qualname__} ({params})")
                callback(*args, **kwargs)
