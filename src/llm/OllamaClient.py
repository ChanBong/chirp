from typing import Dict, Optional, List, Any
import json
import os
from datetime import datetime
import requests
from termcolor import colored


class OllamaClient:
    """Class to handle Ollama API calls."""
    def __init__(self, model: str = "llama3.2:latest", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url.rstrip('/')
        self._initialized = False

    def is_initialized(self) -> bool:
        return self._initialized
    
    def initialize(self, options: Dict[str, Any]):
        self._initialized = True

    def send_request(self, model: str, messages: str):
        """Send a request to the Ollama API.
        
        Args:
            model (str): The Ollama model to use (e.g., 'llama2')
            messages (list): List of message dictionaries
        Returns:
            dict: The API response object
        """
        try:
            # Convert messages to Ollama format
            prompt = self._convert_messages_to_prompt(messages)
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print("Unable to generate response")
            print(f"Exception: {e}")
            return e

    def _convert_messages_to_prompt(self, messages: str) -> str:
        """Convert OpenAI-style messages to Ollama prompt format.
        
        Args:
            messages (list): List of message dictionaries
            
        Returns:
            str: Formatted prompt string
        """
        return messages

    def get_model_response(self, messages: str, model: Optional[str] = None, response_format=None):
        """Get a simple text response from the model.
        
        Args:
            messages (list): List of message dictionaries
            model (str, optional): The model to use. Defaults to initialized model
            response_format (dict, optional): Not supported in Ollama
            
        Returns:
            str: The model's response text
        """
        try:
            if response_format:
                print("Warning: response_format is not supported in Ollama")
                
            model = model or self.model
            response = self.send_request(model, messages)
            return response.get('response', '')
        except Exception as e:
            print(f"Error getting model response: {e}")
            return None

    def save_conversation(self, messages: List[Dict], filename: Optional[str] = None):
        """Save the conversation to a JSON file.
        
        Args:
            messages (list): List of message dictionaries
            filename (str, optional): The filename to save to
        """
        if not filename:
            filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + "_conversation.json"
        with open(filename, 'w') as f:
            json.dump(messages, f, indent=4)


    def num_tokens_from_string(self, messages: List[Dict]) -> int:
        """Estimate the number of tokens in a message.
        Note: This is a rough estimation as Ollama doesn't provide direct token counting.
        
        Args:
            messages (list): List of message dictionaries
            
        Returns:
            int: Estimated number of tokens
        """
        # Rough estimation: assume 4 characters per token on average
        message_dict = messages[0]
        content = message_dict['content']
        return len(str(content)) // 4


    def inference(self, messages: List[Dict]):
        response = {
            "processed": None,
            "error": None
        }
        print("Messages received: ", messages)
        try:
            response['processed'] = self.get_model_response(messages['raw_text'].strip())
        except Exception as e:
            response['error'] = str(e)
        
        return response


    def cleanup(self):
        self.model = None
        self._initialized = False
