# Configuration Reference

This document provides a reference for the application’s configuration structure. The configuration file (`config.yaml`) should follow the schema described here. You can modify the default values according to your needs.

Below is an overview of all configurable sections and their options. Each section has a table describing the available keys, their types, default values, and descriptions. Some entries also provide a list of valid options.

---

## Table of Contents
1. [Global Options](#global-options)
2. [Apps](#apps)
   1. [App Structure](#app-structure)
   2. [Recording Options](#recording-options)
   3. [Output Options](#output-options)
3. [Transcription Backends](#transcription-backends)
   1. [Faster Whisper](#faster_whisper)
   2. [OpenAI](#openai-transcription)
   3. [Vosk](#vosk)
4. [LLM Backends](#llm-backends)
   1. [OpenAI](#openai-llm)
   2. [Ollama](#ollama)
   3. [Perplexity](#perplexity)
   4. [None](#none)
5. [Activation Backends](#activation-backends)
   1. [Press Together](#press_together)
   2. [Rapid Tap](#rapid_tap)

---

## Global Options

These options apply globally to the entire application.

| Key                 | Default    | Type  | Description                                                       |
|---------------------|------------|-------|-------------------------------------------------------------------|
| **active_apps**     | `[Default]`| list  | The apps that are currently active.                               |
| **start_on_startup**| `false`    | bool  | Whether to automatically start the application when the system boots. |
| **start_minimized** | `false`    | bool  | Whether to start the application minimized.                       |
| **print_to_terminal** | `true`   | bool  | Whether to print debug information to the terminal.               |
| **save_debug_audio**| `false`    | bool  | Whether to save audio files for debugging purposes.               |

### Example Usage

```yaml
global_options:
  active_apps: [Default]
  start_on_startup: false
  start_minimized: false
  print_to_terminal: true
  save_debug_audio: false
```

---

## Apps

The `apps` section is a list of app configurations. Each entry describes how a particular app behaves—its name, activation method, recording/transcription/LLM settings, and how outputs are handled.

### App Structure

Below is an example structure of a single app in the list:

```yaml
apps:
  - name:
      value: Default
      type: str
      description: The name of the app.
    activation_backend_type:
      value: press_together
      type: str
      description: "The activation method to use. Options: press_together, rapid_tap"
      options:
        - press_together
        - rapid_tap
    activation_backend:
      type: dict
      description: "The setup for the activation method."
    recording_options:
      ...
    transcription_backend_type:
      ...
    transcription_backend:
      ...
    llm_backend_type:
      ...
    llm_backend:
      ...
    output_options:
      ...
```

#### Common App Fields

| Key                          | Default           | Type | Description                                                                                          | Options                                      |
|------------------------------|-------------------|------|------------------------------------------------------------------------------------------------------|----------------------------------------------|
| **name**.value              | `Default`         | str  | The name of the app.                                                                                 | N/A                                          |
| **activation_backend_type**.value | `press_together` | str  | The activation method to use.                                                                        | `press_together`, `rapid_tap`                |
| **activation_backend**       | *dict*            | dict | The setup details for the activation backend (see [Activation Backends](#activation-backends)).      | N/A                                          |
| **transcription_backend_type**.value | `faster_whisper` | str  | Which transcription backend to use.                                                                  | `faster_whisper`, `openai`, `vosk`           |
| **transcription_backend**    | *dict*            | dict | The setup details for the transcription backend (see [Transcription Backends](#transcription-backends)). | N/A                                          |
| **llm_backend_type**.value   | `ollama`          | str  | The LLM backend to use.                                                                              | `openai`, `ollama`, `perplexity`, `none`     |
| **llm_backend**              | *dict*            | dict | The setup details for the LLM backend (see [LLM Backends](#llm-backends)).                           | N/A                                          |

### Recording Options

Under each app, you can configure `recording_options`:

| Key                             | Default   | Type            | Description                                                                                                                    | Options                    |
|---------------------------------|-----------|-----------------|--------------------------------------------------------------------------------------------------------------------------------|----------------------------|
| **sound_device**.value          | `null`    | int or null     | The numeric index of the sound device to use for recording. Use `python list_audio_devices.py` to find device numbers.         | N/A                        |
| **read_from_clipboard**.value   | `false`   | bool            | Whether to read the clipboard content for the user prompt.                                                                    | N/A                        |
| **language**.value              | `auto`    | str             | The language to use for transcription. Examples: `auto`, `en`, `es`, `fr`, `de`, `it`, `pt`, `zh`, etc.                        | N/A (any valid language)   |
| **gain**.value                  | `1.0`     | float           | Amplification factor for the recorded audio. >1.0 increases volume; <1.0 decreases volume.                                     | N/A                        |

### Output Options

Under each app, you can configure `output_options`:

| Key                                    | Default  | Type  | Description                                                                                                     | Options                              |
|----------------------------------------|----------|-------|-----------------------------------------------------------------------------------------------------------------|--------------------------------------|
| **output_mode**.value                  | `text`   | str   | The mode to use for output.                                                                                     | `text`, `voice`, `clipboard`, `notification`, `pop-up` |
| **is_streaming**.value                 | `false`  | bool  | Whether to stream the output.                                                                                   | N/A                                  |
| **save_output_to_clipboard**.value     | `true`   | bool  | Whether to save the final output to the clipboard.                                                              | N/A                                  |
| **writing_key_press_delay**.value      | `0.005`  | float | The delay in seconds between each key press when writing text. Too short a delay can affect typing special chars. | N/A                                  |

---

## Transcription Backends

Depending on which transcription backend you choose in `transcription_backend_type`, you’ll configure its parameters under `transcription_backend`.

### <a name="faster_whisper"></a>Faster Whisper

```yaml
transcription_backends:
  faster_whisper:
    model:
      value: base
      ...
    compute_type:
      ...
    device:
      ...
    condition_on_previous_text:
      ...
    temperature:
      ...
    initial_prompt:
      ...
```

| Key                                | Default   | Type  | Description                                                                                                                             | Options                                                     |
|------------------------------------|-----------|-------|-----------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------|
| **model**.value                    | `base`    | str   | The Whisper model to use. Larger models provide better accuracy but are slower.                                                         | `tiny`, `tiny.en`, `base`, `base.en`, `small`, `small.en`, `medium`, `medium.en`, `large`, `large-v1`, `large-v2`, `large-v3` |
| **compute_type**.value             | `float16` | str   | The precision to use for the local Whisper model.                                                                                       | `float32`, `float16`, `int8`                                |
| **device**.value                   | `cuda`    | str   | The device to run the local Whisper model on.                                                                                           | `cuda`, `cpu`                                               |
| **condition_on_previous_text**.value | `true`   | bool  | If true, uses previously transcribed text as part of the next prompt.                                                                   | N/A                                                         |
| **temperature**.value              | `0.0`     | float | Controls randomness of the transcription output. Lower values = more deterministic.                                                     | N/A                                                         |
| **initial_prompt**.value           | `null`    | str   | An initial prompt to condition the transcription.                                                                                       | N/A                                                         |

### <a name="openai-transcription"></a>OpenAI

```yaml
transcription_backends:
  openai:
    model:
      value: whisper-1
      ...
    base_url:
      ...
    api_key:
      ...
    temperature:
      ...
    initial_prompt:
      ...
```

| Key                     | Default            | Type  | Description                                                                                                                             | Options     |
|-------------------------|--------------------|-------|-----------------------------------------------------------------------------------------------------------------------------------------|-------------|
| **model**.value        | `whisper-1`        | str   | The model to use for transcription. Currently only `whisper-1` is supported.                                                            | `whisper-1` |
| **base_url**.value     | `https://api.openai.com/v1` | str   | Base URL for the API. Can be changed to use a local endpoint.                                                                           | N/A         |
| **api_key**.value      | `null`             | str   | Your API key for the OpenAI API. Required for any API usage.                                                                            | N/A         |
| **temperature**.value  | `0.0`              | float | Controls randomness of the transcription output.                                                                                       | N/A         |
| **initial_prompt**.value | `null`           | str   | An initial prompt to condition the transcription.                                                                                       | N/A         |

### <a name="vosk"></a>Vosk

```yaml
transcription_backends:
  vosk:
    model_path:
      value: "./model"
      ...
    sample_rate:
      ...
    use_streaming:
      ...
```

| Key                         | Default      | Type   | Description                                                                                                                 | Options                |
|-----------------------------|--------------|--------|-----------------------------------------------------------------------------------------------------------------------------|------------------------|
| **model_path**.value       | `./model`    | dir_path | Path to the folder containing Vosk model files.                                                                             | N/A                    |
| **sample_rate**.value      | `16000`      | int    | The audio sample rate Vosk will use. Typically 16kHz.                                                                       | `8000`, `16000`, `22050`, `44100`, `48000` |
| **use_streaming**.value    | `false`      | bool   | If true, uses streaming mode with partial results; if false, processes only once the entire audio is ready.                 | N/A                    |

---

## LLM Backends

Depending on which LLM backend you choose in `llm_backend_type`, you’ll configure its parameters under `llm_backend`.

### <a name="openai-llm"></a>OpenAI

```yaml
llm_backends:
  openai:
    api_key:
      value: null
      ...
    model:
      ...
    temperature:
      ...
```

| Key                      | Default   | Type  | Description                                                                                | Options                          |
|--------------------------|-----------|-------|--------------------------------------------------------------------------------------------|----------------------------------|
| **api_key**.value        | `null`    | str   | Your API key for the OpenAI API. Required for usage.                                       | N/A                              |
| **model**.value          | `gpt-4o`  | str   | The model to use for LLM processing.                                                       | `gpt-4o`, `gpt-4o-mini`, `o1-mini` |
| **temperature**.value    | `0.0`     | float | Controls randomness of the LLM output. Lower values = more deterministic responses.        | N/A                              |

### <a name="ollama"></a>Ollama

```yaml
llm_backends:
  ollama:
    model:
      value: llama3.2:latest
      ...
    temperature:
      ...
    keep_alive:
      ...
```

| Key                      | Default            | Type  | Description                                                                                             | Options                                              |
|--------------------------|--------------------|-------|---------------------------------------------------------------------------------------------------------|------------------------------------------------------|
| **model**.value          | `llama3.2:latest` | str   | The model to use for LLM processing.                                                                    | `llama3.1`, `llama3.1-uncensored`, `gemma2`, ...     |
| **temperature**.value    | `0.0`             | float | Controls randomness of the LLM output. Lower values = more deterministic.                                | N/A                                                  |
| **keep_alive**.value     | `5m`              | str   | How long the model stays in memory (e.g. `20m`, `24h`, or `-1` to keep indefinitely).                    | N/A                                                  |

### <a name="perplexity"></a>Perplexity

```yaml
llm_backends:
  perplexity:
    model:
      value: llama-3.1-sonar-small-128k-online
      ...
    temperature:
      ...
```

| Key                      | Default                                   | Type  | Description                                                            | Options                                                             |
|--------------------------|-------------------------------------------|-------|------------------------------------------------------------------------|---------------------------------------------------------------------|
| **model**.value          | `llama-3.1-sonar-small-128k-online`       | str   | The model used for the Perplexity backend.                             | `llama-3.1-sonar-small-128k-online`, `llama-3.1-sonar-large-128k-online`, `llama-3.1-sonar-huge-128k-online` |
| **temperature**.value    | `0.0`                                     | float | Controls randomness of the LLM output. Lower values = more deterministic. | N/A                                                                 |

### <a name="none"></a>None

```yaml
llm_backends:
  none:
    value: {}
    ...
```

| Key      | Default | Type | Description                               |
|----------|---------|------|-------------------------------------------|
| **value**| `{}`    | dict | Empty dict. No LLM processing performed. |

---

## Activation Backends

Activation backends dictate how the user activates an app. Possible choices are `press_together` or `rapid_tap`, as set in each app’s `activation_backend_type`.

### <a name="press_together"></a>Press Together

```yaml
activation_backends:
  press_together:
    hotkey:
      value: ctrl+shift+alt+space
      ...
```

| Key                    | Default                      | Type  | Description                                                      |
|------------------------|------------------------------|-------|------------------------------------------------------------------|
| **hotkey**.value       | `ctrl+shift+alt+space`       | str   | The hotkey combination to trigger the app (press simultaneously).|

### <a name="rapid_tap"></a>Rapid Tap

```yaml
activation_backends:
  rapid_tap:
    trigger_key:
      value: CAPS_LOCK
      ...
    secondary_key:
      value: null
      ...
    trigger_delay:
      value: 0.05
      ...
```

| Key                  | Default     | Type  | Description                                                                                                                          |
|----------------------|------------|-------|--------------------------------------------------------------------------------------------------------------------------------------|
| **trigger_key**.value     | `CAPS_LOCK` | str   | The key used to trigger activation by rapidly tapping.                                                                               |
| **secondary_key**.value   | `null`     | str   | A secondary key for activation if desired (optional).                                                                                |
| **trigger_delay**.value   | `0.05`     | float | The delay in seconds between each key press in rapid-tap activation. Too short can affect typing special/shifted characters in uinput mode. |

---

# How to Customize

1. **Locate the `config.yaml` file** in your project.
2. **Edit the desired values** according to the tables above.
3. **Add or remove apps** in the `apps` list if you need multiple configurations.
4. **Verify** that the chosen options are valid (e.g., ensure you only set recognized `activation_backend_type`, `transcription_backend_type`, etc.).
5. **Save the file** and restart the application (if required) to apply changes.

That’s it! With this reference, you can tailor the application to your workflow—everything from how the app is activated to how audio is recorded, transcribed, and processed by language models, and finally how the output is delivered.
```