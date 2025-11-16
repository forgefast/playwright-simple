#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Subtitle extension for playwright-simple.

Provides subtitle generation functionality as an optional extension.
"""

from .extension import SubtitleExtension
from .config import SubtitleConfig
from .generator import SubtitleGenerator

__all__ = ['SubtitleExtension', 'SubtitleConfig', 'SubtitleGenerator']

