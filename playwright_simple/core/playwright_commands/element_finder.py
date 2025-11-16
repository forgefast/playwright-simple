#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Element Finder Module.

Handles finding elements on the page by text, selector, or role.
"""

import logging
from typing import Dict, Any, Optional, List
from playwright.async_api import Page

logger = logging.getLogger(__name__)


class ElementFinder:
    """Handles finding elements on the page."""
    
    def __init__(self, page: Page):
        """Initialize element finder."""
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
                                    if (!directText) {
                                        continue;  // Skip container elements without direct text
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
                return result
            
            if selector:
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
                    if not visible or info.get('visible'):
                        return info
                return None
            
            if role:
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
        Find all elements matching criteria.
        
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

