#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug utilities for cursor management.

Contains methods for taking debug screenshots and logging cursor state.
"""

from typing import Dict, Any
from playwright.async_api import Page

from .constants import (
    CURSOR_ELEMENT_ID,
    CLICK_EFFECT_ELEMENT_ID,
    HOVER_EFFECT_ELEMENT_ID,
)


class CursorDebug:
    """Helper class for cursor debugging."""
    
    def __init__(self, page: Page):
        """
        Initialize cursor debug helper.
        
        Args:
            page: Playwright page instance
        """
        self.page = page
        self._debug_screenshot_count = 0
        self._debug_enabled = True
    
    def enable(self):
        """Enable debug screenshots."""
        self._debug_enabled = True
    
    def disable(self):
        """Disable debug screenshots."""
        self._debug_enabled = False
    
    async def take_screenshot(self, label: str) -> None:
        """
        Take debug screenshot if enabled.
        
        Args:
            label: Label for the screenshot
        """
        if not self._debug_enabled:
            return
        
        try:
            # Get cursor count before screenshot
            cursor_info = await self.page.evaluate(f"""
                (function() {{
                    const CURSOR_ID = '{CURSOR_ELEMENT_ID}';
                    const CLICK_EFFECT_ID = '{CLICK_EFFECT_ELEMENT_ID}';
                    const HOVER_EFFECT_ID = '{HOVER_EFFECT_ELEMENT_ID}';
                    
                    const cursors = document.querySelectorAll('#' + CURSOR_ID);
                    const clickEffect = document.getElementById(CLICK_EFFECT_ID);
                    const hoverEffect = document.getElementById(HOVER_EFFECT_ID);
                    
                    return {{
                        cursorCount: cursors.length,
                        cursorPositions: Array.from(cursors).map(c => ({{
                            left: c.style.left,
                            top: c.style.top,
                            display: c.style.display,
                            visibility: c.style.visibility,
                            opacity: c.style.opacity,
                            zIndex: c.style.zIndex
                        }})),
                        clickEffectExists: clickEffect !== null,
                        hoverEffectExists: hoverEffect !== null
                    }};
                }})();
            """)
            
            # Take screenshot
            self._debug_screenshot_count += 1
            screenshot_path = f"/tmp/cursor_debug_{self._debug_screenshot_count:03d}_{label}.png"
            await self.page.screenshot(path=screenshot_path, full_page=False)
            
            print(f"  📸 Debug screenshot [{self._debug_screenshot_count:03d}] {label}: {screenshot_path}")
            print(f"     Cursors: {cursor_info.get('cursorCount', 0)}, Click Effect: {cursor_info.get('clickEffectExists', False)}, Hover Effect: {cursor_info.get('hoverEffectExists', False)}")
            if cursor_info.get('cursorCount', 0) > 1:
                print(f"     ⚠️  DUPLICATE CURSORS DETECTED! Positions: {cursor_info.get('cursorPositions', [])}")
        except Exception as e:
            print(f"  ⚠️  Error taking debug screenshot: {e}")

