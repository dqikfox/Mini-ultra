"""
Mini-Ultra Error Handlers
Custom exception classes and error handling utilities.
"""
import functools
import asyncio
from utils.logger import log_error


class MiniUltraError(Exception):
    """Base exception for Mini-Ultra."""
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self):
        return {"error": self.message, "details": self.details}


class ConfigError(MiniUltraError):
    """Configuration related errors."""
    pass


class ToolError(MiniUltraError):
    """Tool execution errors."""
    pass


class LLMError(MiniUltraError):
    """LLM communication errors."""
    pass


class MemoryError(MiniUltraError):
    """Memory system errors."""
    pass


def with_retry(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Decorator for retrying failed operations."""
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_error = None
            current_delay = delay
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    log_error("retry", f"Attempt {attempt + 1}/{max_retries} failed: {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
            raise last_error

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            import time
            last_error = None
            current_delay = delay
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    log_error("retry", f"Attempt {attempt + 1}/{max_retries} failed: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(current_delay)
                        current_delay *= backoff
            raise last_error

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator
