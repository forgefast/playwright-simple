#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Special field types for Odoo (html, dropdown/selection).
"""

import asyncio
from playwright.async_api import Page, Locator


class SpecialFieldsHandler:
    """Handler for special Odoo field types."""
    
    def __init__(self, page: Page):
        """Initialize special fields handler."""
        self.page = page
    
    async def fill_html(self, field_locator: Locator, html: str) -> bool:
        """Fill HTML field using locator."""
        # HTML fields use iframes, need special handling
        try:
            # Try to find iframe
            field_name = await field_locator.get_attribute("name")
            if field_name:
                iframe_selector = f'iframe[name*="{field_name}"]'
                iframe = self.page.frame_locator(iframe_selector).first
                body = iframe.locator('body')
                if await body.count() > 0:
                    await body.fill(html)
                    await asyncio.sleep(0.02)
                    return True
        except Exception:
            pass
        return False
    
    async def select_dropdown(self, field_locator: Locator, option: str) -> bool:
        """Select dropdown option using locator."""
        try:
            await field_locator.select_option(label=option)
            await asyncio.sleep(0.02)
            return True
        except Exception:
            return False

