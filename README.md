# LayerLearn

LayerLearn is a real-time voice assistant for desktop (macOS + Windows) that can:

- Listen with push-to-talk (`SPACE`)
- Understand your request with local LLM reasoning (Ollama)
- See your active screen and analyze code/UI issues
- Execute safe desktop tools (open apps, search web, read files, etc.)
- Reply using text-to-speech

It is designed as a practical desktop copilot for coding and everyday workflows.

## Features

- Real-time voice loop:
  - Hold `SPACE` to record
  - Release to transcribe + process
  - Get spoken response
- Screen understanding:
  - Captures the monitor containing the active/frontmost window
  - Vision analysis for UI, code, and errors
- Smart intent + tool routing:
  - Fast regex-based intent detection for common requests
  - LLM fallback for general conversations
- Desktop automation:
  - Open apps/URLs, search web, type text, key presses, system controls
- Safety layer:
  - Confirmation required for destructive actions (writing files, commands, typing, etc.)
- Persistent preferences + memory:
  - Remembers choices like preferred browser
  - Keeps short conversation context
- Structured logs for debugging

## How It Works

1. Audio input is recorded via `sounddevice` while push-to-talk key is held.
2. Audio is transcribed by `faster-whisper`.
3. `Agent` processes text:
   - Fast intent detection for common commands
   - Smart resolver for ambiguous open/app/web requests
   - LLM reasoning fallback
4. If needed, tools execute (screen capture, system actions, file ops, etc.).
5. For screen tasks:
   - Screenshot is captured via `mss`
   - Vision model analyzes image through Ollama
6. Response is summarized and spoken via `edge-tts` + `sounddevice`.

## Tech Stack

- Python
- Ollama (text + vision models)
- `faster-whisper` (STT)
- `edge-tts` (TTS)
- `mss` + `Pillow` (screen capture + image handling)
- `pynput` (push-to-talk hotkey)
- `loguru` + `rich` (logging + terminal UI)

## Project Structure

```text
LayerLearn-1/
├── main.py
├── config.py
├── requirements.txt
├── core/
│   ├── agent.py
│   ├── brain.py
│   ├── memory.py
│   ├── smart_resolver.py
│   ├── safety.py
│   ├── stt.py
│   ├── tts.py
│   ├── vision.py
│   ├── screen_capture.py
│   ├── voice_controller.py
│   └── tools/
├── tests/
├── assets/            # screenshots
├── logs/              # runtime logs
└── .env.example
```

## Requirements

- macOS or Windows 10/11
- Python 3.9+
- Ollama installed and running
- Microphone + screen recording permissions enabled

Recommended system dependencies:

- `ffmpeg` (needed by `pydub` for MP3 decode in TTS path)
- `portaudio` (if `sounddevice` build/runtime needs it)

## Quick Start

### 1. Clone the repo

```bash
git clone <your-repo-url>
cd LayerLearn-1
```

### 2. Create and activate virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install Python dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Install system dependencies (recommended)

```bash
brew install ffmpeg portaudio ollama
```

Windows (PowerShell, with Chocolatey):

```powershell
choco install ollama ffmpeg -y
```

### 5. Start Ollama and pull models

```bash
ollama serve
```

In another terminal:

```bash
ollama pull llama3.2
ollama pull llama3.2-vision
```

### 6. Configure environment

```bash
cp .env.example .env
```

Windows (PowerShell):

```powershell
Copy-Item .env.example .env
```

Edit `.env` as needed.

### 7. Run LayerLearn

Voice mode:

```bash
python3 main.py
```

Windows:

```powershell
python main.py
```

Text mode:

```bash
python3 main.py --text
```

Windows:

```powershell
python main.py --text
```

Debug logging:

```bash
python3 main.py --debug
```

Windows:

```powershell
python main.py --debug
```

## Permissions (Important)

Grant these to your terminal app and Python runtime:

- Microphone
- Screen Recording
- Accessibility / Input control (for keyboard automation)
- Automation permissions when prompted

macOS path: `System Settings -> Privacy & Security`

Windows path:

- Microphone: `Settings -> Privacy & security -> Microphone`
- Notifications: `Settings -> System -> Notifications`
- Run terminal as needed with sufficient access for automation scenarios

After changing permissions, fully restart terminal/python process.

## Usage Examples

- `"what's on my screen"`
- `"look at this"`
- `"a serious problem on the screen"`
- `"help me debug this code"`
- `"open youtube"`
- `"open whatsapp in chrome"`
- `"what app is active"`
- `"read main.py"`
- `"what time is it"`
- `"reset"`

## Configuration

You can set these in `.env`:

- `OLLAMA_HOST`
- `OLLAMA_TEXT_MODEL`
- `OLLAMA_VISION_MODEL`
- `OLLAMA_TEMPERATURE`
- `OLLAMA_MAX_TOKENS`
- `STT_MODEL_SIZE`
- `STT_LANGUAGE`
- `TTS_VOICE`
- `TTS_RATE`
- `PTT_KEY`
- `MAX_MEMORY_TURNS`
- `DEBUG`

If not set, defaults are loaded from `config.py`.

## Safety Model

The assistant asks for confirmation before potentially destructive actions, including:

- Writing files
- Running shell commands
- Typing text / keyboard shortcuts
- Drafting emails
- Quitting apps / lock/sleep/trash actions

## Logs and Debugging

- Main logs: `logs/layerlearn_YYYY-MM-DD.log`
- Safety audit log: `logs/safety_audit.jsonl` (if safety actions are used)
- Screenshots for vision tasks: `assets/screenshot_*.png`

## Run Tests

```bash
pytest -q
```

## Troubleshooting

### 1) `Failed to connect to Ollama` / model errors

- Ensure Ollama is running: `ollama serve`
- Ensure models are pulled:
  - `ollama pull llama3.2`
  - `ollama pull llama3.2-vision`
- Verify `OLLAMA_HOST` in `.env`

### 2) Screen capture not working

- Grant Screen Recording permission
- Restart terminal/python process after granting permission

### 3) Voice input not detected

- Grant Microphone permission
- Check input device in macOS Sound settings

### 4) TTS issues / no audio

- Ensure speakers/headphones are active
- Install `ffmpeg` (`brew install ffmpeg`)

### 5) Automation actions fail

- Grant required OS permissions for input/screen access
- Some actions depend on the target app allowing focus and scripted control

## Notes

- macOS and Windows are supported.
- Linux has partial support with best-effort fallbacks.
- For best results on Windows/macOS, run in a normal desktop session (not headless/remote-only).
