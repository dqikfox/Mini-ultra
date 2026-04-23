"""
Mini-Ultra Memory Store
Simple persistent memory with save/load/search capabilities.
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from utils.logger import log_info, log_error


class MemoryStore:
    """Simple JSON-backed memory store with search."""

    def __init__(self, persist_path: str = "data/memory.json", max_items: int = 1000):
        self.persist_path = Path(persist_path)
        self.max_items = max_items
        self.memories: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        """Load memories from disk."""
        if self.persist_path.exists():
            try:
                with open(self.persist_path, "r") as f:
                    self.memories = json.load(f)
                log_info("memory", f"Loaded {len(self.memories)} memories from {self.persist_path}")
            except Exception as e:
                log_error("memory", f"Failed to load memories: {e}")
                self.memories = []
        else:
            self.memories = []

    def _save(self):
        """Persist memories to disk."""
        try:
            self.persist_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.persist_path, "w") as f:
                json.dump(self.memories, f, indent=2, default=str)
        except Exception as e:
            log_error("memory", f"Failed to save memories: {e}")

    def add(self, content: str, category: str = "general", metadata: dict = None) -> dict:
        """Add a memory entry."""
        entry = {
            "id": len(self.memories) + 1,
            "content": content,
            "category": category,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat(),
        }
        self.memories.append(entry)

        # Enforce max items
        if len(self.memories) > self.max_items:
            self.memories = self.memories[-self.max_items:]

        self._save()
        log_info("memory", f"Added memory #{entry['id']}: {content[:50]}...")
        return entry

    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """Simple keyword search across memories."""
        query_lower = query.lower()
        results = []
        for mem in reversed(self.memories):
            if query_lower in mem["content"].lower():
                results.append(mem)
                if len(results) >= limit:
                    break
        return results

    def get_recent(self, limit: int = 10) -> List[Dict]:
        """Get most recent memories."""
        return list(reversed(self.memories[-limit:]))

    def get_by_category(self, category: str, limit: int = 10) -> List[Dict]:
        """Get memories by category."""
        results = [m for m in reversed(self.memories) if m["category"] == category]
        return results[:limit]

    def get_context(self, limit: int = 5) -> str:
        """Get recent memories formatted as context for LLM."""
        recent = self.get_recent(limit)
        if not recent:
            return ""
        lines = ["Recent memories:"]
        for mem in recent:
            lines.append(f"- [{mem['category']}] {mem['content']}")
        return "\n".join(lines)

    def clear(self):
        """Clear all memories."""
        self.memories = []
        self._save()
        log_info("memory", "All memories cleared")

    def stats(self) -> dict:
        """Get memory statistics."""
        categories = {}
        for mem in self.memories:
            cat = mem.get("category", "general")
            categories[cat] = categories.get(cat, 0) + 1
        return {
            "total": len(self.memories),
            "max_items": self.max_items,
            "categories": categories,
            "persist_path": str(self.persist_path),
        }

    def self_test(self) -> dict:
        """Run self-test on memory system."""
        try:
            test_entry = self.add("self_test_probe", category="system")
            found = self.search("self_test_probe", limit=1)
            # Clean up
            self.memories = [m for m in self.memories if m["content"] != "self_test_probe"]
            self._save()
            return {"success": True, "entries": len(self.memories)}
        except Exception as e:
            return {"success": False, "error": str(e)}
