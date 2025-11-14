#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Element Interactions Module.

Handles interactions with elements (click, type, submit).
"""

import asyncio
import logging
from typing import Optional
from playwright.async_api import Page

logger = logging.getLogger(__name__)


class ElementInteractions:
    """Handles interactions with elements."""
    
    def __init__(self, page: Page):
        """Initialize element interactions."""
        self.page = page
    
    async def click(
        self,
        text: Optional[str] = None,
        selector: Optional[str] = None,
        role: Optional[str] = None,
        index: int = 0,
        cursor_controller = None,
        visual_feedback = None
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
                    
                    # Show visual feedback
                    if visual_feedback and cursor_controller:
                        await visual_feedback.show_click_feedback(x, y, cursor_controller)
                    
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
                        
                        # Show visual feedback
                        if visual_feedback and cursor_controller:
                            await visual_feedback.show_click_feedback(x, y, cursor_controller)
                        
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
                        
                        # Show visual feedback
                        if visual_feedback and cursor_controller:
                            await visual_feedback.show_click_feedback(x, y, cursor_controller)
                        
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
                # Find input by label text and get coordinates
                # Support multiple search strategies for better compatibility
                labelTextLower = into.lower()
                result = await self.page.evaluate("""
                    (labelText, labelTextLower) => {
                        // Strategy 1: Find by label text
                        const labels = Array.from(document.querySelectorAll('label'));
                        for (const label of labels) {
                            const labelTextContent = (label.textContent || '').toLowerCase();
                            if (labelTextContent.includes(labelTextLower)) {
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
                        
                        // Strategy 2: Find by placeholder
                        const inputs = Array.from(document.querySelectorAll('input, textarea'));
                        for (const input of inputs) {
                            const placeholder = (input.placeholder || '').toLowerCase();
                            if (placeholder.includes(labelTextLower)) {
                                const rect = input.getBoundingClientRect();
                                return {
                                    found: true,
                                    x: Math.floor(rect.left + rect.width / 2),
                                    y: Math.floor(rect.top + rect.height / 2)
                                };
                            }
                        }
                        
                        // Strategy 3: Find by name/id/aria-label (for common field names)
                        for (const input of inputs) {
                            const name = (input.name || '').toLowerCase();
                            const id = (input.id || '').toLowerCase();
                            const ariaLabel = (input.getAttribute('aria-label') || '').toLowerCase();
                            
                            if (name.includes(labelTextLower) || 
                                id.includes(labelTextLower) || 
                                ariaLabel.includes(labelTextLower)) {
                                const rect = input.getBoundingClientRect();
                                return {
                                    found: true,
                                    x: Math.floor(rect.left + rect.width / 2),
                                    y: Math.floor(rect.top + rect.height / 2)
                                };
                            }
                        }
                        
                        // Strategy 4: Find by type for common field types
                        const typeMap = {
                            'email': ['email', 'e-mail', 'correio', 'mail'],
                            'password': ['password', 'senha', 'pass', 'pwd'],
                            'login': ['login', 'username', 'user', 'usuário']
                        };
                        
                        for (const input of inputs) {
                            const inputType = input.type || '';
                            for (const [type, keywords] of Object.entries(typeMap)) {
                                if (inputType === type && keywords.some(k => labelTextLower.includes(k))) {
                                    const rect = input.getBoundingClientRect();
                                    return {
                                        found: true,
                                        x: Math.floor(rect.left + rect.width / 2),
                                        y: Math.floor(rect.top + rect.height / 2)
                                    };
                                }
                            }
                        }
                        
                        return {found: false};
                    }
                """, into, labelTextLower)
                
                if result.get('found'):
                    element_coords = {'x': result.get('x'), 'y': result.get('y')}
                    # Find element handle for typing (using same strategies)
                    labelTextLower = into.lower()
                    element = await self.page.evaluate_handle("""
                        (labelText, labelTextLower) => {
                            // Strategy 1: Find by label
                            const labels = Array.from(document.querySelectorAll('label'));
                            for (const label of labels) {
                                const labelTextContent = (label.textContent || '').toLowerCase();
                                if (labelTextContent.includes(labelTextLower)) {
                                    const inputId = label.getAttribute('for');
                                    if (inputId) {
                                        const input = document.getElementById(inputId);
                                        if (input) return input;
                                    }
                                    const input = label.parentElement?.querySelector('input, textarea');
                                    if (input) return input;
                                }
                            }
                            
                            // Strategy 2: Find by placeholder
                            const inputs = Array.from(document.querySelectorAll('input, textarea'));
                            for (const input of inputs) {
                                const placeholder = (input.placeholder || '').toLowerCase();
                                if (placeholder.includes(labelTextLower)) {
                                    return input;
                                }
                            }
                            
                            // Strategy 3: Find by name/id/aria-label
                            for (const input of inputs) {
                                const name = (input.name || '').toLowerCase();
                                const id = (input.id || '').toLowerCase();
                                const ariaLabel = (input.getAttribute('aria-label') || '').toLowerCase();
                                
                                if (name.includes(labelTextLower) || 
                                    id.includes(labelTextLower) || 
                                    ariaLabel.includes(labelTextLower)) {
                                    return input;
                                }
                            }
                            
                            // Strategy 4: Find by type
                            const typeMap = {
                                'email': ['email', 'e-mail', 'correio', 'mail'],
                                'password': ['password', 'senha', 'pass', 'pwd'],
                                'login': ['login', 'username', 'user', 'usuário']
                            };
                            
                            for (const input of inputs) {
                                const inputType = input.type || '';
                                for (const [type, keywords] of Object.entries(typeMap)) {
                                    if (inputType === type && keywords.some(k => labelTextLower.includes(k))) {
                                        return input;
                                    }
                                }
                            }
                            
                            return null;
                        }
                    """, into, labelTextLower)
            
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
                # Always click on field before typing (for better UX in videos)
                # This ensures the cursor moves to the field and clicks it
                if element_coords:
                    # Use visual feedback to move cursor and show click animation
                    if visual_feedback and cursor_controller:
                        await visual_feedback.show_click_feedback(
                            element_coords['x'],
                            element_coords['y'],
                            cursor_controller
                        )
                    # Click on element to focus
                    await self.page.mouse.click(element_coords['x'], element_coords['y'])
                else:
                    # Fallback: try to get coordinates from element
                    try:
                        box = await element.bounding_box()
                        if box:
                            coords = {
                                'x': int(box['x'] + box['width'] / 2),
                                'y': int(box['y'] + box['height'] / 2)
                            }
                            if visual_feedback and cursor_controller:
                                await visual_feedback.show_click_feedback(
                                    coords['x'],
                                    coords['y'],
                                    cursor_controller
                                )
                            await self.page.mouse.click(coords['x'], coords['y'])
                        else:
                            await element.click()
                    except:
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
    
    async def submit_form(
        self,
        button_text: Optional[str] = None,
        cursor_controller = None,
        visual_feedback = None
    ) -> bool:
        """
        Submit a form by clicking the submit button.
        
        Args:
            button_text: Optional text to identify specific submit button
            cursor_controller: Optional CursorController instance for visual feedback
            visual_feedback: Optional VisualFeedback instance
        
        Returns:
            True if form was submitted successfully, False otherwise
        """
        try:
            # Find submit button
            result = await self.page.evaluate("""
                ({buttonText}) => {
                    // Strategy 1: Find submit buttons in forms
                    const submitSelectors = [
                        'input[type="submit"]',
                        'button[type="submit"]',
                        'button:not([type])'  // Button without type is submit by default in forms
                    ];
                    
                    const matches = [];
                    
                    for (const selector of submitSelectors) {
                        const elements = Array.from(document.querySelectorAll(selector));
                        for (const el of elements) {
                            if (el.offsetParent === null || el.style.display === 'none') {
                                continue;
                            }
                            
                            // Check if it's in a form
                            const form = el.closest('form');
                            if (!form) {
                                continue;  // Only buttons in forms
                            }
                            
                            // Get button text
                            const elText = (el.textContent || el.innerText || el.value || '').trim();
                            
                            // If button_text specified, check if it matches
                            if (buttonText) {
                                const buttonTextLower = buttonText.toLowerCase();
                                if (!elText.toLowerCase().includes(buttonTextLower)) {
                                    continue;
                                }
                            }
                            
                            const rect = el.getBoundingClientRect();
                            matches.push({
                                element: el,
                                x: Math.floor(rect.left + rect.width / 2),
                                y: Math.floor(rect.top + rect.height / 2),
                                text: elText
                            });
                        }
                    }
                    
                    // If no matches and button_text specified, try any button in form with that text
                    if (matches.length === 0 && buttonText) {
                        const buttonTextLower = buttonText.toLowerCase();
                        const forms = Array.from(document.querySelectorAll('form'));
                        for (const form of forms) {
                            const buttons = Array.from(form.querySelectorAll('button, input[type="button"]'));
                            for (const btn of buttons) {
                                if (btn.offsetParent === null || btn.style.display === 'none') {
                                    continue;
                                }
                                
                                const btnText = (btn.textContent || btn.innerText || btn.value || '').trim();
                                if (btnText.toLowerCase().includes(buttonTextLower)) {
                                    const rect = btn.getBoundingClientRect();
                                    matches.push({
                                        element: btn,
                                        x: Math.floor(rect.left + rect.width / 2),
                                        y: Math.floor(rect.top + rect.height / 2),
                                        text: btnText
                                    });
                                }
                            }
                        }
                    }
                    
                    // Return first match (or None if no matches)
                    if (matches.length > 0) {
                        return {
                            found: true,
                            x: matches[0].x,
                            y: matches[0].y,
                            text: matches[0].text
                        };
                    }
                    
                    return {found: false};
                }
            """, {'buttonText': button_text})
            
            if not result.get('found'):
                logger.warning(f"Submit button not found (button_text: {button_text})")
                return False
            
            x = result.get('x')
            y = result.get('y')
            button_text_found = result.get('text', '')
            
            # Show visual feedback
            if visual_feedback and cursor_controller:
                await visual_feedback.show_click_feedback(x, y, cursor_controller)
            
            # Perform actual click
            await self.page.mouse.click(x, y)
            logger.info(f"Form submitted (button: '{button_text_found}')")
            return True
            
        except Exception as e:
            logger.error(f"Error submitting form: {e}")
            return False
