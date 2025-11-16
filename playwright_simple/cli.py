#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI Entry Point (Legacy - redirects to new modular CLI).

This file is kept for backward compatibility.
All functionality has been moved to playwright_simple/cli/ module.
"""

# Import from new modular structure
from playwright_simple.cli.main import main
from playwright_simple.cli.parser import create_parser
from playwright_simple.cli.command_handlers import handle_command_commands

__all__ = ['main', 'create_parser', 'handle_command_commands']

# Re-export for backward compatibility
if __name__ == '__main__':
    main()
