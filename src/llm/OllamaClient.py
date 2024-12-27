from typing import Dict, Optional, List
import json
import os
from datetime import datetime
import requests
from termcolor import colored

class OllamaClient:
    """Class to handle Ollama API calls."""
    def __init__(self, model: str = "llama2", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url.rstrip('/')

    def send_request(self, model: str, messages: List[Dict], tools=None, tool_choice=None):
        """Send a request to the Ollama API.
        
        Args:
            model (str): The Ollama model to use (e.g., 'llama2')
            messages (list): List of message dictionaries
            tools (list, optional): List of tools/functions available (not supported in Ollama)
            tool_choice (str, optional): Specific tool to use (not supported in Ollama)
            
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

    def _convert_messages_to_prompt(self, messages: List[Dict]) -> str:
        """Convert OpenAI-style messages to Ollama prompt format.
        
        Args:
            messages (list): List of message dictionaries
            
        Returns:
            str: Formatted prompt string
        """
        prompt = ""
        for message in messages:
            role = message["role"]
            content = message["content"]
            
            if role == "user":
                prompt = content
        
        return prompt.strip()

    def get_model_response(self, messages: List[Dict], model: Optional[str] = None, response_format=None):
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

    def get_message(self, role: str, content: str) -> Dict:
        """Create a formatted message dictionary.
        
        Args:
            role (str): The role ('system', 'user', 'assistant', etc.)
            content (str): The message content
            
        Returns:
            dict: Formatted message dictionary
        """
        return {"role": role, "content": content}

    def get_text_message_content(self, text: str) -> Dict:
        """Format text content for API message.
        
        Args:
            text (str): The text content
            
        Returns:
            dict: Formatted text content dictionary
        """
        return {'type': 'text', 'text': text}

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

    def pretty_print_conversation(self, messages: List[Dict]):
        """Print the conversation with colored output for different roles.
        
        Args:
            messages (list): List of message dictionaries
        """
        role_to_color = {
            "system": "red",
            "user": "green",
            "assistant": "blue",
            "function": "magenta",
        }
        
        for message in messages:
            role = message["role"]
            content = message["content"]
            color = role_to_color.get(role, "white")
            
            print(colored(f"{role}: {content}\n", color))

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
