#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Recorder Configuration Module.

Centralized configuration using dataclasses with type hints and validation.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, Literal

from .exceptions import RecorderConfigurationError


class SpeedLevel(str, Enum):
    """
    Speed levels for recorder execution.
    
    Controls delays, animations, and timeouts to optimize performance
    while maintaining video quality when needed.
    
    Attributes:
        SLOW: Normal delays (1.0x) - for demonstration videos
        NORMAL: Standard delays (1.0x) - default mode
        FAST: Reduced delays (0.1x) - current fast_mode equivalent
        ULTRA_FAST: Minimal delays (0.05x) - maximum performance
    """
    SLOW = 'slow'
    NORMAL = 'normal'
    FAST = 'fast'
    ULTRA_FAST = 'ultra_fast'
    
    def get_multiplier(self) -> float:
        """
        Get delay multiplier for this speed level.
        
        Returns:
            Multiplier to apply to delays (1.0 = no reduction, 0.1 = 10% of normal)
        """
        multipliers = {
            SpeedLevel.SLOW: 1.0,
            SpeedLevel.NORMAL: 1.0,
            SpeedLevel.FAST: 0.1,
            SpeedLevel.ULTRA_FAST: 0.05,
        }
        return multipliers[self]
    
    def get_min_delay(self) -> float:
        """
        Get minimum delay in seconds for this speed level.
        
        Returns:
            Minimum delay in seconds (0.0 = no minimum)
        """
        min_delays = {
            SpeedLevel.SLOW: 0.1,
            SpeedLevel.NORMAL: 0.1,
            SpeedLevel.FAST: 0.05,
            SpeedLevel.ULTRA_FAST: 0.0,  # No minimum for ultra fast
        }
        return min_delays[self]


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
    fast_mode: bool = False  # Deprecated: use speed_level instead
    speed_level: SpeedLevel = SpeedLevel.NORMAL
    mode: Literal['write', 'read'] = 'write'
    log_level: Optional[str] = None
    log_file: Optional[Path] = None
    
    def __post_init__(self):
        """Validate configuration values."""
        # Ensure output_path is a Path object
        if not isinstance(self.output_path, Path):
            self.output_path = Path(self.output_path)
        
        # Backward compatibility: map fast_mode to speed_level
        if self.fast_mode and self.speed_level == SpeedLevel.NORMAL:
            self.speed_level = SpeedLevel.FAST
        
        # Ensure speed_level is a SpeedLevel enum
        if isinstance(self.speed_level, str):
            try:
                self.speed_level = SpeedLevel(self.speed_level.lower())
            except ValueError:
                raise RecorderConfigurationError(
                    f"Invalid speed_level: {self.speed_level}",
                    details={
                        'speed_level': self.speed_level,
                        'valid_levels': [level.value for level in SpeedLevel]
                    }
                )
        
        # Validate mode
        if self.mode not in ('write', 'read'):
            raise RecorderConfigurationError(
                f"Invalid mode: {self.mode}. Must be 'write' or 'read'",
                details={'mode': self.mode, 'valid_modes': ['write', 'read']}
            )
        
        # Validate log_level if provided
        if self.log_level is not None:
            valid_levels = ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
            if self.log_level.upper() not in valid_levels:
                raise RecorderConfigurationError(
                    f"Invalid log_level: {self.log_level}",
                    details={
                        'log_level': self.log_level,
                        'valid_levels': list(valid_levels)
                    }
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
        speed_level: Optional[SpeedLevel] = None,
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
                      Deprecated: use speed_level instead
            speed_level: Speed level (SLOW, NORMAL, FAST, ULTRA_FAST)
            mode: 'write' for recording (export), 'read' for playback (import)
            log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Optional log file path
            
        Returns:
            RecorderConfig instance
        """
        # Determine speed_level: use provided, or map from fast_mode, or default to NORMAL
        if speed_level is None:
            if fast_mode:
                speed_level = SpeedLevel.FAST
            else:
                speed_level = SpeedLevel.NORMAL
        
        return cls(
            output_path=output_path,
            initial_url=initial_url or 'about:blank',
            headless=headless,
            debug=debug,
            fast_mode=fast_mode,
            speed_level=speed_level,
            mode=mode,
            log_level=log_level,
            log_file=log_file
        )

