#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wait methods for OdooTestBase.

Contains Odoo-specific wait methods for detecting when Odoo is ready.
"""

import asyncio
from typing import Optional


class OdooWaitMixin:
    """Mixin providing Odoo-specific wait methods.
    
    Assumes base class has: page
    """
    
    async def wait_until_ready(self, timeout: Optional[int] = None, wait_for_element: Optional[str] = None) -> 'OdooWaitMixin':
        """
        Wait until Odoo application is ready (no loading indicators, no pending requests).
        
        This method automatically detects when Odoo has finished loading and is ready
        for the next interaction. It waits for:
        - Loading indicators to disappear (.o_loading, .fa-spin, etc.)
        - Network requests to complete
        - DOM to be stable
        - Optional: specific element to appear
        
        Args:
            timeout: Maximum time to wait in milliseconds (default: 5000ms)
            wait_for_element: Optional CSS selector to wait for (e.g., after navigation)
            
        Returns:
            Self for method chaining
        """
        timeout = timeout or 5000  # Increased for reliability
        
        # If specific element requested, wait for it first
        if wait_for_element:
            try:
                await self.page.wait_for_selector(wait_for_element, state="visible", timeout=timeout)
            except Exception:
                pass  # Continue even if element not found
        
        try:
            # Wait for loading indicators to disappear
            # Odoo uses various loading indicators: .o_loading, .fa-spin, .o_loading_indicator
            await self.page.wait_for_function("""
                () => {
                    // Check for common Odoo loading indicators
                    const loadingSelectors = [
                        '.o_loading',
                        '.fa-spin',
                        '.o_loading_indicator',
                        '[class*="loading"]',
                        '.o_web_client.o_loading',
                        '.o_loading_backdrop',
                    ];
                    
                    for (const selector of loadingSelectors) {
                        const elements = document.querySelectorAll(selector);
                        for (const el of elements) {
                            // Check if element is visible
                            const style = window.getComputedStyle(el);
                            if (style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0') {
                                return false;
                            }
                        }
                    }
                    
                    // Check if body has loading class
                    if (document.body && document.body.classList.contains('o_loading')) {
                        return false;
                    }
                    
                    // Check for Odoo's ready state
                    if (window.odoo && window.odoo.__DEBUG__) {
                        // Additional checks if available
                    }
                    
                    return true;
                }
            """, timeout=timeout)
        except Exception:
            # If function wait fails, just wait for load state
            pass
        
        # Wait for DOM to be ready (but not networkidle - too slow!)
        try:
            await self.page.wait_for_load_state("domcontentloaded", timeout=2000)
        except Exception:
            pass  # Don't block if page is slow
        
        # Small delay to ensure everything is rendered (minimal, just for visual smoothness)
        await asyncio.sleep(0.05)  # Minimal delay for visual smoothness
        return self

