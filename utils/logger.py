"""
Mini-Ultra Logger
Centralized logging with file and console output.
"""
import logging
import os
from pathlib import Path
from datetime import datetime

_loggers = {}


def get_logger(name: str = "mini_ultra", level: str = "INFO", log_file: str = None) -> logging.Logger:
    """Get or create a named logger."""
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.propagate = False

    # Console handler
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    fmt = logging.Formatter(
        "%(asctime)s | %(name)-15s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console.setFormatter(fmt)
    logger.addHandler(console)

    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(str(log_path))
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    _loggers[name] = logger
    return logger


def log_info(component: str, message: str, **kwargs):
    get_logger().info(f"[{component}] {message}", **kwargs)


def log_error(component: str, message: str, exception: Exception = None, **kwargs):
    logger = get_logger()
    logger.error(f"[{component}] {message}", **kwargs)
    if exception:
        logger.exception(exception)


def log_warning(component: str, message: str, **kwargs):
    get_logger().warning(f"[{component}] {message}", **kwargs)


def log_debug(component: str, message: str, **kwargs):
    get_logger().debug(f"[{component}] {message}", **kwargs)
