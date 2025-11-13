#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Odoo workflow and action execution module.
"""

import asyncio
from typing import Optional
from playwright.async_api import Page


class WorkflowHelper:
    """Helper class for executing workflows and actions."""
    
    def __init__(self, page: Page):
        """Initialize workflow helper."""
        self.page = page
    
    async def click_action_button(self, button_text: str) -> bool:
        """Click an action button."""
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
    
    async def execute_workflow(self, action_name: str) -> bool:
        """Execute a workflow action."""
        # Workflows are usually triggered by buttons
        return await self.click_action_button(action_name)
    
    async def confirm_action(self) -> bool:
        """Confirm an action."""
        selectors = [
            'button:has-text("Confirmar"), button:has-text("Confirm")',
            'button.o_form_button_save',
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
    
    async def cancel_action(self) -> bool:
        """Cancel an action."""
        selectors = [
            'button:has-text("Cancelar"), button:has-text("Cancel")',
            'button.o_form_button_cancel',
        ]
        
        for selector in selectors:
            try:
                btn = self.page.locator(selector).first
                if await btn.count() > 0:
                    await btn.click()
                    await asyncio.sleep(0.5)
                    return True
            except Exception:
                continue
        
        return False

