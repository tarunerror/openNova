# Enterprise Desktop AI Agent

An enterprise-grade desktop AI agent with voice control, visual understanding, and autonomous task execution.

## Features

- 🎤 **Voice Control**: Wake word + hotkey activation
- 👁️ **Visual Understanding**: Screenshot analysis and UI automation
- 🧠 **Multi-LLM Support**: OpenAI, Anthropic, Google, or local (Ollama)
- 🔒 **Privacy First**: Optional 100% local processing
- 🎯 **Multi-Process Architecture**: Responsive UI with powerful backend
- 🔧 **Extensible**: Plugin system for custom skills
- 🤖 **Autonomous**: Event-driven and scheduled task execution

## Installation

### Prerequisites

- Python 3.12+
- Windows 10/11 (with Administrator privileges)
- Optional: NVIDIA GPU for local inference

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd something
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

Configuration is stored in `~/.ai_agent/config.json`. Key settings:

- **LLM Provider**: Choose between `ollama`, `openai`, `anthropic`, or `google`
- **Wake Word**: Customize activation phrase
- **Vision Method**: `accessibility`, `vision`, or `hybrid`
- **Safety**: Enable/disable dangerous action confirmations

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

1. Say "Hey Agent" or press `Ctrl+Space`
2. Speak your command
3. Agent executes and responds

### Example Commands

- "Open Chrome and search for Python tutorials"
- "Summarize the document on my desktop"
- "Schedule an email to send tomorrow at 9 AM"

## Development Status

See `Implementation_Plan.md` for detailed development roadmap.

## License

MIT License
