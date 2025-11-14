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

# Enable debug logging for this module
DEBUG_CURSOR = True  # Set to False to disable cursor debug logs
DEBUG_KEYBOARD = True  # Set to False to disable keyboard debug logs
DEBUG_CLICKS = True  # Set to False to disable click debug logs


class ElementInteractions:
    """Handles interactions with elements."""
    
    def __init__(self, page: Page, fast_mode: bool = False):
        """Initialize element interactions."""
        self.page = page
        self.fast_mode = fast_mode
    
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
                logger.debug(f"[ELEMENT_INTERACTIONS] Procurando elemento por texto: '{text}'")
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
                        
                        // Strategy 3: Labels that can be clicked to focus their associated input
                        const labels = Array.from(document.querySelectorAll('label'));
                        for (const label of labels) {
                            if (label.offsetParent === null || label.style.display === 'none') {
                                continue;
                            }
                            
                            const labelText = (label.textContent || label.innerText || '').trim().toLowerCase();
                            // More flexible matching: check if label text contains the search text or vice versa
                            if (labelText.includes(textLower) || textLower.includes(labelText) || labelText === textLower) {
                                // Find associated input
                                let input = null;
                                const forAttr = label.getAttribute('for');
                                if (forAttr) {
                                    input = document.getElementById(forAttr);
                                }
                                if (!input) {
                                    input = label.querySelector('input, textarea, select');
                                }
                                if (input && input.offsetParent !== null) {
                                    const rect = input.getBoundingClientRect();
                                    matches.push({
                                        element: input,
                                        x: Math.floor(rect.left + rect.width / 2),
                                        y: Math.floor(rect.top + rect.height / 2),
                                        priority: 4,  // Higher than generic clickable, lower than buttons
                                        isSubmit: false
                                    });
                                } else {
                                    // If no input found, click the label itself (some labels are clickable)
                                    const rect = label.getBoundingClientRect();
                                    matches.push({
                                        element: label,
                                        x: Math.floor(rect.left + rect.width / 2),
                                        y: Math.floor(rect.top + rect.height / 2),
                                        priority: 3,
                                        isSubmit: false
                                    });
                                }
                            }
                        }
                        
                        // Strategy 4: Any clickable element with text (lowest priority)
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
                    
                    if DEBUG_CLICKS:
                        logger.info(f"🖱️  [DEBUG] Element found at ({x}, {y}), preparing to click")
                    
                    # Show visual feedback
                    if visual_feedback and cursor_controller:
                        if DEBUG_CURSOR:
                            logger.info(f"🖱️  [DEBUG] Showing visual feedback for click at ({x}, {y})")
                        await visual_feedback.show_click_feedback(x, y, cursor_controller)
                        # After visual feedback moves cursor, sync Playwright mouse position
                        # This ensures the actual click happens where the cursor visual is
                        if DEBUG_CURSOR:
                            logger.info(f"🖱️  [DEBUG] Syncing Playwright mouse to ({x}, {y})")
                        await self.page.mouse.move(x, y)
                        await asyncio.sleep(0.05)  # Small delay to ensure mouse is positioned
                        if DEBUG_CLICKS:
                            logger.info(f"🖱️  [DEBUG] Executing mouse.click at ({x}, {y})")
                        await self.page.mouse.click(x, y)
                        if DEBUG_CLICKS:
                            logger.info(f"🖱️  [DEBUG] Mouse click completed at ({x}, {y})")
                    
                    # Try to find element via Playwright and click it directly (dispatches DOM events that event_capture can catch)
                    # This is more reliable than JavaScript element.click() inside page.evaluate()
                    try:
                        # Find element using the same logic but via Playwright
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
                            # Use Playwright's element.click() which dispatches DOM events that event_capture can catch
                            element = await element_handle.as_element()
                            
                            # Check if this is a link (has href) - links cause navigation and need immediate processing
                            is_link = await element.evaluate("""
                                (el) => {
                                    return el.tagName?.toUpperCase() === 'A' && (el.href || el.getAttribute('href'));
                                }
                            """)
                            
                            # CRITICAL: Mark this as a programmatic click so event_capture ignores it
                            # We add the step directly to YAML, so we don't want event_capture to also capture it
                            await element.evaluate("""
                                (el) => {
                                    // Set a flag on the element to mark it as programmatic
                                    el.__playwright_programmatic_click = true;
                                    // Also set a global flag temporarily
                                    window.__playwright_programmatic_click_active = true;
                                    setTimeout(() => {
                                        window.__playwright_programmatic_click_active = false;
                                    }, 100);
                                }
                            """)
                            
                            await element.click()
                            
                            # If it's a link, we need to ensure the event is captured before navigation
                            # Since links cause immediate navigation, we need to manually dispatch the click event
                            # to ensure it's captured by the event_capture listener
                            if is_link:
                                # Manually dispatch a click event to ensure it's captured
                                # This is necessary because Playwright's element.click() might not trigger
                                # the DOM event listener in time before navigation
                                try:
                                    await element.evaluate("""
                                        (el) => {
                                            // Dispatch a synthetic click event that will be captured by our listener
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
                                
                                # Give time for the event to be added to the array
                                await asyncio.sleep(0.15)
                                
                                # Check if event was captured
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
                                # Small delay for non-links
                                await asyncio.sleep(0.1)
                            return True
                    except Exception as e:
                        logger.debug(f"[ELEMENT_INTERACTIONS] Erro ao clicar via element.click(), usando fallback: {e}")
                    
                    # Fallback: use mouse.click if element.click() didn't work
                    await self.page.mouse.click(x, y)
                    return True
                return False
            
            if selector:
                logger.debug(f"[ELEMENT_INTERACTIONS] Procurando elemento por selector: '{selector}'")
                element = await self.page.query_selector(selector)
                if element:
                    logger.debug(f"[ELEMENT_INTERACTIONS] Elemento encontrado por selector")
                    # Get coordinates for visual feedback
                    box = await element.bounding_box()
                    if box:
                        x = int(box['x'] + box['width'] / 2)
                        y = int(box['y'] + box['height'] / 2)
                        logger.debug(f"[ELEMENT_INTERACTIONS] Coordenadas: ({x}, {y})")
                        
                        # Show visual feedback
                        if visual_feedback and cursor_controller:
                            await visual_feedback.show_click_feedback(x, y, cursor_controller)
                        
                        logger.debug(f"[ELEMENT_INTERACTIONS] Executando click via element.click() para disparar eventos DOM...")
                        # Use element.click() to dispatch DOM events that event_capture can catch
                        await element.click()
                        logger.debug(f"[ELEMENT_INTERACTIONS] Click executado com sucesso!")
                    else:
                        logger.debug(f"[ELEMENT_INTERACTIONS] Sem bounding box, usando element.click()")
                        await element.click()
                    return True
                logger.warning(f"[ELEMENT_INTERACTIONS] Elemento não encontrado: selector='{selector}'")
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
                    
                    # Use element.click() to dispatch DOM events that event_capture can catch
                    await element.click()
                    return True
                return False
            
            return False
            
        except Exception as e:
            logger.error(f"[ELEMENT_INTERACTIONS] Erro ao clicar: {e}", exc_info=True)
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
                    (args) => {
                        const labelText = args.labelText;
                        const labelTextLower = args.labelTextLower;
                        
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
                            'email': ['email', 'e-mail', 'e-mail', 'correio', 'mail'],
                            'password': ['password', 'senha', 'pass', 'pwd'],
                            'login': ['login', 'username', 'user', 'usuário']
                        };
                        
                        for (const input of inputs) {
                            const inputType = input.type || '';
                            for (const [type, keywords] of Object.entries(typeMap)) {
                                // Check if input type matches AND label text contains any keyword
                                if (inputType === type && keywords.some(k => labelTextLower.includes(k) || k.includes(labelTextLower))) {
                                    const rect = input.getBoundingClientRect();
                                    return {
                                        found: true,
                                        x: Math.floor(rect.left + rect.width / 2),
                                        y: Math.floor(rect.top + rect.height / 2)
                                    };
                                }
                            }
                        }
                        
                        // Strategy 5: Find by input order (first text input is usually email/login)
                        // Only if searching for email/login and no other strategy worked
                        if (labelTextLower.includes('email') || labelTextLower.includes('login') || labelTextLower.includes('mail')) {
                            const textInputs = inputs.filter(inp => inp.type === 'text' || inp.type === 'email');
                            if (textInputs.length > 0) {
                                const firstTextInput = textInputs[0];
                                const rect = firstTextInput.getBoundingClientRect();
                                return {
                                    found: true,
                                    x: Math.floor(rect.left + rect.width / 2),
                                    y: Math.floor(rect.top + rect.height / 2)
                                };
                            }
                        }
                        
                        return {found: false};
                    }
                """, {'labelText': into, 'labelTextLower': labelTextLower})
                
                if result.get('found'):
                    element_coords = {'x': result.get('x'), 'y': result.get('y')}
                    # Find element handle for typing (using same strategies)
                    labelTextLower = into.lower()
                    element = await self.page.evaluate_handle("""
                        (args) => {
                            const labelText = args.labelText;
                            const labelTextLower = args.labelTextLower;
                            
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
                                'email': ['email', 'e-mail', 'e-mail', 'correio', 'mail'],
                                'password': ['password', 'senha', 'pass', 'pwd'],
                                'login': ['login', 'username', 'user', 'usuário']
                            };
                            
                            for (const input of inputs) {
                                const inputType = input.type || '';
                                for (const [type, keywords] of Object.entries(typeMap)) {
                                    // Check if input type matches AND label text contains any keyword
                                    if (inputType === type && keywords.some(k => labelTextLower.includes(k) || k.includes(labelTextLower))) {
                                        return input;
                                    }
                                }
                            }
                            
                            // Strategy 5: Find by input order (first text input is usually email/login)
                            // Only if searching for email/login and no other strategy worked
                            if (labelTextLower.includes('email') || labelTextLower.includes('login') || labelTextLower.includes('mail')) {
                                const textInputs = inputs.filter(inp => inp.type === 'text' || inp.type === 'email');
                                if (textInputs.length > 0) {
                                    return textInputs[0];
                                }
                            }
                            
                            // Strategy 6: Find by name/id if it matches common patterns
                            for (const input of inputs) {
                                const name = (input.name || '').toLowerCase();
                                const id = (input.id || '').toLowerCase();
                                
                                // Common patterns: login, email, username, user
                                if (labelTextLower.includes('email') || labelTextLower.includes('login') || labelTextLower.includes('mail')) {
                                    if (name === 'login' || name === 'email' || name === 'username' || name === 'user' ||
                                        id === 'login' || id === 'email' || id === 'username' || id === 'user') {
                                        return input;
                                    }
                                }
                                // Common patterns: password, pass, pwd
                                if (labelTextLower.includes('password') || labelTextLower.includes('senha') || labelTextLower.includes('pass')) {
                                    if (name === 'password' || name === 'pass' || name === 'pwd' ||
                                        id === 'password' || id === 'pass' || id === 'pwd') {
                                        return input;
                                    }
                                }
                            }
                            
                            return null;
                        }
                    """, {'labelText': into, 'labelTextLower': labelTextLower})
            
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
            
            if element:
                # CRITICAL: Always click on field before typing (even in fast_mode)
                # This ensures the click is captured in YAML and matches real user behavior
                # Click must happen BEFORE typing to be captured correctly
                # ALWAYS use visual feedback when available (even in fast_mode) for better UX
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
                    
                    # Use visual feedback to move cursor and show click animation (even in fast_mode)
                    if visual_feedback and cursor_controller:
                        logger.info(f"🎯 Using visual feedback to click at ({coords_to_use['x']}, {coords_to_use['y']})")
                        if DEBUG_CURSOR:
                            logger.info(f"🖱️  [DEBUG] Moving cursor visual to ({coords_to_use['x']}, {coords_to_use['y']})")
                        await visual_feedback.show_click_feedback(
                            coords_to_use['x'],
                            coords_to_use['y'],
                            cursor_controller
                        )
                        # After visual feedback moves cursor, sync Playwright mouse position
                        # This ensures the actual click happens where the cursor visual is
                        if DEBUG_CURSOR:
                            logger.info(f"🖱️  [DEBUG] Syncing Playwright mouse to ({coords_to_use['x']}, {coords_to_use['y']})")
                        await self.page.mouse.move(coords_to_use['x'], coords_to_use['y'])
                        await asyncio.sleep(0.05)  # Small delay to ensure mouse is positioned
                        # Always click - this ensures the click event is captured in YAML
                        # Even if field is already focused, we need the click for the video
                        if DEBUG_CLICKS:
                            logger.info(f"🖱️  [DEBUG] Executing mouse.click at ({coords_to_use['x']}, {coords_to_use['y']})")
                        await self.page.mouse.click(coords_to_use['x'], coords_to_use['y'])
                        if DEBUG_CLICKS:
                            logger.info(f"🖱️  [DEBUG] Mouse click completed at ({coords_to_use['x']}, {coords_to_use['y']})")
                    else:
                        # Fallback: direct mouse click without animation
                        logger.warning(f"⚠️  Clicking directly at ({coords_to_use['x']}, {coords_to_use['y']}) [no visual feedback - visual_feedback={visual_feedback is not None}, cursor_controller={cursor_controller is not None}]")
                        if DEBUG_CLICKS:
                            logger.info(f"🖱️  [DEBUG] Executing direct mouse.click at ({coords_to_use['x']}, {coords_to_use['y']}) [no visual feedback]")
                        await self.page.mouse.click(coords_to_use['x'], coords_to_use['y'])
                    clicked = True
                    # Small delay to allow click event to be captured
                    await asyncio.sleep(0.1)
                else:
                    # Last resort: use element.click() which also triggers click event
                    logger.info(f"Clicking on field using element.click() [fallback - no coordinates]")
                    await element.click()
                    clicked = True
                    await asyncio.sleep(0.1)
                
                if not clicked:
                    logger.error("CRITICAL: Click was not executed before typing! This should never happen.")
                    # Force click as last resort
                    try:
                        await element.click()
                        await asyncio.sleep(0.1)
                    except Exception as e:
                        logger.error(f"Failed to click element even as last resort: {e}")
                
                if self.fast_mode:
                    # In fast mode: type instantly after click (click already happened above)
                    text_str = str(text)
                    logger.debug(f"Fast mode typing: Setting value '{text_str[:50]}...' and dispatching input event")
                    await element.evaluate("""
                        (el, value) => {
                            // Clear and set value instantly
                            el.value = value;
                            // Trigger single input event (not per character - much faster)
                            const inputEvent = new Event('input', { bubbles: true, cancelable: true });
                            el.dispatchEvent(inputEvent);
                            // Trigger change event (for form validation)
                            const changeEvent = new Event('change', { bubbles: true, cancelable: true });
                            el.dispatchEvent(changeEvent);
                        }
                    """, text_str)
                    # Increased delay to allow event_capture to process input before blur
                    # This ensures the input event is captured and processed before blur is triggered
                    logger.debug("Fast mode typing: Waiting for event_capture to process input event")
                    await asyncio.sleep(0.15)  # Increased from 0.05s to 0.15s for better reliability
                    # Trigger blur to finalize (after event_capture has processed input)
                    logger.debug("Fast mode typing: Triggering blur to finalize input")
                    await element.evaluate("""
                        (el) => {
                            el.blur();
                        }
                    """)
                    # Increased delay to ensure blur event is captured and processed
                    # This is critical for password fields and other inputs that might be followed by submit
                    await asyncio.sleep(0.2)  # Increased from 0.05s to 0.2s for better reliability
                else:
                    # Normal mode: click on field before typing (for better UX in videos)
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
                    
                    # Small delay after click
                    await asyncio.sleep(0.1)
                    
                    # Type text character by character to trigger input events
                    # This ensures events are captured by event_capture
                    if clear:
                        await element.fill('')
                    text_str = str(text)
                    for char in text_str:
                        await element.type(char, delay=10)
                        await asyncio.sleep(0.01)
                    
                    # Trigger blur event to finalize input (so it's captured)
                    await element.evaluate('el => el.blur()')
                    await asyncio.sleep(0.1)
                
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
            
            # Use mouse click directly - this will trigger DOM events that event_capture can catch
            # The mouse.click() from Playwright triggers native browser events that are captured by event_capture
            await self.page.mouse.click(x, y)
            
            # Small delay to ensure click event is captured (reduced in fast mode)
            await asyncio.sleep(0.05 if self.fast_mode else 0.15)
            
            logger.info(f"Form submitted (button: '{button_text_found}')")
            return True
            
        except Exception as e:
            logger.error(f"Error submitting form: {e}")
            return False
