import os
from pathlib import Path
from console_manager import console


def build_initial_messages_from_app_name(app_name):
    """
    Get the initial prompt for the given app name.
    
    Args:
        app_name: The name of the app to use.
    Returns:
        The initial prompt as a list of dictionaries.
    """
    if not app_name:
        return []
    else:
        return [{"role": "system", "content": get_system_prompt_message(app_name)}]


def build_initial_messages_from_prompt(prompt):
    """
    Get the initial prompt from a given prompt string.
    
    Args:
        prompt: The prompt string to use.
    Returns:
        The initial prompt as a list of dictionaries.
    """
    if not prompt:
        return []
    else:
        return [{"role": "system", "content": prompt}]


def get_system_prompt_message(app_name):
    """
    Get the system prompt message for the given app name.

    Args:
        app_name: The name of the app to use.
    Returns:
        The system prompt message as a string.
    """
    app_system_path = Path(__file__).parent / 'apps' / app_name / 'SYSTEM.txt'
    default_system_path = Path(__file__).parent / 'apps' / 'SYSTEM.txt'

    try:
        if app_system_path.exists():
            with open(app_system_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        else:
            console.warning(f"Error: System prompt '{app_name}' not found. Using default prompt.")
            with open(default_system_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
    except Exception as e:
        console.warning(f"Error reading system prompt file: {e}")
        return ""


def get_user_prompt_message_from_app_name(app_name):
    """
    Get the user prompt message for the given app name.
    
    Args:
        app_name: The name of the app to use.
    Returns:
        The user prompt message as a string.
    """
    app_user_path = Path(__file__).parent / 'apps' / app_name / 'USER.txt'
    default_user_path = Path(__file__).parent / 'apps' / 'USER.txt'

    try:
        if app_user_path.exists():
            with open(app_user_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            console.warning(f"Error: User prompt '{app_name}' not found. Using default prompt.")
            with open(default_user_path, 'r', encoding='utf-8') as f:
                return f.read()
    except Exception as e:
        console.warning(f"Error reading user prompt file: {e}")
        return ""
