#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Type Handler Module.

Handles typing text into input fields with visual feedback.
"""

import asyncio
import logging
from typing import Optional
from playwright.async_api import Page, ElementHandle

from .element_finder import ElementFinder
from .focus_helper import FocusHelper

logger = logging.getLogger(__name__)

DEBUG_CURSOR = True
DEBUG_CLICKS = True


class TypeHandler:
    """Handles typing text into input fields."""
    
    def __init__(self, page: Page, fast_mode: bool = False):
        """
        Initialize type handler.
        
        Args:
            page: Playwright Page instance
            fast_mode: Enable fast mode
        """
        self.page = page
        self.fast_mode = fast_mode
        self.element_finder = ElementFinder(page)
        self.focus_helper = FocusHelper(page)
    
    async def type_text(
        self,
        text: str,
        into: Optional[str] = None,
        selector: Optional[str] = None,
        clear: bool = True,
        cursor_controller = None,
        visual_feedback = None
    ) -> bool:
        """
        Type text into an input field.
        
        Args:
            text: Text to type
            into: Text label of the input field
            selector: CSS selector of the input field
            clear: Clear field before typing
            cursor_controller: Optional CursorController instance for visual feedback
            visual_feedback: Optional VisualFeedback instance
        
        Returns:
            True if typed successfully, False otherwise
        """
        try:
            element = None
            element_coords = None
            
            if into:
                # Find input by label text
                result = await self.element_finder.find_input_by_label(into)
                if result:
                    element_coords = {'x': result.get('x'), 'y': result.get('y')}
                    element = await self.element_finder.get_input_element_handle(into)
            
            if selector and not element:
                element = await self.page.query_selector(selector)
                if element:
                    box = await element.bounding_box()
                    if box:
                        element_coords = {
                            'x': int(box['x'] + box['width'] / 2),
                            'y': int(box['y'] + box['height'] / 2)
                        }
                        logger.debug(f"Found element by selector '{selector}', coords: {element_coords}")
                    else:
                        logger.debug(f"Element found by selector '{selector}' but bounding_box is None")
                else:
                    logger.warning(f"Element not found by selector '{selector}'")
            
            if not element:
                return False
            
            # CRITICAL: Always click on field before typing
            await self._click_before_typing(element, element_coords, cursor_controller, visual_feedback)
            
            # Type the text
            if self.fast_mode:
                await self._type_fast_mode(element, text)
            else:
                await self._type_normal_mode(element, text, clear, element_coords, cursor_controller, visual_feedback)
            
            return True
            
        except Exception as e:
            logger.error(f"Error typing text: {e}")
            return False
    
    async def _click_before_typing(
        self,
        element: ElementHandle,
        element_coords: Optional[dict],
        cursor_controller,
        visual_feedback
    ) -> None:
        """Click on field before typing to ensure it's focused."""
        clicked = False
        coords_to_use = element_coords
        
        # Get coordinates if not available
        if not coords_to_use:
            try:
                box = await element.bounding_box()
                if box:
                    coords_to_use = {
                        'x': int(box['x'] + box['width'] / 2),
                        'y': int(box['y'] + box['height'] / 2)
                    }
                    if DEBUG_CURSOR:
                        logger.info(f"🖱️  [DEBUG] Got bounding_box for element: {coords_to_use}")
            except Exception as e:
                logger.debug(f"Error getting bounding_box: {e}")
        
        if coords_to_use:
            if DEBUG_CURSOR:
                logger.info(f"🖱️  [DEBUG] Preparing to click at ({coords_to_use['x']}, {coords_to_use['y']}) before typing")
                logger.info(f"🖱️  [DEBUG] visual_feedback={visual_feedback is not None}, cursor_controller={cursor_controller is not None}")
            
            # Check if element is already focused
            is_focused = await self.focus_helper.is_focused(element)
            
            # Use visual feedback to move cursor and show click animation
            if visual_feedback and cursor_controller:
                logger.info(f"🎯 Using visual feedback to click at ({coords_to_use['x']}, {coords_to_use['y']})")
                if DEBUG_CURSOR:
                    logger.info(f"🖱️  [DEBUG] Moving cursor visual to ({coords_to_use['x']}, {coords_to_use['y']})")
                await visual_feedback.show_click_feedback(
                    coords_to_use['x'],
                    coords_to_use['y'],
                    cursor_controller
                )
                logger.debug(f"[MOUSE] Syncing Playwright mouse to ({coords_to_use['x']}, {coords_to_use['y']}) before typing")
                await self.page.mouse.move(coords_to_use['x'], coords_to_use['y'])
                logger.debug(f"[MOUSE] Mouse moved to ({coords_to_use['x']}, {coords_to_use['y']})")
                await asyncio.sleep(0.1)
                
                if not is_focused:
                    logger.debug(f"[CLICK] Executing mouse.click at ({coords_to_use['x']}, {coords_to_use['y']}) [element not focused, before typing]")
                    await self.page.mouse.click(coords_to_use['x'], coords_to_use['y'])
                    logger.debug(f"[CLICK] Mouse click completed at ({coords_to_use['x']}, {coords_to_use['y']})")
                else:
                    logger.debug(f"[CLICK] Skipping mouse.click - element already focused (cursor moved for visual consistency)")
            else:
                # Fallback: direct mouse click without animation
                logger.warning(f"⚠️  Clicking directly at ({coords_to_use['x']}, {coords_to_use['y']}) [no visual feedback]")
                if not is_focused:
                    logger.debug(f"[MOUSE] Moving mouse to ({coords_to_use['x']}, {coords_to_use['y']}) [no visual feedback]")
                    await self.page.mouse.move(coords_to_use['x'], coords_to_use['y'])
                    logger.debug(f"[MOUSE] Mouse moved to ({coords_to_use['x']}, {coords_to_use['y']})")
                    logger.debug(f"[CLICK] Executing direct mouse.click at ({coords_to_use['x']}, {coords_to_use['y']}) [no visual feedback]")
                    await self.page.mouse.click(coords_to_use['x'], coords_to_use['y'])
                    logger.debug(f"[CLICK] Direct mouse.click completed at ({coords_to_use['x']}, {coords_to_use['y']})")
                else:
                    logger.debug(f"[CLICK] Skipping direct mouse.click - element already focused")
            clicked = True
            
            # Small delay to allow click event to be captured
            if not is_focused:
                await asyncio.sleep(0.1)
            else:
                await asyncio.sleep(0.05)
        else:
            # Last resort: use element.click()
            logger.debug(f"[CLICK] Using element.click() [fallback - no coordinates]")
            await element.click()
            logger.debug(f"[CLICK] element.click() completed [fallback]")
            clicked = True
            await asyncio.sleep(0.1)
        
        if not clicked:
            logger.error("CRITICAL: Click was not executed before typing! This should never happen.")
            try:
                logger.debug(f"[CLICK] Force clicking element as last resort")
                await element.click()
                logger.debug(f"[CLICK] Force element.click() completed")
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"[CLICK] Failed to click element even as last resort: {e}")
    
    async def _type_fast_mode(self, element: ElementHandle, text: str) -> None:
        """Type text in fast mode (instant value setting)."""
        text_str = str(text)
        logger.debug(f"[TYPE] Fast mode: Setting value '{text_str[:50]}...' (length={len(text_str)}) and dispatching input event")
        await element.evaluate("""
            (el, value) => {
                el.value = value;
                const inputEvent = new Event('input', { bubbles: true, cancelable: true });
                el.dispatchEvent(inputEvent);
                const changeEvent = new Event('change', { bubbles: true, cancelable: true });
                el.dispatchEvent(changeEvent);
            }
        """, text_str)
        logger.debug(f"[TYPE] Fast mode: Input event dispatched, value='{text_str[:50]}...'")
        await asyncio.sleep(0.15)
        logger.debug(f"[TYPE] Fast mode: Triggering blur to finalize input")
        await element.evaluate("""
            (el) => {
                el.blur();
            }
        """)
        logger.debug(f"[TYPE] Fast mode: Blur event triggered")
        await asyncio.sleep(0.2)
        logger.debug(f"[TYPE] Fast mode: Typing completed, value='{text_str[:50]}...'")
    
    async def _type_normal_mode(
        self,
        element: ElementHandle,
        text: str,
        clear: bool,
        element_coords: Optional[dict],
        cursor_controller,
        visual_feedback
    ) -> None:
        """Type text in normal mode (character by character)."""
        # Click on field before typing (for better UX in videos)
        if element_coords:
            if visual_feedback and cursor_controller:
                await visual_feedback.show_click_feedback(
                    element_coords['x'],
                    element_coords['y'],
                    cursor_controller
                )
            logger.debug(f"[CLICK] Clicking element at ({element_coords['x']}, {element_coords['y']}) [normal mode, before typing]")
            await self.page.mouse.click(element_coords['x'], element_coords['y'])
            logger.debug(f"[CLICK] Click completed at ({element_coords['x']}, {element_coords['y']})")
        else:
            # Fallback: try to get coordinates from element
            try:
                box = await element.bounding_box()
                if box:
                    coords = {
                        'x': int(box['x'] + box['width'] / 2),
                        'y': int(box['y'] + box['height'] / 2)
                    }
                    logger.debug(f"[CLICK] Got coordinates from bounding_box: ({coords['x']}, {coords['y']})")
                    if visual_feedback and cursor_controller:
                        await visual_feedback.show_click_feedback(
                            coords['x'],
                            coords['y'],
                            cursor_controller
                        )
                    logger.debug(f"[CLICK] Clicking element at ({coords['x']}, {coords['y']}) [normal mode, before typing]")
                    await self.page.mouse.click(coords['x'], coords['y'])
                    logger.debug(f"[CLICK] Click completed at ({coords['x']}, {coords['y']})")
                else:
                    logger.debug(f"[CLICK] No bounding_box, using element.click() [normal mode, before typing]")
                    await element.click()
                    logger.debug(f"[CLICK] element.click() completed")
            except Exception as e:
                logger.debug(f"[CLICK] Exception getting coordinates, using element.click(): {e}")
                await element.click()
                logger.debug(f"[CLICK] element.click() completed [exception fallback]")
        
        await asyncio.sleep(0.1)
        
        # Type text character by character
        text_str = str(text)
        logger.debug(f"[TYPE] Normal mode: Typing '{text_str[:50]}...' character by character (length={len(text_str)})")
        if clear:
            logger.debug(f"[TYPE] Clearing field before typing")
            await element.fill('')
        for i, char in enumerate(text_str):
            logger.debug(f"[TYPE] Typing character {i+1}/{len(text_str)}: '{char}'")
            await element.type(char, delay=10)
            await asyncio.sleep(0.01)
        logger.debug(f"[TYPE] All characters typed")
        
        # Trigger blur event to finalize input
        logger.debug(f"[TYPE] Triggering blur to finalize input")
        await element.evaluate('el => el.blur()')
        logger.debug(f"[TYPE] Blur triggered")
        await asyncio.sleep(0.1)
        logger.debug(f"[TYPE] Normal mode: Typing completed, value='{text_str[:50]}...'")

