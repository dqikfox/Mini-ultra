"""
Mini-Ultra Code Executor Tool
Safe Python code execution in a sandboxed environment.
"""
import io
import sys
import traceback
from typing import Any, Dict
from tools.base import BaseTool


class CodeExecutorTool(BaseTool):
    name = "code_executor"
    description = "Execute Python code safely and return the output"

    # Blocked imports for safety
    BLOCKED_MODULES = {"subprocess", "shutil", "ctypes", "importlib"}

    def execute(self, code: str = "", timeout: int = 10, **kwargs) -> Dict[str, Any]:
        if not code:
            return {"success": False, "error": "No code provided"}

        # Basic safety check
        for blocked in self.BLOCKED_MODULES:
            if f"import {blocked}" in code or f"from {blocked}" in code:
                return {"success": False, "error": f"Blocked module: {blocked}"}

        # Capture stdout/stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = captured_out = io.StringIO()
        sys.stderr = captured_err = io.StringIO()

        result = None
        try:
            # Execute in restricted globals
            exec_globals = {
                "__builtins__": {
                    "print": print,
                    "range": range,
                    "len": len,
                    "str": str,
                    "int": int,
                    "float": float,
                    "bool": bool,
                    "list": list,
                    "dict": dict,
                    "tuple": tuple,
                    "set": set,
                    "sorted": sorted,
                    "enumerate": enumerate,
                    "zip": zip,
                    "map": map,
                    "filter": filter,
                    "sum": sum,
                    "min": min,
                    "max": max,
                    "abs": abs,
                    "round": round,
                    "type": type,
                    "isinstance": isinstance,
                    "hasattr": hasattr,
                    "getattr": getattr,
                    "True": True,
                    "False": False,
                    "None": None,
                    "Exception": Exception,
                    "ValueError": ValueError,
                    "TypeError": TypeError,
                    "KeyError": KeyError,
                    "IndexError": IndexError,
                }
            }
            exec(code, exec_globals)
            stdout_val = captured_out.getvalue()
            stderr_val = captured_err.getvalue()

            return {
                "success": True,
                "result": stdout_val if stdout_val else "(no output)",
                "stderr": stderr_val if stderr_val else None,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "stdout": captured_out.getvalue(),
            }
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
