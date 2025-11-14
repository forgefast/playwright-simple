#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug extension configuration.
"""

from dataclasses import dataclass
from typing import Optional, List
from pathlib import Path


@dataclass
class DebugConfig:
    """Configuration for debug extension."""
    enabled: bool = True
    pause_on_error: bool = True
    pause_on_element_not_found: bool = True
    pause_on_navigation_error: bool = True
    interactive_mode: bool = True
    save_state_on_error: bool = True
    state_dir: str = "debug_states"
    html_snapshot_dir: str = "debug_html"
    checkpoint_dir: str = "debug_checkpoints"
    hot_reload_enabled: bool = True
    yaml_watch_enabled: bool = True
    
    def __post_init__(self):
        """Validate configuration."""
        # Create directories
        Path(self.state_dir).mkdir(parents=True, exist_ok=True)
        Path(self.html_snapshot_dir).mkdir(parents=True, exist_ok=True)
        Path(self.checkpoint_dir).mkdir(parents=True, exist_ok=True)

