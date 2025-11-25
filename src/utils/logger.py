"""Logging utilities for Workflow Builder."""

import logging
import sys
from pathlib import Path
from typing import Optional
from config.settings import get_settings

_logger: Optional[logging.Logger] = None


def setup_logger(name: str = "workflow_builder") -> logging.Logger:
    """
    Set up and configure the application logger.
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    global _logger
    
    if _logger is not None:
        return _logger
    
    settings = get_settings()
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    simple_formatter = logging.Formatter(
        fmt="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S"
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # File handler
    try:
        file_handler = logging.FileHandler(settings.log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Could not set up file logging: {e}")
    
    _logger = logger
    logger.info(f"Logger initialized (level: {settings.log_level})")
    
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get the application logger.
    
    Args:
        name: Optional logger name (defaults to 'workflow_builder')
        
    Returns:
        Logger instance
    """
    if _logger is None:
        return setup_logger(name or "workflow_builder")
    return _logger

