#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audio extension for playwright-simple.

Provides text-to-speech (TTS) functionality as an optional extension.
"""

from .extension import AudioExtension
from .config import AudioConfig
from .exceptions import TTSGenerationError
from .tts import TTSManager

__all__ = ['AudioExtension', 'AudioConfig', 'TTSGenerationError', 'TTSManager']

