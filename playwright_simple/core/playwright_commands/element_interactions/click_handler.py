#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Click Handler Module.

Handles clicking on elements with visual feedback and event capture.
"""

import asyncio
import logging
from typing import Optional
from playwright.async_api import Page, ElementHandle

from .element_finder import ElementFinder

logger = logging.getLogger(__name__)

# Enable debug logging for this module
DEBUG_CURSOR = True
DEBUG_CLICKS = True


class ClickHandler:
    """Handles clicking on elements."""
    
    def __init__(self, page: Page, fast_mode: bool = False):
        """
        Initialize click handler.
        
        Args:
            page: Playwright Page instance
            fast_mode: Enable fast mode
        """
        self.page = page
        self.fast_mode = fast_mode
        self.element_finder = ElementFinder(page)
    
    async def click(
        self,
        text: Optional[str] = None,
        selector: Optional[str] = None,
        role: Optional[str] = None,
        index: int = 0,
        cursor_controller = None,
        visual_feedback = None,
        description: str = ""
    ) -> bool:
        """
        Click on an element.
        
        Args:
            text: Text content to search for
            selector: CSS selector
            role: ARIA role
            index: Index if multiple matches (default: 0)
            cursor_controller: Optional CursorController instance for visual feedback
            visual_feedback: Optional VisualFeedback instance
            description: Optional description for logging
        
        Returns:
            True if clicked successfully, False otherwise
        """
        if DEBUG_CLICKS:
            logger.info(f"🖱️  [DEBUG] click() called: text='{text}', selector='{selector}', role='{role}', description='{description}'")
        logger.debug(f"[ELEMENT_INTERACTIONS] click: text='{text}', selector='{selector}', role='{role}', description='{description}'")
        
        try:
            if text:
                return await self._click_by_text(text, index, cursor_controller, visual_feedback)
            
            if selector:
                return await self._click_by_selector(selector, cursor_controller, visual_feedback)
            
            if role:
                return await self._click_by_role(role, index, cursor_controller, visual_feedback)
            
            return False
            
        except Exception as e:
            logger.error(f"[ELEMENT_INTERACTIONS] Erro ao clicar: {e}", exc_info=True)
            return False
    
    async def _click_by_text(
        self,
        text: str,
        index: int,
        cursor_controller,
        visual_feedback
    ) -> bool:
        """Click element found by text."""
        logger.debug(f"[ELEMENT_INTERACTIONS] Procurando elemento por texto: '{text}'")
        
        result = await self.element_finder.find_by_text(text, index)
        if not result:
            return False
        
        x = result.get('x')
        y = result.get('y')
        
        if DEBUG_CLICKS:
            logger.info(f"🖱️  [DEBUG] Element found at ({x}, {y}), preparing to click")
        
        # CRITICAL: Show visual feedback FIRST, then sync mouse, then click
        if visual_feedback and cursor_controller:
            if DEBUG_CURSOR:
                logger.info(f"🖱️  [DEBUG] Showing visual feedback for click at ({x}, {y})")
            await visual_feedback.show_click_feedback(x, y, cursor_controller)
            logger.debug(f"[MOUSE] Moving mouse to ({x}, {y}) before click")
            await self.page.mouse.move(x, y)
            logger.debug(f"[MOUSE] Mouse moved to ({x}, {y})")
            await asyncio.sleep(0.1)
            logger.debug(f"[CLICK] Executing mouse.click at ({x}, {y})")
            await self.page.mouse.click(x, y)
            logger.debug(f"[CLICK] Mouse click completed at ({x}, {y})")
        else:
            logger.debug(f"[MOUSE] No visual feedback, moving mouse to ({x}, {y})")
            await self.page.mouse.move(x, y)
            logger.debug(f"[MOUSE] Mouse moved to ({x}, {y})")
            await asyncio.sleep(0.05)
            logger.debug(f"[CLICK] Executing mouse.click at ({x}, {y}) [no visual feedback]")
            await self.page.mouse.click(x, y)
            logger.debug(f"[CLICK] Mouse click completed at ({x}, {y})")
        
        # Try to find element via Playwright and click it directly
        try:
            element_handle = await self.page.evaluate_handle("""
                ({text, index}) => {
                    const textLower = text.toLowerCase();
                    const matches = [];
                    
                    // Same matching logic as before
                    const submitSelectors = ['input[type="submit"]', 'button[type="submit"]', 'button:not([type])'];
                    for (const selector of submitSelectors) {
                        const elements = Array.from(document.querySelectorAll(selector));
                        for (const el of elements) {
                            if (el.offsetParent === null || el.style.display === 'none') continue;
                            const directText = Array.from(el.childNodes)
                                .filter(node => node.nodeType === Node.TEXT_NODE)
                                .map(node => node.textContent.trim())
                                .join(' ').trim();
                            const elText = (directText || el.textContent || el.innerText || el.value || '').trim();
                            if (elText.toLowerCase() === textLower || elText.toLowerCase().includes(textLower)) {
                                matches.push({element: el, priority: el.closest('form') ? 10 : 5});
                            }
                        }
                    }
                    
                    const clickableSelectors = ['button', 'a', 'input[type="button"]', '[role="button"]', '[role="link"]'];
                    for (const selector of clickableSelectors) {
                        const elements = Array.from(document.querySelectorAll(selector));
                        for (const el of elements) {
                            if (matches.some(m => m.element === el)) continue;
                            if (el.offsetParent === null || el.style.display === 'none') continue;
                            const directText = Array.from(el.childNodes)
                                .filter(node => node.nodeType === Node.TEXT_NODE)
                                .map(node => node.textContent.trim())
                                .join(' ').trim();
                            const elText = (directText || el.textContent || el.innerText || '').trim();
                            if (elText.toLowerCase() === textLower || elText.toLowerCase().includes(textLower)) {
                                matches.push({element: el, priority: 3});
                            }
                        }
                    }
                    
                    matches.sort((a, b) => b.priority - a.priority);
                    if (matches.length > index && matches[index]) {
                        return matches[index].element;
                    }
                    return null;
                }
            """, {'text': text, 'index': index})
            
            if element_handle and await element_handle.as_element():
                element = await element_handle.as_element()
                return await self._click_element(element, cursor_controller, visual_feedback)
        except Exception as e:
            logger.debug(f"[ELEMENT_INTERACTIONS] Erro ao clicar via element.click(), usando fallback: {e}")
        
        # Fallback: use mouse.click if element.click() didn't work
        logger.debug(f"[CLICK] Fallback: executing mouse.click at ({x}, {y})")
        await self.page.mouse.click(x, y)
        logger.debug(f"[CLICK] Fallback mouse.click completed at ({x}, {y})")
        return True
    
    async def _click_by_selector(
        self,
        selector: str,
        cursor_controller,
        visual_feedback
    ) -> bool:
        """Click element found by selector."""
        logger.debug(f"[ELEMENT_INTERACTIONS] Procurando elemento por selector: '{selector}'")
        element = await self.page.query_selector(selector)
        if not element:
            logger.warning(f"[ELEMENT_INTERACTIONS] Elemento não encontrado: selector='{selector}'")
            return False
        
        logger.debug(f"[ELEMENT_INTERACTIONS] Elemento encontrado por selector")
        box = await element.bounding_box()
        if box:
            x = int(box['x'] + box['width'] / 2)
            y = int(box['y'] + box['height'] / 2)
            logger.debug(f"[ELEMENT_INTERACTIONS] Coordenadas: ({x}, {y})")
            
            if visual_feedback and cursor_controller:
                await visual_feedback.show_click_feedback(x, y, cursor_controller)
            
            logger.debug(f"[CLICK] Executing element.click() to dispatch DOM events")
            await element.click()
            logger.debug(f"[CLICK] element.click() completed successfully")
        else:
            logger.debug(f"[CLICK] No bounding box, using element.click()")
            await element.click()
            logger.debug(f"[CLICK] element.click() completed [no bounding box]")
        return True
    
    async def _click_by_role(
        self,
        role: str,
        index: int,
        cursor_controller,
        visual_feedback
    ) -> bool:
        """Click element found by role."""
        elements = await self.page.query_selector_all(f'[role="{role}"]')
        if not elements or len(elements) <= index:
            return False
        
        element = elements[index]
        box = await element.bounding_box()
        if box:
            x = int(box['x'] + box['width'] / 2)
            y = int(box['y'] + box['height'] / 2)
            
            if visual_feedback and cursor_controller:
                await visual_feedback.show_click_feedback(x, y, cursor_controller)
        
        logger.debug(f"[CLICK] Executing element.click() [role={role}]")
        await element.click()
        logger.debug(f"[CLICK] element.click() completed [role={role}]")
        return True
    
    async def _click_element(
        self,
        element: ElementHandle,
        cursor_controller,
        visual_feedback
    ) -> bool:
        """Click an element with proper event handling."""
        # Check if this is a link
        is_link = await element.evaluate("""
            (el) => {
                return el.tagName?.toUpperCase() === 'A' && (el.href || el.getAttribute('href'));
            }
        """)
        
        # Mark as programmatic click
        await element.evaluate("""
            (el) => {
                el.__playwright_programmatic_click = true;
                window.__playwright_programmatic_click_active = true;
                setTimeout(() => {
                    window.__playwright_programmatic_click_active = false;
                }, 100);
            }
        """)
        
        # Get element coordinates
        element_coords = None
        try:
            box = await element.bounding_box()
            if box:
                element_coords = {
                    'x': int(box['x'] + box['width'] / 2),
                    'y': int(box['y'] + box['height'] / 2)
                }
                if visual_feedback and cursor_controller:
                    if DEBUG_CURSOR:
                        logger.info(f"🖱️  [DEBUG] Moving cursor to element at ({element_coords['x']}, {element_coords['y']})")
                    await visual_feedback.show_click_feedback(element_coords['x'], element_coords['y'], cursor_controller)
                    if DEBUG_CURSOR:
                        logger.info(f"🖱️  [DEBUG] Syncing Playwright mouse to ({element_coords['x']}, {element_coords['y']})")
                    logger.debug(f"[MOUSE] Moving mouse to element at ({element_coords['x']}, {element_coords['y']})")
                    await self.page.mouse.move(element_coords['x'], element_coords['y'])
                    logger.debug(f"[MOUSE] Mouse moved to ({element_coords['x']}, {element_coords['y']})")
                    await asyncio.sleep(0.1)
        except Exception as e:
            logger.debug(f"Error getting element coordinates: {e}")
        
        # Click the element
        logger.debug(f"[CLICK] Executing element.click() [mouse already positioned at ({element_coords['x'] if element_coords else 'unknown'}, {element_coords['y'] if element_coords else 'unknown'})]")
        await element.click()
        logger.debug(f"[CLICK] element.click() completed")
        
        # Handle links specially
        if is_link:
            try:
                await element.evaluate("""
                    (el) => {
                        const clickEvent = new MouseEvent('click', {
                            bubbles: true,
                            cancelable: true,
                            view: window,
                            detail: 1
                        });
                        el.dispatchEvent(clickEvent);
                    }
                """)
                logger.debug(f"[ELEMENT_INTERACTIONS] Manually dispatched click event for link")
            except Exception as e:
                logger.debug(f"[ELEMENT_INTERACTIONS] Error dispatching click event: {e}")
            
            await asyncio.sleep(0.15)
            
            try:
                event_count = await self.page.evaluate("""
                    () => {
                        return (window.__playwright_recording_events || []).length;
                    }
                """)
                logger.debug(f"[ELEMENT_INTERACTIONS] Link clicked, {event_count} event(s) in queue (will be processed during navigation)")
            except Exception as e:
                logger.debug(f"[ELEMENT_INTERACTIONS] Error checking link events: {e}")
        else:
            await asyncio.sleep(0.1)
        
        return True

