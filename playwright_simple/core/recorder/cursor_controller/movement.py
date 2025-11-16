#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cursor Movement Module.

Handles cursor movement and positioning.
"""

import logging
import asyncio
from playwright.async_api import Page

logger = logging.getLogger(__name__)

# Import SpeedLevel for type hints
try:
    from ..config import SpeedLevel
except ImportError:
    SpeedLevel = None


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
                # Get speed_level from controller
                speed_level = getattr(self.controller, 'speed_level', None)
                
                # Fallback to fast_mode for backward compatibility
                if speed_level is None:
                    fast_mode = getattr(self.controller, 'fast_mode', False)
                    if fast_mode:
                        speed_level = SpeedLevel.FAST if SpeedLevel else None
                    else:
                        speed_level = SpeedLevel.NORMAL if SpeedLevel else None
                
                # Determine animation duration based on speed level
                if speed_level == SpeedLevel.ULTRA_FAST if (SpeedLevel and speed_level) else False:
                    # Ultra fast: minimal animation (50ms) to keep cursor visible
                    animation_duration = 0.05  # 50ms - minimal but visible
                    timeout = 100  # 100ms timeout
                elif speed_level == SpeedLevel.FAST if (SpeedLevel and speed_level) else False:
                    # Fast: shorter animation (50ms)
                    animation_duration = 0.05  # 50ms
                    timeout = 100  # 100ms timeout
                elif speed_level == SpeedLevel.SLOW if (SpeedLevel and speed_level) else False:
                    # Slow: normal animation (for demonstration videos)
                    animation_duration = 0.3  # 300ms
                    timeout = 350  # 350ms timeout
                else:
                    # Normal mode: standard animation
                    animation_duration = 0.3  # 300ms
                    timeout = 350  # 350ms timeout
                
                # Smooth animation to position
                # Use Promise to wait for animation to complete
                animation_duration_str = str(animation_duration)
                timeout_str = str(timeout)
                await self.page.evaluate(f"""
                    () => {{
                        return new Promise((resolve) => {{
                        const cursor = document.getElementById('__playwright_cursor');
                        if (cursor) {{
                                // Set up transition end listener
                                const onTransitionEnd = () => {{
                                    cursor.removeEventListener('transitionend', onTransitionEnd);
                                    cursor.style.transition = 'none';
                                    resolve(true);
                                }};
                                
                                cursor.addEventListener('transitionend', onTransitionEnd);
                                
                                // Start animation
                                cursor.style.transition = 'left {animation_duration_str}s ease-out, top {animation_duration_str}s ease-out';
                            cursor.style.left = '{x}px';
                            cursor.style.top = '{y}px';
                            cursor.style.display = 'block';
                            
                                // Fallback timeout in case transitionend doesn't fire
                            setTimeout(() => {{
                                    cursor.removeEventListener('transitionend', onTransitionEnd);
                                cursor.style.transition = 'none';
                                    resolve(true);
                                }}, {timeout_str});
                            }} else {{
                                resolve(false);
                        }}
                        }});
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
            
            # Log cursor movement (only in debug mode)
            if self.controller.recorder_logger and self.controller.recorder_logger.is_debug:
                self.controller.recorder_logger.log_cursor_movement(
                    x=x,
                    y=y,
                    animation_duration_ms=animation_duration * 1000 if smooth else None
                )
        except Exception as e:
            logger.error(f"Error moving cursor: {e}")

