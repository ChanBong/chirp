from typing import Dict, Any, List

class NoAIClient:
    def __init__(self):
        self._initialized = True
        self.model = None

    def is_initialized(self):
        return self._initialized
    
    def initialize(self, options: Dict[str, Any]):
        self._initialized = True

    def stream_completion(self, messages, model, **kwargs):
        user_message = messages[-1]['content']
        yield user_message

    def cleanup(self):
        self._initialized = False


