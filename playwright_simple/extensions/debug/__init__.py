#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug extension for playwright-simple.

Provides advanced debugging capabilities:
- Pause on errors
- HTML inspection
- Hot reload of YAML
- Continue from checkpoint
- Element inspector
"""

from .extension import DebugExtension
from .config import DebugConfig

__all__ = ['DebugExtension', 'DebugConfig']

