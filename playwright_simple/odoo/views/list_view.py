#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
List view operations for Odoo (search, open records, filter, etc.).
"""

import asyncio
import re
from typing import Optional, List
from playwright.async_api import Page


class ListViewHandler:
    """Handler for list view operations."""
    
    def __init__(self, page: Page):
        """Initialize list view handler."""
        self.page = page
    
    async def search_records(self, search_text: str) -> List:
        """
        Search for records and return list of found records.
        
        Args:
            search_text: Text to search for
            
        Returns:
            List of record locators found
        """
        # Try multiple search input selectors
        search_selectors = [
            'input[placeholder*="Buscar"]',
            '.o_searchview_input',
            'input[placeholder*="Search"]',
            'input.o_searchview_input',
            '.o_cp_searchview input',
            'input[type="search"]',
        ]
        
        search_input = None
        for selector in search_selectors:
            try:
                locator = self.page.locator(selector).first
                if await locator.count() > 0 and await locator.is_visible():
                    search_input = locator
                    break
            except Exception:
                continue
        
        if not search_input:
            # If no search input found, return empty list
            return []
        
        try:
            # Clear existing search first
            await search_input.click()
            await search_input.fill("")
            await asyncio.sleep(0.1)
            
            # Type the search text
            await search_input.fill(search_text)
            await asyncio.sleep(0.2)  # Small delay for search to trigger
            
            # Press Enter to confirm search (Odoo sometimes needs this)
            await search_input.press("Enter")
            await asyncio.sleep(0.3)  # Wait for search results
            
            # Wait for loading to finish
            try:
                await self.page.wait_for_function("""
                    () => {
                        const loading = document.querySelector('.o_loading, .fa-spin');
                        return !loading || loading.style.display === 'none';
                    }
                """, timeout=2000)
            except Exception:
                pass
            
            # Find all result records
            record_selectors = [
                'tr.o_data_row',
                '.o_kanban_record',
                'tbody tr',
            ]
            
            found_records = []
            for record_sel in record_selectors:
                records = self.page.locator(record_sel)
                count = await records.count()
                if count > 0:
                    for i in range(count):
                        record = records.nth(i)
                        if await record.is_visible():
                            found_records.append(record)
                    break
            
            return found_records
        except Exception:
            pass
        
        return []
    
    async def find_and_open_record(
        self,
        search_text: str,
        position: Optional[str] = None
    ) -> bool:
        """
        Search for records by text and open one based on position.
        
        Args:
            search_text: Text to search for
            position: Position to select ('primeiro', 'segundo', 'último', '1', '2', 'last').
                     If None and multiple results, uses first. If single result, opens automatically.
            
        Returns:
            True if record was found and opened
            
        Raises:
            ValueError: If no records found or position invalid
        """
        # Search for records
        records = await self.search_records(search_text)
        
        if not records:
            raise ValueError(
                f"Nenhum registro encontrado com '{search_text}'. "
                f"Verifique se o texto está correto e se há registros na lista."
            )
        
        # Determine which record to open
        if len(records) == 1:
            # Only one result, open it
            record_index = 0
        elif position:
            # Parse position
            position_lower = position.lower()
            if position_lower in ['primeiro', 'first', '1']:
                record_index = 0
            elif position_lower in ['segundo', 'second', '2']:
                record_index = 1
            elif position_lower in ['último', 'last']:
                record_index = len(records) - 1
            else:
                try:
                    record_index = int(position) - 1
                    if record_index < 0 or record_index >= len(records):
                        raise ValueError(f"Posição '{position}' inválida. Encontrados {len(records)} registros.")
                except ValueError as e:
                    raise ValueError(
                        f"Posição '{position}' inválida. "
                        f"Use 'primeiro', 'segundo', 'último' ou um número (1, 2, etc.). "
                        f"Encontrados {len(records)} registros."
                    ) from e
        else:
            # Multiple results, no position specified, use first
            record_index = 0
        
        # Open the selected record
        record = records[record_index]
        
        # Try multiple strategies to click the record
        click_strategies = [
            # Strategy 1: Try to close any open dropdowns first, then click normally
            lambda: self._click_record_safe(record, close_dropdowns=True),
            # Strategy 2: Try clicking on a specific part of the record (name/link)
            lambda: self._click_record_on_name(record),
            # Strategy 3: Try clicking with force (bypasses actionability checks)
            lambda: self._click_record_force(record),
            # Strategy 4: Try clicking at a specific position (center of element)
            lambda: self._click_record_at_position(record),
        ]
        
        last_error = None
        for strategy in click_strategies:
            try:
                await strategy()
                await asyncio.sleep(1)
                return True
            except Exception as e:
                last_error = e
                continue
        
        # If all strategies failed, raise the last error with context
        raise ValueError(
            f"Erro ao abrir registro na posição {record_index + 1}. "
            f"Total de registros encontrados: {len(records)}. "
            f"Último erro: {str(last_error)}"
        ) from last_error
    
    async def _click_record_safe(self, record, close_dropdowns: bool = False) -> None:
        """Click record with safety checks."""
        if close_dropdowns:
            # Try to close any open dropdowns
            try:
                # Press Escape to close dropdowns
                await self.page.keyboard.press("Escape")
                await asyncio.sleep(0.2)
            except Exception:
                pass
        
        await record.click(timeout=10000)
    
    async def _click_record_on_name(self, record) -> None:
        """Try clicking on the name/link part of the record."""
        # Try to find a clickable element within the record (name, link, etc.)
        name_selectors = [
            "td.o_list_record_name a",
            "td:first-child a",
            ".o_field_name a",
            "a",
            "td:first-child",
        ]
        
        for selector in name_selectors:
            try:
                name_element = record.locator(selector).first
                if await name_element.count() > 0 and await name_element.is_visible():
                    await name_element.click(timeout=10000)
                    return
            except Exception:
                continue
        
        # If no name element found, try clicking the record itself
        await record.click(timeout=10000)
    
    async def _click_record_force(self, record) -> None:
        """Click record with force (bypasses actionability checks)."""
        await record.click(force=True, timeout=10000)
    
    async def _click_record_at_position(self, record) -> None:
        """Click record at a specific position (center)."""
        box = await record.bounding_box()
        if box:
            x = box['x'] + box['width'] / 2
            y = box['y'] + box['height'] / 2
            await record.click(position={"x": box['width'] / 2, "y": box['height'] / 2}, timeout=10000)
        else:
            await record.click(force=True, timeout=10000)
    
    async def open_record(self, index: int = 0) -> bool:
        """Open a record from list/kanban view."""
        selectors = [
            f'tr.o_data_row:nth-child({index + 1})',
            f'.o_kanban_record:nth-child({index + 1})',
            f'tbody tr:nth-child({index + 1})',
        ]
        
        for selector in selectors:
            try:
                row = self.page.locator(selector).first
                if await row.count() > 0:
                    await row.click()
                    await asyncio.sleep(1)
                    return True
            except Exception:
                continue
        
        return False
    
    async def open_filter_menu(self) -> bool:
        """
        Open the Odoo filter dropdown menu by clicking on the filter dropdown arrow.
        
        Uses FilterHelper for the actual implementation.
        
        Returns:
            True if filter menu was opened successfully
        """
        from ..specific.filters import FilterHelper
        filter_helper = FilterHelper(self.page)
        return await filter_helper.open_filter_menu()
    
    async def filter_records(self, filter_name: str, value: Optional[str] = None) -> bool:
        """
        Apply a filter using Odoo's filter menu.
        
        First opens the filter dropdown menu, then selects the filter option.
        
        Args:
            filter_name: Name of the filter to apply (e.g., "Consumidor", "Revendedor")
            value: Optional value for the filter
            
        Returns:
            True if filter was applied successfully
        """
        # Step 1: Open the filter dropdown menu
        menu_opened = await self.open_filter_menu()
        
        if not menu_opened:
            # If menu didn't open, try the old method as fallback
            filter_selectors = [
                'button[title*="Filtros"]',
                'button[title*="Filters"]',
                '.o_filters_menu',
                'button.o_filters_menu_button',
                'button:has-text("Filtros")',
                'button:has-text("Filters")'
            ]
            
            filter_btn = None
            for selector in filter_selectors:
                locator = self.page.locator(selector).first
                if await locator.count() > 0:
                    filter_btn = locator
                    break
            
            if filter_btn and await filter_btn.count() > 0:
                await filter_btn.click()
                await asyncio.sleep(0.3)  # Wait for filter menu to open
            else:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Filter dropdown button not found. Cannot apply filter: {filter_name}")
                return False
        
        # Step 2: Find and click the filter option in the dropdown menu
        from ..specific.filters import FilterHelper
        filter_helper = FilterHelper(self.page)
        return await filter_helper.select_filter(filter_name)

