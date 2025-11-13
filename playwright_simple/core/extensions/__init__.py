#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extension interfaces for playwright-simple.

Defines interfaces that extensions (like Odoo, ForgeERP) can implement
to extend core functionality while maintaining separation of concerns.
"""

from typing import Protocol, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import Page


class IExtensionAuth(Protocol):
    """Interface for extension-specific authentication."""
    
    async def login(self, username: str, password: str, **kwargs) -> 'IExtensionAuth':
        """
        Login to the application.
        
        Args:
            username: Username
            password: Password
            **kwargs: Additional extension-specific parameters
            
        Returns:
            Self for method chaining
        """
        ...
    
    async def logout(self) -> 'IExtensionAuth':
        """
        Logout from the application.
        
        Returns:
            Self for method chaining
        """
        ...


class IExtensionWait(Protocol):
    """Interface for extension-specific wait strategies."""
    
    async def wait_until_ready(self, timeout: Optional[int] = None, **kwargs) -> 'IExtensionWait':
        """
        Wait until the application is ready.
        
        Args:
            timeout: Maximum time to wait in milliseconds
            **kwargs: Additional extension-specific parameters
            
        Returns:
            Self for method chaining
        """
        ...


class IExtensionNavigation(Protocol):
    """Interface for extension-specific navigation."""
    
    async def go_to_menu(self, *menu_path: str) -> 'IExtensionNavigation':
        """
        Navigate to a menu item.
        
        Args:
            *menu_path: Menu path components (e.g., "Vendas", "Pedidos")
            
        Returns:
            Self for method chaining
        """
        ...
    
    async def go_to_dashboard(self) -> 'IExtensionNavigation':
        """
        Navigate to dashboard/home page.
        
        Returns:
            Self for method chaining
        """
        ...


__all__ = ['IExtensionAuth', 'IExtensionWait', 'IExtensionNavigation']

