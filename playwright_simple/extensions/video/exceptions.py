#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Video extension exceptions.
"""

from ...core.exceptions import PlaywrightSimpleError


class VideoProcessingError(PlaywrightSimpleError):
    """
    Raised when video processing fails.
    
    This exception is raised when video recording, processing, or conversion
    fails (e.g., FFmpeg errors, file system errors).
    """
    pass

