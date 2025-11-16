#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration management for playwright-simple.

Supports configuration via:
1. Default values (hardcoded)
2. YAML/JSON config files
3. Environment variables
4. Runtime parameters (highest priority)
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass, field, asdict

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


@dataclass
class CursorConfig:
    """Configuration for cursor customization."""
    style: str = "arrow"  # arrow, dot, circle, custom
    color: str = "#007bff"  # Hex color
    size: str = "medium"  # small, medium, large, or custom pixels
    animation_speed: float = 0.3  # Animation speed in seconds
    click_effect: bool = True
    click_effect_color: str = "#007bff"
    hover_effect: bool = True
    hover_effect_color: str = "#0056b3"
    transition_delay: float = 0.3  # Minimum delay in seconds between step transitions
    
    def __post_init__(self):
        """Validate configuration values."""
        from .exceptions import ConfigurationError
        
        valid_styles = ["arrow", "dot", "circle", "custom"]
        if self.style not in valid_styles:
            raise ConfigurationError(
                f"Invalid cursor style: {self.style}. Must be one of {valid_styles}"
            )
        
        valid_sizes = ["small", "medium", "large"]
        if self.size not in valid_sizes and not isinstance(self.size, (int, float)):
            raise ConfigurationError(
                f"Invalid cursor size: {self.size}. Must be one of {valid_sizes} or a number"
            )
        
        if self.animation_speed < 0:
            raise ConfigurationError(
                f"Animation speed must be non-negative, got: {self.animation_speed}"
            )


# VideoConfig moved to extensions/video/config.py
# Import here for backward compatibility (will be deprecated)
try:
    from ..extensions.video.config import VideoConfig
except ImportError:
    # Fallback if extension not available
    @dataclass
    class VideoConfig:
        """Placeholder - VideoConfig moved to extensions/video/config.py"""
        enabled: bool = False
        quality: str = "high"
        codec: str = "webm"
        dir: str = "videos"
        record_per_test: bool = True
        pause_on_failure: bool = False
        speed: float = 1.0


@dataclass
class ScreenshotConfig:
    """Configuration for screenshots."""
    auto: bool = True  # Automatic screenshots on actions
    on_failure: bool = True  # Screenshot on test failure
    dir: str = "screenshots"
    format: str = "png"  # png, jpeg
    full_page: bool = False  # Full page vs viewport only
    
    def __post_init__(self):
        """Validate configuration values."""
        valid_formats = ["png", "jpeg"]
        if self.format not in valid_formats:
            from .exceptions import ConfigurationError
            raise ConfigurationError(
                f"Invalid screenshot format: {self.format}. Must be one of {valid_formats}"
            )


@dataclass
class BrowserConfig:
    """Configuration for browser settings."""
    headless: bool = True
    slow_mo: int = 10  # Milliseconds to slow down operations
    timeout: int = 30000  # Default timeout in milliseconds
    navigation_timeout: int = 30000
    locale: str = "pt-BR"
    viewport: Dict[str, int] = field(default_factory=lambda: {"width": 1920, "height": 1080})
    wait_for_load: str = "load"  # load, domcontentloaded, networkidle - how to wait after each action
    wait_timeout: int = 10000  # Timeout for wait_for_load_state in milliseconds


@dataclass
class StepConfig:
    """Configuration for step execution."""
    static_min_duration: float = 3.0  # Minimum duration in seconds for static steps
    fast_mode: bool = False  # If True, ignores delays in static steps (for fast debugging)
    
