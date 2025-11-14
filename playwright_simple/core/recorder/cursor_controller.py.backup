#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cursor controller module.

Controls a visual cursor overlay in the browser that can be moved and clicked via terminal commands.
"""

import asyncio
import logging
from typing import Optional, Tuple
from playwright.async_api import Page

logger = logging.getLogger(__name__)


class CursorController:
    """Controls a visual cursor overlay in the browser."""
    
    def __init__(self, page: Page):
        """Initialize cursor controller."""
        self.page = page
        self.is_active = False
        self.current_x = 0
        self.current_y = 0
    
    async def start(self, force: bool = False):
        """Start cursor controller and inject cursor overlay."""
        if self.is_active and not force:
            # Still ensure cursor is visible
            await self.show()
            return
        
        try:
            # Wait for page to be ready
            try:
                await self.page.wait_for_load_state('domcontentloaded', timeout=5000)
            except:
                pass  # Continue even if timeout
            
            # Reset flag to allow reinjection
            await self.page.evaluate("""
                () => {
                    window.__playwright_cursor_initialized = false;
                }
            """)
            
            await self.page.evaluate("""
                (function() {
                    // Always recreate cursor (in case of navigation)
                    const existing = document.getElementById('__playwright_cursor');
                    if (existing) existing.remove();
                    const existingClick = document.getElementById('__playwright_cursor_click');
                    if (existingClick) existingClick.remove();
                    const existingStyle = document.getElementById('__playwright_cursor_style');
                    if (existingStyle) existingStyle.remove();
                    
                    // Create cursor overlay
                    const cursor = document.createElement('div');
                    cursor.id = '__playwright_cursor';
                    cursor.style.cssText = `
                        position: fixed;
                        width: 0;
                        height: 0;
                        border-left: 8px solid transparent;
                        border-right: 8px solid transparent;
                        border-top: 12px solid #0066ff;
                        pointer-events: none;
                        z-index: 999999;
                        transform: translate(-50%, -50%);
                        display: block;
                        left: 100px;
                        top: 100px;
                        filter: drop-shadow(0 0 3px rgba(0, 102, 255, 0.8));
                    `;
                    
                    // Create click indicator
                    const clickIndicator = document.createElement('div');
                    clickIndicator.id = '__playwright_cursor_click';
                    clickIndicator.style.cssText = `
                        position: fixed;
                        width: 30px;
                        height: 30px;
                        border: 3px solid #0066ff;
                        border-radius: 50%;
                        pointer-events: none;
                        z-index: 999998;
                        transform: translate(-50%, -50%);
                        display: none;
                        animation: cursorClick 0.3s ease-out;
                    `;
                    
                    // Add click animation
                    let style = document.getElementById('__playwright_cursor_style');
                    if (!style) {
                        style = document.createElement('style');
                        style.id = '__playwright_cursor_style';
                        style.textContent = `
                            @keyframes cursorClick {
                                0% {
                                    transform: translate(-50%, -50%) scale(0.5);
                                    opacity: 1;
                                }
                                100% {
                                    transform: translate(-50%, -50%) scale(2);
                                    opacity: 0;
                                }
                            }
                        `;
                        document.head.appendChild(style);
                    }
                    
                    document.body.appendChild(cursor);
                    document.body.appendChild(clickIndicator);
                    
                    // Store cursor element
                    window.__playwright_cursor_element = cursor;
                    window.__playwright_cursor_click_element = clickIndicator;
                    window.__playwright_cursor_initialized = true;
                })();
            """)
            
            # Set initial position
            self.current_x = 100
            self.current_y = 100
            
            # Verify cursor was created
            cursor_exists = await self.page.evaluate("""
                () => {
                    return document.getElementById('__playwright_cursor') !== null;
                }
            """)
            
            self.is_active = True
            if cursor_exists:
                logger.info("Cursor controller started - cursor element created")
                print("   ✓ Cursor visual inicializado")
            else:
                logger.warning("Cursor controller started but cursor element not found")
                print("   ⚠️  Cursor visual não foi criado")
        except Exception as e:
            logger.error(f"Error starting cursor controller: {e}", exc_info=True)
            print(f"   ❌ Erro ao inicializar cursor: {e}")
    
    async def show(self):
        """Show cursor overlay."""
        try:
            # Ensure cursor is initialized
            if not self.is_active:
                await self.start()
            
            result = await self.page.evaluate(f"""
                () => {{
                    const cursor = document.getElementById('__playwright_cursor');
                    if (cursor) {{
                        cursor.style.display = 'block';
                        cursor.style.left = '{self.current_x}px';
                        cursor.style.top = '{self.current_y}px';
                        cursor.style.visibility = 'visible';
                        cursor.style.opacity = '1';
                        return true;
                    }} else {{
                        // Reinitialize if missing
                        window.__playwright_cursor_initialized = false;
                        return false;
                    }}
                }}
            """)
            
            if result:
                logger.debug(f"Cursor shown at ({self.current_x}, {self.current_y})")
            else:
                logger.warning("Cursor element not found, reinitializing...")
                # Try to reinitialize
                await self.start(force=True)
                # Try again
                await self.page.evaluate(f"""
                    () => {{
                        const cursor = document.getElementById('__playwright_cursor');
                        if (cursor) {{
                            cursor.style.display = 'block';
                            cursor.style.left = '{self.current_x}px';
                            cursor.style.top = '{self.current_y}px';
                        }}
                    }}
                """)
        except Exception as e:
            logger.debug(f"Error showing cursor: {e}")
            # Try to reinitialize
            await self.start(force=True)
    
    async def hide(self):
        """Hide cursor overlay."""
        try:
            await self.page.evaluate("""
                () => {
                    const cursor = document.getElementById('__playwright_cursor');
                    if (cursor) {
                        cursor.style.display = 'none';
                    }
                }
            """)
            logger.debug("Cursor hidden")
        except Exception as e:
            logger.debug(f"Error hiding cursor: {e}")
    
    async def move(self, x: int, y: int, smooth: bool = True):
        """Move cursor to position."""
        try:
            self.current_x = x
            self.current_y = y
            
            # Ensure cursor is initialized and visible when moving
            if not self.is_active:
                await self.start()
            await self.show()
            
            if smooth:
                # Smooth animation to position
                await self.page.evaluate(f"""
                    () => {{
                        const cursor = document.getElementById('__playwright_cursor');
                        if (cursor) {{
                            cursor.style.transition = 'left 0.3s ease-out, top 0.3s ease-out';
                            cursor.style.left = '{x}px';
                            cursor.style.top = '{y}px';
                            cursor.style.display = 'block';
                            
                            // Remove transition after animation
                            setTimeout(() => {{
                                cursor.style.transition = 'none';
                            }}, 300);
                        }}
                    }}
                """)
            else:
                # Instant move
                await self.page.evaluate(f"""
                    () => {{
                        const cursor = document.getElementById('__playwright_cursor');
                        if (cursor) {{
                            cursor.style.left = '{x}px';
                            cursor.style.top = '{y}px';
                            cursor.style.display = 'block';
                        }}
                    }}
                """)
            logger.debug(f"Cursor moved to ({x}, {y})")
        except Exception as e:
            logger.error(f"Error moving cursor: {e}")
    
    async def click(self, x: Optional[int] = None, y: Optional[int] = None):
        """Click at cursor position or specified coordinates."""
        try:
            click_x = x if x is not None else self.current_x
            click_y = y if y is not None else self.current_y
            
            # Ensure cursor is visible
            await self.show()
            
            # Move cursor if coordinates provided
            if x is not None and y is not None:
                await self.move(click_x, click_y, smooth=True)
                await asyncio.sleep(0.2)  # Small delay so user can see cursor move
            
            # Show click animation
            await self.page.evaluate(f"""
                () => {{
                    const clickIndicator = document.getElementById('__playwright_cursor_click');
                    if (clickIndicator) {{
                        clickIndicator.style.left = '{click_x}px';
                        clickIndicator.style.top = '{click_y}px';
                        clickIndicator.style.display = 'block';
                        setTimeout(() => {{
                            clickIndicator.style.display = 'none';
                        }}, 300);
                    }}
                }}
            """)
            
            # Perform actual click
            await self.page.mouse.click(click_x, click_y)
            logger.info(f"Cursor clicked at ({click_x}, {click_y})")
        except Exception as e:
            logger.error(f"Error clicking cursor: {e}")
    
    async def click_by_text(self, text: str) -> bool:
        """
        Click on element by text content, placeholder, or input type.
        Moves cursor to element and then clicks.
        
        Supports:
        - click Entrar (button text)
        - click placeholder senha (input by placeholder)
        - click input senha (input by label/name/placeholder)
        - click input email (input by type or label)
        
        Args:
            text: Text to search for (partial match, case-insensitive)
                  Can be prefixed with "placeholder " or "input " for specific searches
            
        Returns:
            True if element was found and clicked, False otherwise
        """
        try:
            # Ensure cursor is initialized and visible
            if not self.is_active:
                await self.start()
            await self.show()
            logger.info(f"Attempting to click by text: '{text}'")
            
            # Check for special prefixes
            text_lower = text.lower().strip()
            search_placeholder = text_lower.startswith('placeholder ')
            search_input = text_lower.startswith('input ')
            search_submit = text_lower == 'submit' or text_lower.startswith('submit ')
            
            if search_placeholder:
                search_text = text[11:].strip()  # Remove "placeholder "
                return await self._click_by_placeholder(search_text)
            elif search_input:
                search_text = text[6:].strip()  # Remove "input "
                return await self._click_by_input(search_text)
            elif search_submit:
                search_text = text[7:].strip() if len(text) > 7 else ''  # Remove "submit " if present
                return await self._click_by_submit(search_text)
            
            # Regular text search (buttons, links, etc.)
            # Escape text for JavaScript
            escaped_text = text.replace("'", "\\'").replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')
            
            # Find element by text
            element_info = await self.page.evaluate(f"""
                () => {{
                    // Try multiple strategies
                    const text = '{escaped_text}';
                    const lowerText = text.toLowerCase();
                    
                    // Strategy 1: Button with exact or partial text match (priority)
                    let element = Array.from(document.querySelectorAll('button, a, input[type="button"], input[type="submit"]')).find(el => {{
                        const elText = (el.textContent || el.value || el.getAttribute('aria-label') || '').trim();
                        return elText.toLowerCase() === lowerText || elText.toLowerCase().includes(lowerText);
                    }});
                    
                    // Strategy 2: Any clickable element
                    if (!element) {{
                        element = Array.from(document.querySelectorAll('a, button, [role="button"], [onclick], input[type="button"], input[type="submit"]')).find(el => {{
                            const elText = (el.textContent || el.value || el.getAttribute('aria-label') || '').trim();
                            return elText.toLowerCase().includes(lowerText);
                        }});
                    }}
                    
                    // Strategy 3: Exact text match in any element
                    if (!element) {{
                        element = Array.from(document.querySelectorAll('*')).find(el => {{
                            const elText = (el.textContent || '').trim();
                            return elText.toLowerCase() === lowerText || elText.toLowerCase().includes(lowerText);
                        }});
                    }}
                    
                    if (element) {{
                        const rect = element.getBoundingClientRect();
                        return {{
                            found: true,
                            x: Math.floor(rect.left + rect.width / 2),
                            y: Math.floor(rect.top + rect.height / 2),
                            tagName: element.tagName,
                            text: (element.textContent || element.value || '').trim(),
                            id: element.id || '',
                            name: element.name || ''
                        }};
                    }}
                    
                    return {{ found: false }};
                }}
            """)
            
            if not element_info or not element_info.get('found'):
                logger.warning(f"Element with text '{text}' not found")
                print(f"   ⚠️  Elemento '{text}' não encontrado")
                return False
            
            click_x = element_info['x']
            click_y = element_info['y']
            
            logger.info(f"Found element '{text}' at ({click_x}, {click_y})")
            print(f"   ✓ Elemento '{text}' encontrado em ({click_x}, {click_y})")
            
            # Move cursor to element position with a small delay for visibility
            await self.move(click_x, click_y)
            await asyncio.sleep(0.3)  # Small delay so user can see cursor move
            
            # Show click animation
            await self.page.evaluate(f"""
                () => {{
                    const clickIndicator = document.getElementById('__playwright_cursor_click');
                    if (clickIndicator) {{
                        clickIndicator.style.left = '{click_x}px';
                        clickIndicator.style.top = '{click_y}px';
                        clickIndicator.style.display = 'block';
                        setTimeout(() => {{
                            clickIndicator.style.display = 'none';
                        }}, 300);
                    }}
                }}
            """)
            
            # Perform actual click
            await self.page.mouse.click(click_x, click_y)
            logger.info(f"Clicked on element with text '{text}' at ({click_x}, {click_y})")
            return True
        except Exception as e:
            logger.error(f"Error clicking by text: {e}")
            return False
    
    async def _click_by_placeholder(self, placeholder_text: str) -> bool:
        """Click on input by placeholder."""
        try:
            escaped_text = placeholder_text.replace("'", "\\'").replace('"', '\\"')
            
            element_info = await self.page.evaluate(f"""
                () => {{
                    const searchText = '{escaped_text}'.toLowerCase();
                    
                    // Find input by placeholder
                    let field = Array.from(document.querySelectorAll('input, textarea')).find(el => {{
                        const placeholder = (el.placeholder || '').toLowerCase();
                        return placeholder.includes(searchText);
                    }});
                    
                    if (field) {{
                        const rect = field.getBoundingClientRect();
                        return {{
                            found: true,
                            x: Math.floor(rect.left + rect.width / 2),
                            y: Math.floor(rect.top + rect.height / 2),
                            tagName: field.tagName,
                            placeholder: field.placeholder || '',
                            name: field.name || '',
                            id: field.id || ''
                        }};
                    }}
                    
                    return {{ found: false }};
                }}
            """)
            
            if not element_info or not element_info.get('found'):
                return False
            
            click_x = element_info['x']
            click_y = element_info['y']
            
            await self.move(click_x, click_y)
            await asyncio.sleep(0.2)
            
            await self.page.evaluate(f"""
                () => {{
                    const clickIndicator = document.getElementById('__playwright_cursor_click');
                    if (clickIndicator) {{
                        clickIndicator.style.left = '{click_x}px';
                        clickIndicator.style.top = '{click_y}px';
                        clickIndicator.style.display = 'block';
                        setTimeout(() => {{
                            clickIndicator.style.display = 'none';
                        }}, 300);
                    }}
                }}
            """)
            
            await self.page.mouse.click(click_x, click_y)
            logger.info(f"Clicked on input with placeholder '{placeholder_text}' at ({click_x}, {click_y})")
            return True
        except Exception as e:
            logger.error(f"Error clicking by placeholder: {e}")
            return False
    
    async def _click_by_input(self, search_text: str) -> bool:
        """Click on input by label, name, placeholder, or type."""
        try:
            escaped_text = search_text.replace("'", "\\'").replace('"', '\\"')
            
            element_info = await self.page.evaluate(f"""
                () => {{
                    const searchText = '{escaped_text}'.toLowerCase();
                    
                    // Strategy 1: Find by label text
                    let field = null;
                    const labels = Array.from(document.querySelectorAll('label'));
                    const label = labels.find(l => {{
                        const labelText = (l.textContent || '').trim().toLowerCase();
                        return labelText.includes(searchText);
                    }});
                    
                    if (label) {{
                        if (label.htmlFor) {{
                            field = document.getElementById(label.htmlFor);
                        }} else {{
                            // Find input near label
                            const labelParent = label.parentElement;
                            if (labelParent) {{
                                field = labelParent.querySelector('input, textarea');
                            }}
                        }}
                    }}
                    
                    // Strategy 2: Find by placeholder
                    if (!field) {{
                        field = Array.from(document.querySelectorAll('input, textarea')).find(el => {{
                            const placeholder = (el.placeholder || '').toLowerCase();
                            return placeholder.includes(searchText);
                        }});
                    }}
                    
                    // Strategy 3: Find by name
                    if (!field) {{
                        field = Array.from(document.querySelectorAll('input, textarea')).find(el => {{
                            const name = (el.name || '').toLowerCase();
                            return name.includes(searchText);
                        }});
                    }}
                    
                    // Strategy 4: Find by id
                    if (!field) {{
                        field = Array.from(document.querySelectorAll('input, textarea')).find(el => {{
                            const id = (el.id || '').toLowerCase();
                            return id.includes(searchText);
                        }});
                    }}
                    
                    // Strategy 5: Find by type (email, password, etc.)
                    if (!field) {{
                        field = Array.from(document.querySelectorAll('input, textarea')).find(el => {{
                            const type = (el.type || '').toLowerCase();
                            return type === searchText;
                        }});
                    }}
                    
                    if (field && (field.tagName === 'INPUT' || field.tagName === 'TEXTAREA')) {{
                        const rect = field.getBoundingClientRect();
                        return {{
                            found: true,
                            x: Math.floor(rect.left + rect.width / 2),
                            y: Math.floor(rect.top + rect.height / 2),
                            tagName: field.tagName,
                            placeholder: field.placeholder || '',
                            name: field.name || '',
                            id: field.id || '',
                            type: field.type || ''
                        }};
                    }}
                    
                    return {{ found: false }};
                }}
            """)
            
            if not element_info or not element_info.get('found'):
                return False
            
            click_x = element_info['x']
            click_y = element_info['y']
            
            await self.move(click_x, click_y)
            await asyncio.sleep(0.2)
            
            await self.page.evaluate(f"""
                () => {{
                    const clickIndicator = document.getElementById('__playwright_cursor_click');
                    if (clickIndicator) {{
                        clickIndicator.style.left = '{click_x}px';
                        clickIndicator.style.top = '{click_y}px';
                        clickIndicator.style.display = 'block';
                        setTimeout(() => {{
                            clickIndicator.style.display = 'none';
                        }}, 300);
                    }}
                }}
            """)
            
            await self.page.mouse.click(click_x, click_y)
            logger.info(f"Clicked on input '{search_text}' at ({click_x}, {click_y})")
            return True
        except Exception as e:
            logger.error(f"Error clicking by input: {e}")
            return False
    
    async def _click_by_submit(self, text_filter: str = '') -> bool:
        """Click on submit button (input[type="submit"], button[type="submit"], or buttons with submit text)."""
        try:
            escaped_text = text_filter.replace("'", "\\'").replace('"', '\\"') if text_filter else ''
            
            element_info = await self.page.evaluate(f"""
                () => {{
                    const textFilter = '{escaped_text}'.toLowerCase();
                    
                    // Strategy 1: Find input[type="submit"] or button[type="submit"]
                    let submitButton = Array.from(document.querySelectorAll('input[type="submit"], button[type="submit"]')).find(el => {{
                        if (!textFilter) return true;
                        const elText = (el.value || el.textContent || el.getAttribute('aria-label') || '').trim().toLowerCase();
                        return elText.includes(textFilter);
                    }});
                    
                    // Strategy 2: Find button with submit-like text (Entrar, Login, Submit, Enviar, etc.)
                    if (!submitButton) {{
                        const submitKeywords = ['entrar', 'login', 'submit', 'enviar', 'salvar', 'save', 'confirmar', 'confirm'];
                        submitButton = Array.from(document.querySelectorAll('button, input[type="button"], a[role="button"]')).find(el => {{
                            const elText = (el.textContent || el.value || el.getAttribute('aria-label') || '').trim().toLowerCase();
                            const matchesKeyword = submitKeywords.some(keyword => elText.includes(keyword));
                            
                            if (textFilter) {{
                                return matchesKeyword && elText.includes(textFilter);
                            }}
                            return matchesKeyword;
                        }});
                    }}
                    
                    // Strategy 3: Find button inside a form
                    if (!submitButton) {{
                        const forms = Array.from(document.querySelectorAll('form'));
                        for (const form of forms) {{
                            const submit = form.querySelector('button[type="submit"], input[type="submit"], button:not([type])');
                            if (submit) {{
                                if (!textFilter) {{
                                    submitButton = submit;
                                    break;
                                }}
                                const elText = (submit.textContent || submit.value || '').trim().toLowerCase();
                                if (elText.includes(textFilter)) {{
                                    submitButton = submit;
                                    break;
                                }}
                            }}
                        }}
                    }}
                    
                    if (submitButton) {{
                        const rect = submitButton.getBoundingClientRect();
                        return {{
                            found: true,
                            x: Math.floor(rect.left + rect.width / 2),
                            y: Math.floor(rect.top + rect.height / 2),
                            tagName: submitButton.tagName,
                            text: (submitButton.textContent || submitButton.value || '').trim(),
                            type: submitButton.type || '',
                            id: submitButton.id || '',
                            name: submitButton.name || ''
                        }};
                    }}
                    
                    return {{ found: false }};
                }}
            """)
            
            if not element_info or not element_info.get('found'):
                return False
            
            click_x = element_info['x']
            click_y = element_info['y']
            
            await self.move(click_x, click_y)
            await asyncio.sleep(0.2)
            
            await self.page.evaluate(f"""
                () => {{
                    const clickIndicator = document.getElementById('__playwright_cursor_click');
                    if (clickIndicator) {{
                        clickIndicator.style.left = '{click_x}px';
                        clickIndicator.style.top = '{click_y}px';
                        clickIndicator.style.display = 'block';
                        setTimeout(() => {{
                            clickIndicator.style.display = 'none';
                        }}, 300);
                    }}
                }}
            """)
            
            await self.page.mouse.click(click_x, click_y)
            logger.info(f"Clicked on submit button '{element_info.get('text', '')}' at ({click_x}, {click_y})")
            return True
        except Exception as e:
            logger.error(f"Error clicking by submit: {e}")
            return False
    
    async def get_element_at(self, x: int, y: int) -> Optional[dict]:
        """Get element information at cursor position."""
        try:
            element_info = await self.page.evaluate(f"""
                () => {{
                    const element = document.elementFromPoint({x}, {y});
                    if (!element) return null;
                    
                    return {{
                        tagName: element.tagName || '',
                        text: (element.textContent || '').trim().substring(0, 100),
                        id: element.id || '',
                        className: element.className || '',
                        href: element.href || '',
                        type: element.type || '',
                        name: element.name || '',
                        value: element.value || '',
                        role: (element.getAttribute && element.getAttribute('role')) || '',
                        ariaLabel: (element.getAttribute && element.getAttribute('aria-label')) || '',
                        placeholder: element.placeholder || ''
                    }};
                }}
            """)
            return element_info
        except Exception as e:
            logger.error(f"Error getting element at position: {e}")
            return None
    
    async def type_text(self, text: str, field_selector: Optional[str] = None) -> bool:
        """
        Type text into a field.
        
        Args:
            text: Text to type
            field_selector: Optional selector for the field (label text, placeholder, name, id)
            
        Returns:
            True if field was found and text was typed, False otherwise
        """
        try:
            # Escape text for JavaScript
            escaped_text = text.replace("'", "\\'").replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')
            
            if field_selector:
                # Find field by selector (label, placeholder, name, id)
                escaped_selector = field_selector.replace("'", "\\'").replace('"', '\\"')
                
                # Find field by selector
                field_info = await self.page.evaluate(f"""
                    () => {{
                        const selector = '{escaped_selector}';
                        let field = null;
                        
                        // Try by label text
                        const labels = Array.from(document.querySelectorAll('label'));
                        const label = labels.find(l => l.textContent.trim().toLowerCase().includes(selector.toLowerCase()));
                        if (label && label.htmlFor) {{
                            field = document.getElementById(label.htmlFor);
                        }}
                        
                        // Try by placeholder
                        if (!field) {{
                            field = Array.from(document.querySelectorAll('input, textarea')).find(el => {{
                                return (el.placeholder || '').toLowerCase().includes(selector.toLowerCase());
                            }});
                        }}
                        
                        // Try by name
                        if (!field) {{
                            field = document.querySelector(`input[name*="${{selector}}"], textarea[name*="${{selector}}"]`);
                        }}
                        
                        // Try by id
                        if (!field) {{
                            field = document.getElementById(selector);
                        }}
                        
                        // Try by label text content (find input near label)
                        if (!field && label) {{
                            const labelParent = label.parentElement;
                            if (labelParent) {{
                                field = labelParent.querySelector('input, textarea');
                            }}
                        }}
                        
                        if (field && (field.tagName === 'INPUT' || field.tagName === 'TEXTAREA')) {{
                            const rect = field.getBoundingClientRect();
                            return {{
                                success: true,
                                x: Math.floor(rect.left + rect.width / 2),
                                y: Math.floor(rect.top + rect.height / 2),
                                name: field.name || '',
                                id: field.id || ''
                            }};
                        }}
                        
                        return {{ success: false }};
                    }}
                """)
                
                if field_info and field_info.get('success'):
                    # Move cursor to field
                    await self.move(field_info['x'], field_info['y'])
                    await asyncio.sleep(0.2)
                    
                    # Click to focus
                    await self.page.mouse.click(field_info['x'], field_info['y'])
                    await asyncio.sleep(0.1)
                    
                    # Clear field first
                    await self.page.keyboard.press('Control+A')
                    await asyncio.sleep(0.1)
                    
                    # Type character by character for visual effect
                    for char in text:
                        await self.page.keyboard.type(char, delay=50)  # Small delay between chars
                        await asyncio.sleep(0.03)  # Small delay for visual effect
                    
                    logger.info(f"Typed '{text}' into field '{field_selector}'")
                    return True
                else:
                    return False
            else:
                # Type into focused field or first input
                field_pos = await self.page.evaluate("""
                    () => {
                        let field = document.activeElement;
                        
                        if (!field || (field.tagName !== 'INPUT' && field.tagName !== 'TEXTAREA')) {
                            field = document.querySelector('input:focus, textarea:focus');
                        }
                        
                        if (!field) {
                            field = document.querySelector('input, textarea');
                        }
                        
                        if (field && (field.tagName === 'INPUT' || field.tagName === 'TEXTAREA')) {
                            const rect = field.getBoundingClientRect();
                            return {
                                x: Math.floor(rect.left + rect.width / 2),
                                y: Math.floor(rect.top + rect.height / 2)
                            };
                        }
                        return null;
                    }
                """)
                
                if field_pos:
                    await self.move(field_pos['x'], field_pos['y'])
                    await asyncio.sleep(0.2)
                    
                    # Click to focus
                    await self.page.mouse.click(field_pos['x'], field_pos['y'])
                    await asyncio.sleep(0.1)
                    
                    # Clear field first
                    await self.page.keyboard.press('Control+A')
                    await asyncio.sleep(0.1)
                
                # Type character by character for visual effect
                for char in text:
                    await self.page.keyboard.type(char, delay=50)  # Small delay between chars
                    await asyncio.sleep(0.03)  # Small delay for visual effect
                
                logger.info(f"Typed '{text}' into focused field")
                return True
        except Exception as e:
            logger.error(f"Error typing text: {e}")
            return False
    
    async def press_key(self, key: str):
        """
        Press a key.
        
        Args:
            key: Key to press (Enter, Tab, Escape, Space, etc.)
        """
        try:
            # Map common key names
            key_map = {
                'enter': 'Enter',
                'tab': 'Tab',
                'escape': 'Escape',
                'esc': 'Escape',
                'space': ' ',
                'backspace': 'Backspace',
                'delete': 'Delete',
                'arrowup': 'ArrowUp',
                'arrowdown': 'ArrowDown',
                'arrowleft': 'ArrowLeft',
                'arrowright': 'ArrowRight',
            }
            
            normalized_key = key.lower().strip()
            actual_key = key_map.get(normalized_key, key)
            
            # Special handling for Tab - needs a focused element
            if actual_key == 'Tab':
                # First, ensure we have a focused element
                focused = await self.page.evaluate("""
                    () => {
                        const active = document.activeElement;
                        if (active && (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA' || active.tagName === 'BUTTON' || active.isContentEditable || active.tagName === 'A')) {
                            return true;
                        }
                        
                        // Try to focus first focusable element
                        const focusable = document.querySelector('input:not([disabled]), textarea:not([disabled]), button:not([disabled]), [tabindex]:not([tabindex="-1"]), a[href]');
                        if (focusable) {
                            focusable.focus();
                            return true;
                        }
                        
                        // If still nothing, focus body
                        document.body.focus();
                        return false;
                    }
                """)
                
                # Small delay to ensure focus is set
                await asyncio.sleep(0.1)
                
                # Press Tab - this will move to next focusable element
                await self.page.keyboard.press('Tab')
                
                # Wait a bit for focus to move
                await asyncio.sleep(0.1)
                
                # Get the newly focused element for logging
                new_focus = await self.page.evaluate("""
                    () => {
                        const active = document.activeElement;
                        if (active && active !== document.body) {
                            return {
                                tag: active.tagName,
                                type: active.type || '',
                                name: active.name || '',
                                id: active.id || ''
                            };
                        }
                        return null;
                    }
                """)
                
                if new_focus:
                    logger.info(f"Pressed Tab - moved to {new_focus.get('tag', '')} {new_focus.get('name', new_focus.get('id', ''))}")
                else:
                    logger.info(f"Pressed Tab - no next focusable element")
            else:
                await self.page.keyboard.press(actual_key)
                logger.info(f"Pressed key: {actual_key}")
        except Exception as e:
            logger.error(f"Error pressing key: {e}", exc_info=True)
            raise
    
    async def stop(self):
        """Stop cursor controller."""
        self.is_active = False
        await self.hide()
        logger.info("Cursor controller stopped")

