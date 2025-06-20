# <img src="./assets/chirp_logo.png" alt="Chirp icon" width="25" height="25"> Chirp
![version](https://img.shields.io/badge/version-1.0-blue)

<p align="center">
    <img src="./assets/chirp-demo-01.gif" alt="Chirp demo 01" width="340" height="136">
</p>

Transform your computer interaction with smart, voice-activated hotkeys. Chirp lets you control any application through natural speech, powered by AI.

## Sections

- [Key Features](#key-features)
- [Philosophy](#philosophy)
- [Getting Started](#getting-started)
- [Customization](#customization)
- [Troubleshooting](#troubleshooting)
- [Future](#future)

## Key Features

### 🎯 Smart Hotkeys
- Use traditional or "rapid" hotkey combinations
- Voice-activate any computer function
- Works across all applications
- Replace typing with natural speech

### 🔧 Fully Customizable Stack

<p align="center">
    <img src="./assets/chirp_options.png" alt="Chirp philosophy" width="880" height="540">
</p>

- Choose between cloud or local processing
- Supported backends:
  - Transcription: OpenAI Whisper, Faster-Whisper, VOSK
  - LLM: OpenAI GPT, Ollama, and more
  - Text-to-Speech: Various cloud and local options
- Easy to add new backends

### 🎨 Flexible Output Modes
- Direct text insertion at cursor
- Pop-up windows for detailed responses
- Voice responses through your speakers
- System notifications
- Customizable for each command

### 🔌 Plugin Architecture
- Create new commands without coding
- Simple YAML-based configuration
- Rich marketplace for community plugins
- Full control over data and context

### ⚡ Performance Focused
- Multi-threaded architecture
- Minimal UI with maximum customization
- Lightweight and responsive
- GPU acceleration support

## Philosophy

- Speech is the best way to talk to LLMs
- file over app
- plugins are king
- potential with output modality is unlimited (think home assistants, browser control)

## Getting Started  

### Prerequisites

Before you can run this app, you'll need to have the following software installed:
- Git: [https://git-scm.com/downloads](https://git-scm.com/downloads)
- Python `3.12`: [https://www.python.org/downloads/](https://www.python.org/downloads/)

If you want to run `faster-whisper` on your GPU, you'll also need to install the following NVIDIA libraries:
- [cuBLAS for CUDA 12](https://developer.nvidia.com/cublas)
- [cuDNN 8 for CUDA 12](https://developer.nvidia.com/cudnn)

For local LLM inference, we use [Ollama](https://github.com/ollama/ollama). Download the Ollama client and run it

<details>

<summary>More information on GPU execution</summary>
The below was taken directly from the [`faster-whisper` README](https://github.com/SYSTRAN/faster-whisper?tab=readme-ov-file#gpu):

**Note:** The latest versions of `ctranslate2` support CUDA 12 only. For CUDA 11, the current workaround is downgrading to the `3.24.0` version of `ctranslate2` (This can be done with `pip install --force-reinsall ctranslate2==3.24.0`).

There are multiple ways to install the NVIDIA libraries mentioned above. The recommended way is described in the official NVIDIA documentation, but we also suggest other installation methods below.

#### Use Docker

The libraries (cuBLAS, cuDNN) are installed in these official NVIDIA CUDA Docker images: `nvidia/cuda:12.0.0-runtime-ubuntu20.04` or `nvidia/cuda:12.0.0-runtime-ubuntu22.04`.

#### Install with `pip` (Linux only)  

On Linux these libraries can be installed with `pip`. Note that `LD_LIBRARY_PATH` must be set before launching Python.

```bash
pip install nvidia-cublas-cu12 nvidia-cudnn-cu12
export LD_LIBRARY_PATH=`python3 -c 'import os; import nvidia.cublas.lib; import nvidia.cudnn.lib; print(os.path.dirname(nvidia.cublas.lib.__file__) + ":" + os.path.dirname(nvidia.cudnn.lib.__file__))'`
```

**Note**: Version 9+ of `nvidia-cudnn-cu12` appears to cause issues due its reliance on cuDNN 9 (Faster-Whisper does not currently support cuDNN 9). Ensure your version of the Python package is for cuDNN 8.

#### Download the libraries from Purfview's repository (Windows & Linux)

Purfview's [whisper-standalone-win](https://github.com/Purfview/whisper-standalone-win) provides the required NVIDIA libraries for Windows & Linux in a [single archive](https://github.com/Purfview/whisper-standalone-win/releases/tag/libs). Decompress the archive and place the libraries in a directory included in the `PATH`.

</details>

### Installation

#### 1. Clone the repository:

```bash
git clone https://github.com/ChanBong/chirp
cd chirp
```

#### 2. Create a virtual environment and activate it:

```bash
python -m venv venv

# For Linux and macOS:
source venv/bin/activate

# For Windows:
venv\Scripts\activate
```

#### 3. Install the required packages:

Base packages:

```bash
pip install -r requirements.txt
```
The following packages are optional.
Transcription backends (you need at least one):

```
# For local Whisper models
pip install faster-whisper==1.0.3

# For cloud Whisper models, using OpenAI API
pip install openai==1.44.1

# For local VOSK models
pip install vosk==0.3.45
```

#### 4. Run:

```
python run.py
```

## Customization 

- This [file]() goes through all the customization options, I've also tried to make the UI super intuitive so you can click on any specific option that you don't know in this channel and read the helpful message.

<p align="center">
    <img src="./assets/customization-options.png" alt="Customization options" width="880" height="540">
</p>

## Troubleshooting

-  This should redirect to troubleshooting.md and I have included what to do in case of frequently Ask questions.
-  So, if the check if Ollama is running, check your config.yaml
-  You can also check for any GPU related issues. So if your model is not being loaded in the GPU or fast service for is not using GPU, there is troubleshooting code that you can use. Also, you can set verbose equals to true in the settings to get verbose output to your terminal. And you can hit debug audio saving checkbox to save the audio for later debugging.

## Future

### Are you a Whisper ninja ?
Help me add various enhancements like add words to dictionary, better proper noun detection and other stuff

### Are you a UI guy ?
Help me design a better UI 

### Do you have a cracked local-first perplexity like implementation ?
Please drop a message. I'll be happy to integrate it.

### Can you write hardware plugins ?
I am planning to use this as a backed for a wearable (could be anything), will be fun to build together
