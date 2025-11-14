#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cursor Visual Module.

Handles visual aspects of the cursor (injection, show/hide, styling).
"""

import logging
from playwright.async_api import Page

logger = logging.getLogger(__name__)


class CursorVisual:
    """Handles visual aspects of the cursor."""
    
    def __init__(self, page: Page):
        """Initialize cursor visual."""
        self.page = page
        self.is_active = False
    
    async def start(self, force: bool = False, initial_x: int = None, initial_y: int = None):
        """
        Start cursor controller and inject cursor overlay.
        
        Args:
            force: Force reinjection even if already active
            initial_x: Initial X position (None = center of screen)
            initial_y: Initial Y position (None = center of screen)
        """
        if self.is_active and not force:
            # Still ensure cursor is visible
            await self.show()
            return
        
        try:
            # Wait for page to be ready using dynamic waits
            try:
                # Wait for DOM to be ready (with reasonable timeout for slow connections)
                await self.page.wait_for_load_state('domcontentloaded', timeout=10000)
            except Exception as e:
                logger.debug(f"DOM ready timeout in cursor start, continuing: {e}")
                # Try to wait for at least document.readyState as fallback
                try:
                    await self.page.wait_for_function(
                        "document.readyState === 'interactive' || document.readyState === 'complete'",
                        timeout=5000
                    )
                except:
                    pass  # Continue even if timeout
            
            # Get viewport size to calculate center
            viewport = self.page.viewport_size
            if viewport:
                screen_center_x = viewport['width'] // 2
                screen_center_y = viewport['height'] // 2
            else:
                # Fallback if viewport not available
                screen_center_x = 960  # Default 1920x1080 center
                screen_center_y = 540
            
            # Use provided position or center of screen
            cursor_x = initial_x if initial_x is not None else screen_center_x
            cursor_y = initial_y if initial_y is not None else screen_center_y
            
            # Try to get last cursor position from window storage (for navigation persistence)
            last_position = await self.page.evaluate("""
                () => {
                    return window.__playwright_cursor_last_position || null;
                }
            """)
            
            # If we have a last position and no explicit initial position, use it
            if last_position and initial_x is None and initial_y is None:
                cursor_x = last_position.get('x', cursor_x)
                cursor_y = last_position.get('y', cursor_y)
            
            # Store position for next navigation
            await self.page.evaluate(f"""
                () => {{
                    window.__playwright_cursor_last_position = {{
                        x: {cursor_x},
                        y: {cursor_y}
                    }};
                }}
            """)
            
            # Reset flag to allow reinjection
            await self.page.evaluate("""
                () => {
                    window.__playwright_cursor_initialized = false;
                }
            """)
            
            script = """
                (function() {{
                    // Always recreate cursor (in case of navigation)
                    const existing = document.getElementById('__playwright_cursor');
                    if (existing) existing.remove();
                    const existingClick = document.getElementById('__playwright_cursor_click');
                    if (existingClick) existingClick.remove();
                    const existingStyle = document.getElementById('__playwright_cursor_style');
                    if (existingStyle) existingStyle.remove();
                    
                    // Create cursor overlay
                    const cursor = document.createElement('div');
                    cursor.id = '__playwright_cursor';
                    cursor.style.cssText = `
                        position: fixed;
                        width: 0;
                        height: 0;
                        border-left: 8px solid transparent;
                        border-right: 8px solid transparent;
                        border-top: 12px solid #0066ff;
                        pointer-events: none;
                        z-index: 999999;
                        transform: translate(-50%, -50%);
                        display: block;
                        left: {cursor_x}px;
                        top: {cursor_y}px;
                        filter: drop-shadow(0 0 3px rgba(0, 102, 255, 0.8));
                    `;
                    
                    // Create click indicator
                    const clickIndicator = document.createElement('div');
                    clickIndicator.id = '__playwright_cursor_click';
                    clickIndicator.style.cssText = `
                        position: fixed;
                        width: 30px;
                        height: 30px;
                        border: 3px solid #0066ff;
                        border-radius: 50%;
                        pointer-events: none;
                        z-index: 999998;
                        transform: translate(-50%, -50%);
                        display: none;
                        animation: cursorClick 0.3s ease-out;
                    `;
                    
                    // Add click animation
                    let style = document.getElementById('__playwright_cursor_style');
                    if (!style) {{
                        style = document.createElement('style');
                        style.id = '__playwright_cursor_style';
                        style.textContent = `
                            @keyframes cursorClick {{
                                0% {{
                                    transform: translate(-50%, -50%) scale(0.5);
                                    opacity: 1;
                                }}
                                100% {{
                                    transform: translate(-50%, -50%) scale(2);
                                    opacity: 0;
                                }}
                            }}
                        `;
                        document.head.appendChild(style);
                    }}
                    
                    document.body.appendChild(cursor);
                    document.body.appendChild(clickIndicator);
                    
                    // Store cursor element
                    window.__playwright_cursor_element = cursor;
                    window.__playwright_cursor_click_element = clickIndicator;
                    window.__playwright_cursor_initialized = true;
                    window.__playwright_cursor_last_position = {{
                        x: {cursor_x},
                        y: {cursor_y}
                    }};
                    console.log('[Playwright Cursor] Injected and initialized at (' + {cursor_x} + ', ' + {cursor_y} + ').');
                }})();
            """.format(cursor_x=cursor_x, cursor_y=cursor_y)
            
            await self.page.evaluate(script)
            self.is_active = True
            logger.info(f"Cursor controller started and injected at ({cursor_x}, {cursor_y})")
        except Exception as e:
            logger.error(f"Error starting cursor controller: {e}")
            self.is_active = False
            raise
    
    async def show(self):
        """Show cursor overlay."""
        try:
            await self.page.evaluate("""
                () => {
                    const cursor = document.getElementById('__playwright_cursor');
                    if (cursor) {
                        cursor.style.display = 'block';
                    }
                }
            """)
        except Exception as e:
            logger.debug(f"Error showing cursor: {e}")
    
    async def hide(self):
        """Hide cursor overlay."""
        try:
            await self.page.evaluate("""
                () => {
                    const cursor = document.getElementById('__playwright_cursor');
                    if (cursor) {
                        cursor.style.display = 'none';
                    }
                }
            """)
        except Exception as e:
            logger.debug(f"Error hiding cursor: {e}")
    
    async def stop(self):
        """Stop cursor controller."""
        try:
            await self.page.evaluate("""
                () => {
                    const cursor = document.getElementById('__playwright_cursor');
                    if (cursor) cursor.remove();
                    const clickIndicator = document.getElementById('__playwright_cursor_click');
                    if (clickIndicator) clickIndicator.remove();
                    const style = document.getElementById('__playwright_cursor_style');
                    if (style) style.remove();
                    window.__playwright_cursor_initialized = false;
                }
            """)
            self.is_active = False
        except Exception as e:
            logger.debug(f"Error stopping cursor: {e}")

