#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Element Finder Module.

Handles finding elements by text, selector, role, etc.
"""

import logging
from typing import Optional, Dict, Any
from playwright.async_api import Page, ElementHandle

logger = logging.getLogger(__name__)


class ElementFinder:
    """Helper class for finding elements on the page."""
    
    def __init__(self, page: Page):
        """
        Initialize element finder.
        
        Args:
            page: Playwright Page instance
        """
        self.page = page
    
    async def find_by_text(
        self,
        text: str,
        index: int = 0
    ) -> Optional[Dict[str, Any]]:
        """
        Find element by text content.
        
        Args:
            text: Text content to search for
            index: Index if multiple matches (default: 0)
            
        Returns:
            Dictionary with 'found', 'x', 'y', 'element', 'isSubmit' or None
        """
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
        
        return result if result.get('found') else None
    
    async def find_input_by_label(
        self,
        label_text: str
    ) -> Optional[Dict[str, Any]]:
        """
        Find input element by label text.
        
        Args:
            label_text: Label text to search for
            
        Returns:
            Dictionary with 'found', 'x', 'y' or None
        """
        labelTextLower = label_text.lower()
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
        """, {'labelText': label_text, 'labelTextLower': labelTextLower})
        
        return result if result.get('found') else None
    
    async def get_input_element_handle(
        self,
        label_text: str
    ) -> Optional[ElementHandle]:
        """
        Get input element handle by label text.
        
        Args:
            label_text: Label text to search for
            
        Returns:
            ElementHandle or None
        """
        labelTextLower = label_text.lower()
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
        """, {'labelText': label_text, 'labelTextLower': labelTextLower})
        
        if element:
            # evaluate_handle already returns an ElementHandle, not a JSHandle
            # So we can use it directly without calling as_element()
            return element
        return None
    
    async def find_submit_button(
        self,
        button_text: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Find submit button in a form.
        
        Args:
            button_text: Optional text to identify specific submit button
            
        Returns:
            Dictionary with 'found', 'x', 'y', 'text' or None
        """
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
        
        return result if result.get('found') else None

