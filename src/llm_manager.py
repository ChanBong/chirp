from typing import Dict, Any, Optional, List
import threading
import time
import queue

from config_manager import ConfigManager
from event_bus import EventBus
from llm.OpenAIClient import OpenAIClient
from llm.OllamaClient import OllamaClient


class LLMManager:
    def __init__(self, app, event_bus: EventBus):
        self.app_name = app.name
        self.event_bus = event_bus
        self.inference_queue = app.inference_queue
        self.backend_type = ConfigManager.get_value('llm_backend_type', self.app_name)
        self.backend = self._get_backend_instance()
        self.current_session_id = None
        self.processing_thread = None
        self.stop_event = threading.Event()
        self.llm_event = threading.Event()

    def _get_backend_instance(self):
        if self.backend_type == 'openai':
            return OpenAIClient()
        elif self.backend_type == 'ollama':
            return OllamaClient()
        else:
            raise ValueError(f"Unsupported LLM backend type: {self.backend_type}")

    def start(self):
        """Initialize the LLM backend with configuration."""
        if not self.backend.is_initialized():
            backend_options = ConfigManager.get_section('backend', self.app_name)
            try:
                self.backend.initialize(backend_options)
            except Exception as e:
                raise RuntimeError(f"Failed to initialize LLM backend for app "
                                 f"{self.app_name}.\n{e}")
            
        if not self.processing_thread:
            self.processing_thread = threading.Thread(target=self._llm_thread)
            self.processing_thread.start()
    
    def stop(self):
        self.stop_event.set()
        self.llm_event.set()
        if self.processing_thread:
            self.processing_thread.join()
            self.processing_thread = None

    def start_inference(self, session_id: str):
        self.current_session_id = session_id
        self.stop_event.clear()
        self.llm_event.set()

    def _llm_thread(self):
        while not self.stop_event.is_set():
            self.llm_event.wait()
            self.llm_event.clear()

            if self.stop_event.is_set():
                break

            self._process_messages()

    def _process_messages(self) -> Optional[str]:
        """Process a list of messages and return the model's response."""
        if not self.backend:
            ConfigManager.log_print("Backend not initialized. LLM cannot start.")
            return None
        
        try:
            while not self.stop_event.is_set():
                try:
                    print(f"Inference queue contents: {list(self.inference_queue.queue)}")
                    message = self.inference_queue.get(timeout=0.2)
                    if message is None:
                        break
                    start_time = time.time()
                    print("Messages from the queue: ", message)
                    response = self.backend.inference(messages=message)
                    end_time = time.time()
                    inference_time = end_time - start_time
                    ConfigManager.log_print(
                        f'LLM response generated in {inference_time:.2f} seconds.\n'
                        f'Response: {response}')
                    self._emit_result(response)
                except queue.Empty:
                    continue
        finally:
            self.current_session_id = None
            self.event_bus.emit("inferencing_finished", self.app_name)

    def _emit_result(self, result: Dict[str, Any]):
        """Emit the result through the event bus."""
        if result['error']:
            self.event_bus.emit("inferencing_error", result['error'])
        self.event_bus.emit("inferencing_result", result, self.current_session_id)

    def cleanup(self):
        """Cleanup any resources used by the LLM backend."""
        self.stop()
        if self.backend:
            self.backend.cleanup()
            self.backend = None
