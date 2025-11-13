#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cursor customization system for playwright-simple.

Provides visual cursor overlay with customizable style, color, size, and animations.
"""

import asyncio
from typing import Optional, Dict, Any
from playwright.async_api import Page

from .config import CursorConfig


class CursorManager:
    """Manages cursor visualization and effects."""
    
    def __init__(self, page: Page, config: CursorConfig):
        """
        Initialize cursor manager.
        
        Args:
            page: Playwright page instance
            config: Cursor configuration
        """
        self.page = page
        self.config = config
        self._injected = False
    
    async def inject(self, force: bool = False):
        """
        Inject cursor CSS and JavaScript into the page.
        
        Args:
            force: Force re-injection even if already injected
        """
        if self._injected and not force:
            # Just ensure cursor exists on current page
            await self._ensure_cursor_exists()
            return
        
        viewport = self.page.viewport_size or {"width": 1920, "height": 1080}
        center_x = viewport['width'] / 2
        center_y = viewport['height'] / 2
        
        # Get cursor styles
        cursor_style = self._get_cursor_css()
        click_effect_style = self._get_click_effect_css()
        
        await self.page.add_init_script(f"""
            (function() {{
                const centerX = {center_x};
                const centerY = {center_y};
                
                // Cursor styles
                const cursorStyle = `{cursor_style}`;
                const clickEffectStyle = `{click_effect_style}`;
                
                // Create cursor
                function createCursor() {{
                    const old = document.getElementById('playwright-cursor');
                    if (old) old.remove();
                    
                    const cursor = document.createElement('div');
                    cursor.id = 'playwright-cursor';
                    cursor.style.cssText = cursorStyle;
                    cursor.style.left = centerX + 'px';
                    cursor.style.top = centerY + 'px';
                    document.body.appendChild(cursor);
                    return cursor;
                }}
                
                // Create click effect
                function createClickEffect() {{
                    const old = document.getElementById('playwright-click-effect');
                    if (old) old.remove();
                    
                    const clickEffect = document.createElement('div');
                    clickEffect.id = 'playwright-click-effect';
                    clickEffect.style.cssText = clickEffectStyle;
                    clickEffect.style.left = centerX + 'px';
                    clickEffect.style.top = centerY + 'px';
                    document.body.appendChild(clickEffect);
                    return clickEffect;
                }}
                
                // Create hover effect
                function createHoverEffect() {{
                    const old = document.getElementById('playwright-hover-effect');
                    if (old) old.remove();
                    
                    const hoverEffect = document.createElement('div');
                    hoverEffect.id = 'playwright-hover-effect';
                    hoverEffect.style.cssText = `
                        position: fixed !important;
                        width: 0 !important;
                        height: 0 !important;
                        border: 3px solid {self.config.hover_effect_color} !important;
                        border-radius: 50% !important;
                        pointer-events: none !important;
                        z-index: 2147483645 !important;
                        transform: translate(-50%, -50%) !important;
                        transition: all 0.2s ease-out !important;
                        opacity: 0 !important;
                    `;
                    hoverEffect.style.left = centerX + 'px';
                    hoverEffect.style.top = centerY + 'px';
                    document.body.appendChild(hoverEffect);
                    return hoverEffect;
                }}
                
                // Create on page load
                if (document.readyState === 'loading') {{
                    document.addEventListener('DOMContentLoaded', () => {{
                        createCursor();
                        createClickEffect();
                        if ({str(self.config.hover_effect).lower()}) {{
                            createHoverEffect();
                        }}
                    }});
                }} else {{
                    createCursor();
                    createClickEffect();
                    if ({str(self.config.hover_effect).lower()}) {{
                        createHoverEffect();
                    }}
                }}
            }})();
        """)
        
        # Also inject directly on current page
        await self._ensure_cursor_exists()
        
        self._injected = True
    
    async def _ensure_cursor_exists(self):
        """Ensure cursor elements exist on current page."""
        viewport = self.page.viewport_size or {"width": 1920, "height": 1080}
        center_x = viewport['width'] / 2
        center_y = viewport['height'] / 2
        
        cursor_style = self._get_cursor_css()
        click_effect_style = self._get_click_effect_css()
        
        await self.page.evaluate(f"""
            (function() {{
                const centerX = {center_x};
                const centerY = {center_y};
                const cursorStyle = `{cursor_style}`;
                const clickEffectStyle = `{click_effect_style}`;
                
                // Create cursor if doesn't exist
                if (!document.getElementById('playwright-cursor')) {{
                    const cursor = document.createElement('div');
                    cursor.id = 'playwright-cursor';
                    cursor.style.cssText = cursorStyle;
                    cursor.style.left = centerX + 'px';
                    cursor.style.top = centerY + 'px';
                    cursor.style.display = 'block';
                    cursor.style.visibility = 'visible';
                    cursor.style.opacity = '1';
                    if (document.body) {{
                        document.body.appendChild(cursor);
                    }} else {{
                        // If body doesn't exist yet, wait for it
                        const observer = new MutationObserver(() => {{
                            if (document.body && !document.getElementById('playwright-cursor')) {{
                                document.body.appendChild(cursor);
                                observer.disconnect();
                            }}
                        }});
                        observer.observe(document.documentElement, {{ childList: true }});
                    }}
                }} else {{
                    // Ensure cursor is visible and positioned
                    const cursor = document.getElementById('playwright-cursor');
                    cursor.style.left = centerX + 'px';
                    cursor.style.top = centerY + 'px';
                    cursor.style.display = 'block';
                    cursor.style.visibility = 'visible';
                    cursor.style.opacity = '1';
                }}
                
                // Create click effect if doesn't exist
                if (!document.getElementById('playwright-click-effect')) {{
                    const clickEffect = document.createElement('div');
                    clickEffect.id = 'playwright-click-effect';
                    clickEffect.style.cssText = clickEffectStyle;
                    clickEffect.style.left = centerX + 'px';
                    clickEffect.style.top = centerY + 'px';
                    if (document.body) {{
                        document.body.appendChild(clickEffect);
                    }}
                }}
                
                // Create hover effect if doesn't exist
                if ({str(self.config.hover_effect).lower()} && !document.getElementById('playwright-hover-effect')) {{
                    const hoverEffect = document.createElement('div');
                    hoverEffect.id = 'playwright-hover-effect';
                    hoverEffect.style.cssText = `
                        position: fixed !important;
                        width: 0 !important;
                        height: 0 !important;
                        border: 3px solid {self.config.hover_effect_color} !important;
                        border-radius: 50% !important;
                        pointer-events: none !important;
                        z-index: 2147483645 !important;
                        transform: translate(-50%, -50%) !important;
                        transition: all 0.2s ease-out !important;
                        opacity: 0 !important;
                    `;
                    hoverEffect.style.left = centerX + 'px';
                    hoverEffect.style.top = centerY + 'px';
                    if (document.body) {{
                        document.body.appendChild(hoverEffect);
                    }}
                }}
            }})();
        """)
    
    def _get_cursor_css(self) -> str:
        """Generate CSS for cursor based on configuration."""
        size_px = self._get_size_pixels()
        color = self.config.color
        
        if self.config.style == "arrow":
            return f"""
                position: fixed !important;
                width: 0 !important;
                height: 0 !important;
                border-left: {size_px * 0.4}px solid transparent !important;
                border-right: {size_px * 0.4}px solid transparent !important;
                border-top: {size_px * 0.6}px solid {color} !important;
                pointer-events: none !important;
                z-index: 2147483647 !important;
                transform: translate(-50%, -50%) rotate(45deg) !important;
                display: block !important;
                filter: drop-shadow(0 0 3px rgba(0, 0, 0, 0.5)) !important;
            """
        elif self.config.style == "dot":
            return f"""
                position: fixed !important;
                width: {size_px}px !important;
                height: {size_px}px !important;
                background: {color} !important;
                border-radius: 50% !important;
                pointer-events: none !important;
                z-index: 2147483647 !important;
                transform: translate(-50%, -50%) !important;
                display: block !important;
                box-shadow: 0 0 {size_px * 0.3}px {color} !important;
            """
        elif self.config.style == "circle":
            return f"""
                position: fixed !important;
                width: {size_px}px !important;
                height: {size_px}px !important;
                border: {size_px * 0.15}px solid {color} !important;
                border-radius: 50% !important;
                background: transparent !important;
                pointer-events: none !important;
                z-index: 2147483647 !important;
                transform: translate(-50%, -50%) !important;
                display: block !important;
                box-shadow: 0 0 {size_px * 0.3}px {color} !important;
            """
        else:  # custom
            return f"""
                position: fixed !important;
                width: {size_px}px !important;
                height: {size_px}px !important;
                background: {color} !important;
                pointer-events: none !important;
                z-index: 2147483647 !important;
                transform: translate(-50%, -50%) !important;
                display: block !important;
            """
    
    def _get_click_effect_css(self) -> str:
        """Generate CSS for click effect - more visible."""
        return f"""
            position: fixed !important;
            width: 0 !important;
            height: 0 !important;
            border: 8px solid {self.config.click_effect_color} !important;
            border-radius: 50% !important;
            pointer-events: none !important;
            z-index: 2147483646 !important;
            transform: translate(-50%, -50%) !important;
            transition: all 0.4s ease-out !important;
            box-shadow: 0 0 20px {self.config.click_effect_color} !important;
        """
    
    def _get_size_pixels(self) -> int:
        """Convert size string to pixels."""
        if isinstance(self.config.size, (int, float)):
            return int(self.config.size)
        
        size_map = {
            "small": 12,
            "medium": 20,
            "large": 32,
        }
        return size_map.get(self.config.size, 20)
    
    async def move_to(self, x: float, y: float):
        """
        Move cursor to position with smooth animation.
        
        Args:
            x: X coordinate
            y: Y coordinate
        """
        # Ensure cursor exists before moving
        await self._ensure_cursor_exists()
        
        # Get viewport for default position
        viewport = self.page.viewport_size or {"width": 1920, "height": 1080}
        default_x = viewport['width'] / 2
        default_y = viewport['height'] / 2
        
        # Get current cursor position first
        current_pos = await self.page.evaluate("""
            (function() {
                const cursor = document.getElementById('playwright-cursor');
                if (cursor) {
                    const left = parseFloat(cursor.style.left) || 0;
                    const top = parseFloat(cursor.style.top) || 0;
                    return {x: left, y: top, exists: true};
                }
                return {x: 0, y: 0, exists: false};
            })();
        """)
        
        if not current_pos.get('exists'):
            # Cursor doesn't exist, create it first
            await self._ensure_cursor_exists()
            current_pos = {'x': default_x, 'y': default_y}
        
        current_x = current_pos.get('x', default_x) if current_pos.get('x', 0) > 0 else default_x
        current_y = current_pos.get('y', default_y) if current_pos.get('y', 0) > 0 else default_y
        
        # Move cursor with smooth animation - use Promise to wait for completion
        result = await self.page.evaluate(f"""
            (function() {{
                const cursor = document.getElementById('playwright-cursor');
                if (!cursor) {{
                    return Promise.resolve({{success: false, error: 'Cursor not found'}});
                }}
                
                const currentX = {current_x};
                const currentY = {current_y};
                const targetX = {x};
                const targetY = {y};
                
                // Ensure cursor is visible
                cursor.style.display = 'block';
                cursor.style.visibility = 'visible';
                cursor.style.opacity = '1';
                cursor.style.zIndex = '2147483647';
                
                // Animate movement with requestAnimationFrame and return Promise
                const duration = {self.config.animation_speed} * 1000;
                const startTime = performance.now();
                
                return new Promise((resolve) => {{
                    function animate() {{
                        const elapsed = performance.now() - startTime;
                        const progress = Math.min(elapsed / duration, 1);
                        
                        // Ease-out cubic
                        const easeOut = 1 - Math.pow(1 - progress, 3);
                        
                        const posX = currentX + (targetX - currentX) * easeOut;
                        const posY = currentY + (targetY - currentY) * easeOut;
                        
                        cursor.style.left = posX + 'px';
                        cursor.style.top = posY + 'px';
                        
                        if (progress < 1) {{
                            requestAnimationFrame(animate);
                        }} else {{
                            // Final position
                            cursor.style.left = targetX + 'px';
                            cursor.style.top = targetY + 'px';
                            resolve({{success: true, completed: true}});
                        }}
                    }}
                    
                    requestAnimationFrame(animate);
                }});
            }})();
        """)
        
        if result and not result.get('success'):
            print(f"⚠️  Warning: Cursor movement may have failed: {result.get('error', 'Unknown error')}")
        
        # Wait for animation to complete - the JavaScript Promise will resolve when done
        # Add a small buffer to ensure animation is fully rendered
        await asyncio.sleep(0.1)
    
    async def show_click_effect(self, x: float, y: float):
        """
        Show click effect at position and wait for animation to complete.
        
        Args:
            x: X coordinate
            y: Y coordinate
        """
        if not self.config.click_effect:
            return
        
        # Ensure cursor exists
        await self._ensure_cursor_exists()
        
        # Show click effect with animation and wait for it to complete
        await self.page.evaluate(f"""
            (function() {{
                return new Promise((resolve) => {{
                    const effect = document.getElementById('playwright-click-effect');
                    if (!effect) {{
                        resolve({{success: false, error: 'Click effect element not found'}});
                        return;
                    }}
                    
                    // Reset to initial state - make it more visible
                    effect.style.left = '{x}px';
                    effect.style.top = '{y}px';
                    effect.style.width = '0px';
                    effect.style.height = '0px';
                    effect.style.borderWidth = '8px';
                    effect.style.opacity = '1';
                    effect.style.display = 'block';
                    effect.style.visibility = 'visible';
                    effect.style.transition = 'all 0.4s ease-out';
                    effect.style.boxShadow = '0 0 20px {self.config.click_effect_color}';
                    
                    // Force reflow
                    effect.offsetHeight;
                    
                    // Animate to expanded state - larger and more visible
                    requestAnimationFrame(() => {{
                        effect.style.width = '60px';
                        effect.style.height = '60px';
                        effect.style.borderWidth = '3px';
                        effect.style.opacity = '0';
                        effect.style.boxShadow = '0 0 30px {self.config.click_effect_color}';
                        
                        // Wait for animation to complete
                        setTimeout(() => {{
                            resolve({{success: true, completed: true}});
                        }}, 400); // Match transition duration
                    }});
                }});
            }})();
        """)
    
    async def show_hover_effect(self, x: float, y: float, show: bool = True):
        """
        Show or hide hover effect at position.
        
        Args:
            x: X coordinate
            y: Y coordinate
            show: Whether to show or hide
        """
        if not self.config.hover_effect:
            return
        
        # Ensure cursor exists
        await self._ensure_cursor_exists()
        
        opacity = "0.6" if show else "0"
        size = "30px" if show else "0px"
        
        await self.page.evaluate(f"""
            (function() {{
                const effect = document.getElementById('playwright-hover-effect');
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


