#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logging Configuration Module.

Standardized logging configuration for the Playwright Simple framework.
"""

import logging
import sys
from typing import Optional
from pathlib import Path


class FrameworkLogger:
    """Standardized logger for Playwright Simple framework."""
    
    # Log format padrão
    DEFAULT_FORMAT = '%(asctime)s [%(levelname)8s] %(name)s: %(message)s'
    DEBUG_FORMAT = '%(asctime)s [%(levelname)8s] [%(module)s:%(lineno)d] %(name)s: %(message)s'
    
    # Cores para terminal (se suportado)
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'
    }
    
    _configured = False
    _log_file: Optional[Path] = None
    
    @classmethod
    def configure(
        cls,
        level: str = 'INFO',
        debug: bool = False,
        log_file: Optional[Path] = None,
        enable_colors: bool = True
    ) -> None:
        """
        Configure framework logging.
        
        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            debug: Enable debug mode (sets level to DEBUG)
            log_file: Optional file path for logging
            enable_colors: Enable colored output in terminal
        """
        if cls._configured:
            return
        
        # Determine log level
        if debug:
            log_level = logging.DEBUG
        else:
            log_level = getattr(logging, level.upper(), logging.INFO)
        
        # Create formatter
        if log_level == logging.DEBUG:
            formatter = logging.Formatter(cls.DEBUG_FORMAT, datefmt='%Y-%m-%d %H:%M:%S')
        else:
            formatter = logging.Formatter(cls.DEFAULT_FORMAT, datefmt='%Y-%m-%d %H:%M:%S')
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # Remove existing handlers
        root_logger.handlers.clear()
        
        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        
        if enable_colors and sys.stdout.isatty():
            # Colored formatter for console
            class ColoredFormatter(logging.Formatter):
                def format(self, record):
                    log_color = cls.COLORS.get(record.levelname, cls.COLORS['RESET'])
                    record.levelname = f"{log_color}{record.levelname}{cls.COLORS['RESET']}"
                    return super().format(record)
            
            console_formatter = ColoredFormatter(
                cls.DEBUG_FORMAT if log_level == logging.DEBUG else cls.DEFAULT_FORMAT,
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        else:
            console_formatter = formatter
        
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        
        # File handler (if specified)
        if log_file:
            cls._log_file = Path(log_file)
            cls._log_file.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(cls._log_file, encoding='utf-8')
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        
        cls._configured = True
        
        # Log configuration
        logger = logging.getLogger(__name__)
        logger.info(f"Logging configured: level={logging.getLevelName(log_level)}, debug={debug}")
        if log_file:
            logger.info(f"Log file: {log_file}")
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Get a logger instance with standardized name.
        
        Args:
            name: Logger name (usually __name__)
            
        Returns:
            Logger instance
        """
        # Normalize logger name to framework format
        if not name.startswith('playwright_simple'):
            # If it's a module name, extract the relevant part
            parts = name.split('.')
            if 'playwright_simple' in parts:
                idx = parts.index('playwright_simple')
                name = '.'.join(parts[idx:])
        
        return logging.getLogger(name)


# Convenience functions for common logging patterns
def log_action(action: str, details: dict = None, level: str = 'INFO'):
    """
    Log a framework action.
    
    Args:
        action: Action name
        details: Optional details dictionary
        level: Log level
    """
    logger = FrameworkLogger.get_logger('playwright_simple.core.actions')
    message = f"🎬 {action}"
    if details:
        detail_str = ', '.join(f"{k}={v}" for k, v in details.items())
        message += f" | {detail_str}"
    
    getattr(logger, level.lower())(message)


def log_mouse_action(action: str, x: int, y: int, **kwargs):
    """
    Log a mouse action.
    
    Args:
        action: Action type (move, click, etc.)
        x: X coordinate
        y: Y coordinate
        **kwargs: Additional details
    """
    logger = FrameworkLogger.get_logger('playwright_simple.core.mouse')
    details = f"x={x}, y={y}"
    if kwargs:
        details += ', ' + ', '.join(f"{k}={v}" for k, v in kwargs.items())
    logger.debug(f"🖱️  [{action.upper()}] {details}")


def log_keyboard_action(action: str, text: str = None, **kwargs):
    """
    Log a keyboard action.
    
    Args:
        action: Action type (type, press, etc.)
        text: Text being typed
        **kwargs: Additional details
    """
    logger = FrameworkLogger.get_logger('playwright_simple.core.keyboard')
    details = []
    if text:
        text_preview = text[:50] + '...' if len(text) > 50 else text
        details.append(f"text='{text_preview}'")
    if kwargs:
        details.extend(f"{k}={v}" for k, v in kwargs.items())
    logger.debug(f"⌨️  [{action.upper()}] {', '.join(details)}")


def log_cursor_action(action: str, x: float = None, y: float = None, **kwargs):
    """
    Log a cursor action.
    
    Args:
        action: Action type (move, show, hide, etc.)
        x: X coordinate
        y: Y coordinate
        **kwargs: Additional details
    """
    logger = FrameworkLogger.get_logger('playwright_simple.core.cursor')
    details = []
    if x is not None and y is not None:
        details.append(f"x={x}, y={y}")
    if kwargs:
        details.extend(f"{k}={v}" for k, v in kwargs.items())
    logger.debug(f"🖱️  [CURSOR:{action.upper()}] {', '.join(details)}")


def log_element_action(action: str, element_info: dict = None, **kwargs):
    """
    Log an element interaction.
    
    Args:
        action: Action type (click, type, submit, etc.)
        element_info: Element information dictionary
        **kwargs: Additional details
    """
    logger = FrameworkLogger.get_logger('playwright_simple.core.elements')
    details = []
    if element_info:
        if 'text' in element_info:
            details.append(f"text='{element_info['text']}'")
        if 'selector' in element_info:
            details.append(f"selector='{element_info['selector']}'")
        if 'tag' in element_info:
            details.append(f"tag={element_info['tag']}")
    if kwargs:
        details.extend(f"{k}={v}" for k, v in kwargs.items())
    logger.debug(f"🎯 [ELEMENT:{action.upper()}] {', '.join(details)}")


def log_error(error: Exception, context: str = None, **kwargs):
    """
    Log an error with context.
    
    Args:
        error: Exception instance
        context: Context where error occurred
        **kwargs: Additional details
    """
    logger = FrameworkLogger.get_logger('playwright_simple.core.errors')
    message = f"❌ Error"
    if context:
        message += f" in {context}"
    message += f": {type(error).__name__}: {str(error)}"
    if kwargs:
        detail_str = ', '.join(f"{k}={v}" for k, v in kwargs.items())
        message += f" | {detail_str}"
    logger.error(message, exc_info=True)

