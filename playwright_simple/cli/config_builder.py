#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Config Builder from CLI Arguments.

Builds TestConfig from command-line arguments.
"""

import argparse
from pathlib import Path
from typing import Optional

from playwright_simple import TestConfig
from playwright_simple.core.logger import get_logger, set_logger, StructuredLogger
from .parser import parse_viewport


def create_config_from_args(args: argparse.Namespace) -> TestConfig:
    """Create TestConfig from command-line arguments."""
    # Load base config from file if provided
    if args.config:
        config = TestConfig.from_file(args.config)
    else:
        config = TestConfig()
    
    # Override with CLI arguments
    
    # Base URL
    if args.base_url:
        config.base_url = args.base_url
    
    # Logging - Always set logger with CLI level
    logger = StructuredLogger(
        name="playwright_simple",
        level=args.log_level,
        log_file=Path(args.log_file) if args.log_file else None,
        json_log=args.json_log,
        console_output=not args.no_console_log
    )
    set_logger(logger)
    
    # Browser
    if args.headless:
        config.browser.headless = True
    elif args.no_headless:
        config.browser.headless = False
    
    if args.viewport:
        config.browser.viewport = parse_viewport(args.viewport)
    
    if args.slow_mo is not None:
        config.browser.slow_mo = args.slow_mo
    
    if args.timeout is not None:
        config.browser.timeout = args.timeout
    
    # Video
    if args.video:
        config.video.enabled = True
    elif args.no_video:
        config.video.enabled = False
    
    if args.video_quality:
        config.video.quality = args.video_quality
    
    if args.video_codec:
        config.video.codec = args.video_codec
    
    if args.video_speed is not None:
        config.video.speed = args.video_speed
    
    if args.video_dir:
        config.video.dir = args.video_dir
    
    # Audio
    if args.audio:
        config.video.audio = True
        config.video.narration = True
    elif args.no_audio:
        config.video.audio = False
        config.video.narration = False
    
    if args.audio_lang:
        config.video.audio_lang = args.audio_lang
        config.video.narration_lang = args.audio_lang
    
    if args.audio_engine:
        config.video.audio_engine = args.audio_engine
    
    if args.audio_slow:
        config.video.audio_slow = True
    
    # Subtitles
    if args.subtitles:
        config.video.subtitles = True
    elif args.no_subtitles:
        config.video.subtitles = False
    
    if args.hard_subtitles:
        config.video.hard_subtitles = True
    
    # Debug
    if args.debug:
        config.debug.enabled = True
    
    if args.screenshot_on_failure:
        config.debug.screenshot_on_failure = True
    
    if args.pause_on_failure:
        config.debug.pause_on_failure = True
    
    return config

