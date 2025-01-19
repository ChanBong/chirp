import os
import sys
import subprocess
from dotenv import load_dotenv
from src.console_manager import console

load_dotenv()

def main():
    try:
        console.highlight("Starting Chirp...")
        subprocess.run([sys.executable, os.path.join('src', 'main.py')])
        
    except Exception as e:
        console.error(f"Application error: {str(e)}")
        return 1
        
    console.success("Application completed successfully")
    return 0

if __name__ == "__main__":
    exit(main())
