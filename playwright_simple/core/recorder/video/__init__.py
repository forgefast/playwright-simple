#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Video processing module for recorder.

Provides functionality for processing videos: subtitles, audio embedding, and cleanup.
"""

from .processor import VideoProcessor
from .subtitles import SubtitleGenerator
from .audio_embedder import AudioEmbedder

__all__ = [
    'VideoProcessor',
    'SubtitleGenerator',
    'AudioEmbedder'
]

