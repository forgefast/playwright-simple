#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Browser Service Interface and Implementation.

Provides abstraction for browser lifecycle management.
"""

from typing import Protocol, Optional, Dict, Any
from playwright.async_api import Browser, BrowserContext, Page


class IBrowserService(Protocol):
    """Interface for browser service."""
    
    async def start(self) -> Page:
        """Start browser and return page."""
        ...
    
    async def stop(self) -> None:
        """Stop browser."""
        ...
    
    @property
    def browser(self) -> Optional[Browser]:
        """Get browser instance."""
        ...
    
    @property
    def context(self) -> Optional[BrowserContext]:
        """Get browser context."""
        ...
    
    @property
    def page(self) -> Optional[Page]:
        """Get page instance."""
        ...


class BrowserService:
    """Browser service implementation using BrowserManager."""
    
    def __init__(self, browser_manager):
        """
        Initialize browser service.
        
        Args:
            browser_manager: BrowserManager instance
        """
        self._browser_manager = browser_manager
    
    async def start(self) -> Page:
        """Start browser and return page."""
        return await self._browser_manager.start()
    
    async def stop(self) -> None:
        """Stop browser."""
        await self._browser_manager.stop()
    
    @property
    def browser(self) -> Optional[Browser]:
        """Get browser instance."""
        return self._browser_manager.browser
    
    @property
    def context(self) -> Optional[BrowserContext]:
        """Get browser context."""
        return self._browser_manager.context
    
    @property
    def page(self) -> Optional[Page]:
        """Get page instance."""
        return self._browser_manager.page

