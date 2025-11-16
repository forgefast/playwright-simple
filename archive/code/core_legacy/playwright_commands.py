#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Playwright Direct Commands Interface (Legacy - redirects to new modular structure).

This file is kept for backward compatibility.
All functionality has been moved to playwright_simple/core/playwright_commands/ module.
"""

# Import from new modular structure
from playwright_simple.core.playwright_commands.commands import PlaywrightCommands, create_commands

__all__ = ['PlaywrightCommands', 'create_commands']
