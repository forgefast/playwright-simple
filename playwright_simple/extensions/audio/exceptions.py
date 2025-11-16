#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audio extension exceptions.
"""

from ...core.exceptions import PlaywrightSimpleError


class TTSGenerationError(PlaywrightSimpleError):
    """
    Raised when TTS (Text-to-Speech) generation fails.
    
    This exception is raised when TTS audio generation fails (e.g., API errors,
    file system errors, unsupported languages).
    """
    pass

