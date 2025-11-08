"""Logging utility for exchange listeners with support for console and file output."""

import logging
import json
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Optional


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data)


class TextFormatter(logging.Formatter):
    """Human-readable text formatter."""
    
    def __init__(self, include_timestamp: bool = True):
        """
        Initialize text formatter.
        
        Args:
            include_timestamp: Whether to include timestamp in log messages
        """
        if include_timestamp:
            fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            datefmt = "%Y-%m-%d %H:%M:%S"
        else:
            fmt = "%(name)s - %(levelname)s - %(message)s"
            datefmt = None
        
        super().__init__(fmt=fmt, datefmt=datefmt)


def setup_logger(
    name: str,
    config: Dict[str, Any],
    exchange_name: str = None
) -> logging.Logger:
    """
    Set up logger with console and optional file handlers.
    
    Args:
        name: Logger name (usually module name)
        config: Logging configuration from YAML
        exchange_name: Exchange name for log file naming
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Get logging configuration
    log_config = config.get("logging", {})
    level = log_config.get("level", "INFO").upper()
    format_type = log_config.get("format", "text").lower()
    include_timestamp = log_config.get("include_timestamp", True)
    
    # Set log level
    logger.setLevel(getattr(logging, level, logging.INFO))
    
    # Create formatter based on format type
    if format_type == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter(include_timestamp=include_timestamp)
    
    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level, logging.INFO))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    file_config = log_config.get("file", {})
    if file_config.get("enabled", False):
        log_path = file_config.get("path")
        
        # If no explicit path, generate one
        if not log_path:
            log_dir = Path("/app/logs")
            log_dir.mkdir(parents=True, exist_ok=True)
            log_filename = f"{exchange_name or 'listener'}.log"
            log_path = log_dir / log_filename
        else:
            log_path = Path(log_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Get rotation settings
        max_bytes = file_config.get("max_bytes", 10 * 1024 * 1024)  # 10MB default
        backup_count = file_config.get("backup_count", 5)  # 5 backups default
        
        # Create rotating file handler
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, level, logging.INFO))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Log the file location (using print to ensure it shows up during init)
        print(f"Logging to file: {log_path}")
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get existing logger by name.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

