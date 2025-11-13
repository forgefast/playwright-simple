#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Odoo wizard and dialog interaction module.
"""

import asyncio
from typing import Optional, Dict, Any
from playwright.async_api import Page, Locator


class WizardHelper:
    """Helper class for interacting with wizards and dialogs."""
    
    def __init__(self, page: Page):
        """Initialize wizard helper."""
        self.page = page
        self._wizard_active = False
    
    async def is_wizard_visible(self) -> bool:
        """
        Check if a wizard/modal is currently visible.
        
        Returns:
            True if wizard is visible, False otherwise
        """
        wizard_selectors = [
            '.modal:visible',
            '.o_dialog:visible',
            '.modal-dialog:visible',
            '[role="dialog"]:visible',
            '.o_popup:visible',
            '.o_wizard:visible',
            '.ui-dialog:visible',
        ]
        
        for selector in wizard_selectors:
            try:
                wizard = self.page.locator(selector).first
                if await wizard.count() > 0 and await wizard.is_visible():
                    self._wizard_active = True
                    return True
            except Exception:
                continue
        
        self._wizard_active = False
        return False
    
    async def get_wizard_locator(self) -> Optional[Locator]:
        """
        Get locator for the active wizard/modal.
        
        Returns:
            Locator for wizard or None if not found
        """
        if not await self.is_wizard_visible():
            return None
        
        wizard_selectors = [
            '.modal:visible',
            '.o_dialog:visible',
            '.modal-dialog:visible',
            '[role="dialog"]:visible',
            '.o_popup:visible',
            '.o_wizard:visible',
        ]
        
        for selector in wizard_selectors:
            try:
                wizard = self.page.locator(selector).first
                if await wizard.count() > 0:
                    return wizard
            except Exception:
                continue
        
        return None
    
    async def open_wizard(self, button_text: str) -> bool:
        """Open a wizard by clicking a button."""
        selectors = [
            f'button:has-text("{button_text}")',
            f'a:has-text("{button_text}")',
            f'button[title*="{button_text}"]',
        ]
        
        for selector in selectors:
            try:
                btn = self.page.locator(selector).first
                if await btn.count() > 0:
                    await btn.click()
                    await asyncio.sleep(1)
                    return True
            except Exception:
                continue
        
        return False
    
    async def fill_wizard_form(self, fields: Dict[str, Any]) -> bool:
        """Fill wizard form fields."""
        from .fields import FieldHelper
        
        field_helper = FieldHelper(self.page)
        
        for field_name, value in fields.items():
            if isinstance(value, dict) and 'type' in value:
                field_type = value['type']
                field_value = value['value']
                
                if field_type == 'many2one':
                    await field_helper.fill_many2one(field_name, field_value)
                elif field_type == 'char':
                    await field_helper.fill_char(field_name, field_value)
                elif field_type == 'boolean':
                    await field_helper.toggle_boolean(field_name)
            else:
                await field_helper.fill_char(field_name, str(value))
            
            await asyncio.sleep(0.02)
        
        return True
    
    async def confirm_wizard(self) -> bool:
        """Confirm wizard."""
        selectors = [
            'button:has-text("Confirmar"), button:has-text("Confirm")',
            'button.o_form_button_save',
            'button[type="submit"]',
        ]
        
        for selector in selectors:
            try:
                btn = self.page.locator(selector).first
                if await btn.count() > 0:
                    await btn.click()
                    await asyncio.sleep(1)
                    return True
            except Exception:
                continue
        
        return False
    
    async def cancel_wizard(self) -> bool:
        """Cancel wizard."""
        selectors = [
            'button:has-text("Cancelar"), button:has-text("Cancel")',
            'button.o_form_button_cancel',
        ]
        
        for selector in selectors:
            try:
                btn = self.page.locator(selector).first
                if await btn.count() > 0:
                    await btn.click()
                    await asyncio.sleep(0.05)
                    return True
            except Exception:
                continue
        
        return False
    
    async def handle_dialog(self, accept: bool = True, text: Optional[str] = None) -> bool:
        """Handle browser dialogs (alert, confirm, prompt)."""
        try:
            if accept:
                self.page.on("dialog", lambda dialog: dialog.accept(text) if text else dialog.accept())
            else:
                self.page.on("dialog", lambda dialog: dialog.dismiss())
            return True
        except Exception:
            return False

