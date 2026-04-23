"""
Mini-Ultra Tool Base Class
All tools must inherit from BaseTool.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseTool(ABC):
    """Base class for all Mini-Ultra tools."""

    name: str = "base_tool"
    description: str = "Base tool - override this"
    version: str = "1.0.0"

    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool with given parameters.

        Returns:
            Dict with at least 'success' (bool) and 'result' or 'error' keys.
        """
        pass

    def get_schema(self) -> Dict[str, Any]:
        """Return tool schema for LLM function calling."""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
        }

    def self_test(self) -> Dict[str, Any]:
        """Run a self-test. Override for custom tests."""
        try:
            return {"success": True, "tool": self.name}
        except Exception as e:
            return {"success": False, "tool": self.name, "error": str(e)}

    def __repr__(self):
        return f"<Tool: {self.name} v{self.version}>"
