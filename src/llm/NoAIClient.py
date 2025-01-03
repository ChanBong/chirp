from typing import Dict, Any, List

class NoAIClient:
    def __init__(self):
        self._initialized = True

    def is_initialized(self):
        return self._initialized
    
    def initialize(self, options: Dict[str, Any]):
        self._initialized = True

    def inference(self, messages: List[Dict]):
        response = {
            "processed": messages['raw_text'].strip(),
            "error": None
        }
        return response

    def cleanup(self):
        self._initialized = False


