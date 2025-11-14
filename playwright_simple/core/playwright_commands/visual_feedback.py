#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Visual Feedback Module.

Handles visual feedback for user interactions (cursor movement, click animations).
"""

import asyncio
import logging
from typing import Optional, Tuple
from playwright.async_api import Page

logger = logging.getLogger(__name__)

# Enable debug logging for cursor movements
DEBUG_CURSOR_MOVEMENT = True


class VisualFeedback:
    """Handles visual feedback for interactions."""
    
    def __init__(self, page: Page, fast_mode: bool = False, enable_animations: bool = True):
        """
        Initialize visual feedback.
        
        Args:
            page: Playwright Page instance
            fast_mode: Enable fast mode (reduce delays, but animations can still be enabled)
            enable_animations: Whether to show animations (default: True, even in fast_mode for recording)
        """
        self.page = page
        self.fast_mode = fast_mode
        self.enable_animations = enable_animations
    
    async def show_click_feedback(
        self,
        x: int,
        y: int,
        cursor_controller = None
    ) -> None:
        """
        Show visual feedback for a click.
        
        Args:
            x: X coordinate
            y: Y coordinate
            cursor_controller: Optional CursorController or CursorManager instance
        """
        if cursor_controller:
            try:
                # Check if it's CursorController (has move method) or CursorManager (has move_to method)
                has_move = hasattr(cursor_controller, 'move')
                has_move_to = hasattr(cursor_controller, 'move_to')
                
                if DEBUG_CURSOR_MOVEMENT:
                    logger.info(f"🖱️  [DEBUG] Visual feedback: moving cursor to ({x}, {y})")
                    logger.info(f"🖱️  [DEBUG] Cursor type: has_move={has_move}, has_move_to={has_move_to}, enable_animations={self.enable_animations}")
                
                logger.info(f"🎬 Visual feedback: moving cursor to ({x}, {y}) [has_move={has_move}, has_move_to={has_move_to}, enable_animations={self.enable_animations}]")
                
                if has_move:
                    # CursorController interface
                    if DEBUG_CURSOR_MOVEMENT:
                        logger.info(f"🖱️  [DEBUG] Using CursorController.move({x}, {y}, smooth={self.enable_animations})")
                    await cursor_controller.show()
                    # Move cursor to position (this will save position automatically)
                    # Use smooth animation if animations are enabled (even in fast_mode for recording)
                    await cursor_controller.move(x, y, smooth=self.enable_animations)
                    # Wait for cursor to reach position (only if smooth animation)
                    if self.enable_animations:
                        if DEBUG_CURSOR_MOVEMENT:
                            logger.info(f"🖱️  [DEBUG] Waiting for smooth animation to complete (0.3s)")
                        await asyncio.sleep(0.3)  # Smooth animation takes ~0.3s
                elif has_move_to:
                    # CursorManager interface
                    # Move cursor to position with smooth animation
                    logger.info(f"🎬 Moving cursor using CursorManager.move_to({x}, {y})")
                    if DEBUG_CURSOR_MOVEMENT:
                        logger.info(f"🖱️  [DEBUG] Calling CursorManager.move_to({x}, {y})")
                    await cursor_controller.move_to(x, y)
                    # Wait for cursor to reach position (only if smooth animation)
                    if self.enable_animations:
                        if DEBUG_CURSOR_MOVEMENT:
                            logger.info(f"🖱️  [DEBUG] Waiting for smooth animation to complete (0.3s)")
                    await asyncio.sleep(0.3)  # Smooth animation takes ~0.3s
                    else:
                        # Even without animation, wait a bit for cursor to be positioned
                        await asyncio.sleep(0.1)
                    
                    # Use CursorManager's show_click_effect if available
                    if hasattr(cursor_controller, 'show_click_effect'):
                        logger.info(f"🎬 Showing click effect at ({x}, {y})")
                        if DEBUG_CURSOR_MOVEMENT:
                            logger.info(f"🖱️  [DEBUG] Showing click effect at ({x}, {y})")
                        await cursor_controller.show_click_effect(x, y)
                        if self.enable_animations:
                            await asyncio.sleep(0.1)  # Small delay for animation
                        # Don't return - we still need to ensure mouse is synced
                    # CRITICAL: After moving cursor visual, we need to ensure mouse is synced
                    # This is done by the caller (element_interactions), but we can add a small delay here
                    if DEBUG_CURSOR_MOVEMENT:
                        logger.info(f"🖱️  [DEBUG] Cursor visual moved to ({x}, {y}), waiting for mouse sync")
                
                # Show click animation manually (for CursorController or fallback)
                if self.enable_animations and has_move:  # Only for CursorController
                    animation_duration = 300
                    await self.page.evaluate(f"""
                        () => {{
                            const clickIndicator = document.getElementById('__playwright_cursor_click');
                            if (clickIndicator) {{
                                clickIndicator.style.left = '{x}px';
                                clickIndicator.style.top = '{y}px';
                                clickIndicator.style.display = 'block';
                                setTimeout(() => {{
                                    clickIndicator.style.display = 'none';
                                }}, {animation_duration});
                            }}
                        }}
                    """)
                    await asyncio.sleep(0.1)  # Small delay for animation
                # No delay in fast mode
            except Exception as e:
                logger.debug(f"Error showing cursor feedback: {e}")

