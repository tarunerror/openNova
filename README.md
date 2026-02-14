# openNova Desktop Assistant

openNova is an enterprise-grade desktop assistant with voice control, visual understanding, and autonomous task execution.

## Features

- 🎤 **Voice Control**: Wake word + hotkey activation
- 👁️ **Visual Understanding**: Screenshot analysis and UI automation
- 🧠 **Multi-LLM Support**: OpenAI, Anthropic, Google, or local (Ollama)
- 🔒 **Privacy First**: Optional 100% local processing
- 🛡️ **Triple Confirmation Safety**: Dangerous actions require 3 explicit confirms
- 🎯 **Multi-Process Architecture**: Responsive UI with powerful backend
- 🔧 **Extensible**: Plugin system for custom skills
- 🧪 **Imitation Learning**: Record and replay macro traces for repeated workflows
- 🤖 **Autonomous**: Event-driven and scheduled task execution

## Installation

### Prerequisites

- Python 3.12+
- Windows 10/11 (with Administrator privileges)
- Optional: NVIDIA GPU for local inference

### Setup

1. Clone the repository:
```bash
[<git clone tarunerror/openNova>](https://github.com/tarunerror/openNova)
cd openNova
```

2. Create virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the agent:
```bash
python main.py
```

## Configuration

Configuration is stored in `~/.openNova/config.json`. Key settings:

- **LLM Provider**: Choose between `ollama`, `openai`, `anthropic`, or `google`
- **Wake Word**: Customize activation phrase
- **Vision Method**: `accessibility`, `vision`, or `hybrid`
- **Safety**: Enable/disable dangerous action confirmations

### Environment Variables

Create a `.env` file in the project root:

```env
# LLM API Keys (choose your provider)
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GOOGLE_API_KEY=your_google_key

# Local LLM (Ollama)
OLLAMA_HOST=http://localhost:11434
```

## Architecture

```
/src
  /gui        - PyQt6 Frontend (Process 1)
  /core       - Application Logic & AI Backend (Process 2)
  /audio      - Speech-to-Text & Text-to-Speech
  /vision     - Screen Capture & UI Automation
  /actions    - Input Simulation & Shell Execution
  /llm        - LLM Provider Abstraction
  /memory     - Vector DB & Long-term Memory
  /skills     - Custom Plugin Scripts
```

## Usage

### Voice Commands

1. Say "Hey openNova" or press `Ctrl+Space`
2. Speak your command
3. Agent executes and responds

### Drag and Drop

Simply drag files onto the openNova window to process them. The assistant will ask what you'd like to do with the files.

### Example Commands

- "Open Chrome and search for Python tutorials"
- "Summarize the document on my desktop"
- "Schedule an email to send tomorrow at 9 AM"
- "What's the weather like?" (via weather plugin)
- "Move the mouse to the File menu and click"
- "Start macro recording named invoice_flow"
- "Stop macro recording"
- "Replay macro invoice_flow"

### Dangerous Action Confirmation

For dangerous operations (delete/format/registry/system commands), the agent will block execution and require three separate "confirm" responses before running the plan. Say "cancel" at any time to abort.

## Plugin Development

Create custom skills by extending the `Skill` base class:

```python
# skills/my_skill.py
from src.plugins.skill_base import Skill

class MySkill(Skill):
    @property
    def name(self) -> str:
        return "MySkill"
    
    @property
    def description(self) -> str:
        return "Does something cool"
    
    def can_handle(self, user_input: str) -> bool:
        return "my trigger" in user_input.lower()
    
    def execute(self, user_input: str, context=None):
        # Your logic here
        return {
            "success": True,
            "response": "Task completed!",
            "data": {}
        }
```

Place your skill file in the `skills/` directory and it will be automatically loaded on startup.

## Building

To create a standalone executable:

```powershell
# Install build dependencies
pip install pyinstaller

# Run the build script
.\build.ps1
```

The executable will be created in `dist\openNova.exe` with all dependencies bundled.

## Scheduled Tasks

The agent supports scheduled task execution:

```python
# Schedule a task to run every day at 9 AM
scheduler.schedule_cron(
    task_id="daily_report",
    func=generate_report,
    hour="9",
    minute="0"
)
```

## File Monitoring

Watch directories for changes:

```python
# Watch a folder for new files
file_watcher.watch_directory(
    path="C:\\Downloads",
    on_created=lambda file: process_new_file(file),
    patterns=["*.pdf", "*.docx"]
)
```

## Development Status

See `Implementation_Plan.md` for detailed development roadmap.

## License

MIT License
