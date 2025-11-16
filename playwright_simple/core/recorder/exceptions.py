#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Recorder-specific exceptions.

Custom exceptions for recorder operations with detailed error context.
"""

from typing import Optional, Dict, Any
from pathlib import Path


class RecorderError(Exception):
    """Base exception for recorder errors."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        """
        Initialize recorder error.
        
        Args:
            message: Error message
            details: Additional error details
            cause: Original exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.cause = cause
    
    def __str__(self) -> str:
        """Return formatted error message."""
        msg = self.message
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            msg = f"{msg} ({details_str})"
        if self.cause:
            msg = f"{msg} - Caused by: {self.cause}"
        return msg


class RecorderConfigurationError(RecorderError):
    """Error in recorder configuration."""
    pass


class RecorderInitializationError(RecorderError):
    """Error during recorder initialization."""
    pass


class RecordingSessionError(RecorderError):
    """Error during recording session."""
    pass


class PlaybackSessionError(RecorderError):
    """Error during playback session."""
    pass


class YAMLProcessingError(RecorderError):
    """Error processing YAML file."""
    
    def __init__(
        self,
        message: str,
        yaml_path: Optional[Path] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        """
        Initialize YAML processing error.
        
        Args:
            message: Error message
            yaml_path: Path to YAML file that caused the error
            details: Additional error details
            cause: Original exception that caused this error
        """
        super().__init__(message, details, cause)
        self.yaml_path = yaml_path
        if yaml_path:
            self.details['yaml_path'] = str(yaml_path)


class EventCaptureError(RecorderError):
    """Error during event capture."""
    pass


class ActionConversionError(RecorderError):
    """Error converting event to action."""
    pass


class BrowserServiceError(RecorderError):
    """Error in browser service."""
    pass


class VideoServiceError(RecorderError):
    """Error in video service."""
    pass


class YAMLServiceError(RecorderError):
    """Error in YAML service."""
    pass

