#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cursor movement and animation.

Contains methods for moving the cursor with smooth animations.
"""

import asyncio
from playwright.async_api import Page

from .config import CursorConfig
from .constants import (
    CURSOR_ELEMENT_ID,
    CURSOR_Z_INDEX,
    CURSOR_ANIMATION_MIN_DURATION,
    CURSOR_AFTER_MOVE_DELAY,
    DEFAULT_VIEWPORT_WIDTH,
    DEFAULT_VIEWPORT_HEIGHT,
)


class CursorMovement:
    """Helper class for cursor movement and animation."""
    
    def __init__(self, page: Page, config: CursorConfig):
        """
        Initialize cursor movement helper.
        
        Args:
            page: Playwright page instance
            config: Cursor configuration
        """
        self.page = page
        self.config = config
    
    async def move_to(self, x: float, y: float) -> None:
        """
        Move cursor to position with smooth animation.
        
        Args:
            x: X coordinate
            y: Y coordinate
        """
        # Get viewport for default position
        viewport = self.page.viewport_size or {
            "width": DEFAULT_VIEWPORT_WIDTH,
            "height": DEFAULT_VIEWPORT_HEIGHT
        }
        default_x = viewport['width'] / 2
        default_y = viewport['height'] / 2
        
        # Get current cursor position first - use actual position, not default
        cursor_id = CURSOR_ELEMENT_ID
        current_pos = await self.page.evaluate(f"""
            (function() {{
                const cursor = document.getElementById('{cursor_id}');
                if (cursor) {{
                    let left = parseFloat(cursor.style.left);
                    let top = parseFloat(cursor.style.top);
                    if (isNaN(left) || left === 0) {{
                        const rect = cursor.getBoundingClientRect();
                        left = rect.left + rect.width / 2;
                    }}
                    if (isNaN(top) || top === 0) {{
                        const rect = cursor.getBoundingClientRect();
                        top = rect.top + rect.height / 2;
                    }}
                    if (isNaN(left) || left === 0) {{
                        left = window.innerWidth / 2;
                    }}
                    if (isNaN(top) || top === 0) {{
                        top = window.innerHeight / 2;
                    }}
                    return {{x: left, y: top, exists: true}};
                }}
                return {{x: 0, y: 0, exists: false}};
            }})();
        """)
        
        if not current_pos.get('exists'):
            current_pos = {'x': default_x, 'y': default_y}
        
        # Use actual position - don't default to center if position is valid
        current_x = current_pos.get('x', default_x)
        current_y = current_pos.get('y', default_y)
        
        # Move cursor with smooth animation - use Promise to wait for completion
        # Use a minimum duration to ensure movement is visible in videos (but fast enough)
        min_duration = max(self.config.animation_speed, CURSOR_ANIMATION_MIN_DURATION)
        
        cursor_id = CURSOR_ELEMENT_ID
        result = await self.page.evaluate(f"""
            (function() {{
                const cursor = document.getElementById('{cursor_id}');
                if (!cursor) {{
                    return Promise.resolve({{success: false, error: 'Cursor not found'}});
                }}
                
                const currentX = {current_x};
                const currentY = {current_y};
                const targetX = {x};
                const targetY = {y};
                
                // Ensure cursor is visible and on top
                cursor.style.display = 'block';
                cursor.style.visibility = 'visible';
                cursor.style.opacity = '1';
                cursor.style.zIndex = '{CURSOR_Z_INDEX}';
                cursor.style.pointerEvents = 'none';
                
                // Animate movement with requestAnimationFrame and return Promise
                const duration = {min_duration} * 1000;
                const startTime = performance.now();
                
                return new Promise((resolve) => {{
                    function animate() {{
                        const elapsed = performance.now() - startTime;
                        const progress = Math.min(elapsed / duration, 1);
                        
                        // Ease-out cubic for smooth movement
                        const easeOut = 1 - Math.pow(1 - progress, 3);
                        
                        const posX = currentX + (targetX - currentX) * easeOut;
                        const posY = currentY + (targetY - currentY) * easeOut;
                        
                        // Update cursor position
                        cursor.style.left = posX + 'px';
                        cursor.style.top = posY + 'px';
                        
                        // Force reflow to ensure position is updated
                        cursor.offsetHeight;
                        
                        if (progress < 1) {{
                            requestAnimationFrame(animate);
                        }} else {{
                            // Final position - ensure exact target
                            cursor.style.left = targetX + 'px';
                            cursor.style.top = targetY + 'px';
                            cursor.offsetHeight; // Force reflow
                            resolve({{success: true, completed: true}});
                        }}
                    }}
                    
                    // Start animation
                    requestAnimationFrame(animate);
                }});
            }})();
        """)
        
        # Wait for animation to complete - the JavaScript Promise will resolve when done
        # Add a minimal buffer to ensure animation is fully rendered in video
        await asyncio.sleep(CURSOR_AFTER_MOVE_DELAY)

