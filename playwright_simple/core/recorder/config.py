#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Recorder Configuration Module.

Centralized configuration using dataclasses with type hints and validation.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Literal


@dataclass
class RecorderConfig:
    """
    Configuration for Recorder.
    
    Consolidates all recorder initialization parameters into a single,
    type-safe configuration object.
    
    Example:
        ```python
        config = RecorderConfig(
            output_path=Path("test.yaml"),
            initial_url="http://localhost:8000",
            headless=True,
            fast_mode=True
        )
        recorder = Recorder(config)
        ```
    """
    
    # Required parameters
    output_path: Path
    
    # Optional parameters with defaults
    initial_url: str = 'about:blank'
    headless: bool = False
    debug: bool = False
    fast_mode: bool = False
    mode: Literal['write', 'read'] = 'write'
    log_level: Optional[str] = None
    log_file: Optional[Path] = None
    
    def __post_init__(self):
        """Validate configuration values."""
        # Ensure output_path is a Path object
        if not isinstance(self.output_path, Path):
            self.output_path = Path(self.output_path)
        
        # Validate mode
        if self.mode not in ('write', 'read'):
            raise ValueError(f"Invalid mode: {self.mode}. Must be 'write' or 'read'")
        
        # Validate log_level if provided
        if self.log_level is not None:
            valid_levels = ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
            if self.log_level.upper() not in valid_levels:
                raise ValueError(
                    f"Invalid log_level: {self.log_level}. "
                    f"Must be one of {valid_levels}"
                )
        
        # Note: In read mode, output_path must exist, but we don't validate here
        # to allow Recorder to handle the error with better context
    
    @classmethod
    def from_kwargs(
        cls,
        output_path: Path,
        initial_url: Optional[str] = None,
        headless: bool = False,
        debug: bool = False,
        fast_mode: bool = False,
        mode: str = 'write',
        log_level: Optional[str] = None,
        log_file: Optional[Path] = None
    ) -> 'RecorderConfig':
        """
        Create RecorderConfig from keyword arguments.
        
        This is a convenience method to maintain backward compatibility
        with the existing Recorder.__init__ signature.
        
        Args:
            output_path: Path to output YAML file
            initial_url: Initial URL to open (default: about:blank)
            headless: Run browser in headless mode
            debug: Enable debug mode (verbose logging)
            fast_mode: Accelerate steps (reduce delays, instant animations)
            mode: 'write' for recording (export), 'read' for playback (import)
            log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Optional log file path
            
        Returns:
            RecorderConfig instance
        """
        return cls(
            output_path=output_path,
            initial_url=initial_url or 'about:blank',
            headless=headless,
            debug=debug,
            fast_mode=fast_mode,
            mode=mode,
            log_level=log_level,
            log_file=log_file
        )

