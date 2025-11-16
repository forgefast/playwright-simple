#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Recorder Logger Module.

Specialized logger for recorder that provides structured logging with context.
"""

import logging
import json
import time
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
from pathlib import Path

from .logging_config import RecorderLoggingConfig
from ..logger import StructuredLogger, LogLevel, LogContext


class RecorderLogger:
    """
    Specialized logger for recorder operations.
    
    Provides structured logging with context for:
    - User actions (click, type, submit)
    - Screen events (page load, navigation, stability)
    - Step execution (success/failure)
    - Critical failures
    - Cursor movement
    """
    
    def __init__(
        self,
        name: str = "recorder",
        console_level: Optional[str] = None,
        file_level: Optional[str] = None,
        log_file: Optional[Path] = None,
        json_format: bool = False
    ):
        """
        Initialize recorder logger.
        
        Args:
            name: Logger name
            console_level: Console log level (default: from env or INFO)
            file_level: File log level (default: from env or DEBUG)
            log_file: Optional log file path
            json_format: Whether to use JSON format for file output
        """
        self.name = name
        self.json_format = json_format or RecorderLoggingConfig.should_use_json_format()
        
        # Get log levels
        self.console_level = RecorderLoggingConfig.get_console_level(console_level)
        self.file_level = RecorderLoggingConfig.get_file_level(file_level)
        self.is_debug = RecorderLoggingConfig.is_debug_mode(self.console_level)
        
        # Get log file path
        self.log_file = RecorderLoggingConfig.get_log_file_path(log_file)
        
        # Initialize structured logger
        self.structured_logger = StructuredLogger(
            name=name,
            level=logging.getLevelName(self.console_level),
            log_file=self.log_file,
            json_log=self.json_format,
            console_output=True
        )
        
        # Current execution context
        self.current_step_number: Optional[int] = None
        self.current_action_type: Optional[str] = None
        self.current_page_state: Optional[Dict[str, Any]] = None
        
        # Performance tracking
        self.action_start_times: Dict[str, float] = {}
    
    def set_step_context(self, step_number: Optional[int], action_type: Optional[str] = None):
        """Set current step context."""
        self.current_step_number = step_number
        self.current_action_type = action_type
    
    def set_page_state(self, page_state: Dict[str, Any]):
        """Set current page state."""
        self.current_page_state = page_state
    
    def _get_context(self, **kwargs) -> LogContext:
        """Build log context from current state and kwargs."""
        element_info = kwargs.get('element_info')
        page_state = kwargs.get('page_state') or self.current_page_state
        
        # Build element string if available
        element_str = None
        if element_info:
            if isinstance(element_info, dict):
                text = element_info.get('text') or element_info.get('label', '')
                selector = element_info.get('selector', '')
                element_str = text or selector or str(element_info)
            else:
                element_str = str(element_info)
        
        return LogContext(
            test_name=None,
            step_number=self.current_step_number,
            action=self.current_action_type or kwargs.get('action_type'),
            element=element_str,
            selector=kwargs.get('selector'),
            url=page_state.get('url') if page_state else None,
            duration=kwargs.get('duration_ms') / 1000.0 if kwargs.get('duration_ms') else None
        )
    
    def _build_log_data(
        self,
        level: str,
        message: str,
        action_type: Optional[str] = None,
        element_info: Optional[Dict[str, Any]] = None,
        page_state: Optional[Dict[str, Any]] = None,
        success: Optional[bool] = None,
        duration_ms: Optional[float] = None,
        error: Optional[str] = None,
        warnings: Optional[list] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Build structured log data."""
        # Use provided or current context
        action_type = action_type or self.current_action_type
        page_state = page_state or self.current_page_state
        
        # Base log data
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': level,
            'message': message,
            'step_number': self.current_step_number,
            'action_type': action_type,
        }
        
        # Add element info (configurable detail level)
        if element_info:
            if self.is_debug or level in ('ERROR', 'WARNING', 'CRITICAL'):
                # Full context for debug or errors
                log_data['element_info'] = element_info
            else:
                # Minimal context for production
                minimal_element = {}
                if 'text' in element_info:
                    minimal_element['text'] = element_info['text']
                if 'coordinates' in element_info:
                    minimal_element['coordinates'] = element_info['coordinates']
                if minimal_element:
                    log_data['element_info'] = minimal_element
        
        # Add page state (configurable detail level)
        if page_state:
            if self.is_debug or level in ('ERROR', 'WARNING', 'CRITICAL'):
                # Full context
                log_data['page_state'] = page_state
            else:
                # Minimal context
                minimal_state = {}
                if 'url' in page_state:
                    minimal_state['url'] = page_state['url']
                if 'title' in page_state:
                    minimal_state['title'] = page_state['title']
                if minimal_state:
                    log_data['page_state'] = minimal_state
        
        # Add success/failure info
        if success is not None:
            log_data['success'] = success
        if duration_ms is not None:
            log_data['duration_ms'] = round(duration_ms, 2)
        if error:
            log_data['error'] = error
        if warnings:
            log_data['warnings'] = warnings
        
        # Add any additional kwargs
        log_data.update(kwargs)
        
        return log_data
    
    def _log(
        self,
        level: str,
        message: str,
        action_type: Optional[str] = None,
        element_info: Optional[Dict[str, Any]] = None,
        page_state: Optional[Dict[str, Any]] = None,
        success: Optional[bool] = None,
        duration_ms: Optional[float] = None,
        error: Optional[str] = None,
        warnings: Optional[list] = None,
        **kwargs
    ):
        """Internal logging method."""
        log_data = self._build_log_data(
            level=level,
            message=message,
            action_type=action_type,
            element_info=element_info,
            page_state=page_state,
            success=success,
            duration_ms=duration_ms,
            error=error,
            warnings=warnings,
            **kwargs
        )
        
        # Build context for structured logger
        context = self._get_context(
            action_type=action_type,
            element_info=element_info,
            page_state=page_state,
            duration_ms=duration_ms
        )
        
        # Map level to LogLevel enum
        level_map = {
            'DEBUG': LogLevel.DEBUG,
            'INFO': LogLevel.INFO,
            'WARNING': LogLevel.WARNING,
            'ERROR': LogLevel.ERROR,
            'CRITICAL': LogLevel.CRITICAL
        }
        log_level = level_map.get(level, LogLevel.INFO)
        
        # Format message for console
        if self.json_format:
            # JSON format
            log_message = json.dumps(log_data, default=str)
        else:
            # Human-readable format
            log_message = self._format_console_message(log_data)
        
        # Log using structured logger
        self.structured_logger._log(log_level, log_message, context=context)
    
    def _format_console_message(self, log_data: Dict[str, Any]) -> str:
        """Format log data for console output."""
        parts = []
        
        # Step number
        if log_data.get('step_number'):
            parts.append(f"[Step {log_data['step_number']}]")
        
        # Action type
        if log_data.get('action_type'):
            parts.append(f"[{log_data['action_type']}]")
        
        # Message
        parts.append(log_data['message'])
        
        # Element info
        element_info = log_data.get('element_info')
        if element_info:
            element_parts = []
            if element_info.get('text'):
                element_parts.append(f'"{element_info["text"]}"')
            if element_info.get('coordinates'):
                x, y = element_info['coordinates']
                element_parts.append(f'at ({x}, {y})')
            if element_parts:
                parts.append('| Element: ' + ' '.join(element_parts))
        
        # Page state
        page_state = log_data.get('page_state')
        if page_state:
            page_parts = []
            if page_state.get('url'):
                url = page_state['url']
                if len(url) > 60:
                    url = url[:57] + '...'
                page_parts.append(f'URL: {url}')
            if page_state.get('title'):
                title = page_state['title']
                if len(title) > 40:
                    title = title[:37] + '...'
                page_parts.append(f'Title: {title}')
            if page_parts:
                parts.append('| ' + ' | '.join(page_parts))
        
        # Success/failure
        if log_data.get('success') is not None:
            status = "SUCCESS" if log_data['success'] else "FAILED"
            parts.append(f'| {status}')
        
        # Duration
        if log_data.get('duration_ms'):
            parts.append(f'| Duration: {log_data["duration_ms"]}ms')
        
        # Error
        if log_data.get('error'):
            parts.append(f'| Error: {log_data["error"]}')
        
        return ' '.join(parts)
    
    def log_user_action(
        self,
        action_type: str,
        element_info: Optional[Dict[str, Any]] = None,
        success: bool = True,
        duration_ms: Optional[float] = None,
        error: Optional[str] = None,
        warnings: Optional[list] = None,
        **details
    ):
        """Log user action (click, type, submit)."""
        level = 'ERROR' if error else ('WARNING' if warnings else 'INFO')
        message = f"User action: {action_type}"
        if element_info and element_info.get('text'):
            message += f' "{element_info["text"]}"'
        
        self._log(
            level=level,
            message=message,
            action_type=action_type,
            element_info=element_info,
            success=success,
            duration_ms=duration_ms,
            error=error,
            warnings=warnings,
            **details
        )
    
    def log_screen_event(
        self,
        event_type: str,
        page_state: Optional[Dict[str, Any]] = None,
        **details
    ):
        """Log screen event (page load, navigation, stability)."""
        self._log(
            level='INFO',
            message=f"Screen event: {event_type}",
            action_type='screen_event',
            page_state=page_state,
            event_type=event_type,
            **details
        )
    
    def log_step_execution(
        self,
        step_number: int,
        action: str,
        success: bool,
        duration_ms: Optional[float] = None,
        error: Optional[str] = None,
        element_info: Optional[Dict[str, Any]] = None,
        page_state: Optional[Dict[str, Any]] = None,
        **details
    ):
        """Log step execution (from YAML or command)."""
        level = 'CRITICAL' if error and not success else ('ERROR' if error else 'INFO')
        message = f"Step {step_number} executed: {action}"
        if success:
            message += " - SUCCESS"
        else:
            message += " - FAILED"
        
        self._log(
            level=level,
            message=message,
            action_type=action,
            element_info=element_info,
            page_state=page_state,
            success=success,
            duration_ms=duration_ms,
            error=error,
            **details
        )
    
    def log_critical_failure(
        self,
        action: str,
        error: str,
        element_info: Optional[Dict[str, Any]] = None,
        page_state: Optional[Dict[str, Any]] = None,
        **context
    ):
        """Log critical failure that interrupts flow."""
        self._log(
            level='CRITICAL',
            message=f"Critical failure in {action}: {error}",
            action_type=action,
            element_info=element_info,
            page_state=page_state,
            success=False,
            error=error,
            **context
        )
    
    def log_cursor_movement(
        self,
        x: int,
        y: int,
        target_element: Optional[Dict[str, Any]] = None,
        animation_duration_ms: Optional[float] = None
    ):
        """Log cursor movement."""
        if not self.is_debug:
            return  # Skip cursor movement logs in production
        
        element_text = None
        if target_element:
            element_text = target_element.get('text') or target_element.get('label', '')
        
        message = f"Cursor moved to ({x}, {y})"
        if element_text:
            message += f', target: "{element_text}"'
        message += ')'
        
        self._log(
            level='DEBUG',
            message=message,
            action_type='cursor_movement',
            element_info=target_element,
            cursor_x=x,
            cursor_y=y,
            animation_duration_ms=animation_duration_ms
        )
    
    def start_action_timer(self, action_id: str):
        """Start timer for an action."""
        self.action_start_times[action_id] = time.time()
    
    def end_action_timer(self, action_id: str) -> Optional[float]:
        """End timer for an action and return duration in ms."""
        if action_id not in self.action_start_times:
            return None
        
        duration = (time.time() - self.action_start_times[action_id]) * 1000
        del self.action_start_times[action_id]
        return duration
    
    def warning(self, message: str, **details):
        """Log warning message."""
        self._log(
            level='WARNING',
            message=message,
            **details
        )
    
    def error(self, message: str, **details):
        """Log error message."""
        self._log(
            level='ERROR',
            message=message,
            **details
        )
    
    def info(self, message: str, **details):
        """Log info message."""
        self._log(
            level='INFO',
            message=message,
            **details
        )
    
    def debug(self, message: str, **details):
        """Log debug message."""
        self._log(
            level='DEBUG',
            message=message,
            **details
        )

