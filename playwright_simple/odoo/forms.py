#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Form interaction methods for OdooTestBase.

Contains methods for filling forms and clicking buttons in Odoo.
"""

import asyncio
from typing import Optional, Any


class OdooFormsMixin:
    """Mixin providing form interaction methods for OdooTestBase.
    
    Assumes base class has: page, wizard, field
    """
    
    async def fill(
        self,
        label_or_assignment: str,
        value: Optional[Any] = None,
        context: Optional[str] = None
    ) -> 'OdooFormsMixin':
        """
        Fill a field by its visible label. Supports two syntaxes:
        
        1. `await test.fill("Cliente", "João Silva")`
        2. `await test.fill("Cliente = João Silva")`
        
        Uses Odoo-specific field detection for many2one, one2many, etc.
        Falls back to generic fill_by_label for simple fields.
        
        Args:
            label_or_assignment: Field label or assignment string (e.g., "Cliente = João Silva")
            value: Value to fill (if label_or_assignment is just the label)
            context: Optional context to narrow search (e.g., "Seção Cliente")
            
        Returns:
            Self for method chaining
            
        Example:
            ```python
            await test.fill("Cliente", "João Silva")
            await test.fill("Cliente = João Silva")
            await test.fill("Data", "01/01/2024", context="Seção Datas")
            ```
        """
        # Parse assignment syntax if value is None
        if value is None and '=' in label_or_assignment:
            parts = label_or_assignment.split('=', 1)
            label = parts[0].strip()
            value = parts[1].strip()
        else:
            label = label_or_assignment
        
        # Use Odoo field helper (which handles Odoo-specific field types)
        # It will use generic methods from core when appropriate
        await self.field.fill_field(label, value, context)
        return self
    
    async def click_button(
        self,
        text: str,
        context: Optional[str] = None
    ) -> 'OdooFormsMixin':
        """
        Click a button by its visible text. Automatically detects if button is in wizard or form.
        Also handles view switching buttons (Lista, Kanban, Formulário, etc.).
        
        Args:
            text: Button text (e.g., "Salvar", "Confirmar", "Criar", "Lista", "Kanban")
            context: Optional context ("wizard" or "form"). If not specified, auto-detects.
            
        Returns:
            Self for method chaining
            
        Raises:
            ValueError: If button not found
            
        Example:
            ```python
            await test.click_button("Salvar")
            await test.click_button("Confirmar", context="wizard")
            await test.click_button("Lista")  # Switches to list view
            ```
        """
        # Check if this is a view switch button
        text_lower = text.lower().strip()
        view_switches = {
            "lista": "list",
            "list": "list",
            "list view": "list",
            "kanban": "kanban",
            "kanban view": "kanban",
            "formulário": "form",
            "form": "form",
            "form view": "form",
            "gráfico": "graph",
            "graph": "graph",
            "graph view": "graph",
            "pivot": "pivot",
            "pivot view": "pivot",
        }
        
        if text_lower in view_switches:
            # Try to switch view using ViewHelper
            view_type = view_switches[text_lower]
            if hasattr(self, 'view') and hasattr(self.view, 'switch_to_list_view'):
                # Use the appropriate switch method
                switch_methods = {
                    "list": self.view.switch_to_list_view,
                    "kanban": self.view.switch_to_kanban_view,
                    "form": self.view.switch_to_form_view,
                    "graph": self.view.switch_to_graph_view,
                    "pivot": self.view.switch_to_pivot_view,
                }
                if view_type in switch_methods:
                    result = await switch_methods[view_type]()
                    if result:
                        await asyncio.sleep(0.5)  # Wait for view to switch
                        return self
        
        # Check if wizard is visible
        wizard_visible = await self.wizard.is_wizard_visible()
        
        # Determine search scope
        if context == "wizard":
            # Search only in wizard
            wizard_loc = await self.wizard.get_wizard_locator()
            if not wizard_loc:
                raise ValueError(f"Wizard não encontrado. Botão '{text}' não pode ser clicado.")
            search_scope = wizard_loc
        elif context == "form":
            # Search only in form (not in wizard)
            search_scope = self.page
            # Exclude wizard areas
            wizard_loc = await self.wizard.get_wizard_locator()
            if wizard_loc:
                # We'll search in page but exclude wizard
                pass
        else:
            # Auto-detect: if wizard visible, search there first, else search in form
            if wizard_visible:
                wizard_loc = await self.wizard.get_wizard_locator()
                search_scope = wizard_loc if wizard_loc else self.page
            else:
                search_scope = self.page
        
        # Build button selectors
        button_selectors = [
            f'button:has-text("{text}")',
            f'button:has-text("{text}"):visible',
            f'a:has-text("{text}")',
            f'a:has-text("{text}"):visible',
            f'button[title*="{text}"]',
            f'button[aria-label*="{text}"]',
            f'[role="button"]:has-text("{text}")',
        ]
        
        # Try to find and click button
        for selector in button_selectors:
            try:
                if context == "wizard" and wizard_visible:
                    # Search within wizard
                    wizard_loc = await self.wizard.get_wizard_locator()
                    if wizard_loc:
                        buttons = wizard_loc.locator(selector)
                    else:
                        buttons = self.page.locator(selector)
                elif context == "form":
                    # Search in page but exclude wizard
                    buttons = self.page.locator(selector)
                    # Filter out buttons inside wizard
                    count = await buttons.count()
                    for i in range(count):
                        btn = buttons.nth(i)
                        is_in_wizard = await btn.evaluate("""
                            (el) => {
                                let wizard = el.closest('.modal, .o_dialog, [role="dialog"], .o_popup');
                                return wizard !== null;
                            }
                        """)
                        if not is_in_wizard and await btn.is_visible():
                            await btn.click()
                            await asyncio.sleep(0.02)
                            await self.wizard.is_wizard_visible()
                            return self
                    continue
                else:
                    # Auto-detect: search in wizard first if visible, else in page
                    if wizard_visible:
                        wizard_loc = await self.wizard.get_wizard_locator()
                        if wizard_loc:
                            buttons = wizard_loc.locator(selector)
                        else:
                            buttons = self.page.locator(selector)
                    else:
                        buttons = self.page.locator(selector)
                
                count = await buttons.count()
                
                if count > 0:
                    button = buttons.first
                    if await button.is_visible():
                        await button.click()
                        await asyncio.sleep(0.02)
                        
                        # Update wizard state
                        await self.wizard.is_wizard_visible()
                        
                        return self
            except Exception:
                continue
        
        # If not found, provide helpful error
        location = "wizard" if (wizard_visible and context != "form") else "formulário"
        raise ValueError(
            f"Botão '{text}' não encontrado no {location}. "
            f"Verifique se o texto está correto e se está na tela correta."
        )
    
    async def click(
        self,
        selector_or_text: str,
        description: Optional[str] = None
    ) -> 'OdooFormsMixin':
        """
        Click an element. If selector looks like a CSS selector, uses it directly.
        Otherwise, treats as button text and uses click_button().
        
        Args:
            selector_or_text: CSS selector or button text
            description: Description for logging (optional)
            
        Returns:
            Self for method chaining
        """
        # Check if it looks like a CSS selector (contains special chars)
        is_css_selector = any(char in selector_or_text for char in ['.', '#', '[', ':', '>', ' ', '(', ')'])
        
        if is_css_selector:
            # Use parent class method (from SimpleTestBase)
            await super().click(selector_or_text, description or selector_or_text)
        else:
            # Treat as button text
            await self.click_button(selector_or_text)
        
        return self

