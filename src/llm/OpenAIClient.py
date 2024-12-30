from typing import Dict, Optional
import json
import os
from datetime import datetime
import openai
import tiktoken
from dotenv import load_dotenv
from tenacity import retry, wait_random_exponential, stop_after_attempt
from termcolor import colored

class OpenAIClient:
    """Class to handle OpenAI API calls."""
    def __init__(self, model: str = "gpt-4o", api_key: Optional[str] = None):
        load_dotenv()
        self.model = model
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("API key must be provided either as an argument or through the environment variable 'OPENAI_API_KEY'.")
        
        openai.api_key = self.api_key
        self.client = openai.Client()

    @retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
    def send_request(self, model, messages, tools=None, tool_choice=None):
        """Send a request to the OpenAI API with retry logic.
        
        Args:
            model (str): The OpenAI model to use (e.g., 'gpt-4')
            messages (list): List of message dictionaries
            tools (list, optional): List of tools/functions available
            tool_choice (str, optional): Specific tool to use
            
        Returns:
            OpenAIResponse: The API response object
        """
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
            )
            return response
        except Exception as e:
            print("Unable to generate ChatCompletion response")
            print(f"Exception: {e}")
            return e

    def send_request_with_response_format(self, model, messages, response_format):
        try:
            response = self.client.beta.chat.completions.parse(
                model=model,
                messages=messages,
                response_format=response_format
            )
            return response
        except Exception as e:
            print(f"Error sending request with response format: {e}")
            return e
        
    def get_model_response(self, messages, model="gpt-4o", response_format=None):
        """Get a simple text response from the model.
        
        Args:
            messages (list): List of message dictionaries
            model (str, optional): The model to use. Defaults to 'gpt-4o'
            
        Returns:
            str: The model's response text
        """
        try:
            if response_format:
                response = self.send_request_with_response_format(model, messages, response_format)
                return response.choices[0].message.parsed
            else:
                response = self.send_request(model, messages)
                return response.choices[0].message.content
        except Exception as e:
            print(f"Error getting model response: {e}")
            return None


    def get_message(self, role, content):
        """Create a formatted message dictionary.
        
        Args:
            role (str): The role ('system', 'user', 'assistant', etc.)
            content (str): The message content
            
        Returns:
            dict: Formatted message dictionary
        """
        return {"role": role, "content": content}

    def get_text_message_content(self, text):
        """Format text content for API message.
        
        Args:
            text (str): The text content
            
        Returns:
            dict: Formatted text content dictionary
        """
        return {'type': 'text', 'text': text}

    def save_conversation(self, messages, filename):
        if not filename:
            filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + "conversation.json"
        with open(filename, 'w') as f:
            json.dump(messages, f, indent=4)    

    def pretty_print_conversation(self, messages):
        role_to_color = {
            "system": "red",
            "user": "green",
            "assistant": "blue",
            "function": "magenta",
        }
        
        for message in messages:
            if message["role"] == "system":
                print(colored(f"system: {message['content']}\n", role_to_color[message["role"]]))
            elif message["role"] == "user":
                print(colored(f"user: {message['content']}\n", role_to_color[message["role"]]))
            elif message["role"] == "assistant" and message.get("function_call"):
                print(colored(f"assistant: {message['function_call']}\n", role_to_color[message["role"]]))
            elif message["role"] == "assistant" and not message.get("function_call"):
                print(colored(f"assistant: {message['content']}\n", role_to_color[message["role"]]))
            elif message["role"] == "function":
                print(colored(f"function ({message['name']}): {message['content']}\n", role_to_color[message["role"]]))


    def num_tokens_from_string(string, encoding_name: str) -> int:
        """Calculate the number of tokens in a string based on the encoding.

        :param string: Input string to encode.
        :param encoding_name: Name of the encoding model.
        :return: Number of tokens.
        """
        message_dict = string[0]
        content = message_dict['content']
        encoding = tiktoken.encoding_for_model(encoding_name)
        num_tokens = len(encoding.encode(str(content)))
        return num_tokens