@dataclass
class TestConfig:
    """
    Main configuration class for playwright-simple.
    
    Configuration priority (highest to lowest):
    1. Runtime parameters (passed to constructor)
    2. Environment variables
    3. Config file (YAML/JSON)
    4. Default values
    
    Example:
        ```python
        config = TestConfig(
            base_url="http://localhost:8000",
            cursor_style="arrow",
            cursor_color="#ff0000",
        )
        ```
    """
    
    # Base configuration
    base_url: str = "http://localhost:8000"
    
    # Sub-configurations
    cursor: CursorConfig = field(default_factory=CursorConfig)
    # video: VideoConfig - kept for backward compatibility, but use extensions/video for new code
    video: 'VideoConfig' = field(default_factory=lambda: VideoConfig())
    screenshots: ScreenshotConfig = field(default_factory=ScreenshotConfig)
    browser: BrowserConfig = field(default_factory=BrowserConfig)
    step: StepConfig = field(default_factory=StepConfig)
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate()
    
    @classmethod
    def from_file(cls, config_path: Union[str, Path]) -> 'TestConfig':
        """
        Load configuration from YAML or JSON file.
        
        Args:
            config_path: Path to config file (YAML or JSON)
            
        Returns:
            TestConfig instance
            
        Example:
            ```python
            config = TestConfig.from_file("config.yaml")
            ```
        """
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        # Load file
        with open(config_path, 'r', encoding='utf-8') as f:
            if config_path.suffix in ['.yaml', '.yml']:
                if not YAML_AVAILABLE:
                    raise ImportError("PyYAML is required for YAML config files. Install with: pip install pyyaml")
                data = yaml.safe_load(f)
            elif config_path.suffix == '.json':
                data = json.load(f)
            else:
                raise ValueError(f"Unsupported config file format: {config_path.suffix}")
        
        # Create config from data
        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestConfig':
        """
        Create TestConfig from dictionary.
        
        Args:
            data: Configuration dictionary
            
        Returns:
            TestConfig instance
        """
        # Extract base_url
        base_url = data.get('base_url', 'http://localhost:8000')
        
        # Extract sub-configs
        cursor_data = data.get('cursor', {})
        screenshots_data = data.get('screenshots', {})
        browser_data = data.get('browser', {})
        
        # Create sub-configs
        cursor = CursorConfig(**cursor_data)
        screenshots = ScreenshotConfig(**screenshots_data)
        
        # Ensure viewport is in browser_data
        if 'viewport' not in browser_data:
            browser_data['viewport'] = {"width": 1920, "height": 1080}
        
        browser = BrowserConfig(**browser_data)
        
        # Create video config if provided (for backward compatibility)
        video_data = data.get('video', {})
        try:
            from ..extensions.video.config import VideoConfig
            # Add all video config fields
            video = VideoConfig(
                enabled=video_data.get('enabled', True),
                quality=video_data.get('quality', 'high'),
                codec=video_data.get('codec', 'webm'),
                dir=video_data.get('dir', 'videos'),
                speed=video_data.get('speed', 1.0)
            )
            # Add extension-specific fields as attributes
            video.subtitles = video_data.get('subtitles', False)
            video.hard_subtitles = video_data.get('hard_subtitles', False)
            video.audio = video_data.get('audio', False)
            video.narration = video_data.get('narration', False)
            video.narration_lang = video_data.get('narration_lang', 'pt-BR')
            video.narration_engine = video_data.get('narration_engine', 'gtts')
            video.narration_slow = video_data.get('narration_slow', False)
            video.audio_file = video_data.get('audio_file')
            video.audio_lang = video_data.get('audio_lang', 'pt-BR')
            video.audio_engine = video_data.get('audio_engine', 'gtts')
            video.audio_voice = video_data.get('audio_voice')
            video.audio_rate = video_data.get('audio_rate')
            video.audio_pitch = video_data.get('audio_pitch')
            video.audio_volume = video_data.get('audio_volume')
        except ImportError:
            # Fallback
            video = VideoConfig(
                enabled=video_data.get('enabled', True),
                quality=video_data.get('quality', 'high'),
                codec=video_data.get('codec', 'webm'),
                dir=video_data.get('dir', 'videos'),
                speed=video_data.get('speed', 1.0)
            )
            video.subtitles = video_data.get('subtitles', False)
            video.hard_subtitles = video_data.get('hard_subtitles', False)
            video.audio = video_data.get('audio', False)
            video.narration = video_data.get('narration', False)
            video.narration_lang = video_data.get('narration_lang', 'pt-BR')
            video.narration_engine = video_data.get('narration_engine', 'gtts')
            video.narration_slow = video_data.get('narration_slow', False)
        
        return cls(
            base_url=base_url,
            cursor=cursor,
            video=video,
            screenshots=screenshots,
            browser=browser,
        )
    
    @classmethod
    def from_env(cls) -> 'TestConfig':
        """
        Load configuration from environment variables.
        
        Environment variables:
            PLAYWRIGHT_SIMPLE_BASE_URL
            PLAYWRIGHT_SIMPLE_CURSOR_STYLE
            PLAYWRIGHT_SIMPLE_CURSOR_COLOR
            PLAYWRIGHT_SIMPLE_VIDEO_ENABLED
            PLAYWRIGHT_SIMPLE_VIDEO_QUALITY
            PLAYWRIGHT_SIMPLE_SCREENSHOTS_AUTO
            PLAYWRIGHT_SIMPLE_HEADLESS
            etc.
        
        Returns:
            TestConfig instance
        """
        config_dict = {}
        
        # Base URL
        if base_url := os.getenv('PLAYWRIGHT_SIMPLE_BASE_URL'):
            config_dict['base_url'] = base_url
        
        # Cursor config
        cursor_dict = {}
        if style := os.getenv('PLAYWRIGHT_SIMPLE_CURSOR_STYLE'):
            cursor_dict['style'] = style
        if color := os.getenv('PLAYWRIGHT_SIMPLE_CURSOR_COLOR'):
            cursor_dict['color'] = color
        if size := os.getenv('PLAYWRIGHT_SIMPLE_CURSOR_SIZE'):
            cursor_dict['size'] = size
        
        if cursor_dict:
            config_dict['cursor'] = cursor_dict
        
        # Video config removed - use extensions/video instead
        # Video config is now handled by extensions
        
        # Screenshots config
        screenshots_dict = {}
        if auto := os.getenv('PLAYWRIGHT_SIMPLE_SCREENSHOTS_AUTO'):
            screenshots_dict['auto'] = auto.lower() in ('true', '1', 'yes')
        if on_failure := os.getenv('PLAYWRIGHT_SIMPLE_SCREENSHOTS_ON_FAILURE'):
            screenshots_dict['on_failure'] = on_failure.lower() in ('true', '1', 'yes')
        
        if screenshots_dict:
            config_dict['screenshots'] = screenshots_dict
        
        # Browser config
        browser_dict = {}
        if headless := os.getenv('PLAYWRIGHT_SIMPLE_HEADLESS'):
            browser_dict['headless'] = headless.lower() in ('true', '1', 'yes')
        if timeout := os.getenv('PLAYWRIGHT_SIMPLE_TIMEOUT'):
            browser_dict['timeout'] = int(timeout)
        
        if browser_dict:
            config_dict['browser'] = browser_dict
        
        # Create config with defaults, then override with env vars
        config = cls()
        if config_dict:
            env_config = cls.from_dict(config_dict)
            # Merge: env vars override defaults
            return cls._merge(config, env_config)
        
        return config
    
    @classmethod
    def _merge(cls, base: 'TestConfig', override: 'TestConfig') -> 'TestConfig':
        """Merge two configs, with override taking precedence."""
        # Merge base_url
        base_url = override.base_url if override.base_url != "http://localhost:8000" else base.base_url
        
        # Merge sub-configs (simple merge for now)
        cursor = override.cursor if override.cursor != CursorConfig() else base.cursor
        # video removed - use extensions/video instead
        screenshots = override.screenshots if override.screenshots != ScreenshotConfig() else base.screenshots
        browser = override.browser if override.browser != BrowserConfig() else base.browser
        
        return cls(
            base_url=base_url,
            cursor=cursor,
            screenshots=screenshots,
            browser=browser,
        )
    
    @classmethod
    def load(
        cls,
        config_file: Optional[Union[str, Path]] = None,
        use_env: bool = True,
        **kwargs
    ) -> 'TestConfig':
        """
        Load configuration with priority: kwargs > env > file > defaults.
        
        Args:
            config_file: Path to config file (optional)
            use_env: Whether to load from environment variables
            **kwargs: Runtime parameters (highest priority)
            
        Returns:
            TestConfig instance
            
        Example:
            ```python
            config = TestConfig.load(
                config_file="config.yaml",
                base_url="http://localhost:8000",
                cursor_style="arrow"
            )
            ```
        """
        # Start with defaults
        config = cls()
        
        # Load from file if provided
        if config_file:
            file_config = cls.from_file(config_file)
            config = cls._merge(config, file_config)
        
        # Load from environment if enabled
        if use_env:
            env_config = cls.from_env()
            config = cls._merge(config, env_config)
        
        # Apply runtime parameters (highest priority)
        if kwargs:
            # Handle nested configs
            cursor_kwargs = {}
            screenshots_kwargs = {}
            browser_kwargs = {}
            
            for key, value in kwargs.items():
                if key.startswith('cursor_'):
                    cursor_kwargs[key[7:]] = value  # Remove 'cursor_' prefix
                elif key.startswith('screenshots_'):
                    screenshots_kwargs[key[11:]] = value  # Remove 'screenshots_' prefix
                elif key.startswith('browser_'):
                    browser_kwargs[key[7:]] = value  # Remove 'browser_' prefix
                elif hasattr(config, key):
                    setattr(config, key, value)
            
            # Update sub-configs
            if cursor_kwargs:
                for k, v in cursor_kwargs.items():
                    if hasattr(config.cursor, k):
                        setattr(config.cursor, k, v)
            
            if screenshots_kwargs:
                for k, v in screenshots_kwargs.items():
                    if hasattr(config.screenshots, k):
                        setattr(config.screenshots, k, v)
            
            if browser_kwargs:
                for k, v in browser_kwargs.items():
                    if hasattr(config.browser, k):
                        setattr(config.browser, k, v)
        
        config._validate()
        return config
    
    def _validate(self):
        """Validate configuration values."""
        from .exceptions import ConfigurationError
        
        # Validate base_url
        if not self.base_url:
            raise ConfigurationError("base_url cannot be empty")
        
        # Sub-configs validate themselves in __post_init__
        # This method is kept for backward compatibility and additional cross-config validation
        if self.screenshots.format not in ['png', 'jpeg']:
            raise ValueError(f"Invalid screenshot format: {self.screenshots.format}. Must be: png, jpeg")
        
        # Validate browser
        if self.browser.timeout < 0:
            raise ValueError("browser.timeout must be >= 0")
        
        if 'width' not in self.browser.viewport or 'height' not in self.browser.viewport:
            raise ValueError("browser.viewport must have 'width' and 'height'")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            'base_url': self.base_url,
            'cursor': asdict(self.cursor),
            # 'video' removed - use extensions/video instead
            'screenshots': asdict(self.screenshots),
            'browser': {
                **asdict(self.browser),
                'viewport': self.browser.viewport,
            },
        }
    
    def save(self, path: Union[str, Path], format: str = 'yaml'):
        """
        Save configuration to file.
        
        Args:
            path: Path to save config file
            format: Format to save ('yaml' or 'json')
        """
        path = Path(path)
        data = self.to_dict()
        
        if format == 'yaml':
            if not YAML_AVAILABLE:
                raise ImportError("PyYAML is required for YAML config files. Install with: pip install pyyaml")
            with open(path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        elif format == 'json':
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, sort_keys=False)
        else:
            raise ValueError(f"Unsupported format: {format}. Must be 'yaml' or 'json'")


