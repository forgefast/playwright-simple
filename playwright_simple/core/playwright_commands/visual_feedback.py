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


class VisualFeedback:
    """Handles visual feedback for interactions."""
    
    def __init__(self, page: Page, fast_mode: bool = False):
        """Initialize visual feedback."""
        self.page = page
        self.fast_mode = fast_mode
    
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
            cursor_controller: Optional CursorController instance
        """
        if cursor_controller:
            try:
                await cursor_controller.show()
                # Move cursor to position (this will save position automatically)
                # In fast mode, use instant movement instead of smooth animation
                await cursor_controller.move(x, y, smooth=not self.fast_mode)
                # Wait for cursor to reach position (only if smooth animation)
                if not self.fast_mode:
                    await asyncio.sleep(0.3)  # Smooth animation takes ~0.3s
                # No delay in fast mode - instant movement
                
                # Show click animation (skip in fast mode for speed)
                if not self.fast_mode:
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

