#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced logging system for playwright-simple.

Provides structured logging with context, levels, and detailed debugging information.
"""

import logging
import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum


class LogLevel(Enum):
    """Log levels for structured logging."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    ACTION = "ACTION"  # Special level for user actions
    STATE = "STATE"  # Special level for state changes
    ELEMENT = "ELEMENT"  # Special level for element operations


@dataclass
class LogContext:
    """Context information for a log entry."""
    test_name: Optional[str] = None
    step_number: Optional[int] = None
    action: Optional[str] = None
    element: Optional[str] = None
    selector: Optional[str] = None
    url: Optional[str] = None
    timestamp: Optional[datetime] = None
    duration: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        result = {}
        if self.test_name:
            result['test_name'] = self.test_name
        if self.step_number is not None:
            result['step_number'] = self.step_number
        if self.action:
            result['action'] = self.action
        if self.element:
            result['element'] = self.element
        if self.selector:
            result['selector'] = self.selector
        if self.url:
            result['url'] = self.url
        if self.timestamp:
            result['timestamp'] = self.timestamp.isoformat()
        if self.duration is not None:
            result['duration'] = self.duration
        if self.metadata:
            result['metadata'] = self.metadata
        return result


class StructuredLogger:
    """
    Advanced structured logger for playwright-simple.
    
    Provides:
    - Structured logging with context
    - Multiple output formats (console, JSON, file)
    - Log levels and filtering
    - Performance tracking
    - Element operation tracking
    """
    
    def __init__(
        self,
        name: str = "playwright_simple",
        level: str = "INFO",
        log_file: Optional[Path] = None,
        json_log: bool = False,
        console_output: bool = True
    ):
        """
        Initialize structured logger.
        
        Args:
            name: Logger name
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Optional file path for logging
            json_log: Whether to output JSON format
            console_output: Whether to output to console
        """
        self.name = name
        self.log_file = log_file
        self.json_log = json_log
        self.console_output = console_output
        
        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            # Console handler
            if console_output:
                console_handler = logging.StreamHandler(sys.stdout)
                if json_log:
                    console_handler.setFormatter(JSONFormatter())
                else:
                    console_handler.setFormatter(StructuredFormatter())
                self.logger.addHandler(console_handler)
            
            # File handler
            if log_file:
                log_file.parent.mkdir(parents=True, exist_ok=True)
                file_handler = logging.FileHandler(log_file, encoding='utf-8')
                if json_log:
                    file_handler.setFormatter(JSONFormatter())
                else:
                    file_handler.setFormatter(StructuredFormatter())
                self.logger.addHandler(file_handler)
        
        # Context stack for nested operations
        self._context_stack: List[LogContext] = []
        self._current_context: Optional[LogContext] = None
    
    def push_context(self, context: LogContext) -> None:
        """Push context onto stack."""
        self._context_stack.append(self._current_context)
        self._current_context = context
    
    def pop_context(self) -> Optional[LogContext]:
        """Pop context from stack."""
        old_context = self._current_context
        if self._context_stack:
            self._current_context = self._context_stack.pop()
        else:
            self._current_context = None
        return old_context
    
    def get_context(self) -> Optional[LogContext]:
        """Get current context."""
        return self._current_context
    
    def _log(
        self,
        level: LogLevel,
        message: str,
        context: Optional[LogContext] = None,
        **kwargs
    ) -> None:
        """Internal logging method."""
        # Use provided context or current context
        log_context = context or self._current_context
        
        # Prepare log data
        log_data = {
            'level': level.value,
            'message': message,
            'context': log_context.to_dict() if log_context else {},
            **kwargs
        }
        
        # Log based on format
        if self.json_log:
            log_message = json.dumps(log_data, default=str)
        else:
            log_message = self._format_message(level, message, log_context, **kwargs)
        
        # Log using appropriate level
        # Map custom levels to standard logging levels
        level_map = {
            LogLevel.ACTION: "info",
            LogLevel.STATE: "info",
            LogLevel.ELEMENT: "info",
        }
        log_level = level_map.get(level, level.value.lower())
        log_method = getattr(self.logger, log_level)
        log_method(log_message)
    
    def _format_message(
        self,
        level: LogLevel,
        message: str,
        context: Optional[LogContext],
        **kwargs
    ) -> str:
        """Format message for console output."""
        parts = []
        
        # Level
        level_emoji = {
            LogLevel.DEBUG: "🔍",
            LogLevel.INFO: "ℹ️",
            LogLevel.WARNING: "⚠️",
            LogLevel.ERROR: "❌",
            LogLevel.CRITICAL: "🚨",
            LogLevel.ACTION: "🎬",
            LogLevel.STATE: "🔄",
            LogLevel.ELEMENT: "🎯"
        }
        parts.append(f"{level_emoji.get(level, '📝')} [{level.value}]")
        
        # Context info
        if context:
            if context.test_name:
                parts.append(f"Test: {context.test_name}")
            if context.step_number is not None:
                parts.append(f"Step: {context.step_number}")
            if context.action:
                parts.append(f"Action: {context.action}")
            if context.element:
                parts.append(f"Element: {context.element}")
            if context.selector:
                parts.append(f"Selector: {context.selector}")
            if context.url:
                parts.append(f"URL: {context.url}")
            if context.duration is not None:
                parts.append(f"Duration: {context.duration:.3f}s")
        
        # Additional kwargs
        if kwargs:
            for key, value in kwargs.items():
                parts.append(f"{key}: {value}")
        
        # Message
        parts.append(f"Message: {message}")
        
        return " | ".join(parts)
    
    # Convenience methods
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        self._log(LogLevel.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        self._log(LogLevel.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self._log(LogLevel.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        # Remover campos que não são válidos em LogContext
        valid_fields = {'test_name', 'step_number', 'action', 'element', 'selector', 'url', 'timestamp', 'duration'}
        context_kwargs = {k: v for k, v in kwargs.items() if k in valid_fields}
        # Colocar campos extras no metadata
        metadata = {k: v for k, v in kwargs.items() if k not in valid_fields}
        if metadata:
            context_kwargs['metadata'] = metadata
        
        context = LogContext(**context_kwargs) if context_kwargs else None
        self._log(LogLevel.ERROR, message, context=context, **{k: v for k, v in kwargs.items() if k not in valid_fields})
    
    def critical(self, message: str, **kwargs) -> None:
        """Log critical message."""
        self._log(LogLevel.CRITICAL, message, **kwargs)
    
    def action(self, message: str, action: str, **kwargs) -> None:
        """Log action message."""
        # Remover campos que não são válidos em LogContext
        valid_fields = {'test_name', 'step_number', 'element', 'selector', 'url', 'timestamp', 'duration'}
        context_kwargs = {k: v for k, v in kwargs.items() if k in valid_fields}
        # Colocar campos extras no metadata
        metadata = {k: v for k, v in kwargs.items() if k not in valid_fields}
        if metadata:
            context_kwargs['metadata'] = metadata
        
        context = LogContext(action=action, **context_kwargs)
        self._log(LogLevel.ACTION, message, context=context)
    
    def state(self, message: str, **kwargs) -> None:
        """Log state change message."""
        # Remover campos que não são válidos em LogContext
        valid_fields = {'test_name', 'step_number', 'action', 'element', 'selector', 'url', 'timestamp', 'duration'}
        context_kwargs = {k: v for k, v in kwargs.items() if k in valid_fields}
        # Colocar campos extras no metadata
        metadata = {k: v for k, v in kwargs.items() if k not in valid_fields}
        if metadata:
            context_kwargs['metadata'] = metadata
        
        context = LogContext(**context_kwargs) if context_kwargs else None
        self._log(LogLevel.STATE, message, context=context, **{k: v for k, v in kwargs.items() if k not in valid_fields})
    
    def element(self, message: str, element: str, selector: Optional[str] = None, **kwargs) -> None:
        """Log element operation message."""
        # Remover campos que não são válidos em LogContext
        valid_fields = {'test_name', 'step_number', 'action', 'url', 'timestamp', 'duration'}
        context_kwargs = {k: v for k, v in kwargs.items() if k in valid_fields}
        # Colocar campos extras no metadata
        metadata = {k: v for k, v in kwargs.items() if k not in valid_fields}
        if metadata:
            context_kwargs['metadata'] = metadata
        
        context = LogContext(element=element, selector=selector, **context_kwargs)
        self._log(LogLevel.ELEMENT, message, context=context)


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record."""
        return record.getMessage()


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add any extra fields
        if hasattr(record, 'context'):
            log_data['context'] = record.context
        
        return json.dumps(log_data, default=str)


# Global logger instance
_global_logger: Optional[StructuredLogger] = None


def get_logger(
    name: str = "playwright_simple",
    level: str = "INFO",
    log_file: Optional[Path] = None,
    json_log: bool = False
) -> StructuredLogger:
    """
    Get or create global logger instance.
    
    Args:
        name: Logger name
        level: Log level
        log_file: Optional log file path
        json_log: Whether to use JSON format
        
    Returns:
        StructuredLogger instance
    """
    global _global_logger
    
    if _global_logger is None:
        _global_logger = StructuredLogger(
            name=name,
            level=level,
            log_file=log_file,
            json_log=json_log
        )
    
    return _global_logger


def set_logger(logger: StructuredLogger) -> None:
    """Set global logger instance."""
    global _global_logger
    _global_logger = logger

