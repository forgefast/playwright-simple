#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cursor injection and initialization.

Contains methods for injecting cursor JavaScript and CSS into pages.
"""

from playwright.async_api import Page

from .config import CursorConfig
from .constants import (
    CURSOR_ELEMENT_ID,
    CLICK_EFFECT_ELEMENT_ID,
    HOVER_EFFECT_ELEMENT_ID,
    DEFAULT_VIEWPORT_WIDTH,
    DEFAULT_VIEWPORT_HEIGHT,
)
from .cursor_styles import CursorStyles


class CursorInjection:
    """Helper class for cursor injection."""
    
    def __init__(self, page: Page, config: CursorConfig):
        """
        Initialize cursor injection helper.
        
        Args:
            page: Playwright page instance
            config: Cursor configuration
        """
        self.page = page
        self.config = config
    
    async def add_init_script(self) -> None:
        """Add initialization script to page (only once per page)."""
        viewport = self.page.viewport_size or {
            "width": DEFAULT_VIEWPORT_WIDTH,
            "height": DEFAULT_VIEWPORT_HEIGHT
        }
        center_x = viewport['width'] / 2
        center_y = viewport['height'] / 2
        
        # Get cursor styles
        cursor_style = CursorStyles.get_cursor_css(self.config)
        click_effect_style = CursorStyles.get_click_effect_css(self.config)
        
        # Add init script with global flag to prevent duplicate execution
        await self.page.add_init_script(f"""
            (function() {{
                // Global flag to prevent duplicate script execution
                if (window.__playwright_cursor_init_script_added) {{
                    return; // Script already added, skip
                }}
                window.__playwright_cursor_init_script_added = true;
                
                // Constants
                const CURSOR_ID = '{CURSOR_ELEMENT_ID}';
                const CLICK_EFFECT_ID = '{CLICK_EFFECT_ELEMENT_ID}';
                const HOVER_EFFECT_ID = '{HOVER_EFFECT_ELEMENT_ID}';
                
                const centerX = {center_x};
                const centerY = {center_y};
                
                // Cursor styles
                const cursorStyle = `{cursor_style}`;
                const clickEffectStyle = `{click_effect_style}`;
                
                // Create cursor - removes duplicates first
                function createCursor() {{
                    // ALWAYS remove all existing cursors first
                    const existingCursors = document.querySelectorAll('#' + CURSOR_ID);
                    for (let i = 0; i < existingCursors.length; i++) {{
                        existingCursors[i].remove();
                    }}
                    
                    // Now create a single cursor
                    const cursor = document.createElement('div');
                    cursor.id = CURSOR_ID;
                    cursor.style.cssText = cursorStyle;
                    cursor.style.left = centerX + 'px';
                    cursor.style.top = centerY + 'px';
                    if (document.body) {{
                        document.body.appendChild(cursor);
                    }}
                    return cursor;
                }}
                
                // Create click effect - only if it doesn't exist
                function createClickEffect() {{
                    const existing = document.getElementById(CLICK_EFFECT_ID);
                    if (existing) {{
                        // Ensure it's hidden
                        existing.style.opacity = '0';
                        existing.style.display = 'none';
                        existing.style.width = '0px';
                        existing.style.height = '0px';
                        return existing;
                    }}
                    
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
                    return clickEffect;
                }}
                
                // Create hover effect - only if enabled and doesn't exist
                function createHoverEffect() {{
                    // Remove hover effect if disabled
                    const existingHover = document.getElementById(HOVER_EFFECT_ID);
                    if (!{str(self.config.hover_effect).lower()}) {{
                        if (existingHover) {{
                            existingHover.remove();
                        }}
                        return null;
                    }}
                    
                    // Hover effect is enabled - create if doesn't exist
                    if (existingHover) {{
                        // Ensure it's hidden
                        existingHover.style.opacity = '0';
                        existingHover.style.display = 'none';
                        return existingHover;
                    }}
                    
                    const hoverEffect = document.createElement('div');
                    hoverEffect.id = HOVER_EFFECT_ID;
                    hoverEffect.style.cssText = `{CursorStyles.get_hover_effect_css(self.config)}`;
                    hoverEffect.style.left = centerX + 'px';
                    hoverEffect.style.top = centerY + 'px';
                    if (document.body) {{
                        document.body.appendChild(hoverEffect);
                    }}
                    return hoverEffect;
                }}
                
                // Create on page load - but check for duplicates first
                let initCursorCalled = false;
                function initCursor() {{
                    // Prevent multiple calls
                    if (initCursorCalled) {{
                        return;
                    }}
                    initCursorCalled = true;
                    
                    // Remove any existing cursors before creating
                    const existingCursors = document.querySelectorAll('#' + CURSOR_ID);
                    for (let i = 0; i < existingCursors.length; i++) {{
                        existingCursors[i].remove();
                    }}
                    
                    createCursor();
                    createClickEffect();
                    createHoverEffect(); // Will remove if disabled
                }}
                
                // Use a single initialization point
                if (document.readyState === 'loading') {{
                    document.addEventListener('DOMContentLoaded', initCursor, {{ once: true }});
                }} else {{
                    initCursor();
                }}
                
                // Also listen for navigation events to clean up duplicates
                window.addEventListener('beforeunload', function() {{
                    const cursors = document.querySelectorAll('#' + CURSOR_ID);
                    if (cursors.length > 1) {{
                        for (let i = 1; i < cursors.length; i++) {{
                            cursors[i].remove();
                        }}
                    }}
                }});
            }})();
        """)

