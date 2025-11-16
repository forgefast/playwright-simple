#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Form view operations for Odoo (create, delete, add lines, etc.).
"""

import asyncio
from typing import Optional
from playwright.async_api import Page

from ..selectors import get_button_selectors


class FormViewHandler:
    """Handler for form view operations."""
    
    def __init__(self, page: Page):
        """Initialize form view handler."""
        self.page = page
    
    async def create_record(self) -> bool:
        """Click the Create button to create a new record."""
        button_sel = get_button_selectors().get("create", "")
        selectors = button_sel.split(", ") if button_sel else []
        
        for selector in selectors:
            try:
                btn = self.page.locator(selector).first
                if await btn.count() > 0 and await btn.is_visible():
                    await btn.click()
                    await asyncio.sleep(1)
                    return True
            except Exception:
                continue
        
        return False
    
    async def delete_record(self, index: int = 0) -> bool:
        """Delete a record."""
        # First open the record
        # Note: This requires list view handler, but we'll keep it simple here
        # The ViewHelper will coordinate between handlers
        
        # Click delete button
        button_sel = get_button_selectors().get("delete", "")
        selectors = button_sel.split(", ") if button_sel else []
        
        for selector in selectors:
            try:
                btn = self.page.locator(selector).first
                if await btn.count() > 0:
                    await btn.click()
                    await asyncio.sleep(0.05)
                    # Confirm deletion if dialog appears
                    await self.page.get_by_role("button", name="Ok").click()
                    await asyncio.sleep(0.05)
                    return True
            except Exception:
                continue
        
        return False
    
    async def add_line(self, button_text: Optional[str] = None) -> bool:
        """
        Add a line to a One2many table.
        
        Args:
            button_text: Optional button text to search for (e.g., "Adicionar linha", "Add a line").
                        If not provided, auto-detects the add button.
            
        Returns:
            True if line was added successfully
            
        Raises:
            ValueError: If add button not found
        """
        # Common button texts for adding lines
        if button_text:
            button_texts = [button_text]
        else:
            # Try common texts in Portuguese and English
            button_texts = [
                "Adicionar linha",
                "Add a line",
                "Adicionar",
                "Add",
                "Adicionar uma linha",
                "Add a new line",
            ]
        
        # Selectors for add buttons in One2many fields
        add_button_selectors = [
            '.o_field_x2many_list_row_add a',
            '.o_field_one2many .o_list_button_add',
            'a:has-text("{}")',
            'button:has-text("{}")',
            '.o_field_one2many a[title*="Adicionar"]',
            '.o_field_one2many a[title*="Add"]',
        ]
        
        for btn_text in button_texts:
            for selector_template in add_button_selectors:
                try:
                    if '{}' in selector_template:
                        selector = selector_template.format(btn_text)
                    else:
                        selector = selector_template
                    
                    button = self.page.locator(selector).first
                    if await button.count() > 0 and await button.is_visible():
                        await button.click()
                        await asyncio.sleep(0.05)
                        return True
                except Exception:
                    continue
        
        # If not found with specific text, try generic selectors
        generic_selectors = [
            '.o_field_x2many_list_row_add a',
            '.o_field_one2many .o_list_button_add',
            '.o_field_one2many a[title*="Adicionar"]',
            '.o_field_one2many a[title*="Add"]',
        ]
        
        for selector in generic_selectors:
            try:
                button = self.page.locator(selector).first
                if await button.count() > 0 and await button.is_visible():
                    await button.click()
                    await asyncio.sleep(0.05)
                    return True
            except Exception:
                continue
        
        raise ValueError(
            f"Botão para adicionar linha não encontrado. "
            f"Verifique se está em uma tabela One2many e se o botão está visível."
        )

