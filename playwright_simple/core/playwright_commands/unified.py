#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified Command Interface.

Centralized functions for all command operations (click, type, submit, etc.)
used by recording, CLI commands, and YAML replay.

This ensures that all code paths use exactly the same implementation.
"""

import logging
from typing import Optional, Dict, Any, Callable
from playwright.async_api import Page

logger = logging.getLogger(__name__)

# Try to import PlaywrightCommands
try:
    from .commands import PlaywrightCommands
    PLAYWRIGHT_COMMANDS_AVAILABLE = True
except ImportError:
    PlaywrightCommands = None
    PLAYWRIGHT_COMMANDS_AVAILABLE = False
    logger.warning("PlaywrightCommands not available")


def get_playwright_commands(
    page: Page,
    fast_mode: bool = False,
    cache_key: Optional[Any] = None,
    cache: Optional[Dict[Any, PlaywrightCommands]] = None
) -> Optional['PlaywrightCommands']:
    """
    Get or create PlaywrightCommands instance with consistent parameters.
    
    This is the SINGLE source of truth for creating PlaywrightCommands instances.
    All code should use this function instead of creating instances directly.
    
    Args:
        page: Playwright Page instance
        fast_mode: Enable fast mode (reduce delays, instant animations)
        cache_key: Optional key for caching (e.g., test instance)
        cache: Optional cache dictionary to store instances
    
    Returns:
        PlaywrightCommands instance or None if not available
    """
    if not PLAYWRIGHT_COMMANDS_AVAILABLE:
        logger.warning("PlaywrightCommands not available")
        return None
    
    if not page:
        logger.warning("Page not available for PlaywrightCommands")
        return None
    
    # Check cache if provided
    if cache is not None and cache_key is not None:
        if cache_key in cache:
            logger.debug("Reusing cached PlaywrightCommands instance")
            return cache[cache_key]
    
    # Create new instance with consistent parameters
    try:
        commands = PlaywrightCommands(page, fast_mode=fast_mode)
        logger.debug(f"Created PlaywrightCommands instance (fast_mode={fast_mode})")
        
        # Cache if provided
        if cache is not None and cache_key is not None:
            cache[cache_key] = commands
        
        return commands
    except Exception as e:
        logger.error(f"Error creating PlaywrightCommands: {e}", exc_info=True)
        return None


def parse_click_args(args: str) -> Dict[str, Any]:
    """
    Parse click command arguments consistently.
    
    Supports formats:
    - "text" -> text="text"
    - "selector #id" -> selector="#id"
    - "role button" -> role="button"
    - "text[0]" -> text="text", index=0
    
    Args:
        args: Command arguments string
    
    Returns:
        Dictionary with parsed arguments: {text, selector, role, index}
    """
    if not args:
        return {'text': None, 'selector': None, 'role': None, 'index': 0}
    
    args = args.strip()
    index = 0
    
    # Parse index if present (e.g., "text[0]")
    if '[' in args and ']' in args:
        try:
            index_part = args[args.index('[')+1:args.index(']')]
            index = int(index_part)
            args = args[:args.index('[')].strip()
        except (ValueError, IndexError):
            pass
    
    # Parse format prefix
    if args.startswith('selector '):
        selector = args[9:].strip().strip('"\'')
        return {'text': None, 'selector': selector, 'role': None, 'index': index}
    elif args.startswith('role '):
        role = args[5:].strip().strip('"\'')
        return {'text': None, 'selector': None, 'role': role, 'index': index}
    else:
        # Treat as text
        text = args.strip('"\'')
        return {'text': text, 'selector': None, 'role': None, 'index': index}


async def unified_click(
    page: Page,
    text: Optional[str] = None,
    selector: Optional[str] = None,
    role: Optional[str] = None,
    index: int = 0,
    cursor_controller = None,
    fast_mode: bool = False,
    description: str = "",
    cache_key: Optional[Any] = None,
    cache: Optional[Dict[Any, PlaywrightCommands]] = None
) -> bool:
    """
    Unified click function used by ALL click operations.
    
    This ensures that recording, CLI commands, and YAML replay
    all use exactly the same code path.
    
    Args:
        page: Playwright Page instance
        text: Text content to search for
        selector: CSS selector
        role: ARIA role
        index: Index if multiple matches
        cursor_controller: Optional cursor controller for visual feedback
        fast_mode: Enable fast mode
        description: Optional description for logging
        cache_key: Optional key for caching PlaywrightCommands
        cache: Optional cache dictionary
    
    Returns:
        True if clicked successfully, False otherwise
    """
    if not page:
        logger.error("Page not available for unified_click")
        return False
    
    # Get PlaywrightCommands instance (cached if possible)
    commands = get_playwright_commands(page, fast_mode=fast_mode, cache_key=cache_key, cache=cache)
    if not commands:
        logger.error("Failed to get PlaywrightCommands for unified_click")
        return False
    
    # Call the same click method used everywhere
    try:
        result = await commands.click(
            text=text,
            selector=selector,
            role=role,
            index=index,
            cursor_controller=cursor_controller,
            description=description
        )
        logger.debug(f"unified_click result: {result} (text={text}, selector={selector}, role={role})")
        return result
    except Exception as e:
        logger.error(f"Error in unified_click: {e}", exc_info=True)
        return False


def parse_type_args(args: str) -> Dict[str, Any]:
    """
    Parse type command arguments consistently.
    
    Supports formats:
    - "text into field" -> text="text", into="field"
    - "text selector #id" -> text="text", selector="#id"
    - "text" -> text="text" (no field)
    
    Args:
        args: Command arguments string
    
    Returns:
        Dictionary with parsed arguments: {text, into, selector}
    """
    if not args:
        return {'text': None, 'into': None, 'selector': None}
    
    args = args.strip()
    
    # Normalize --into to into
    if ' --into ' in args or ' --into' in args:
        args = args.replace('--into', 'into')
    
    # Check for "into" keyword
    if ' into ' in args.lower():
        parts = args.split(' into ', 1)
        if len(parts) == 2:
            text = parts[0].strip().strip('"\'')
            field = parts[1].strip().strip('"\'')
            
            if field.startswith('selector '):
                selector = field[9:].strip().strip('"\'')
                return {'text': text, 'into': None, 'selector': selector}
            else:
                return {'text': text, 'into': field, 'selector': None}
    
    # No "into" - just text
    text = args.strip('"\'')
    return {'text': text, 'into': None, 'selector': None}


async def unified_type(
    page: Page,
    text: str,
    into: Optional[str] = None,
    selector: Optional[str] = None,
    clear: bool = True,
    cursor_controller = None,
    fast_mode: bool = False,
    cache_key: Optional[Any] = None,
    cache: Optional[Dict[Any, PlaywrightCommands]] = None
) -> bool:
    """
    Unified type function used by ALL type operations.
    
    This ensures that recording, CLI commands, and YAML replay
    all use exactly the same code path.
    
    Args:
        page: Playwright Page instance
        text: Text to type
        into: Text label of the input field
        selector: CSS selector of the input field
        clear: Clear field before typing
        cursor_controller: Optional cursor controller for visual feedback
        fast_mode: Enable fast mode
        cache_key: Optional key for caching PlaywrightCommands
        cache: Optional cache dictionary
    
    Returns:
        True if typed successfully, False otherwise
    """
    if not page:
        logger.error("Page not available for unified_type")
        return False
    
    if not text:
        logger.error("Text is required for unified_type")
        return False
    
    # Get PlaywrightCommands instance (cached if possible)
    commands = get_playwright_commands(page, fast_mode=fast_mode, cache_key=cache_key, cache=cache)
    if not commands:
        logger.error("Failed to get PlaywrightCommands for unified_type")
        return False
    
    # Call the same type_text method used everywhere
    try:
        result = await commands.type_text(
            text=text,
            into=into,
            selector=selector,
            clear=clear,
            cursor_controller=cursor_controller
        )
        logger.debug(f"unified_type result: {result} (text={text}, into={into}, selector={selector})")
        return result
    except Exception as e:
        logger.error(f"Error in unified_type: {e}", exc_info=True)
        return False


async def unified_submit(
    page: Page,
    button_text: Optional[str] = None,
    cursor_controller = None,
    fast_mode: bool = False,
    cache_key: Optional[Any] = None,
    cache: Optional[Dict[Any, PlaywrightCommands]] = None
) -> bool:
    """
    Unified submit function used by ALL submit operations.
    
    This ensures that recording, CLI commands, and YAML replay
    all use exactly the same code path.
    
    Args:
        page: Playwright Page instance
        button_text: Optional text to identify specific submit button
        cursor_controller: Optional cursor controller for visual feedback
        fast_mode: Enable fast mode
        cache_key: Optional key for caching PlaywrightCommands
        cache: Optional cache dictionary
    
    Returns:
        True if form was submitted successfully, False otherwise
    """
    if not page:
        logger.error("Page not available for unified_submit")
        return False
    
    # Get PlaywrightCommands instance (cached if possible)
    commands = get_playwright_commands(page, fast_mode=fast_mode, cache_key=cache_key, cache=cache)
    if not commands:
        logger.error("Failed to get PlaywrightCommands for unified_submit")
        return False
    
    # Call the same submit_form method used everywhere
    try:
        result = await commands.submit_form(
            button_text=button_text,
            cursor_controller=cursor_controller
        )
        logger.debug(f"unified_submit result: {result} (button_text={button_text})")
        return result
    except Exception as e:
        logger.error(f"Error in unified_submit: {e}", exc_info=True)
        return False

