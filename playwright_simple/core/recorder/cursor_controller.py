#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cursor Controller (Legacy - redirects to new modular structure).

This file is kept for backward compatibility.
All functionality has been moved to playwright_simple/core/recorder/cursor_controller/ module.
"""

# Import from new modular structure
from playwright_simple.core.recorder.cursor_controller.controller import CursorController

__all__ = ['CursorController']
