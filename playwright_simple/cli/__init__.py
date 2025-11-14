"""
CLI module for playwright-simple.

Refactored into smaller, more maintainable modules.
"""

from .main import main
from .parser import create_parser
from .command_handlers import handle_command_commands

__all__ = ['main', 'create_parser', 'handle_command_commands']

