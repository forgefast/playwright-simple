#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTMX helpers for playwright-simple.

Provides utilities for interacting with HTMX-powered dynamic content,
including waiting for swaps, detecting loading states, and handling responses.

HTMX is a popular library for making AJAX requests and updating DOM content.
These helpers are generic and can be used with any application using HTMX.
"""

import asyncio
from typing import Optional, List
from playwright.async_api import Page, Locator, TimeoutError as PlaywrightTimeoutError


class HTMXHelper:
    """
    Helper for HTMX interactions in web applications.
    
    HTMX allows you to access modern browser features directly from HTML,
    rather than using JavaScript. This helper provides methods to wait for
    HTMX swaps, detect loading states, and handle HTMX responses.
    
    Example:
        ```python
        from playwright_simple.core.htmx import HTMXHelper
        
        htmx = HTMXHelper(page)
        await htmx.wait_for_htmx_swap("#result-container")
        content = await htmx.get_htmx_result("#result-container")
        ```
    """
    
    def __init__(self, page: Page, timeout: int = 30000, error_selectors: Optional[List[str]] = None):
        """
        Initialize HTMX helper.
        
        Args:
            page: Playwright page instance
            timeout: Default timeout in milliseconds
            error_selectors: Optional list of CSS selectors to detect errors.
                            Defaults to common error patterns.
        """
        self.page = page
        self.timeout = timeout
        
        # Default error selectors (common patterns)
        self.error_selectors = error_selectors or [
            '.bg-red-50',
            '.text-red-600',
            '.text-red-700',
            '[role="alert"]',
            ':has-text("Error")',
            ':has-text("Failed")',
            '.error',
            '.alert-danger',
            '.alert-error',
        ]
    
    async def wait_for_htmx_swap(
        self,
        container_selector: str,
        timeout: Optional[int] = None
    ) -> Locator:
        """
        Wait for HTMX swap to complete in a container.
        
        HTMX adds classes during swapping: `htmx-swapping`, `htmx-request`.
        This method waits for these classes to be removed, indicating the
        swap is complete.
        
        Args:
            container_selector: Selector for the HTMX target container
            timeout: Timeout in milliseconds (uses default if None)
            
        Returns:
            Locator for the container after swap
            
        Raises:
            TimeoutError: If swap doesn't complete within timeout
        """
        timeout = timeout or self.timeout
        
        # Wait for container to exist
        container = self.page.locator(container_selector).first
        await container.wait_for(state="attached", timeout=timeout)
        
        # Wait for HTMX swap to complete
        # HTMX adds classes during swapping: htmx-swapping, htmx-swapped
        # We wait for these to be removed
        try:
            await self.page.wait_for_function(
                f"""
                () => {{
                    const container = document.querySelector('{container_selector}');
                    if (!container) return false;
                    // Check if HTMX is done swapping (no swapping classes)
                    const hasSwapping = container.classList.contains('htmx-swapping') ||
                                       container.classList.contains('htmx-request');
                    return !hasSwapping;
                }}
                """,
                timeout=timeout
            )
        except Exception:
            # If function wait fails, try waiting for network idle
            await self.page.wait_for_load_state("networkidle", timeout=timeout)
        
        # Additional wait to ensure content is rendered
        await asyncio.sleep(0.3)
        
        return container
    
    async def wait_for_htmx_loading(
        self,
        indicator_selector: str = ".htmx-indicator",
        timeout: Optional[int] = None,
        wait_for_hidden: bool = True
    ) -> None:
        """
        Wait for HTMX loading indicator to appear or disappear.
        
        Args:
            indicator_selector: Selector for the loading indicator.
                               Defaults to `.htmx-indicator` (HTMX standard).
            timeout: Timeout in milliseconds
            wait_for_hidden: If True, wait for indicator to be hidden (default)
                           If False, wait for indicator to be visible
        """
        timeout = timeout or self.timeout
        
        indicator = self.page.locator(indicator_selector).first
        
        if wait_for_hidden:
            # Wait for indicator to be hidden (loading complete)
            try:
                await indicator.wait_for(state="hidden", timeout=timeout)
            except Exception:
                # If hidden state doesn't work, check visibility
                try:
                    await self.page.wait_for_function(
                        f"""
                        () => {{
                            const indicator = document.querySelector('{indicator_selector}');
                            if (!indicator) return true; // Not found = hidden
                            const style = window.getComputedStyle(indicator);
                            return style.display === 'none' || style.visibility === 'hidden' || 
                                   !indicator.classList.contains('htmx-indicator');
                        }}
                        """,
                        timeout=timeout
                    )
                except Exception:
                    pass  # Continue anyway
        else:
            # Wait for indicator to be visible (loading started)
            await indicator.wait_for(state="visible", timeout=min(timeout, 5000))
    
    async def detect_htmx_error(
        self,
        container_selector: str,
        skip_texts: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Detect error messages in HTMX response container.
        
        Args:
            container_selector: Selector for the HTMX result container
            skip_texts: Optional list of text patterns to skip (false positives).
                       Defaults to common non-error messages.
            
        Returns:
            Error message if found, None otherwise
        """
        skip_texts = skip_texts or [
            'not configured',
            'action required',
            'check connectivity',
            'no data',
            'empty',
        ]
        
        try:
            container = self.page.locator(container_selector).first
            if await container.count() == 0:
                return None
            
            # Check for common error patterns
            for error_sel in self.error_selectors:
                error_elem = container.locator(error_sel).first
                if await error_elem.count() > 0:
                    text = await error_elem.text_content()
                    if text and text.strip():
                        # Filter out false positives
                        text_lower = text.lower()
                        if any(skip in text_lower for skip in skip_texts):
                            continue
                        return text.strip()
            
            return None
        except Exception:
            return None
    
    async def get_htmx_result(
        self,
        container_id: str,
        wait_for_swap: bool = True,
        timeout: Optional[int] = None
    ) -> str:
        """
        Get text content from HTMX result container.
        
        Args:
            container_id: ID of the container (with or without #)
            wait_for_swap: Whether to wait for swap to complete first
            timeout: Timeout in milliseconds
            
        Returns:
            Text content of the container
        """
        # Ensure container_id starts with #
        if not container_id.startswith('#'):
            container_id = f'#{container_id}'
        
        if wait_for_swap:
            await self.wait_for_htmx_swap(container_id, timeout)
        
        container = self.page.locator(container_id).first
        if await container.count() == 0:
            return ""
        
        return (await container.text_content()) or ""
    
    async def wait_for_htmx_response(
        self,
        container_selector: str,
        timeout: Optional[int] = None,
        check_for_errors: bool = True,
        skip_texts: Optional[List[str]] = None
    ) -> Locator:
        """
        Wait for HTMX response and optionally check for errors.
        
        Args:
            container_selector: Selector for the HTMX target container
            timeout: Timeout in milliseconds
            check_for_errors: Whether to check for errors after response
            skip_texts: Optional list of text patterns to skip when detecting errors
            
        Returns:
            Locator for the container
            
        Raises:
            AssertionError: If errors are detected and check_for_errors is True
        """
        timeout = timeout or self.timeout
        
        # Wait for swap to complete
        container = await self.wait_for_htmx_swap(container_selector, timeout)
        
        # Check for errors if requested
        if check_for_errors:
            error_msg = await self.detect_htmx_error(container_selector, skip_texts)
            if error_msg:
                raise AssertionError(f"HTMX error detected: {error_msg}")
        
        return container
    
    async def is_htmx_swapping(self, container_selector: Optional[str] = None) -> bool:
        """
        Check if HTMX is currently swapping content.
        
        Args:
            container_selector: Optional container selector to check
                              If None, checks entire page
            
        Returns:
            True if swapping is in progress
        """
        if container_selector:
            try:
                container = self.page.locator(container_selector).first
                if await container.count() == 0:
                    return False
                
                has_swapping = await container.evaluate("""
                    (el) => {
                        return el.classList.contains('htmx-swapping') ||
                               el.classList.contains('htmx-request');
                    }
                """)
                return has_swapping
            except Exception:
                return False
        else:
            # Check entire page
            try:
                has_swapping = await self.page.evaluate("""
                    () => {
                        return document.querySelector('.htmx-swapping, .htmx-request') !== null;
                    }
                """)
                return has_swapping
            except Exception:
                return False

