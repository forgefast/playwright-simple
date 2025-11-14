#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Video extension for playwright-simple.

Provides video recording functionality as an optional extension.
"""

from .extension import VideoExtension
from .config import VideoConfig
from .exceptions import VideoProcessingError

__all__ = ['VideoExtension', 'VideoConfig', 'VideoProcessingError']

