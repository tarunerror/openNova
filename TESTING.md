# Testing Guide for AI Agent

## Quick Start

### 1. Prerequisites Check

Before testing, ensure you have:

```powershell
# Check Python version (requires 3.12+)
python --version

# Check if virtual environment is active
echo $env:VIRTUAL_ENV
```

### 2. Install Dependencies

```powershell
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install all dependencies
pip install -r requirements.txt
```

### 3. Configure LLM Provider

**Option A: Local (Ollama) - Recommended for testing**

```powershell
# Install Ollama from https://ollama.ai
# Then pull a model
ollama pull llama3.2-vision
```

**Option B: Cloud Provider**

```powershell
# Copy environment template
cp .env.example .env

# Edit .env and add your API key
notepad .env
```

Configuration is stored in `~/.ai_agent/config.json` (created on first run).

---

## Running the Application

### Method 1: Direct Python Execution

```powershell
# Run with admin privileges (right-click PowerShell -> Run as Administrator)
python main.py
```

**Expected behavior:**
- Application requests admin elevation (if not already admin)
- Floating window appears in top-right corner
- Status shows "Ready" with green indicator
- Console shows "AI Backend started - waiting for commands..."

---

## Testing Features

### Test 1: Backend Connection

**Steps:**
1. Run the application
2. Check if floating window appears
3. Look for "AI Backend is operational!" in console

**Expected:** Green status indicator, no errors in console

---

### Test 2: Voice Recording (Basic)

**Steps:**
1. Click the microphone button OR press `Ctrl+Space`
2. Status should change to "Listening..." (orange indicator)
3. Speak: "Hello, how are you?"
4. Click button again OR press `Ctrl+Space` to stop
5. Status changes to "Thinking..." (blue) then "Ready" (green)

**Expected:**
- Console shows: `Transcribed: hello how are you`
- TTS speaks back the transcription

**Common Issues:**
- No microphone access: Check Windows privacy settings
- No transcription: Ensure faster-whisper models downloaded (automatic on first run)

---

### Test 3: Simple Action Plan

**Steps:**
1. Press `Ctrl+Space` to start recording
2. Say: "Open Notepad"
3. Stop recording

**Expected:**
- Console shows action plan: `[{"action": "open", "application": "notepad"}]`
- Notepad launches
- Agent says "Task completed successfully"

---

### Test 4: Mouse Control

**Steps:**
1. Say: "Move mouse to the center of the screen"

**Expected:**
- Mouse moves smoothly to center (with tween animation)
- Action logged in console

---

### Test 5: Typing Simulation

**Steps:**
1. Open Notepad manually
2. Say: "Type 'Hello from AI Agent'"

**Expected:**
- Text appears in Notepad
- Each character typed with small delay

---

### Test 6: Plugin System

**Steps:**
1. Say: "What's the weather like?"

**Expected:**
- Weather skill activates (mock response)
- Console shows: `Command handled by plugin`
- Agent speaks mock weather info

**To add custom skills:**
```powershell
# Create a new skill in skills/ directory
notepad skills\my_skill.py
```

---

### Test 7: Drag and Drop

**Steps:**
1. Drag a file from Explorer
2. Drop it onto the AI Agent window
3. Window shows "Drop files here..."

**Expected:**
- Console logs: `Files dropped: [file paths]`
- Agent asks: "What would you like me to do with them?"

---

### Test 8: File Monitoring (Advanced)

**Test in Python REPL:**

```python
from src.watcher.file_watcher import file_watcher

# Watch Downloads folder
file_watcher.watch_directory(
    path="C:\\Users\\Error\\Downloads",
    on_created=lambda f: print(f"New file: {f}"),
    patterns=["*.pdf"]
)

# Create a PDF in Downloads to trigger
```

---

### Test 9: Scheduled Tasks (Advanced)

**Test in Python REPL:**

```python
from src.scheduler.task_scheduler import task_scheduler
from datetime import datetime, timedelta

def test_task():
    print("Scheduled task executed!")

# Schedule to run in 10 seconds
run_time = datetime.now() + timedelta(seconds=10)
task_scheduler.schedule_once("test", test_task, run_time)

# Wait 10 seconds...
```

---

## Debugging

### Enable Debug Logging

Edit `src/utils/logging_config.py` and change level to `logging.DEBUG`:

```python
logger.setLevel(logging.DEBUG)
```

Or set environment variable:
```powershell
$env:LOG_LEVEL="DEBUG"
python main.py
```

### Check Logs

```powershell
# View AI backend log
Get-Content logs\ai_backend.log -Tail 50

# Watch logs in real-time
Get-Content logs\ai_backend.log -Wait
```

### Common Issues

**Issue: "Audio recorder not available"**
- Install PyAudio: `pip install pyaudio`
- On error, install via: `pip install pipwin; pipwin install pyaudio`

**Issue: "No module named 'faster_whisper'"**
- `pip install faster-whisper`
- First run downloads ~140MB model files

**Issue: "ChromaDB connection error"**
- Delete `~/.ai_agent/chroma_db/` and restart
- `pip install --upgrade chromadb`

**Issue: "Ollama connection refused"**
- Ensure Ollama is running: `ollama serve`
- Check URL in config: `~/.ai_agent/config.json`

**Issue: "PyQt6 not found"**
- `pip install PyQt6`
- Requires Windows 10+

**Issue: GUI not visible**
- Check multiple monitors
- Reset position in config: delete `~/.ai_agent/config.json`

---

## Performance Testing

### Check Response Time

```powershell
# Time a command
Measure-Command {
    # Say command and wait for completion
}
```

**Expected Times:**
- Voice recognition: 1-3 seconds
- Plan creation: 0.5-2 seconds (local) / 1-3 seconds (cloud)
- Action execution: < 1 second per action

### Memory Usage

```powershell
# Monitor process
Get-Process python | Select-Object CPU, WorkingSet64
```

**Expected:**
- Idle: ~200-400 MB
- Active: ~500-800 MB (with local LLM models loaded)

---

## Integration Testing

### End-to-End Test

```powershell
# Complete workflow test
python main.py

# 1. Voice: "Open Notepad"
# 2. Voice: "Type 'Testing AI Agent'"
# 3. Voice: "Save this file as test.txt"
# 4. Voice: "Close Notepad"
```

**Expected:** All steps execute successfully without errors

---

## Building & Distribution Testing

```powershell
# Build executable
.\build.ps1

# Test the built executable
.\dist\AIAgent.exe
```

**Expected:**
- Single .exe file in dist/
- Runs without Python installation
- All features work identically

---

## Automated Testing (Optional)

Create test scripts:

```python
# tests/test_actions.py
from src.actions.input_simulator import input_simulator

def test_mouse_move():
    start_pos = input_simulator.get_position()
    input_simulator.move_to(500, 500, duration=0.5)
    end_pos = input_simulator.get_position()
    assert end_pos == (500, 500)

# Run with pytest
# pip install pytest
# pytest tests/
```

---

## Next Steps

1. **Basic Test**: Run application, test voice recording
2. **Action Test**: Test simple commands (open app, type text)
3. **Plugin Test**: Create custom skill, test plugin system
4. **Advanced**: Test scheduling, file monitoring
5. **Production**: Build .exe and test on clean Windows machine

For issues, check:
- Console output for error messages
- Log files in `logs/` directory
- Configuration in `~/.ai_agent/config.json`

Happy testing! 🚀
