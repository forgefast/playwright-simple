#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cursor Interaction Module.

Handles cursor interactions (click, type, press key, get element).
"""

import asyncio
import logging
from typing import Optional
from playwright.async_api import Page

logger = logging.getLogger(__name__)

# Import SpeedLevel for type hints
try:
    from ..config import SpeedLevel
except ImportError:
    SpeedLevel = None


def _get_delay(controller, normal_delay: float, min_delay: float = None) -> float:
    """Get delay based on speed_level.
    
    Args:
        controller: CursorController instance
        normal_delay: Normal delay in seconds
        min_delay: Minimum delay (overrides speed_level reduction if provided)
        
    Returns:
        Reduced delay based on speed_level, otherwise normal delay
    """
    # Try to get speed_level from controller
    speed_level = getattr(controller, 'speed_level', None)
    
    # Fallback to fast_mode for backward compatibility
    if speed_level is None:
        fast_mode = getattr(controller, 'fast_mode', False)
        if fast_mode:
            # Map fast_mode to FAST speed level behavior
            multiplier = 0.1
            min_delay_for_level = 0.01
        else:
            # Normal mode
            multiplier = 1.0
            min_delay_for_level = 0.1
    else:
        # Use speed_level
        if SpeedLevel is not None and isinstance(speed_level, SpeedLevel):
            multiplier = speed_level.get_multiplier()
            min_delay_for_level = speed_level.get_min_delay()
        else:
            # Fallback if SpeedLevel not available
            multiplier = 1.0
            min_delay_for_level = 0.1
    
    # Calculate delay
    calculated_delay = normal_delay * multiplier
    
    # Apply minimum delay: use provided min_delay if given, otherwise use level's min_delay
    if min_delay is not None:
        return max(calculated_delay, min_delay)
    
    # For ULTRA_FAST, don't enforce minimum unless explicitly provided
    if speed_level == SpeedLevel.ULTRA_FAST if (SpeedLevel and speed_level) else False:
        return calculated_delay
    
    return max(calculated_delay, min_delay_for_level)


class CursorInteraction:
    """Handles cursor interactions."""
    
    def __init__(self, page: Page, controller):
        """Initialize cursor interaction."""
        self.page = page
        self.controller = controller
    
    async def click(self, x: Optional[int] = None, y: Optional[int] = None):
        """Click at cursor position or specified coordinates."""
        try:
            click_x = x if x is not None else self.controller.current_x
            click_y = y if y is not None else self.controller.current_y
            
            # Ensure cursor is visible
            await self.controller.show()
            
            # Move cursor if coordinates provided
            if x is not None and y is not None:
                # Always use smooth=True to ensure cursor moves visibly
                await self.controller.move(click_x, click_y, smooth=True)
                # Small delay so user can see cursor at destination before clicking
                # Use minimum delay based on speed_level, but ensure cursor is visible
                speed_level = getattr(self.controller, 'speed_level', None)
                if speed_level and SpeedLevel and speed_level == SpeedLevel.ULTRA_FAST:
                    # Ultra fast: minimal delay but still visible
                    await asyncio.sleep(0.05)  # 50ms minimum for visibility
                else:
                    await asyncio.sleep(_get_delay(self.controller, 0.15, min_delay=0.05))
            
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
            if not self.controller.is_active:
                await self.controller.start()
            await self.controller.show()
            logger.info(f"Attempting to click by text: '{text}'")
            
            # Wait for page to be ready (especially after navigation)
            try:
                await self.page.wait_for_load_state('domcontentloaded', timeout=5000)
                # Wait a bit more for dynamic content
                await asyncio.sleep(_get_delay(self.controller, 0.5))
            except:
                pass  # Continue even if timeout
            
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
            # First, check for elements in closed dropdowns and open them if needed
            await self._open_dropdowns_if_needed(text)
            
            # Check if web_responsive Apps Menu is open and wait for it if needed
            await self._wait_for_web_responsive_menu_if_needed(text)
            
            # Wait a bit for dynamic content to appear
            await asyncio.sleep(_get_delay(self.controller, 0.3))
            
            element_info = await self.page.evaluate(f"""
                () => {{
                    // Try multiple strategies with priority
                    const text = '{escaped_text}';
                    const lowerText = text.toLowerCase();
                    const candidates = [];
                    
                    // FIRST: Check if this looks like a form field name (senha, email, usuário, etc.)
                    // If so, prioritize inputs over links
                    const fieldKeywords = ['senha', 'password', 'email', 'e-mail', 'usuário', 'user', 'username', 'nome', 'name', 'telefone', 'phone', 'cpf', 'cnpj', 'endereço', 'address'];
                    const isFieldName = fieldKeywords.some(keyword => lowerText === keyword || lowerText.includes(keyword) || lowerText.includes('email') || lowerText.includes('e-mail'));
                    
                    // If it looks like a field name, search inputs first
                    if (isFieldName) {{
                        const inputs = Array.from(document.querySelectorAll('input, textarea'));
                        for (const input of inputs) {{
                            if (input.offsetParent === null || input.style.display === 'none' || input.style.visibility === 'hidden') {{
                                continue;
                            }}
                            
                            // Check label
                            let labelText = '';
                            const labels = input.labels || [];
                            for (const label of labels) {{
                                labelText = (label.textContent || '').trim().toLowerCase();
                                if (labelText === lowerText || labelText.includes(lowerText)) {{
                                    const rect = input.getBoundingClientRect();
                                    candidates.push({{
                                        element: input,
                                        priority: 15, // Very high priority for input fields
                                        text: labelText,
                                        tagName: input.tagName,
                                        type: 'input-label'
                                    }});
                                    break;
                                }}
                            }}
                            
                            // Check placeholder
                            const placeholder = (input.placeholder || '').toLowerCase();
                            if (placeholder === lowerText || placeholder.includes(lowerText)) {{
                                const rect = input.getBoundingClientRect();
                                candidates.push({{
                                    element: input,
                                    priority: 14, // High priority for placeholder match
                                    text: placeholder,
                                    tagName: input.tagName,
                                    type: 'input-placeholder'
                                }});
                            }}
                            
                            // Check name/id
                            const name = (input.name || '').toLowerCase();
                            const id = (input.id || '').toLowerCase();
                            if (name === lowerText || id === lowerText || name.includes(lowerText) || id.includes(lowerText)) {{
                                const rect = input.getBoundingClientRect();
                                candidates.push({{
                                    element: input,
                                    priority: 13, // High priority for name/id match
                                    text: name || id,
                                    tagName: input.tagName,
                                    type: 'input-name-id'
                                }});
                            }}
                        }}
                    }}
                    
                    // Check if web_responsive Apps Menu is open
                    const menuContainer = document.querySelector('div.app-menu-container');
                    const isMenuOpen = menuContainer && menuContainer.offsetParent !== null;
                    
                    // Collect all potential matches with priority scores
                    // Include menu items and other interactive elements
                    // If menu is open, prioritize elements inside the menu
                    let searchScope = document;
                    if (isMenuOpen && menuContainer) {{
                        // First search inside menu container (higher priority)
                        searchScope = menuContainer;
                    }}
                    
                    const allClickable = Array.from(searchScope.querySelectorAll('button, a, input[type="button"], input[type="submit"], [role="button"], [role="menuitem"], [role="menuitemcheckbox"], [role="menuitemradio"], [onclick], span[role="menuitemcheckbox"], span[role="menuitem"], .o-app-menu-list a, .o-app-menu-list button'));
                    
                    for (const el of allClickable) {{
                        // Skip hidden elements
                        if (el.offsetParent === null || el.style.display === 'none' || el.style.visibility === 'hidden') {{
                            continue;
                        }}
                        
                        const elText = (el.textContent || el.value || el.getAttribute('aria-label') || '').trim();
                        const elTextLower = elText.toLowerCase();
                        
                        // Calculate priority score
                        let priority = 0;
                        let matches = false;
                        
                        // Priority 10: Exact match
                        if (elTextLower === lowerText) {{
                            priority = 10;
                            matches = true;
                        }}
                        // Priority 8: Starts with text (for buttons like "Login" vs "Login here")
                        else if (elTextLower.startsWith(lowerText + ' ') || elTextLower.startsWith(lowerText + '\\n') || elTextLower.startsWith(lowerText + '\\t')) {{
                            priority = 8;
                            matches = true;
                        }}
                        // Priority 6: Ends with text
                        else if (elTextLower.endsWith(' ' + lowerText) || elTextLower.endsWith('\\n' + lowerText)) {{
                            priority = 6;
                            matches = true;
                        }}
                        // Priority 4: Contains as whole word (not part of another word)
                        // Use regex to match word boundaries
                        else {{
                            const wordBoundaryRegex = new RegExp('\\\\b' + lowerText.replace(/[.*+?^${{}}()|[\\\\]\\\\]/g, '\\\\$&') + '\\\\b', 'i');
                            if (wordBoundaryRegex.test(elText)) {{
                                priority = 4;
                                matches = true;
                            }}
                            // Priority 2: Contains text (partial match - lowest priority, only if no word boundary match)
                            else if (elTextLower.includes(lowerText)) {{
                                priority = 2;
                                matches = true;
                            }}
                        }}
                        
                        if (matches) {{
                            // Bonus for buttons over links
                            if (el.tagName === 'BUTTON' || el.type === 'button' || el.type === 'submit') {{
                                priority += 1;
                            }}
                            // Penalty for links when we're looking for field names
                            else if (isFieldName && el.tagName === 'A') {{
                                priority -= 2; // Reduce priority for links when searching for field names
                            }}
                            
                            // Bonus priority for elements inside web_responsive menu when menu is open
                            if (isMenuOpen && menuContainer && menuContainer.contains(el)) {{
                                priority += 5; // High bonus for menu items
                            }}
                            
                            candidates.push({{
                                element: el,
                                priority: priority,
                                text: elText,
                                tagName: el.tagName
                            }});
                        }}
                    }}
                    
                    // If menu is open and no candidates found in menu, search in full document
                    if (isMenuOpen && candidates.length === 0) {{
                        const allClickableFull = Array.from(document.querySelectorAll('button, a, input[type="button"], input[type="submit"], [role="button"], [role="menuitem"], [role="menuitemcheckbox"], [role="menuitemradio"], [onclick], span[role="menuitemcheckbox"], span[role="menuitem"]'));
                        
                        for (const el of allClickableFull) {{
                            if (el.offsetParent === null || el.style.display === 'none' || el.style.visibility === 'hidden') {{
                                continue;
                            }}
                            
                            const elText = (el.textContent || el.value || el.getAttribute('aria-label') || '').trim();
                            const elTextLower = elText.toLowerCase();
                            
                            if (elTextLower.includes(lowerText) || elTextLower === lowerText) {{
                                let priority = elTextLower === lowerText ? 10 : 4;
                                if (el.tagName === 'BUTTON' || el.type === 'button' || el.type === 'submit') {{
                                    priority += 1;
                                }}
                                
                                candidates.push({{
                                    element: el,
                                    priority: priority,
                                    text: elText,
                                    tagName: el.tagName
                                }});
                            }}
                        }}
                    }}
                    
                    // Sort by priority (highest first)
                    candidates.sort((a, b) => b.priority - a.priority);
                    
                    // Return the highest priority match
                    if (candidates.length > 0) {{
                        const best = candidates[0].element;
                        const rect = best.getBoundingClientRect();
                        return {{
                            found: true,
                            x: Math.floor(rect.left + rect.width / 2),
                            y: Math.floor(rect.top + rect.height / 2),
                            tagName: best.tagName,
                            text: (best.textContent || best.value || '').trim(),
                            id: best.id || '',
                            name: best.name || '',
                            priority: candidates[0].priority
                        }};
                    }}
                    
                    return {{ found: false }};
                }}
            """)
            
            if not element_info or not element_info.get('found'):
                # Try opening dropdowns again (in case they closed or weren't detected)
                await self._open_dropdowns_if_needed(text)
                await asyncio.sleep(_get_delay(self.controller, 0.2))
                
                # Retry search after opening dropdowns
                element_info = await self.page.evaluate(f"""
                    () => {{
                        const text = '{escaped_text}';
                        const lowerText = text.toLowerCase();
                        const allClickable = Array.from(document.querySelectorAll(
                            'button, a, [role="button"], [role="menuitem"], [role="link"], [role="menuitemcheckbox"], [role="menuitemradio"]'
                        ));
                        
                        for (const el of allClickable) {{
                            if (el.offsetParent === null || el.style.display === 'none' || el.style.visibility === 'hidden') {{
                                continue;
                            }}
                            const elText = (el.textContent || el.innerText || el.getAttribute('aria-label') || '').trim().toLowerCase();
                            if (elText.includes(lowerText) || elText === lowerText) {{
                                const rect = el.getBoundingClientRect();
                                return {{
                                    found: true,
                                    x: Math.floor(rect.left + rect.width / 2),
                                    y: Math.floor(rect.top + rect.height / 2),
                                    text: elText,
                                    priority: 10
                                }};
                            }}
                        }}
                        return {{ found: false }};
                    }}
                """)
                
            if not element_info or not element_info.get('found'):
                # Try waiting for dynamic element to appear (Approach 1: Wait)
                logger.debug(f"Element '{text}' not found immediately, waiting for dynamic content...")
                element_appeared = await self._wait_for_dynamic_element(text)
                
                if element_appeared:
                    # Retry finding the element
                    element_info = await self.page.evaluate(f"""
                        () => {{
                            const text = '{escaped_text}';
                            const lowerText = text.toLowerCase();
                            const candidates = [];
                            
                            // Same search logic as before but with more specific selectors (Approach 2: Specific selectors)
                            const specificSelectors = [
                                'button[aria-label*="' + lowerText + '"]',
                                'a[aria-label*="' + lowerText + '"]',
                                '[role="menuitem"][aria-label*="' + lowerText + '"]',
                                '[data-menu-xmlid*="' + lowerText + '"]',
                                '.o-dropdown-item:has-text("' + text + '")',
                                '[role="menuitem"]:has-text("' + text + '")'
                            ];
                            
                            for (const selector of specificSelectors) {{
                                try {{
                                    const elements = Array.from(document.querySelectorAll(selector));
                                    for (const el of elements) {{
                                        if (el.offsetParent === null || el.style.display === 'none') {{
                                            continue;
                                        }}
                                        const rect = el.getBoundingClientRect();
                                        candidates.push({{
                                            element: el,
                                            x: Math.floor(rect.left + rect.width / 2),
                                            y: Math.floor(rect.top + rect.height / 2),
                                            priority: 12
                                        }});
                                    }}
                                }} catch (e) {{
                                    // Selector might not be supported, continue
                                }}
                            }}
                            
                            // Also try general search
                            const allClickable = Array.from(document.querySelectorAll(
                                'button, a, [role="button"], [role="menuitem"], [role="link"]'
                            ));
                            
                            for (const el of allClickable) {{
                                if (el.offsetParent === null || el.style.display === 'none') {{
                                    continue;
                                }}
                                const elText = (el.textContent || el.innerText || el.getAttribute('aria-label') || '').trim().toLowerCase();
                                if (elText.includes(lowerText) || elText === lowerText) {{
                                    const rect = el.getBoundingClientRect();
                                    candidates.push({{
                                        element: el,
                                        x: Math.floor(rect.left + rect.width / 2),
                                        y: Math.floor(rect.top + rect.height / 2),
                                        priority: 5
                                    }});
                                }}
                            }}
                            
                            if (candidates.length > 0) {{
                                const best = candidates[0];
                                return {{
                                    found: true,
                                    x: best.x,
                                    y: best.y,
                                    text: (best.element.textContent || '').trim(),
                                    priority: best.priority
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
            found_text = element_info.get('text', '')
            priority = element_info.get('priority', 0)
            
            logger.info(f"Found element '{text}' at ({click_x}, {click_y}), actual text: '{found_text}', priority: {priority}")
            print(f"   ✓ Elemento '{text}' encontrado em ({click_x}, {click_y})")
            if found_text.lower() != text.lower():
                print(f"   ℹ️  Texto real do elemento: '{found_text}' (prioridade: {priority})")
            
            # Move cursor to element position and wait for animation to complete
            # The move() method now waits for the animation to complete
            # Always use smooth=True to ensure cursor moves visibly, even in fast_mode
            # In fast_mode, the animation is shorter (150ms) but still visible
            await self.controller.move(click_x, click_y, smooth=True)
            
            # Log cursor movement with target element
            if self.controller.recorder_logger and self.controller.recorder_logger.is_debug:
                target_element = {
                    'text': found_text,
                    'coordinates': (click_x, click_y)
                }
                self.controller.recorder_logger.log_cursor_movement(
                    x=click_x,
                    y=click_y,
                    target_element=target_element
                )
            
            # Small additional delay so user can see cursor at destination before clicking
            # Use minimum 50ms even in fast_mode to ensure cursor is visible at destination
            await asyncio.sleep(_get_delay(self.controller, 0.15, min_delay=0.05))
            
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
            
            await self.controller.move(click_x, click_y)
            await asyncio.sleep(_get_delay(self.controller, 0.2))
            
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
            
            await self.controller.move(click_x, click_y)
            await asyncio.sleep(_get_delay(self.controller, 0.2))
            
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
    
    async def _open_dropdowns_if_needed(self, search_text: str) -> None:
        """
        Check if element is in a closed dropdown and open it if needed.
        Uses two approaches:
        1. Wait for elements to appear (if they're dynamically loaded)
        2. Open dropdowns that contain the search text
        """
        try:
            escaped_text = search_text.replace("'", "\\'").replace('"', '\\"')
            
            # Check for closed dropdowns that might contain the element
            dropdown_info = await self.page.evaluate(f"""
                () => {{
                    const searchText = '{escaped_text}'.toLowerCase();
                    const dropdowns = [];
                    
                    // Find all dropdown toggles (both open and closed)
                    const dropdownToggles = Array.from(document.querySelectorAll(
                        'button[aria-expanded], ' +
                        'a[aria-expanded], ' +
                        '[data-bs-toggle="dropdown"], ' +
                        '.dropdown-toggle, ' +
                        '.o-dropdown.dropdown-toggle, ' +
                        '[role="button"][aria-haspopup="true"]'
                    ));
                    
                    for (const toggle of dropdownToggles) {{
                        const isExpanded = toggle.getAttribute('aria-expanded') === 'true';
                        if (isExpanded) {{
                            continue; // Skip already open dropdowns
                        }}
                        
                        // Check if dropdown menu exists and might contain the text
                        const toggleId = toggle.getAttribute('id');
                        const dropdownId = toggle.getAttribute('data-bs-target') || 
                                         toggle.getAttribute('aria-controls') ||
                                         (toggleId ? toggleId.replace('toggle', 'menu') : null);
                        
                        let menu = null;
                        if (dropdownId) {{
                            // Remove # if present
                            const id = dropdownId.replace('#', '');
                            menu = document.getElementById(id) || 
                                   document.querySelector(`[id="${{id}}"]`);
                        }}
                        
                        // Also check for sibling dropdown-menu or parent dropdown
                        if (!menu) {{
                            const parent = toggle.closest('.dropdown, [role="menu"], .o-dropdown');
                            if (parent) {{
                                menu = parent.querySelector('.dropdown-menu, [role="menu"], .o-dropdown--menu');
                            }}
                        }}
                        
                        // Also check for any visible dropdown menu in the document
                        if (!menu) {{
                            const allMenus = Array.from(document.querySelectorAll(
                                '.dropdown-menu, [role="menu"], .o-dropdown--menu, .o_popover'
                            ));
                            // Find menu that might be associated with this toggle
                            for (const m of allMenus) {{
                                const menuText = (m.textContent || '').toLowerCase();
                                if (menuText.includes(searchText)) {{
                                    // Check if this menu is near the toggle
                                    const toggleRect = toggle.getBoundingClientRect();
                                    const menuRect = m.getBoundingClientRect();
                                    const distance = Math.abs(toggleRect.top - menuRect.top) + 
                                                   Math.abs(toggleRect.left - menuRect.left);
                                    if (distance < 500) {{ // Within reasonable distance
                                        menu = m;
                                        break;
                                    }}
                                }}
                            }}
                        }}
                        
                        if (menu) {{
                            // Check if menu contains text matching search
                            const menuText = (menu.textContent || '').toLowerCase();
                            if (menuText.includes(searchText)) {{
                                const rect = toggle.getBoundingClientRect();
                                dropdowns.push({{
                                    toggle: toggle,
                                    x: Math.floor(rect.left + rect.width / 2),
                                    y: Math.floor(rect.top + rect.height / 2),
                                    menuText: menuText.substring(0, 50)
                                }});
                            }}
                        }}
                    }}
                    
                    return dropdowns;
                }}
            """)
            
            # Open dropdowns that might contain the element
            if dropdown_info and len(dropdown_info) > 0:
                for dropdown in dropdown_info[:1]:  # Open first matching dropdown
                    try:
                        click_x = dropdown['x']
                        click_y = dropdown['y']
                        await self.page.mouse.click(click_x, click_y)
                        logger.debug(f"Opened dropdown at ({click_x}, {click_y}) for search '{search_text}'")
                        # Wait for dropdown to open and content to load
                        await asyncio.sleep(_get_delay(self.controller, 0.4))
                    except Exception as e:
                        logger.debug(f"Error opening dropdown: {e}")
                        
        except Exception as e:
            logger.debug(f"Error checking dropdowns: {e}")
    
    async def _wait_for_web_responsive_menu_if_needed(self, search_text: str) -> None:
        """
        Check if web_responsive Apps Menu needs to be opened and wait for it.
        The web_responsive module uses a fullscreen overlay menu instead of a dropdown.
        """
        try:
            # Check if Apps Menu button was recently clicked
            menu_info = await self.page.evaluate("""
                () => {
                    // Check if web_responsive Apps Menu exists
                    const appsMenuButton = document.querySelector('button.o_grid_apps_menu__button');
                    if (!appsMenuButton) {
                        return { hasButton: false };
                    }
                    
                    // Check if menu container is visible (menu is open)
                    const menuContainer = document.querySelector('div.app-menu-container');
                    const isOpen = menuContainer && menuContainer.offsetParent !== null;
                    
                    return {
                        hasButton: true,
                        isOpen: isOpen,
                        hasContainer: !!menuContainer
                    };
                }
            """)
            
            # If menu button exists but menu is not open, we might need to wait
            # This happens when we just clicked the button and menu is opening
            if menu_info.get('hasButton') and not menu_info.get('isOpen'):
                # Wait a bit for menu to open (it's an overlay that appears)
                await asyncio.sleep(_get_delay(self.controller, 0.5))
                
                # Check again if menu opened
                menu_info = await self.page.evaluate("""
                    () => {
                        const menuContainer = document.querySelector('div.app-menu-container');
                        return {
                            isOpen: menuContainer && menuContainer.offsetParent !== null
                        };
                    }
                """)
                
                if menu_info.get('isOpen'):
                    logger.debug("web_responsive Apps Menu opened")
                else:
                    logger.debug("web_responsive Apps Menu button exists but menu not open")
                    
        except Exception as e:
            logger.debug(f"Error checking web_responsive menu: {e}")
    
    async def _wait_for_dynamic_element(self, search_text: str, max_attempts: int = 3) -> bool:
        """
        Wait for dynamic elements to appear after interaction.
        Uses two approaches:
        1. Wait with polling for element to appear
        2. Use more specific selectors if element doesn't appear
        """
        try:
            escaped_text = search_text.replace("'", "\\'").replace('"', '\\"')
            
            for attempt in range(max_attempts):
                # Check if element exists now
                element_exists = await self.page.evaluate(f"""
                    () => {{
                        const searchText = '{escaped_text}'.toLowerCase();
                        const allElements = Array.from(document.querySelectorAll(
                            'button, a, [role="button"], [role="menuitem"], [role="link"]'
                        ));
                        
                        for (const el of allElements) {{
                            if (el.offsetParent === null || el.style.display === 'none') {{
                                continue;
                            }}
                            
                            const elText = (el.textContent || el.innerText || el.getAttribute('aria-label') || '').trim().toLowerCase();
                            if (elText.includes(searchText) || elText === searchText) {{
                                return true;
                            }}
                        }}
                        return false;
                    }}
                """)
                
                if element_exists:
                    return True
                
                # Wait a bit before next attempt
                if attempt < max_attempts - 1:
                    await asyncio.sleep(_get_delay(self.controller, 0.3))
            
            return False
        except Exception as e:
            logger.debug(f"Error waiting for dynamic element: {e}")
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
            
            await self.controller.move(click_x, click_y)
            await asyncio.sleep(_get_delay(self.controller, 0.2))
            
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
    
    async def click_by_selector(self, selector: str) -> bool:
        """
        Click on element by CSS selector.
        Supports both standard Odoo and web_responsive selectors.
        
        Args:
            selector: CSS selector for the element
            
        Returns:
            True if element was found and clicked, False otherwise
        """
        try:
            # Ensure cursor is initialized and visible
            if not self.controller.is_active:
                await self.controller.start()
            await self.controller.show()
            
            # Wait for page to be ready
            try:
                await self.page.wait_for_load_state('domcontentloaded', timeout=5000)
                await asyncio.sleep(_get_delay(self.controller, 0.3))
            except:
                pass  # Continue even if timeout
            
            # Special handling for Apps Menu button - try both selectors
            if 'apps_menu' in selector.lower() or 'o_grid_apps' in selector or 'o_navbar_apps' in selector:
                # Try web_responsive selector first
                element = await self.page.query_selector('button.o_grid_apps_menu__button')
                if not element:
                    # Fallback to standard Odoo selector
                    element = await self.page.query_selector('div.o_navbar_apps_menu button')
                if not element:
                    # Try with data-hotkey="h" (common for Apps Menu)
                    element = await self.page.query_selector('button[data-hotkey="h"]')
            else:
                # For other selectors, try the provided selector
                element = await self.page.query_selector(selector)
            
            if not element:
                # Wait a bit more and try again (for dynamic content)
                await asyncio.sleep(_get_delay(self.controller, 0.5))
                if 'apps_menu' in selector.lower() or 'o_grid_apps' in selector or 'o_navbar_apps' in selector:
                    element = await self.page.query_selector('button.o_grid_apps_menu__button')
                    if not element:
                        element = await self.page.query_selector('div.o_navbar_apps_menu button')
                    if not element:
                        element = await self.page.query_selector('button[data-hotkey="h"]')
                else:
                    element = await self.page.query_selector(selector)
            
            if not element:
                logger.warning(f"Element with selector '{selector}' not found")
                print(f"   ⚠️  Elemento com seletor '{selector}' não encontrado")
                return False
            
            # Get element coordinates
            box = await element.bounding_box()
            if not box:
                # If no bounding box, try to click directly
                await element.click()
                logger.info(f"Clicked on element with selector '{selector}' (no bounding box)")
                return True
            
            click_x = int(box['x'] + box['width'] / 2)
            click_y = int(box['y'] + box['height'] / 2)
            
            logger.info(f"Found element with selector '{selector}' at ({click_x}, {click_y})")
            
            # Move cursor to element position
            await self.controller.move(click_x, click_y)
            await asyncio.sleep(_get_delay(self.controller, 0.2))
            
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
            
            # Move Playwright mouse to position before clicking (consistent with other methods)
            await self.page.mouse.move(click_x, click_y)
            await asyncio.sleep(_get_delay(self.controller, 0.1))
            
            # Perform actual click using mouse (consistent with other methods)
            await self.page.mouse.click(click_x, click_y)
            logger.info(f"Clicked on element with selector '{selector}' at ({click_x}, {click_y})")
            return True
        except Exception as e:
            logger.error(f"Error clicking by selector: {e}")
            return False
    
    async def click_by_role(self, role: str, index: int = 0) -> bool:
        """
        Click on element by ARIA role.
        
        Args:
            role: ARIA role (e.g., 'button', 'link', 'menuitem')
            index: Index if multiple matches (default: 0)
            
        Returns:
            True if element was found and clicked, False otherwise
        """
        try:
            # Ensure cursor is initialized and visible
            if not self.controller.is_active:
                await self.controller.start()
            await self.controller.show()
            
            # Find elements by role
            elements = await self.page.query_selector_all(f'[role="{role}"]')
            if not elements or len(elements) <= index:
                logger.warning(f"Element with role '{role}' (index {index}) not found")
                return False
            
            element = elements[index]
            
            # Get element coordinates
            box = await element.bounding_box()
            if not box:
                # If no bounding box, try to click directly
                await element.click()
                logger.info(f"Clicked on element with role '{role}' (index {index}, no bounding box)")
                return True
            
            click_x = int(box['x'] + box['width'] / 2)
            click_y = int(box['y'] + box['height'] / 2)
            
            logger.info(f"Found element with role '{role}' (index {index}) at ({click_x}, {click_y})")
            
            # Move cursor to element position
            await self.controller.move(click_x, click_y)
            await asyncio.sleep(_get_delay(self.controller, 0.2))
            
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
            
            # Move Playwright mouse to position before clicking (consistent with other methods)
            await self.page.mouse.move(click_x, click_y)
            await asyncio.sleep(_get_delay(self.controller, 0.1))
            
            # Perform actual click using mouse (consistent with other methods)
            await self.page.mouse.click(click_x, click_y)
            logger.info(f"Clicked on element with role '{role}' (index {index}) at ({click_x}, {click_y})")
            return True
        except Exception as e:
            logger.error(f"Error clicking by role: {e}")
            return False
    
    async def submit_form(self, button_text: Optional[str] = None) -> bool:
        """
        Submit a form by clicking the submit button.
        
        Args:
            button_text: Optional text to identify specific submit button (e.g., "Entrar", "Login")
            
        Returns:
            True if form was submitted successfully, False otherwise
        """
        # Use existing _click_by_submit method
        return await self._click_by_submit(button_text or '')
    
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
                    await self.controller.move(field_info['x'], field_info['y'])
                    await asyncio.sleep(_get_delay(self.controller, 0.2))
                    
                    # Click to focus
                    await self.page.mouse.click(field_info['x'], field_info['y'])
                    await asyncio.sleep(_get_delay(self.controller, 0.1))
                    
                    # Clear field first
                    await self.page.keyboard.press('Control+A')
                    await asyncio.sleep(_get_delay(self.controller, 0.1))
                    
                    # Type character by character for visual effect
                    # Use speed_level to determine typing delay
                    speed_level = getattr(self.controller, 'speed_level', None)
                    if speed_level is None:
                        # Fallback to fast_mode for backward compatibility
                        fast_mode = getattr(self.controller, 'fast_mode', False)
                        speed_level = SpeedLevel.FAST if (SpeedLevel and fast_mode) else SpeedLevel.NORMAL if SpeedLevel else None
                    
                    if speed_level == SpeedLevel.ULTRA_FAST if (SpeedLevel and speed_level) else False:
                        # Ultra fast: instant typing (delay=0)
                        await self.page.keyboard.type(text, delay=0)
                    elif speed_level == SpeedLevel.FAST if (SpeedLevel and speed_level) else False:
                        # Fast: type quickly with minimal delay (delay=5)
                        await self.page.keyboard.type(text, delay=5)
                    else:
                        # Normal/Slow mode: type character by character for visual effect
                        for char in text:
                            await self.page.keyboard.type(char, delay=50)  # Small delay between chars
                            await asyncio.sleep(_get_delay(self.controller, 0.03))  # Small delay for visual effect
                    
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
                    await self.controller.move(field_pos['x'], field_pos['y'])
                    await asyncio.sleep(_get_delay(self.controller, 0.2))
                    
                    # Check if field is already focused before clicking
                    is_focused = await self.page.evaluate("""
                        () => {
                            const active = document.activeElement;
                            if (!active) return false;
                            const field = document.querySelector('input:focus, textarea:focus');
                            return field !== null;
                        }
                    """)
                    
                    # Only click if field is not already focused
                    if not is_focused:
                        if self.controller.recorder_logger:
                            self.controller.recorder_logger.debug(
                                message="Clicking field to focus before typing",
                                details={'field_selector': field_selector, 'position': field_pos}
                            )
                        # Click to focus
                        await self.page.mouse.click(field_pos['x'], field_pos['y'])
                        await asyncio.sleep(_get_delay(self.controller, 0.1))
                    else:
                        if self.controller.recorder_logger:
                            self.controller.recorder_logger.debug(
                                message="Field already focused, skipping click",
                                details={'field_selector': field_selector}
                            )
                    
                    # Clear field first
                    await self.page.keyboard.press('Control+A')
                    await asyncio.sleep(_get_delay(self.controller, 0.1))
                
                # Type character by character for visual effect
                # Use speed_level to determine typing delay
                speed_level = getattr(self.controller, 'speed_level', None)
                if speed_level is None:
                    # Fallback to fast_mode for backward compatibility
                    fast_mode = getattr(self.controller, 'fast_mode', False)
                    speed_level = SpeedLevel.FAST if (SpeedLevel and fast_mode) else SpeedLevel.NORMAL if SpeedLevel else None
                
                if speed_level == SpeedLevel.ULTRA_FAST if (SpeedLevel and speed_level) else False:
                    # Ultra fast: instant typing (delay=0)
                    await self.page.keyboard.type(text, delay=0)
                elif speed_level == SpeedLevel.FAST if (SpeedLevel and speed_level) else False:
                    # Fast: type quickly with minimal delay (delay=5)
                    await self.page.keyboard.type(text, delay=5)
                else:
                    # Normal/Slow mode: type character by character for visual effect
                    for char in text:
                        await self.page.keyboard.type(char, delay=50)  # Small delay between chars
                        await asyncio.sleep(_get_delay(self.controller, 0.03))  # Small delay for visual effect
                
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

