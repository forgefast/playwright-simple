#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cursor Movement Module.

Handles cursor movement and positioning.
"""

import logging
from playwright.async_api import Page

logger = logging.getLogger(__name__)


class CursorMovement:
    """Handles cursor movement."""
    
    def __init__(self, page: Page, controller):
        """Initialize cursor movement."""
        self.page = page
        self.controller = controller
        self.current_x = 0
        self.current_y = 0
    
    async def move(self, x: int, y: int, smooth: bool = True):
        """Move cursor to position."""
        try:
            self.current_x = x
            self.current_y = y
            
            # Store position for persistence across navigations
            # Use both window property and sessionStorage for reliability
            await self.page.evaluate(f"""
                () => {{
                    const position = {{
                        x: {x},
                        y: {y}
                    }};
                    window.__playwright_cursor_last_position = position;
                    // Also store in sessionStorage for persistence across navigations
                    try {{
                        sessionStorage.setItem('__playwright_cursor_last_position', JSON.stringify(position));
                    }} catch (e) {{
                        // sessionStorage might not be available in some contexts
                    }}
                }}
            """)
            
            # Ensure cursor is initialized and visible when moving
            if not self.controller.is_active:
                await self.controller.start()
            await self.controller.show()
            
            if smooth:
                # Smooth animation to position
                await self.page.evaluate(f"""
                    () => {{
                        const cursor = document.getElementById('__playwright_cursor');
                        if (cursor) {{
                            cursor.style.transition = 'left 0.3s ease-out, top 0.3s ease-out';
                            cursor.style.left = '{x}px';
                            cursor.style.top = '{y}px';
                            cursor.style.display = 'block';
                            
                            // Remove transition after animation
                            setTimeout(() => {{
                                cursor.style.transition = 'none';
                            }}, 300);
                        }}
                    }}
                """)
            else:
                # Instant move
                await self.page.evaluate(f"""
                    () => {{
                        const cursor = document.getElementById('__playwright_cursor');
                        if (cursor) {{
                            cursor.style.left = '{x}px';
                            cursor.style.top = '{y}px';
                            cursor.style.display = 'block';
                        }}
                    }}
                """)
            logger.debug(f"Cursor moved to ({x}, {y})")
        except Exception as e:
            logger.error(f"Error moving cursor: {e}")

