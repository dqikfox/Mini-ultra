# Mini-Ultra Agent

A lightweight, modular AI agent built as a streamlined version of the [ULTRON Agent](https://github.com/dqikfox/ultron_agent). Mini-Ultra retains the core architecture — LLM integration, dynamic tool loading, persistent memory, REST API, and a web chat interface — in a clean, easy-to-extend codebase.

## Features

- **Multi-LLM Support** — Ollama (local) and OpenAI-compatible APIs
- **Dynamic Tool System** — Drop a Python file in `tools/` and it auto-loads
- **Persistent Memory** — JSON-backed memory store with search and categories
- **REST API** — Full Flask API with chat, tools, memory, and health endpoints
- **Web GUI** — Dark cyberpunk-themed chat interface
- **CLI Mode** — Interactive terminal chat with built-in commands
- **Unified Launcher** — Single entry point for all modes (api/web/cli/full)
- **Self-Diagnosis** — Health checks and self-tests for all subsystems
- **Docker Ready** — Dockerfile and CI/CD workflows included

## Quick Start

### 1. Install

```bash
git clone https://github.com/dqikfox/Mini-ultra.git
cd Mini-ultra
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your API keys (or use Ollama locally)
```

The default config (`mini_ultra_config.json`) uses Ollama. To use OpenAI, set `OPENAI_API_KEY` in your `.env` file and change the provider:

```json
{
  "llm": {
    "provider": "openai",
    "openai_api_key": "sk-..."
  }
}
```

### 3. Launch

```bash
# Interactive CLI (default)
python main.py

# Web GUI + API
python mini_ultra_launch.py --mode web

# API server only
python mini_ultra_launch.py --mode api

# Full stack (API on :5000 + Web on :8080)
python mini_ultra_launch.py --mode full
```

## Architecture

```
Mini-ultra/
├── main.py                    # Main entry point
├── mini_ultra_launch.py       # Unified launcher (api/web/cli/full)
├── agent_core.py              # Core agent: LLM routing, tool loading, memory
├── mini_ultra_config.json     # Configuration file
├── requirements.txt           # Python dependencies
├── web_server.py              # Web GUI server
│
├── api/
│   └── server.py              # Flask REST API
│
├── tools/
│   ├── base.py                # BaseTool abstract class
│   ├── web_search_tool.py     # Web search via DuckDuckGo
│   ├── file_tool.py           # File read/write/list
│   ├── code_executor_tool.py  # Safe Python execution
│   └── system_info_tool.py    # System metrics
│
├── memory/
│   └── memory_store.py        # JSON-backed persistent memory
│
├── utils/
│   ├── logger.py              # Centralized logging
│   ├── error_handlers.py      # Custom exceptions & retry logic
│   └── config_loader.py       # Config loading with env overrides
│
├── web_gui/
│   ├── index.html             # Chat interface (dark theme)
│   └── app.js                 # Frontend JavaScript
│
├── deployment/
│   └── Dockerfile             # Docker container config
│
└── .github/workflows/
    ├── ci.yml                 # CI pipeline
    └── deploy.yml             # Deployment pipeline
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API info and available endpoints |
| GET | `/health` | Health check with LLM status |
| POST | `/chat` | Send a message, get a response |
| GET | `/tools` | List available tools |
| POST | `/tools/<name>/execute` | Execute a tool directly |
| GET | `/memory` | Get recent memories |
| GET | `/memory/search?q=term` | Search memories |
| POST | `/memory` | Add a memory entry |
| DELETE | `/memory` | Clear all memories |
| GET | `/diagnosis` | Run self-diagnosis |
| POST | `/conversation/reset` | Reset conversation history |

## Adding Custom Tools

Create a new file in `tools/` that extends `BaseTool`:

```python
from tools.base import BaseTool

class MyTool(BaseTool):
    name = "my_tool"
    description = "Does something useful"

    def execute(self, param1="", **kwargs):
        return {"success": True, "result": f"Processed: {param1}"}
```

The agent will auto-discover and load it on startup.

## Docker

```bash
# Build
docker build -f deployment/Dockerfile -t mini-ultra .

# Run (full stack)
docker run -p 5000:5000 -p 8080:8080 mini-ultra

# Run (API only)
docker run -p 5000:5000 mini-ultra python mini_ultra_launch.py --mode api
```

## CLI Commands

When running in CLI mode:

| Command | Description |
|---------|-------------|
| `help` | Show available commands |
| `health` | Run health check |
| `tools` | List loaded tools |
| `diagnose` | Run self-diagnosis |
| `memory` | Show memory stats |
| `reset` | Clear conversation history |
| `quit` | Exit |

## Configuration

Configuration is loaded from `mini_ultra_config.json` with environment variable overrides. See `.env.example` for available environment variables.

## Contributing

Pull requests are welcome! If you find issues or have suggestions, feel free to open an issue or submit a PR.

## License

MIT
