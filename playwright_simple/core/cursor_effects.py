#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Visual effects for cursor interactions.

Contains methods for showing click and hover effects.
"""

import asyncio
from playwright.async_api import Page

from .config import CursorConfig
from .constants import (
    CURSOR_ELEMENT_ID,
    CLICK_EFFECT_ELEMENT_ID,
    HOVER_EFFECT_ELEMENT_ID,
    CLICK_EFFECT_Z_INDEX,
)


class CursorEffects:
    """Helper class for cursor visual effects."""
    
    def __init__(self, page: Page, config: CursorConfig):
        """
        Initialize cursor effects helper.
        
        Args:
            page: Playwright page instance
            config: Cursor configuration
        """
        self.page = page
        self.config = config
    
    async def show_click_effect(self, x: float, y: float) -> None:
        """
        Show click effect at position and wait for animation to complete.
        
        Args:
            x: X coordinate
            y: Y coordinate
        """
        if not self.config.click_effect:
            return
        
        # IMPORTANT: Hide hover effect before showing click effect (they shouldn't appear together)
        if self.config.hover_effect:
            await self.show_hover_effect(x, y, show=False)
        
        # Show click effect with animation and wait for it to complete
        # Ensure only one effect is active at a time
        # IMPORTANT: Wait for animation to complete so it's visible in video
        await self.page.evaluate(f"""
            (function() {{
                return new Promise((resolve) => {{
                    const effect = document.getElementById('{CLICK_EFFECT_ELEMENT_ID}');
                    if (!effect) {{
                        resolve({{success: false, error: 'Click effect element not found'}});
                        return;
                    }}
                    
                    // Cancel any ongoing animation by resetting transition
                    effect.style.transition = 'none';
                    effect.style.width = '0px';
                    effect.style.height = '0px';
                    effect.style.opacity = '0';
                    
                    // Force reflow to reset
                    effect.offsetHeight;
                    
                    // Reset to initial state - make it more visible and larger
                    effect.style.left = '{x}px';
                    effect.style.top = '{y}px';
                    effect.style.width = '0px';
                    effect.style.height = '0px';
                    effect.style.borderWidth = '12px';
                    effect.style.opacity = '1';
                    effect.style.display = 'block';
                    effect.style.visibility = 'visible';
                    effect.style.zIndex = '{CLICK_EFFECT_Z_INDEX}';  // Below cursor (cursor is on top)
                    effect.style.transition = 'all 0.3s ease-out';  // Faster animation for iteration
                    effect.style.boxShadow = '0 0 30px {self.config.click_effect_color}';
                    
                    // Force reflow to ensure initial state is rendered
                    effect.offsetHeight;
                    
                    // Animate to expanded state - visible ripple effect
                    requestAnimationFrame(() => {{
                        requestAnimationFrame(() => {{
                            effect.style.width = '80px';
                            effect.style.height = '80px';
                            effect.style.borderWidth = '4px';
                            effect.style.opacity = '0';
                            effect.style.boxShadow = '0 0 40px {self.config.click_effect_color}';
                            
                            // Wait for animation to complete (300ms transition)
                            setTimeout(() => {{
                                // Hide effect after animation
                                effect.style.display = 'none';
                                resolve({{success: true, completed: true}});
                            }}, 300); // Match transition duration
                        }});
                    }});
                }});
            }})();
        """)
        
        # Wait for animation to complete before continuing - ensure it's fully visible
        await asyncio.sleep(0.35)  # Wait full animation duration (0.3s) + small buffer to ensure visibility
        
        # IMPORTANT: Ensure hover effect is hidden after click effect completes
        if self.config.hover_effect:
            await self.show_hover_effect(x, y, show=False)
    
    async def show_hover_effect(self, x: float, y: float, show: bool = True) -> None:
        """
        Show or hide hover effect at position.
        
        Args:
            x: X coordinate
            y: Y coordinate
            show: Whether to show or hide
        """
        if not self.config.hover_effect:
            return
        
        opacity = "0.6" if show else "0"
        size = "30px" if show else "0px"
        
        await self.page.evaluate(f"""
            (function() {{
                const effect = document.getElementById('{HOVER_EFFECT_ELEMENT_ID}');
                if (effect) {{
                    effect.style.left = '{x}px';
                    effect.style.top = '{y}px';
                    effect.style.width = '{size}';
                    effect.style.height = '{size}';
                    effect.style.opacity = '{opacity}';
                    effect.style.display = 'block';
                    effect.style.visibility = 'visible';
                }}
            }})();
        """)

