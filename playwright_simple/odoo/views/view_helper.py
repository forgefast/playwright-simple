#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main ViewHelper class that composes specialized view handlers.
"""

import asyncio
from typing import Optional, List
from playwright.async_api import Page

from .view_switcher import ViewSwitcher
from .list_view import ListViewHandler
from .form_view import FormViewHandler


class ViewHelper:
    """Helper class for interacting with Odoo views."""
    
    def __init__(self, page: Page):
        """Initialize view helper."""
        self.page = page
        
        # Initialize specialized handlers
        self.switcher = ViewSwitcher(page)
        self.list_view = ListViewHandler(page)
        self.form_view = FormViewHandler(page)
    
    # Delegate view switching methods
    async def switch_to_list_view(self) -> bool:
        """Switch to List view."""
        return await self.switcher.switch_to_list_view()
    
    async def switch_to_kanban_view(self) -> bool:
        """Switch to Kanban view."""
        return await self.switcher.switch_to_kanban_view()
    
    async def switch_to_form_view(self) -> bool:
        """Switch to Form view."""
        return await self.switcher.switch_to_form_view()
    
    async def switch_to_graph_view(self) -> bool:
        """Switch to Graph view."""
        return await self.switcher.switch_to_graph_view()
    
    async def switch_to_pivot_view(self) -> bool:
        """Switch to Pivot view."""
        return await self.switcher.switch_to_pivot_view()
    
    # Delegate list view methods
    async def search_records(self, search_text: str) -> List:
        """Search for records and return list of found records."""
        return await self.list_view.search_records(search_text)
    
    async def find_and_open_record(
        self,
        search_text: str,
        position: Optional[str] = None
    ) -> bool:
        """Search for records by text and open one based on position."""
        return await self.list_view.find_and_open_record(search_text, position)
    
    async def open_record(self, index: int = 0) -> bool:
        """Open a record from list/kanban view."""
        return await self.list_view.open_record(index)
    
    async def open_filter_menu(self) -> bool:
        """Open the Odoo filter dropdown menu by clicking on the filter dropdown arrow."""
        return await self.list_view.open_filter_menu()
    
    async def filter_records(self, filter_name: str, value: Optional[str] = None) -> bool:
        """Apply a filter using Odoo's filter menu."""
        return await self.list_view.filter_records(filter_name, value)
    
    # Delegate form view methods
    async def create_record(self) -> bool:
        """Click the Create button to create a new record."""
        return await self.form_view.create_record()
    
    async def delete_record(self, index: int = 0) -> bool:
        """Delete a record."""
        # Note: delete_record needs to open record first, which requires list_view
        # For now, we'll keep the simple implementation
        # In a more complex refactoring, we could have a coordinator
        return await self.form_view.delete_record(index)
    
    async def add_line(self, button_text: Optional[str] = None) -> bool:
        """Add a line to a One2many table."""
        return await self.form_view.add_line(button_text)

