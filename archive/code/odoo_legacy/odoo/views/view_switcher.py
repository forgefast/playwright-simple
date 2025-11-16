#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
View switcher for Odoo (switching between List, Kanban, Form, Graph, Pivot views).
"""

import asyncio
from playwright.async_api import Page


class ViewSwitcher:
    """Handler for switching between Odoo views."""
    
    def __init__(self, page: Page):
        """Initialize view switcher."""
        self.page = page
    
    async def switch_to_list_view(self) -> bool:
        """Switch to List view."""
        return await self._switch_view("list")
    
    async def switch_to_kanban_view(self) -> bool:
        """Switch to Kanban view."""
        return await self._switch_view("kanban")
    
    async def switch_to_form_view(self) -> bool:
        """Switch to Form view."""
        return await self._switch_view("form")
    
    async def switch_to_graph_view(self) -> bool:
        """Switch to Graph view."""
        return await self._switch_view("graph")
    
    async def switch_to_pivot_view(self) -> bool:
        """Switch to Pivot view."""
        return await self._switch_view("pivot")
    
    async def _switch_view(self, view_type: str) -> bool:
        """Switch to a specific view type."""
        # Special handling for list view: if we're in form view, try to go back first
        if view_type == "list":
            # Check if we're in form view
            form_view = self.page.locator('.o_form_view, .o_form_editable')
            if await form_view.count() > 0:
                # Try to go back using breadcrumb or back button
                back_selectors = [
                    '.o_breadcrumb a:first-child',  # First breadcrumb item
                    '.o_control_panel_breadcrumbs a',
                    'button[title*="Voltar"], button[title*="Back"]',
                    '.o_form_button_back',
                ]
                for selector in back_selectors:
                    try:
                        back_btn = self.page.locator(selector).first
                        if await back_btn.count() > 0 and await back_btn.is_visible():
                            await back_btn.click(timeout=5000)
                            await asyncio.sleep(0.5)
                            # After going back, we should be in list view
                            return True
                    except Exception:
                        continue
        
        # Map view types to Portuguese/English button text
        view_texts = {
            "list": ["Lista", "List", "List View"],
            "kanban": ["Kanban", "Kanban View"],
            "form": ["Formulário", "Form", "Form View"],
            "graph": ["Gráfico", "Graph", "Graph View"],
            "pivot": ["Pivot", "Pivot View"],
        }
        
        texts_to_try = view_texts.get(view_type, [view_type.title()])
        
        # Try multiple selector strategies
        selectors = []
        for text in texts_to_try:
            selectors.extend([
                f'button[data-view-type="{view_type}"]',
                f'a[data-view-type="{view_type}"]',
                f'.o_switch_view.o_{view_type}',  # Class-based selector for Odoo 18
                f'.o_cp_switch_buttons .o_switch_view.o_{view_type}',
                f'button:has-text("{text}")',
                f'a:has-text("{text}")',
                f'[role="button"]:has-text("{text}")',
                f'.o_cp_switch_buttons button:has-text("{text}")',
                f'.o_control_panel button:has-text("{text}")',
                f'.o_view_controller button:has-text("{text}")',
            ])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_selectors = []
        for selector in selectors:
            if selector not in seen:
                seen.add(selector)
                unique_selectors.append(selector)
        
        for selector in unique_selectors:
            try:
                btn = self.page.locator(selector).first
                if await btn.count() > 0 and await btn.is_visible():
                    await btn.click(timeout=5000)
                    await asyncio.sleep(0.5)  # Wait for view to switch
                    return True
            except Exception:
                continue
        
        return False

