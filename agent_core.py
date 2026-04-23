"""
Mini-Ultra Agent Core
Main agent class - handles LLM communication, tool routing, memory, and self-diagnosis.
Lightweight version of the ULTRON Agent architecture.
"""
import asyncio
import importlib
import inspect
import json
import os
import sys
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from utils.logger import get_logger, log_info, log_error, log_warning
from utils.config_loader import load_config, Config
from utils.error_handlers import ConfigError, ToolError, LLMError, with_retry
from memory.memory_store import MemoryStore
from tools.base import BaseTool

logger = get_logger("agent_core")


class AgentStatus(Enum):
    INITIALIZING = "initializing"
    RUNNING = "running"
    MAINTENANCE = "maintenance"
    ERROR = "error"


class MiniUltraAgent:
    """
    Main Mini-Ultra Agent class.
    Handles command routing, tool loading, LLM communication, and memory.
    """

    def __init__(self, config_path: str = "mini_ultra_config.json"):
        self.status = AgentStatus.INITIALIZING
        self.config: Config = load_config(config_path)
        self.tools: Dict[str, BaseTool] = {}
        self.memory: Optional[MemoryStore] = None
        self.conversation_history: List[Dict[str, str]] = []
        self.start_time = datetime.now()

        log_info("agent_core", f"Initializing Mini-Ultra Agent v{self.config.get('version', '1.0.0')}")

        # Initialize subsystems
        self._init_memory()
        self._load_tools()

        self.status = AgentStatus.RUNNING
        log_info("agent_core", f"Agent initialized. Status: {self.status.value}, Tools: {len(self.tools)}")

    def _init_memory(self):
        """Initialize the memory system."""
        if self.config.get("features.memory_enabled", True):
            try:
                self.memory = MemoryStore(
                    persist_path=self.config.get("memory.persist_path", "data/memory.json"),
                    max_items=self.config.get("memory.max_items", 1000),
                )
                log_info("agent_core", "Memory system initialized")
            except Exception as e:
                log_error("agent_core", f"Memory init failed: {e}")
                self.memory = None

    def _load_tools(self):
        """Dynamically load all tools from the tools/ directory."""
        if not self.config.get("features.tools_enabled", True):
            log_info("agent_core", "Tools disabled by config")
            return

        tools_dir = Path("tools")
        if not tools_dir.exists():
            log_warning("agent_core", "tools/ directory not found")
            return

        for py_file in tools_dir.glob("*.py"):
            if py_file.name.startswith("_") or py_file.name == "base.py":
                continue

            module_name = f"tools.{py_file.stem}"
            try:
                module = importlib.import_module(module_name)
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (inspect.isclass(attr)
                            and issubclass(attr, BaseTool)
                            and attr is not BaseTool):
                        tool_instance = attr()
                        self.tools[tool_instance.name] = tool_instance
                        log_info("agent_core", f"Loaded tool: {tool_instance.name}")
            except Exception as e:
                log_error("agent_core", f"Failed to load tool from {py_file.name}: {e}")

        log_info("agent_core", f"Total tools loaded: {len(self.tools)}")

    def _build_system_prompt(self) -> str:
        """Build the system prompt with context."""
        agent_name = self.config.get("agent_name", "Mini-Ultra")
        tool_list = "\n".join(
            f"  - {t.name}: {t.description}" for t in self.tools.values()
        )
        memory_context = self.memory.get_context(5) if self.memory else ""

        prompt = f"""You are {agent_name}, a capable AI assistant agent.
You have access to the following tools:
{tool_list}

To use a tool, respond with a JSON block:
```tool
{{"tool": "tool_name", "params": {{"key": "value"}}}}
```

{memory_context}

Be helpful, concise, and proactive. If a tool can help answer the user's question, use it.
If no tool is needed, respond directly with your knowledge."""
        return prompt

    def _call_ollama(self, messages: List[Dict]) -> str:
        """Send messages to Ollama API."""
        base_url = self.config.get("llm.ollama_base_url", "http://localhost:11434")
        model = self.config.get("llm.ollama_model", "llama3.2:latest")

        try:
            resp = requests.post(
                f"{base_url}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": self.config.get("llm.temperature", 0.7),
                        "num_predict": self.config.get("llm.max_tokens", 2000),
                    }
                },
                timeout=self.config.get("llm.timeout", 30),
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("message", {}).get("content", "")
        except requests.ConnectionError:
            raise LLMError("Cannot connect to Ollama. Is it running?", {"url": base_url})
        except Exception as e:
            raise LLMError(f"Ollama error: {e}", {"model": model})

    def _call_openai(self, messages: List[Dict]) -> str:
        """Send messages to OpenAI-compatible API."""
        api_key = self.config.get("llm.openai_api_key", "")
        base_url = self.config.get("llm.openai_base_url", "https://api.openai.com/v1")
        model = self.config.get("llm.openai_model", "gpt-4.1-mini")

        if not api_key:
            raise LLMError("OpenAI API key not configured")

        try:
            resp = requests.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": self.config.get("llm.temperature", 0.7),
                    "max_tokens": self.config.get("llm.max_tokens", 2000),
                },
                timeout=self.config.get("llm.timeout", 30),
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            raise LLMError(f"OpenAI error: {e}", {"model": model})

    def _call_llm(self, messages: List[Dict]) -> str:
        """Route to the configured LLM provider."""
        provider = self.config.get("llm.provider", "ollama")
        if provider == "openai":
            return self._call_openai(messages)
        else:
            return self._call_ollama(messages)

    def _extract_tool_call(self, response: str) -> Optional[Dict]:
        """Extract tool call from LLM response if present."""
        import re
        pattern = r'```tool\s*\n?(.*?)\n?```'
        match = re.search(pattern, response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                return None
        return None

    def _execute_tool(self, tool_name: str, params: dict) -> Dict:
        """Execute a tool by name with given parameters."""
        if tool_name not in self.tools:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}

        tool = self.tools[tool_name]
        try:
            result = tool.execute(**params)
            log_info("agent_core", f"Tool '{tool_name}' executed: success={result.get('success')}")
            return result
        except Exception as e:
            log_error("agent_core", f"Tool '{tool_name}' failed: {e}")
            return {"success": False, "error": str(e)}

    def process_message(self, user_message: str) -> str:
        """Process a user message: route through LLM, handle tool calls, return response."""
        log_info("agent_core", f"Processing message: {user_message[:80]}...")

        # Store in memory
        if self.memory:
            self.memory.add(user_message, category="user_input")

        # Build conversation
        system_prompt = self._build_system_prompt()
        messages = [{"role": "system", "content": system_prompt}]

        # Add recent conversation history
        for msg in self.conversation_history[-10:]:
            messages.append(msg)

        messages.append({"role": "user", "content": user_message})

        try:
            # Get LLM response
            response = self._call_llm(messages)

            # Check for tool calls
            tool_call = self._extract_tool_call(response)
            if tool_call:
                tool_name = tool_call.get("tool", "")
                params = tool_call.get("params", {})
                log_info("agent_core", f"Tool call detected: {tool_name}")

                tool_result = self._execute_tool(tool_name, params)

                # Send tool result back to LLM for final response
                messages.append({"role": "assistant", "content": response})
                messages.append({
                    "role": "user",
                    "content": f"Tool '{tool_name}' returned:\n{json.dumps(tool_result, indent=2, default=str)}\n\nPlease provide a final response based on this result."
                })

                response = self._call_llm(messages)

            # Update conversation history
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": response})

            # Trim history
            if len(self.conversation_history) > 50:
                self.conversation_history = self.conversation_history[-30:]

            # Store response in memory
            if self.memory:
                self.memory.add(response[:200], category="agent_response")

            return response

        except LLMError as e:
            error_msg = f"LLM Error: {e.message}"
            log_error("agent_core", error_msg)
            return f"I'm having trouble connecting to the AI backend. {error_msg}"
        except Exception as e:
            log_error("agent_core", f"Unexpected error: {e}")
            return f"An error occurred while processing your message: {str(e)}"

    def health_check(self) -> Dict[str, Any]:
        """Run a comprehensive health check."""
        health = {
            "status": self.status.value,
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "tools_loaded": len(self.tools),
            "tool_names": list(self.tools.keys()),
            "memory_enabled": self.memory is not None,
            "memory_stats": self.memory.stats() if self.memory else None,
            "conversation_length": len(self.conversation_history),
            "config": {
                "llm_provider": self.config.get("llm.provider"),
                "llm_model": self.config.get(
                    f"llm.{self.config.get('llm.provider', 'ollama')}_model"
                ),
            },
            "timestamp": datetime.now().isoformat(),
        }

        # Test LLM connectivity
        try:
            provider = self.config.get("llm.provider", "ollama")
            if provider == "ollama":
                base_url = self.config.get("llm.ollama_base_url", "http://localhost:11434")
                resp = requests.get(f"{base_url}/api/tags", timeout=5)
                health["llm_connected"] = resp.status_code == 200
            else:
                health["llm_connected"] = bool(self.config.get("llm.openai_api_key"))
        except Exception:
            health["llm_connected"] = False

        return health

    def self_diagnosis(self) -> Dict[str, Any]:
        """Run self-tests on all subsystems."""
        results = {}

        # Memory test
        if self.memory:
            results["memory"] = self.memory.self_test()
        else:
            results["memory"] = {"success": False, "error": "Memory not initialized"}

        # Tool tests
        results["tools"] = {}
        for name, tool in self.tools.items():
            results["tools"][name] = tool.self_test()

        # LLM test
        try:
            test_response = self._call_llm([
                {"role": "user", "content": "Respond with exactly: OK"}
            ])
            results["llm"] = {"success": bool(test_response), "response_length": len(test_response)}
        except Exception as e:
            results["llm"] = {"success": False, "error": str(e)}

        return results

    def get_tool_list(self) -> List[Dict]:
        """Get list of available tools and their schemas."""
        return [tool.get_schema() for tool in self.tools.values()]

    def reset_conversation(self):
        """Clear conversation history."""
        self.conversation_history = []
        log_info("agent_core", "Conversation history cleared")
