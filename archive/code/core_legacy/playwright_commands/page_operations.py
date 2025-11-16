#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Page Operations Module.

Handles page-level operations (wait, navigate, screenshot, HTML, info).
"""

import asyncio
import logging
import tempfile
import os
from typing import Dict, Any, Optional
from playwright.async_api import Page

logger = logging.getLogger(__name__)


class PageOperations:
    """Handles page-level operations."""
    
    def __init__(self, page: Page):
        """Initialize page operations."""
        self.page = page
    
    async def wait_for_element(
        self,
        text: Optional[str] = None,
        selector: Optional[str] = None,
        role: Optional[str] = None,
        timeout: int = 5000
    ) -> bool:
        """
        Wait for an element to appear on the page.
        
        Args:
            text: Text content to wait for
            selector: CSS selector
            role: ARIA role
            timeout: Timeout in milliseconds
        
        Returns:
            True if element appeared, False if timeout
        """
        try:
            if selector:
                await self.page.wait_for_selector(selector, timeout=timeout)
                return True
            
            if text:
                # Wait for text to appear
                await self.page.wait_for_function("""
                    (text) => {
                        const elements = Array.from(document.querySelectorAll('*'));
                        for (const el of elements) {
                            const elText = (el.textContent || el.innerText || '').trim();
                            if (elText.includes(text) && el.offsetParent !== null) {
                                return true;
                            }
                        }
                        return false;
                    }
                """, text, timeout=timeout)
                return True
            
            if role:
                await self.page.wait_for_selector(f'[role="{role}"]', timeout=timeout)
                return True
            
            return False
            
        except Exception as e:
            logger.debug(f"Timeout waiting for element: {e}")
            return False
    
    async def get_page_info(self) -> Dict[str, Any]:
        """
        Get current page information.
        
        Returns:
            Dict with URL, title, and basic page info
        """
        try:
            return {
                'url': self.page.url,
                'title': await self.page.title(),
                'ready_state': await self.page.evaluate('document.readyState')
            }
        except Exception as e:
            logger.error(f"Error getting page info: {e}")
            return {}
    
    async def navigate(self, url: str) -> bool:
        """
        Navigate to a URL.
        
        Args:
            url: URL to navigate to
        
        Returns:
            True if navigation successful
        """
        try:
            await self.page.goto(url, wait_until='domcontentloaded')
            return True
        except Exception as e:
            logger.error(f"Error navigating: {e}")
            return False
    
    async def take_screenshot(self, path: Optional[str] = None) -> Optional[str]:
        """
        Take a screenshot of the current page.
        
        Args:
            path: Optional path to save screenshot
        
        Returns:
            Path to saved screenshot or None
        """
        try:
            if not path:
                path = os.path.join(
                    tempfile.gettempdir(),
                    f'screenshot_{asyncio.get_event_loop().time()}.png'
                )
            
            await self.page.screenshot(path=path)
            return path
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return None
    
    async def get_html(
        self,
        selector: Optional[str] = None,
        pretty: bool = False,
        max_length: Optional[int] = None
    ) -> Optional[str]:
        """
        Get HTML content of the page or a specific element.
        
        Args:
            selector: Optional CSS selector to get HTML of specific element
            pretty: Format HTML with indentation (default: False)
            max_length: Maximum length of HTML to return (None = no limit)
        
        Returns:
            HTML string or None if error
        """
        try:
            if selector:
                # Get HTML of specific element
                element = await self.page.query_selector(selector)
                if not element:
                    return None
                
                html = await element.inner_html()
            else:
                # Get HTML of entire page
                html = await self.page.content()
            
            # Format if requested
            if pretty:
                try:
                    # Simple pretty formatting (basic indentation)
                    html = html.replace('><', '>\n<')
                    # Add basic indentation
                    lines = html.split('\n')
                    indent = 0
                    formatted = []
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                        if line.startswith('</'):
                            indent = max(0, indent - 1)
                        formatted.append('  ' * indent + line)
                        if line.startswith('<') and not line.startswith('</') and not line.endswith('/>'):
                            indent += 1
                    html = '\n'.join(formatted)
                except Exception:
                    # If formatting fails, return original
                    pass
            
            # Limit length if requested
            if max_length and len(html) > max_length:
                html = html[:max_length] + f"\n\n... (truncated, total length: {len(html)} characters)"
            
            return html
        except Exception as e:
            logger.error(f"Error getting HTML: {e}")
            return None
