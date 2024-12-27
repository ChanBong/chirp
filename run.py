import os
import sys
import subprocess
from dotenv import load_dotenv

load_dotenv()
print('Starting Chirp...')

subprocess.run([sys.executable, os.path.join('src', 'main.py')])
