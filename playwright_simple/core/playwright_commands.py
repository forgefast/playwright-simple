#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Playwright Direct Commands Interface.

Provides a simple interface for sending direct commands to Playwright browser.
This is useful for:
- AI assistants with limited capabilities
- Manual testing and debugging
- Interactive command execution during recording

Commands are simple and human-readable, making them easy to use by both humans and AI.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Union
from playwright.async_api import Page, Browser, BrowserContext

logger = logging.getLogger(__name__)


class PlaywrightCommands:
    """Interface for direct Playwright commands."""
    
    def __init__(self, page: Page):
        """
        Initialize Playwright commands interface.
        
        Args:
            page: Playwright Page instance
        """
        self.page = page
    
    async def find_element(
        self,
        text: Optional[str] = None,
        selector: Optional[str] = None,
        role: Optional[str] = None,
        visible: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Find an element on the page.
        
        Args:
            text: Text content to search for
            selector: CSS selector or XPath
            role: ARIA role (button, link, textbox, etc)
            visible: Only return visible elements
        
        Returns:
            Element info dict or None if not found
        """
        try:
            if text:
                # Try to find by text (most common case)
                # Priority: clickable elements (a, button) first, then others
                result = await self.page.evaluate("""
                    ({text, visible}) => {
                        const textLower = text.toLowerCase();
                        
                        // Strategy 1: Prioritize clickable elements (links, buttons)
                        const clickableSelectors = ['a', 'button', 'input[type="button"]', 'input[type="submit"]', '[role="button"]', '[role="link"]'];
                        for (const selector of clickableSelectors) {
                            const elements = Array.from(document.querySelectorAll(selector));
                            for (const el of elements) {
                                // Check direct text content (not from children)
                                const directText = Array.from(el.childNodes)
                                    .filter(node => node.nodeType === Node.TEXT_NODE)
                                    .map(node => node.textContent.trim())
                                    .join(' ')
                                    .trim();
                                const elText = (directText || el.textContent || el.innerText || '').trim();
                                
                                // Check if text matches (exact or contains)
                                if (elText.toLowerCase() === textLower || elText.toLowerCase().includes(textLower)) {
                                    if (visible && (el.offsetParent === null || el.style.display === 'none')) {
                                        continue;
                                    }
                                    return {
                                        tag: el.tagName,
                                        text: elText.substring(0, 100),
                                        id: el.id || '',
                                        className: el.className || '',
                                        href: el.href || '',
                                        role: el.getAttribute('role') || '',
                                        visible: el.offsetParent !== null && el.style.display !== 'none'
                                    };
                                }
                            }
                        }
                        
                        // Strategy 2: Any element with exact or partial text match
                        const allElements = Array.from(document.querySelectorAll('*'));
                        for (const el of allElements) {
                            const elText = (el.textContent || el.innerText || '').trim();
                            if (elText.toLowerCase() === textLower || elText.toLowerCase().includes(textLower)) {
                                // Skip if it's a container element without direct text
                                if (['DIV', 'SPAN', 'SECTION', 'ARTICLE', 'MAIN'].includes(el.tagName)) {
                                    const directText = Array.from(el.childNodes)
                                        .filter(node => node.nodeType === Node.TEXT_NODE)
                                        .map(node => node.textContent.trim())
                                        .join(' ')
                                        .trim();
                                    if (!directText || !directText.toLowerCase().includes(textLower)) {
                                        continue; // Skip containers that only have text in children
                                    }
                                }
                                
                                if (visible && (el.offsetParent === null || el.style.display === 'none')) {
                                    continue;
                                }
                                return {
                                    tag: el.tagName,
                                    text: elText.substring(0, 100),
                                    id: el.id || '',
                                    className: el.className || '',
                                    href: el.href || '',
                                    role: el.getAttribute('role') || '',
                                    visible: el.offsetParent !== null && el.style.display !== 'none'
                                };
                            }
                        }
                        return null;
                    }
                """, {'text': text, 'visible': visible})
                
                if result:
                    return result
            
            if selector:
                # Try CSS selector or XPath
                try:
                    element = await self.page.query_selector(selector)
                    if element:
                        info = await element.evaluate("""
                            (el) => {
                                return {
                                    tag: el.tagName,
                                    text: (el.textContent || el.innerText || '').trim().substring(0, 100),
                                    id: el.id || '',
                                    className: el.className || '',
                                    href: el.href || '',
                                    role: el.getAttribute('role') || '',
                                    visible: el.offsetParent !== null && el.style.display !== 'none'
                                };
                            }
                        """)
                        return info
                except Exception as e:
                    logger.debug(f"Selector failed: {e}")
            
            if role:
                # Find by ARIA role
                result = await self.page.evaluate("""
                    ({role, visible}) => {
                        const elements = Array.from(document.querySelectorAll(`[role="${role}"]`));
                        for (const el of elements) {
                            if (visible && (el.offsetParent === null || el.style.display === 'none')) {
                                continue;
                            }
                            return {
                                tag: el.tagName,
                                text: (el.textContent || el.innerText || '').trim().substring(0, 100),
                                id: el.id || '',
                                className: el.className || '',
                                href: el.href || '',
                                role: el.getAttribute('role') || '',
                                visible: el.offsetParent !== null && el.style.display !== 'none'
                            };
                        }
                        return null;
                    }
                """, {'role': role, 'visible': visible})
                
                if result:
                    return result
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding element: {e}")
            return None
    
    async def find_all_elements(
        self,
        text: Optional[str] = None,
        selector: Optional[str] = None,
        role: Optional[str] = None,
        visible: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Find all matching elements on the page.
        
        Args:
            text: Text content to search for
            selector: CSS selector
            role: ARIA role
            visible: Only return visible elements
        
        Returns:
            List of element info dicts
        """
        try:
            if text:
                result = await self.page.evaluate("""
                    ({text, visible}) => {
                        const elements = Array.from(document.querySelectorAll('*'));
                        const matches = [];
                        for (const el of elements) {
                            const elText = (el.textContent || el.innerText || '').trim();
                            if (elText.includes(text)) {
                                if (visible && (el.offsetParent === null || el.style.display === 'none')) {
                                    continue;
                                }
                                matches.push({
                                    tag: el.tagName,
                                    text: elText.substring(0, 100),
                                    id: el.id || '',
                                    className: el.className || '',
                                    href: el.href || '',
                                    role: el.getAttribute('role') || '',
                                    visible: el.offsetParent !== null && el.style.display !== 'none'
                                });
                            }
                        }
                        return matches;
                    }
                """, {'text': text, 'visible': visible})
                return result or []
            
            if selector:
                elements = await self.page.query_selector_all(selector)
                results = []
                for element in elements:
                    info = await element.evaluate("""
                        (el) => {
                            return {
                                tag: el.tagName,
                                text: (el.textContent || el.innerText || '').trim().substring(0, 100),
                                id: el.id || '',
                                className: el.className || '',
                                href: el.href || '',
                                role: el.getAttribute('role') || '',
                                visible: el.offsetParent !== null && el.style.display !== 'none'
                            };
                        }
                    """)
                    if not visible or info.get('visible'):
                        results.append(info)
                return results
            
            if role:
                result = await self.page.evaluate("""
                    ({role, visible}) => {
                        const elements = Array.from(document.querySelectorAll(`[role="${role}"]`));
                        const matches = [];
                        for (const el of elements) {
                            if (visible && (el.offsetParent === null || el.style.display === 'none')) {
                                continue;
                            }
                            matches.push({
                                tag: el.tagName,
                                text: (el.textContent || el.innerText || '').trim().substring(0, 100),
                                id: el.id || '',
                                className: el.className || '',
                                href: el.href || '',
                                role: el.getAttribute('role') || '',
                                visible: el.offsetParent !== null && el.style.display !== 'none'
                            });
                        }
                        return matches;
                    }
                """, {'role': role, 'visible': visible})
                return result or []
            
            return []
            
        except Exception as e:
            logger.error(f"Error finding elements: {e}")
            return []
    
    async def click(
        self,
        text: Optional[str] = None,
        selector: Optional[str] = None,
        role: Optional[str] = None,
        index: int = 0,
        cursor_controller = None
    ) -> bool:
        """
        Click on an element.
        
        Args:
            text: Text content to search for
            selector: CSS selector
            role: ARIA role
            index: Index if multiple matches (default: 0)
            cursor_controller: Optional CursorController instance for visual feedback
        
        Returns:
            True if clicked successfully, False otherwise
        """
        try:
            if text:
                # Find by text - prioritize submit buttons and get coordinates
                result = await self.page.evaluate("""
                    ({text, index}) => {
                        const textLower = text.toLowerCase();
                        const matches = [];
                        
                        // Strategy 1: Prioritize SUBMIT buttons first (most important for forms)
                        const submitSelectors = ['input[type="submit"]', 'button[type="submit"]', 'button:not([type])'];
                        for (const selector of submitSelectors) {
                            const elements = Array.from(document.querySelectorAll(selector));
                            for (const el of elements) {
                                if (el.offsetParent === null || el.style.display === 'none') {
                                    continue;
                                }
                                
                                // Check if it's inside a form
                                const isInForm = el.closest('form') !== null;
                                
                                // Check direct text content
                                const directText = Array.from(el.childNodes)
                                    .filter(node => node.nodeType === Node.TEXT_NODE)
                                    .map(node => node.textContent.trim())
                                    .join(' ')
                                    .trim();
                                const elText = (directText || el.textContent || el.innerText || el.value || '').trim();
                                
                                if (elText.toLowerCase() === textLower || elText.toLowerCase().includes(textLower)) {
                                    const rect = el.getBoundingClientRect();
                                    // Higher priority for submit buttons in forms
                                    matches.push({
                                        element: el,
                                        x: Math.floor(rect.left + rect.width / 2),
                                        y: Math.floor(rect.top + rect.height / 2),
                                        priority: isInForm ? 10 : 5,  // Higher priority if in form
                                        isSubmit: true
                                    });
                                }
                            }
                        }
                        
                        // Strategy 2: Other clickable elements (links, buttons) - but lower priority
                        const clickableSelectors = ['button', 'a', 'input[type="button"]', '[role="button"]', '[role="link"]'];
                        for (const selector of clickableSelectors) {
                            const elements = Array.from(document.querySelectorAll(selector));
                            for (const el of elements) {
                                // Skip if already in matches
                                if (matches.some(m => m.element === el)) {
                                    continue;
                                }
                                
                                if (el.offsetParent === null || el.style.display === 'none') {
                                    continue;
                                }
                                
                                // Check direct text content
                                const directText = Array.from(el.childNodes)
                                    .filter(node => node.nodeType === Node.TEXT_NODE)
                                    .map(node => node.textContent.trim())
                                    .join(' ')
                                    .trim();
                                const elText = (directText || el.textContent || el.innerText || '').trim();
                                
                                if (elText.toLowerCase() === textLower || elText.toLowerCase().includes(textLower)) {
                                    const rect = el.getBoundingClientRect();
                                    const tag = el.tagName.toLowerCase();
                                    const isInForm = el.closest('form') !== null;
                                    // Lower priority for links, especially if not in form
                                    matches.push({
                                        element: el,
                                        x: Math.floor(rect.left + rect.width / 2),
                                        y: Math.floor(rect.top + rect.height / 2),
                                        priority: (tag === 'a' && !isInForm) ? 1 : 3,  // Links outside forms have lowest priority
                                        isSubmit: false
                                    });
                                }
                            }
                        }
                        
                        // Strategy 3: Any clickable element with text (lowest priority)
                        if (matches.length <= index) {
                            const allElements = Array.from(document.querySelectorAll('*'));
                            for (const el of allElements) {
                                if (el.offsetParent === null || el.style.display === 'none') {
                                    continue;
                                }
                                
                                const elText = (el.textContent || el.innerText || '').trim();
                                if (elText.toLowerCase().includes(textLower)) {
                                    const tag = el.tagName.toLowerCase();
                                    if (tag === 'button' || tag === 'a' || 
                                        el.getAttribute('role') === 'button' ||
                                        el.getAttribute('onclick') ||
                                        el.style.cursor === 'pointer') {
                                        const rect = el.getBoundingClientRect();
                                        matches.push({
                                            element: el,
                                            x: Math.floor(rect.left + rect.width / 2),
                                            y: Math.floor(rect.top + rect.height / 2),
                                            priority: 2,
                                            isSubmit: false
                                        });
                                    }
                                }
                            }
                        }
                        
                        // Sort by priority (highest first) - submit buttons in forms first
                        matches.sort((a, b) => b.priority - a.priority);
                        
                        if (matches.length > index && matches[index]) {
                            return {
                                found: true,
                                x: matches[index].x,
                                y: matches[index].y,
                                element: matches[index].element,
                                isSubmit: matches[index].isSubmit || false
                            };
                        }
                        return {found: false};
                    }
                """, {'text': text, 'index': index})
                
                if result.get('found'):
                    x = result.get('x')
                    y = result.get('y')
                    
                    # Move cursor and show visual feedback if cursor_controller available
                    if cursor_controller:
                        try:
                            await cursor_controller.show()
                            await cursor_controller.move(x, y, smooth=True)
                            await asyncio.sleep(0.3)  # Small delay so user can see cursor move
                            
                            # Show click animation
                            await self.page.evaluate(f"""
                                () => {{
                                    const clickIndicator = document.getElementById('__playwright_cursor_click');
                                    if (clickIndicator) {{
                                        clickIndicator.style.left = '{x}px';
                                        clickIndicator.style.top = '{y}px';
                                        clickIndicator.style.display = 'block';
                                        setTimeout(() => {{
                                            clickIndicator.style.display = 'none';
                                        }}, 300);
                                    }}
                                }}
                            """)
                            await asyncio.sleep(0.1)  # Small delay for animation
                        except Exception as e:
                            logger.debug(f"Error showing cursor feedback: {e}")
                    
                    # Perform actual click
                    await self.page.mouse.click(x, y)
                    return True
                return False
            
            if selector:
                element = await self.page.query_selector(selector)
                if element:
                    # Get coordinates for visual feedback
                    box = await element.bounding_box()
                    if box:
                        x = int(box['x'] + box['width'] / 2)
                        y = int(box['y'] + box['height'] / 2)
                        
                        # Move cursor and show visual feedback if cursor_controller available
                        if cursor_controller:
                            try:
                                await cursor_controller.show()
                                await cursor_controller.move(x, y, smooth=True)
                                await asyncio.sleep(0.3)
                                
                                # Show click animation
                                await self.page.evaluate(f"""
                                    () => {{
                                        const clickIndicator = document.getElementById('__playwright_cursor_click');
                                        if (clickIndicator) {{
                                            clickIndicator.style.left = '{x}px';
                                            clickIndicator.style.top = '{y}px';
                                            clickIndicator.style.display = 'block';
                                            setTimeout(() => {{
                                                clickIndicator.style.display = 'none';
                                            }}, 300);
                                        }}
                                    }}
                                """)
                                await asyncio.sleep(0.1)
                            except Exception as e:
                                logger.debug(f"Error showing cursor feedback: {e}")
                        
                        await self.page.mouse.click(x, y)
                    else:
                        await element.click()
                    return True
                return False
            
            if role:
                elements = await self.page.query_selector_all(f'[role="{role}"]')
                if elements and len(elements) > index:
                    element = elements[index]
                    # Get coordinates for visual feedback
                    box = await element.bounding_box()
                    if box:
                        x = int(box['x'] + box['width'] / 2)
                        y = int(box['y'] + box['height'] / 2)
                        
                        # Move cursor and show visual feedback if cursor_controller available
                        if cursor_controller:
                            try:
                                await cursor_controller.show()
                                await cursor_controller.move(x, y, smooth=True)
                                await asyncio.sleep(0.3)
                                
                                # Show click animation
                                await self.page.evaluate(f"""
                                    () => {{
                                        const clickIndicator = document.getElementById('__playwright_cursor_click');
                                        if (clickIndicator) {{
                                            clickIndicator.style.left = '{x}px';
                                            clickIndicator.style.top = '{y}px';
                                            clickIndicator.style.display = 'block';
                                            setTimeout(() => {{
                                                clickIndicator.style.display = 'none';
                                            }}, 300);
                                        }}
                                    }}
                                """)
                                await asyncio.sleep(0.1)
                            except Exception as e:
                                logger.debug(f"Error showing cursor feedback: {e}")
                        
                        await self.page.mouse.click(x, y)
                    else:
                        await element.click()
                    return True
                return False
            
            return False
            
        except Exception as e:
            logger.error(f"Error clicking element: {e}")
            return False
    
    async def type_text(
        self,
        text: str,
        into: Optional[str] = None,
        selector: Optional[str] = None,
        clear: bool = True,
        cursor_controller = None
    ) -> bool:
        """
        Type text into an input field.
        
        Args:
            text: Text to type
            into: Text label of the input field
            selector: CSS selector of the input field
            clear: Clear field before typing
            cursor_controller: Optional CursorController instance for visual feedback
        
        Returns:
            True if typed successfully, False otherwise
        """
        try:
            element = None
            element_coords = None
            
            if into:
                # Find input by label text and get coordinates
                result = await self.page.evaluate("""
                    (labelText) => {
                        const labels = Array.from(document.querySelectorAll('label'));
                        for (const label of labels) {
                            if ((label.textContent || '').includes(labelText)) {
                                const inputId = label.getAttribute('for');
                                let input = null;
                                if (inputId) {
                                    input = document.getElementById(inputId);
                                }
                                if (!input) {
                                    input = label.parentElement?.querySelector('input, textarea');
                                }
                                if (input) {
                                    const rect = input.getBoundingClientRect();
                                    return {
                                        found: true,
                                        x: Math.floor(rect.left + rect.width / 2),
                                        y: Math.floor(rect.top + rect.height / 2)
                                    };
                                }
                            }
                        }
                        // Try to find input with placeholder
                        const inputs = Array.from(document.querySelectorAll('input, textarea'));
                        for (const input of inputs) {
                            if ((input.placeholder || '').includes(labelText)) {
                                const rect = input.getBoundingClientRect();
                                return {
                                    found: true,
                                    x: Math.floor(rect.left + rect.width / 2),
                                    y: Math.floor(rect.top + rect.height / 2)
                                };
                            }
                        }
                        return {found: false};
                    }
                """, into)
                
                if result.get('found'):
                    element_coords = {'x': result.get('x'), 'y': result.get('y')}
                    # Find element handle for typing
                    element = await self.page.evaluate_handle("""
                        (labelText) => {
                            const labels = Array.from(document.querySelectorAll('label'));
                            for (const label of labels) {
                                if ((label.textContent || '').includes(labelText)) {
                                    const inputId = label.getAttribute('for');
                                    if (inputId) {
                                        return document.getElementById(inputId);
                                    }
                                    const input = label.parentElement?.querySelector('input, textarea');
                                    if (input) return input;
                                }
                            }
                            const inputs = Array.from(document.querySelectorAll('input, textarea'));
                            for (const input of inputs) {
                                if ((input.placeholder || '').includes(labelText)) {
                                    return input;
                                }
                            }
                            return null;
                        }
                    """, into)
            
            if selector and not element:
                element = await self.page.query_selector(selector)
                if element:
                    box = await element.bounding_box()
                    if box:
                        element_coords = {
                            'x': int(box['x'] + box['width'] / 2),
                            'y': int(box['y'] + box['height'] / 2)
                        }
            
            if element:
                # Click on field before typing (for better UX in videos)
                if element_coords and cursor_controller:
                    try:
                        await cursor_controller.show()
                        await cursor_controller.move(element_coords['x'], element_coords['y'], smooth=True)
                        await asyncio.sleep(0.2)  # Small delay so user can see cursor move
                        
                        # Show click animation
                        await self.page.evaluate(f"""
                            () => {{
                                const clickIndicator = document.getElementById('__playwright_cursor_click');
                                if (clickIndicator) {{
                                    clickIndicator.style.left = '{element_coords['x']}px';
                                    clickIndicator.style.top = '{element_coords['y']}px';
                                    clickIndicator.style.display = 'block';
                                    setTimeout(() => {{
                                        clickIndicator.style.display = 'none';
                                    }}, 300);
                                }}
                            }}
                        """)
                        await asyncio.sleep(0.1)
                    except Exception as e:
                        logger.debug(f"Error showing cursor feedback: {e}")
                
                # Click on element to focus (even if already focused, for visual clarity)
                if element_coords:
                    await self.page.mouse.click(element_coords['x'], element_coords['y'])
                else:
                    await element.click()
                
                await asyncio.sleep(0.1)  # Small delay after click
                
                if clear:
                    await element.fill('')
                await element.type(text)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error typing text: {e}")
            return False
    
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
                import tempfile
                import os
                path = os.path.join(tempfile.gettempdir(), f'screenshot_{asyncio.get_event_loop().time()}.png')
            
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
                    from html import parser
                    import re
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


# Convenience functions for easy access
async def create_commands(page: Page) -> PlaywrightCommands:
    """Create a PlaywrightCommands instance from a page."""
    return PlaywrightCommands(page)

