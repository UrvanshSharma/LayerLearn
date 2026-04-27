# LayerLearn

LayerLearn is a desktop AI copilot with voice + text interaction, screen understanding, and safe tool execution.

It now uses Google Gemma/Gemini API by default, with Ollama fallback support.

## Will It Run On Windows?

Yes. The current codebase includes explicit Windows support for:

- Active window detection and bounds
- Browser/app opening
- Input and automation flows
- Voice, TTS, screen capture, and tool orchestration

Supported platforms:

- Windows 10/11: Fully supported
- macOS: Fully supported
- Linux: Best-effort/partial support

## Key Features

- Push-to-talk voice assistant (default key: Shift)
- Parallel text console mode in the same process
- Screen capture + vision reasoning
- Tool execution with safety confirmations for risky actions
- Smart app/web/file intent resolution
- Session memory + user preference memory

## Updated Project Structure

```text
LayerLearn/
├── main.py
├── gui.py
├── config.py
├── requirements.txt
├── .env.example
├── GEMMA_SETUP.md
├── QUICKSTART_GEMMA.md
├── SETUP_CHECKLIST.md
├── core/
│   ├── agent.py
│   ├── brain.py
│   ├── context_memory.py
│   ├── gemma_client.py
│   ├── memory.py
│   ├── platform_utils.py
│   ├── screen_capture.py
│   ├── smart_resolver.py
│   ├── stt.py
│   ├── tts.py
│   ├── vision.py
│   ├── voice_controller.py
│   ├── window_utils.py
│   └── tools/
│       ├── automation_tools.py
│       ├── communication_tools.py
│       ├── file_tools.py
│       ├── screen_tools.py
│       ├── system_tools.py
│       └── utility_tools.py
├── tests/
├── assets/
└── logs/
```

## Prerequisites

- Python 3.10+
- Microphone enabled
- Screen recording permissions enabled
- ffmpeg installed (required for TTS audio path)

Optional:

- Ollama (only needed when you set LLM_BACKEND=ollama or when using fallback)

## Setup And Run

### 1) Clone

```bash
git clone https://github.com/UrvanshSharma/LayerLearn
cd LayerLearn
```

### 2) Create virtual environment

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Windows CMD:

```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

### 3) Install dependencies

macOS/Linux:

```bash
python3 -m pip install --upgrade pip
pip install -r requirements.txt
```

Windows PowerShell:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4) Install OS packages

macOS (Homebrew):

```bash
brew install ffmpeg portaudio
```

Windows (winget):

```powershell
winget install Gyan.FFmpeg
```

If you use Ollama backend/fallback locally:

```bash
ollama pull llama3.2
ollama pull llama3.2-vision
```

### 5) Configure environment

macOS/Linux:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Edit .env and set at minimum:

```env
LLM_BACKEND=gemma
GOOGLE_API_KEY=your_api_key_here
GEMMA_MODEL=gemini-2.0-flash
```

### 6) Run

All modes are started together by the same command:

```bash
python main.py
```

What you get:

- Voice mode: hold Shift to talk, release to process
- Text mode: type commands at the Text > prompt

Note: current main.py does not use CLI flags like --text or --debug.

## Useful Commands Inside LayerLearn

- what's on my screen
- help me debug this code
- open chrome
- open youtube in edge
- read file main.py
- what app is active
- reset

## Windows Permissions Checklist

- Settings > Privacy & security > Microphone
- Settings > Privacy & security > Screen capture (if required by your environment)
- Run terminal with permissions needed for automation actions

After changing permissions, restart your terminal and rerun python main.py.

## Logs And Diagnostics

- Runtime logs: logs/layerlearn_YYYY-MM-DD.log
- Safety audit: logs/safety_audit.jsonl
- Vision screenshots: assets/screenshot_*.png

Run tests:

```bash
pytest -q
```

## Common Issues

1. Gemma API key errors

- Ensure .env exists
- Ensure GOOGLE_API_KEY is set
- Restart process after editing .env

2. Ollama fallback errors

- Start ollama serve
- Pull required models
- Verify OLLAMA_HOST

3. No audio/TTS

- Check speaker output
- Confirm ffmpeg is installed

4. Screen capture or automation fails

- Grant OS permissions (microphone/screen/accessibility)
- Retry in a normal desktop session (not headless)

## Additional Docs

- GEMMA_SETUP.md
- QUICKSTART_GEMMA.md
- SETUP_CHECKLIST.md
