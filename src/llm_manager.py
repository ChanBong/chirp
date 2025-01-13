from typing import Dict, Any, Optional, List
import threading
import time
import queue

from config_manager import ConfigManager
from event_bus import EventBus
from llm.OpenAIClient import OpenAIClient
from llm.OllamaClient import OllamaClient
from llm.NoAIClient import NoAIClient
from llm.PerplexityClient import PerplexityClient
from llm.GroqClient import GroqClient
import prompt

class LLMManager:
    def __init__(self, app, event_bus: EventBus):
        self.app_name = app.name
        self.event_bus = event_bus
        self.inference_queue = app.inference_queue
        self.backend_type = ConfigManager.get_value('llm_backend_type', self.app_name)
        self.is_streaming = ConfigManager.get_value('output_options.is_streaming', self.app_name)
        print(f"{self.app_name} is streaming: {self.is_streaming}")
        self.backend = self._get_backend_instance()
        self.current_session_id = None
        self.processing_thread = None
        self.stop_event = threading.Event()
        self.llm_event = threading.Event()
        self.verbose = True

    def _get_backend_instance(self):
        model = ConfigManager.get_value('llm_backend.model', self.app_name)
        if self.backend_type == 'none':
            return NoAIClient()
        elif self.backend_type == 'openai':
            return OpenAIClient()
        elif self.backend_type == 'ollama':
            return OllamaClient(model=model, keep_alive=ConfigManager.get_value('llm_backend.keep_alive', self.app_name))
        elif self.backend_type == 'perplexity':
            return PerplexityClient()
        elif self.backend_type == 'groq':
            return GroqClient()
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

    def handle_non_streaming_response(self, messages, model, **kwargs):
        """Get completion from the selected AI client and return the entire response.

        Args:
            messages (list): List of messages.
            model (str): Model for completion.
            **kwargs: Additional keyword arguments.

        Returns:
            str: The complete response from the AI client, or None if an error occurs.
        """
        try:
            # Make sure the token count is within the limit
            #messages = maintain_token_limit(messages, config.MAX_TOKENS)
            
            completion_stream = self.backend.stream_completion(messages, model, **kwargs)
            
            # Accumulate the entire response
            full_response = ""
            for chunk in completion_stream:
                full_response += chunk

            return full_response

        except Exception as e:
            if self.verbose:
                import traceback
                traceback.print_exc()
            else:
                print(f"An error occurred while getting completion: {e}")
            return None


    def handle_streaming_response(self, messages, model, **kwargs):
        try:
            completion_stream = self.backend.stream_completion(messages, model, **kwargs)
            full_response = ""
            
            for chunk in completion_stream:
                if full_response == "":
                    start_response = {
                        "assistant": "<start_of_stream>",
                        "error": None
                    }
                    self._emit_result(start_response)
                full_response += chunk
                response = {
                    "assistant": chunk,
                    "error": None
                }
                self._emit_result(response)

            end_response = {
                "assistant": "<end_of_stream>",
                "error": None
            }
            self._emit_result(end_response)

            return full_response

        except Exception as e:
            if self.verbose:
                import traceback
                traceback.print_exc()
            else:
                print(f"An error occurred while getting completion: {e}")
            return None

    def _process_messages(self) -> Optional[str]:
        """Process a list of messages and return the model's response."""
        if not self.backend:
            ConfigManager.log_print("Backend not initialized. LLM cannot start.")
            return None
        
        try:
            while not self.stop_event.is_set():
                try:
                    user_message = self.inference_queue.get(timeout=0.2)
                    if user_message is None:
                        break

                    start_time = time.time()

                    transcribed_message = user_message.get('transcription', "")
                    clipboard_content = user_message.get('clipboard_content', "")
                    messages = prompt.build_initial_messages_from_app_name(self.app_name)
                    message_content = prompt.get_user_prompt_message_from_app_name(self.app_name)
                    message_content = message_content.replace("{{transcription}}", transcribed_message)
                    message_content = message_content.replace("{{clipboard_content}}", clipboard_content)
                    new_message = {"role": "user", "content": message_content}
                    messages.append(new_message)

                    if self.is_streaming:
                        model_response = self.handle_streaming_response(messages=messages, model=self.backend.model)
                    else:
                        model_response = self.handle_non_streaming_response(messages=messages, model=self.backend.model)

                    response = {
                        "assistant": model_response,
                        "error": None
                    }

                    end_time = time.time()
                    inference_time = end_time - start_time
                    ConfigManager.log_print(
                        f'LLM response generated in {inference_time:.2f} seconds.\n'
                        f'Response: {response}')

                    if not self.is_streaming:
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
