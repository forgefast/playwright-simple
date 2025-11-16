#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logging Configuration Module for Recorder.

Handles configuration of logging levels, formats, and destinations.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any


class RecorderLoggingConfig:
    """Configuration for recorder logging."""
    
    # Default levels
    DEFAULT_CONSOLE_LEVEL = logging.INFO
    DEFAULT_FILE_LEVEL = logging.DEBUG
    
    # Log format strings
    CONSOLE_FORMAT = '%(asctime)s [%(levelname)8s] [%(name)s] %(message)s'
    CONSOLE_DEBUG_FORMAT = '%(asctime)s [%(levelname)8s] [%(name)s:%(lineno)d] %(message)s'
    FILE_FORMAT = '%(asctime)s [%(levelname)8s] [%(name)s:%(lineno)d] %(message)s'
    
    @classmethod
    def get_log_level(cls, level: Optional[str] = None) -> int:
        """
        Get log level from string or environment variable.
        
        Args:
            level: Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
                  If None, reads from PLAYWRIGHT_SIMPLE_LOG_LEVEL env var
                  
        Returns:
            Logging level constant
        """
        if level is None:
            level = os.getenv('PLAYWRIGHT_SIMPLE_LOG_LEVEL', 'INFO')
        
        level_upper = level.upper()
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        
        return level_map.get(level_upper, logging.INFO)
    
    @classmethod
    def get_console_level(cls, level: Optional[str] = None) -> int:
        """Get console log level."""
        if level is None:
            level = os.getenv('PLAYWRIGHT_SIMPLE_LOG_LEVEL_CONSOLE', None)
        return cls.get_log_level(level) if level else cls.DEFAULT_CONSOLE_LEVEL
    
    @classmethod
    def get_file_level(cls, level: Optional[str] = None) -> int:
        """Get file log level."""
        if level is None:
            level = os.getenv('PLAYWRIGHT_SIMPLE_LOG_LEVEL_FILE', None)
        return cls.get_log_level(level) if level else cls.DEFAULT_FILE_LEVEL
    
    @classmethod
    def get_log_file_path(cls, log_file: Optional[Path] = None) -> Optional[Path]:
        """
        Get log file path from parameter or environment variable.
        
        Args:
            log_file: Optional log file path
            
        Returns:
            Path to log file or None
        """
        if log_file:
            return Path(log_file)
        
        env_log_file = os.getenv('PLAYWRIGHT_SIMPLE_LOG_FILE')
        if env_log_file:
            return Path(env_log_file)
        
        return None
    
    @classmethod
    def should_use_json_format(cls) -> bool:
        """Check if JSON format should be used for file logging."""
        return os.getenv('PLAYWRIGHT_SIMPLE_LOG_JSON', 'false').lower() == 'true'
    
    @classmethod
    def is_debug_mode(cls, level: Optional[int] = None) -> bool:
        """Check if debug mode is enabled."""
        if level is None:
            level = cls.get_log_level()
        return level <= logging.DEBUG

