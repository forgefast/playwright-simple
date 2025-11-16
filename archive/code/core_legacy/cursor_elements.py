#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Element management for cursor system.

Contains methods for creating, removing, and managing cursor DOM elements.
"""

import logging
import logging
from typing import Dict, Any
from playwright.async_api import Page

from .config import CursorConfig

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)
from .constants import (
    CURSOR_ELEMENT_ID,
    CLICK_EFFECT_ELEMENT_ID,
    HOVER_EFFECT_ELEMENT_ID,
    CURSOR_Z_INDEX,
    DEFAULT_VIEWPORT_WIDTH,
    DEFAULT_VIEWPORT_HEIGHT,
)
from .cursor_styles import CursorStyles


class CursorElements:
    """Helper class for managing cursor DOM elements."""
    
    def __init__(self, page: Page, config: CursorConfig):
        """
        Initialize cursor elements helper.
        
        Args:
            page: Playwright page instance
            config: Cursor configuration
        """
        self.page = page
        self.config = config
    
    async def remove_duplicate_cursors(self) -> Dict[str, Any]:
        """
        Remove all duplicate cursors, keeping only the first one.
        
        This is an atomic operation that ensures only one cursor exists.
        IMPORTANT: Only removes elements with CURSOR_ELEMENT_ID, not click/hover effects.
        Returns information about what was removed.
        """
        result = await self.page.evaluate(f"""
            (function() {{
                const CURSOR_ID = '{CURSOR_ELEMENT_ID}';
                const CLICK_EFFECT_ID = '{CLICK_EFFECT_ELEMENT_ID}';
                const HOVER_EFFECT_ID = '{HOVER_EFFECT_ELEMENT_ID}';
                
                // Only look for cursor elements, NOT click/hover effects
                const cursors = document.querySelectorAll('#' + CURSOR_ID);
                if (cursors.length > 1) {{
                    // Keep only the first one (most likely the original)
                    const firstCursor = cursors[0];
                    // Ensure first cursor is visible and on top
                    firstCursor.style.display = 'block';
                    firstCursor.style.visibility = 'visible';
                    firstCursor.style.opacity = '1';
                    firstCursor.style.zIndex = '{CURSOR_Z_INDEX}';
                    
                    // Remove all duplicates
                    for (let i = 1; i < cursors.length; i++) {{
                        cursors[i].remove();
                    }}
                    return {{removed: cursors.length - 1, kept: 1}};
                }} else if (cursors.length === 1) {{
                    // Ensure the single cursor is visible and on top
                    const cursor = cursors[0];
                    cursor.style.display = 'block';
                    cursor.style.visibility = 'visible';
                    cursor.style.opacity = '1';
                    cursor.style.zIndex = '{CURSOR_Z_INDEX}';
                }}
                return {{removed: 0, kept: cursors.length}};
            }})();
        """)
        
        return result
    
    async def ensure_cursor_exists(self) -> None:
        """Ensure cursor elements exist on current page."""
        # Remove duplicates if any exist
        await self.remove_duplicate_cursors()
        
        viewport = self.page.viewport_size or {
            "width": DEFAULT_VIEWPORT_WIDTH,
            "height": DEFAULT_VIEWPORT_HEIGHT
        }
        center_x = viewport['width'] / 2
        center_y = viewport['height'] / 2
        
        # Try to get saved cursor position from storage (for navigation persistence)
        # This helps maintain cursor position across navigations
        saved_pos = await self.page.evaluate(f"""
            (function() {{
                // Try sessionStorage first (more reliable across navigations)
                try {{
                    const stored = sessionStorage.getItem('__playwright_cursor_last_position');
                    if (stored) {{
                        const pos = JSON.parse(stored);
                        if (pos.x && pos.y) {{
                            return {{x: pos.x, y: pos.y, exists: true, source: 'sessionStorage'}};
                        }}
                    }}
                }} catch (e) {{
                    // sessionStorage might not be available
                }}
                // Fallback to window property
                if (window.__playwright_cursor_last_position) {{
                    const pos = window.__playwright_cursor_last_position;
                    if (pos.x && pos.y) {{
                        return {{x: pos.x, y: pos.y, exists: true, source: 'window'}};
                    }}
                }}
                // Try to get current cursor position from DOM
                const CURSOR_ID = '{CURSOR_ELEMENT_ID}';
                const cursor = document.getElementById(CURSOR_ID);
                if (cursor) {{
                    const rect = cursor.getBoundingClientRect();
                    const left = parseFloat(cursor.style.left) || rect.left;
                    const top = parseFloat(cursor.style.top) || rect.top;
                    // Only return if position is valid (not 0,0 or NaN)
                    if (!isNaN(left) && !isNaN(top) && left > 0 && top > 0) {{
                        return {{x: left, y: top, exists: true, source: 'dom'}};
                    }}
                }}
                return {{x: 0, y: 0, exists: false}};
            }})();
        """)
        
        # Use saved position if available, otherwise use center
        if saved_pos.get('exists'):
            initial_x = saved_pos.get('x', center_x)
            initial_y = saved_pos.get('y', center_y)
        else:
            initial_x = center_x
            initial_y = center_y
        
        cursor_style = CursorStyles.get_cursor_css(self.config)
        click_effect_style = CursorStyles.get_click_effect_css(self.config)
        
        # Always try to create/ensure cursor exists
        await self.page.evaluate(f"""
            (function() {{
                const centerX = {center_x};
                const centerY = {center_y};
                const initialX = {initial_x};
                const initialY = {initial_y};
                const cursorStyle = `{cursor_style}`;
                const clickEffectStyle = `{click_effect_style}`;
                
                // Create cursor if doesn't exist
                const CURSOR_ID = '{CURSOR_ELEMENT_ID}';
                
                if (!document.getElementById(CURSOR_ID)) {{
                    const cursor = document.createElement('div');
                    cursor.id = CURSOR_ID;
                    cursor.style.cssText = cursorStyle;
                    // CRITICAL: Set position IMMEDIATELY before appending to DOM
                    // This prevents cursor from appearing at center (0,0) before animation
                    // Use initial position (from previous page if available, otherwise center)
                    cursor.style.left = initialX + 'px';
                    cursor.style.top = initialY + 'px';
                    cursor.style.display = 'block';
                    cursor.style.visibility = 'visible';
                    cursor.style.opacity = '1';
                    // Disable transitions during creation to prevent animation from center
                    cursor.style.transition = 'none';
                    
                    // Try to append to body, or documentElement if body doesn't exist
                    if (document.body) {{
                        document.body.appendChild(cursor);
                        // Re-enable transitions after cursor is positioned (for future movements)
                        setTimeout(() => {{
                            cursor.style.transition = '';
                        }}, 0);
                    }} else if (document.documentElement) {{
                        // If body doesn't exist, append to documentElement
                        document.documentElement.appendChild(cursor);
                        // Re-enable transitions after cursor is positioned
                        setTimeout(() => {{
                            cursor.style.transition = '';
                        }}, 0);
                    }} else {{
                        // If neither exists, wait for body
                        const observer = new MutationObserver(() => {{
                            // Check again for duplicates before appending
                            const cursors = document.querySelectorAll('#' + CURSOR_ID);
                            if (cursors.length > 0) {{
                                // Cursor already exists, don't add another
                                observer.disconnect();
                                return;
                            }}
                            if (document.body && !document.getElementById(CURSOR_ID)) {{
                                document.body.appendChild(cursor);
                                // Re-enable transitions after cursor is positioned
                                setTimeout(() => {{
                                    cursor.style.transition = '';
                                }}, 0);
                                observer.disconnect();
                            }}
                        }});
                        observer.observe(document.documentElement || document, {{ childList: true }});
                    }}
                }} else {{
                    // Ensure cursor is visible but PRESERVE current position - never reset to center
                    const cursor = document.getElementById(CURSOR_ID);
                    const rect = cursor.getBoundingClientRect();
                    const currentLeft = parseFloat(cursor.style.left) || rect.left;
                    const currentTop = parseFloat(cursor.style.top) || rect.top;
                    
                    // Only set position if it's truly unset (0, NaN, or empty)
                    // Otherwise preserve the current position
                    if (isNaN(currentLeft) || currentLeft === 0 || cursor.style.left === '' || cursor.style.left === '0px') {{
                        // Disable transition when setting initial position to prevent animation
                        const oldTransition = cursor.style.transition;
                        cursor.style.transition = 'none';
                        cursor.style.left = initialX + 'px';
                        // Re-enable transition after position is set
                        setTimeout(() => {{
                            cursor.style.transition = oldTransition;
                        }}, 0);
                    }}
                    if (isNaN(currentTop) || currentTop === 0 || cursor.style.top === '' || cursor.style.top === '0px') {{
                        // Disable transition when setting initial position to prevent animation
                        const oldTransition = cursor.style.transition;
                        cursor.style.transition = 'none';
                        cursor.style.top = initialY + 'px';
                        // Re-enable transition after position is set
                        setTimeout(() => {{
                            cursor.style.transition = oldTransition;
                        }}, 0);
                    }}
                    cursor.style.display = 'block';
                    cursor.style.visibility = 'visible';
                    cursor.style.opacity = '1';
                }}
                
                // Create click effect if doesn't exist
                const CLICK_EFFECT_ID = '{CLICK_EFFECT_ELEMENT_ID}';
                const clickEffectElement = document.getElementById(CLICK_EFFECT_ID);
                if (!clickEffectElement) {{
                    const clickEffect = document.createElement('div');
                    clickEffect.id = CLICK_EFFECT_ID;
                    clickEffect.style.cssText = clickEffectStyle;
                    clickEffect.style.left = centerX + 'px';
                    clickEffect.style.top = centerY + 'px';
                    // Ensure it starts hidden
                    clickEffect.style.opacity = '0';
                    clickEffect.style.display = 'none';
                    if (document.body) {{
                        document.body.appendChild(clickEffect);
                    }}
                }} else {{
                    // Ensure existing click effect is hidden
                    clickEffectElement.style.opacity = '0';
                    clickEffectElement.style.display = 'none';
                    clickEffectElement.style.width = '0px';
                    clickEffectElement.style.height = '0px';
                }}
                
                // Remove hover effect if disabled, or create if enabled
                const HOVER_EFFECT_ID = '{HOVER_EFFECT_ELEMENT_ID}';
                const hoverEffectElement = document.getElementById(HOVER_EFFECT_ID);
                if (!{str(self.config.hover_effect).lower()}) {{
                    // Hover effect is disabled - remove it if it exists
                    if (hoverEffectElement) {{
                        hoverEffectElement.remove();
                    }}
                }} else {{
                    // Hover effect is enabled - create if doesn't exist
                    if (!hoverEffectElement) {{
                        const hoverEffect = document.createElement('div');
                        hoverEffect.id = HOVER_EFFECT_ID;
                        hoverEffect.style.cssText = `{CursorStyles.get_hover_effect_css(self.config)}`;
                        hoverEffect.style.left = centerX + 'px';
                        hoverEffect.style.top = centerY + 'px';
                        if (document.body) {{
                            document.body.appendChild(hoverEffect);
                        }}
                    }} else {{
                        // Ensure existing hover effect is hidden
                        hoverEffectElement.style.opacity = '0';
                        hoverEffectElement.style.display = 'none';
                    }}
                }}
            }})();
        """)
    
    async def remove_hover_effect_if_disabled(self) -> None:
        """Remove hover effect if it's disabled."""
        if not self.config.hover_effect:
            await self.page.evaluate(f"""
                (function() {{
                    const HOVER_EFFECT_ID = '{HOVER_EFFECT_ELEMENT_ID}';
                    const hoverEffect = document.getElementById(HOVER_EFFECT_ID);
                    if (hoverEffect) {{
                        hoverEffect.remove();
                    }}
                }})();
            """)
    
    async def ensure_click_effect_hidden(self) -> None:
        """Ensure click effect is hidden when not in use."""
        await self.page.evaluate(f"""
            (function() {{
                const CLICK_EFFECT_ID = '{CLICK_EFFECT_ELEMENT_ID}';
                const clickEffect = document.getElementById(CLICK_EFFECT_ID);
                if (clickEffect) {{
                    clickEffect.style.opacity = '0';
                    clickEffect.style.display = 'none';
                    clickEffect.style.width = '0px';
                    clickEffect.style.height = '0px';
                }}
            }})();
        """)
    
    async def cursor_exists(self) -> bool:
        """Check if cursor element exists."""
        return await self.page.evaluate(f"""
            (function() {{
                return document.getElementById('{CURSOR_ELEMENT_ID}') !== null;
            }})();
        """)

