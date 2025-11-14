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
    
    async def start(self, force: bool = False):
        """Start cursor controller and inject cursor overlay."""
        if self.is_active and not force:
            # Still ensure cursor is visible
            await self.show()
            return
        
        try:
            # Wait for page to be ready
            try:
                await self.page.wait_for_load_state('domcontentloaded', timeout=5000)
            except:
                pass  # Continue even if timeout
            
            # Reset flag to allow reinjection
            await self.page.evaluate("""
                () => {
                    window.__playwright_cursor_initialized = false;
                }
            """)
            
            await self.page.evaluate("""
                (function() {
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
                        left: 100px;
                        top: 100px;
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
                    if (!style) {
                        style = document.createElement('style');
                        style.id = '__playwright_cursor_style';
                        style.textContent = `
                            @keyframes cursorClick {
                                0% {
                                    transform: translate(-50%, -50%) scale(0.5);
                                    opacity: 1;
                                }
                                100% {
                                    transform: translate(-50%, -50%) scale(2);
                                    opacity: 0;
                                }
                            }
                        `;
                        document.head.appendChild(style);
                    }
                    
                    document.body.appendChild(cursor);
                    document.body.appendChild(clickIndicator);
                    
                    // Store cursor element
                    window.__playwright_cursor_element = cursor;
                    window.__playwright_cursor_click_element = clickIndicator;
                    window.__playwright_cursor_initialized = true;
                    console.log('[Playwright Cursor] Injected and initialized.');
                })();
            """)
            self.is_active = True
            logger.info("Cursor controller started and injected.")
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

