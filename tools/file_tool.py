"""
Mini-Ultra File Tool
Read, write, and list files.
"""
import os
from pathlib import Path
from typing import Any, Dict
from tools.base import BaseTool


class FileTool(BaseTool):
    name = "file_manager"
    description = "Read, write, list, and manage files on the filesystem"

    # Restrict operations to safe directories
    ALLOWED_ROOTS = [os.getcwd(), "/tmp"]

    def _is_safe_path(self, path: str) -> bool:
        """Check if path is within allowed directories."""
        abs_path = os.path.abspath(path)
        return any(abs_path.startswith(os.path.abspath(root)) for root in self.ALLOWED_ROOTS)

    def execute(self, action: str = "list", path: str = ".", content: str = "", **kwargs) -> Dict[str, Any]:
        if not self._is_safe_path(path):
            return {"success": False, "error": f"Access denied: {path} is outside allowed directories"}

        try:
            if action == "read":
                return self._read(path)
            elif action == "write":
                return self._write(path, content)
            elif action == "list":
                return self._list(path)
            elif action == "info":
                return self._info(path)
            elif action == "delete":
                return self._delete(path)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _read(self, path: str) -> Dict:
        p = Path(path)
        if not p.exists():
            return {"success": False, "error": f"File not found: {path}"}
        if not p.is_file():
            return {"success": False, "error": f"Not a file: {path}"}
        content = p.read_text(errors="replace")
        return {"success": True, "result": content, "size": len(content), "path": str(p.absolute())}

    def _write(self, path: str, content: str) -> Dict:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return {"success": True, "result": f"Written {len(content)} chars to {path}", "path": str(p.absolute())}

    def _list(self, path: str) -> Dict:
        p = Path(path)
        if not p.exists():
            return {"success": False, "error": f"Path not found: {path}"}
        if not p.is_dir():
            return {"success": False, "error": f"Not a directory: {path}"}
        entries = []
        for item in sorted(p.iterdir()):
            entries.append({
                "name": item.name,
                "type": "dir" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else None,
            })
        return {"success": True, "result": entries, "path": str(p.absolute()), "count": len(entries)}

    def _info(self, path: str) -> Dict:
        p = Path(path)
        if not p.exists():
            return {"success": False, "error": f"Path not found: {path}"}
        stat = p.stat()
        return {
            "success": True,
            "result": {
                "name": p.name,
                "path": str(p.absolute()),
                "type": "dir" if p.is_dir() else "file",
                "size": stat.st_size,
                "modified": stat.st_mtime,
            }
        }

    def _delete(self, path: str) -> Dict:
        p = Path(path)
        if not p.exists():
            return {"success": False, "error": f"Path not found: {path}"}
        if p.is_file():
            p.unlink()
            return {"success": True, "result": f"Deleted file: {path}"}
        return {"success": False, "error": "Cannot delete directories for safety"}
