#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Text-to-Speech (TTS) module for playwright-simple.

This file is kept for backward compatibility.
The actual implementation has been moved to tts/manager.py.
"""

# Import from new structure for backward compatibility
from .tts import TTSManager

__all__ = ['TTSManager']
