#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command Handlers (Legacy - redirects to new modular structure).

This file is kept for backward compatibility.
All functionality has been moved to playwright_simple/core/recorder/command_handlers/ module.
"""

# Import from new modular structure
from playwright_simple.core.recorder.command_handlers.handlers import CommandHandlers

__all__ = ['CommandHandlers']
