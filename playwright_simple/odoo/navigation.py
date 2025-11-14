#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Navigation methods for OdooTestBase.

Contains Odoo-specific navigation methods for menus, dashboard, and models.
"""

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class OdooNavigationMixin:
    """Mixin providing Odoo-specific navigation methods.
    
    Assumes base class has: page, config, menu, wait_until_ready, go_to (from parent)
    """
    
    def _resolve_user_friendly_url(self, text: str) -> Optional[str]:
        """
        Resolve user-friendly text to URL or action.
        
        Args:
            text: User-friendly text (e.g., "Dashboard", "Portal", "Loja")
            
        Returns:
            URL string or None if should use menu navigation
        """
        text_lower = text.lower().strip()
        
        # Dashboard/Home mappings
        if text_lower in ["dashboard", "menu principal", "home", "início", "página inicial"]:
            return "DASHBOARD"  # Special marker for dashboard navigation
        
        # Portal mappings
        if text_lower in ["portal", "meu portal", "portal do cliente"]:
            return "/my"
        
        # E-commerce/Shop mappings
        if text_lower in ["loja", "e-commerce", "shop", "compras"]:
            return "/shop"
        
        # Common portal pages
        if text_lower in ["meus pedidos", "pedidos", "orders"]:
            return "/my/orders"
        
        if text_lower in ["meu perfil", "perfil", "profile"]:
            return "/my/profile"
        
        # If it looks like a URL, return as-is
        if text.startswith("/") or text.startswith("http"):
            return text
        
        # Otherwise, treat as menu path
        return None
    
    async def go_to_menu(self, menu: str, submenu: Optional[str] = None) -> 'OdooNavigationMixin':
        """
        Navigate to a menu.
        
        Supports two formats:
        1. `go_to_menu("Vendas", "Pedidos")` - separate arguments
        2. `go_to_menu("Vendas > Pedidos")` - single string with separator
        
        Args:
            menu: Main menu name or full path (e.g., "Vendas" or "Vendas > Pedidos")
            submenu: Submenu name (optional, ignored if menu contains '>')
            
        Returns:
            Self for method chaining
        """
        await self.menu.go_to_menu(menu, submenu)
        return self
    
    async def go_to(self, menu_path_or_url: str) -> 'OdooNavigationMixin':
        """
        Navigate to a menu, URL, or user-friendly location.
        
        Supports multiple formats:
        1. Menu path: "Vendas > Pedidos"
        2. User-friendly: "Dashboard", "Portal", "Loja", "Menu principal"
        3. URL: "/web", "/my", "/shop"
        
        Args:
            menu_path_or_url: Menu path, user-friendly text, or URL
            
        Returns:
            Self for method chaining
            
        Example:
            ```python
            await test.go_to("Vendas > Pedidos")
            await test.go_to("Dashboard")
            await test.go_to("Portal")
            await test.go_to("/web")
            ```
        """
        logger.info(f"Iniciando navegação Odoo para: {menu_path_or_url}")
        current_url = self.page.url
        logger.debug(f"URL atual antes da navegação Odoo: {current_url}")
        
        # First check if it's a URL (starts with / or http)
        if menu_path_or_url.startswith("/") or menu_path_or_url.startswith("http"):
            # It's a URL, use parent's go_to
            logger.debug(f"Tratando como URL: {menu_path_or_url}")
            await super().go_to(menu_path_or_url)
            return self
        
        # Resolve user-friendly URLs
        resolved = self._resolve_user_friendly_url(menu_path_or_url)
        logger.debug(f"Resolvido '{menu_path_or_url}' para: {resolved}")
        
        try:
            if resolved == "DASHBOARD":
                # Navigate to dashboard
                logger.info(f"Navegando para Dashboard")
                success = await self.menu.go_to_dashboard()
                if not success:
                    raise ValueError("Não foi possível navegar para o Dashboard - logo não encontrado ou clique não funcionou")
                logger.info(f"Navegação para Dashboard concluída")
            elif resolved and resolved.startswith("/"):
                # It's a URL, use parent's go_to
                logger.debug(f"Usando URL resolvida: {resolved}")
                await super().go_to(resolved)
            elif resolved and resolved.startswith("http"):
                # It's a full URL, use parent's go_to
                logger.debug(f"Usando URL completa resolvida: {resolved}")
                await super().go_to(resolved)
            else:
                # Not a special URL, treat as menu path (e.g., "Vendas", "Contatos")
                # This includes when resolved is None
                logger.info(f"Navegando pelo menu Odoo: {menu_path_or_url}")
                success = await self.menu.go_to_menu(menu_path_or_url)
                if not success:
                    # If menu navigation failed, raise error
                    logger.error(f"Falha na navegação pelo menu Odoo: {menu_path_or_url}")
                    raise ValueError(
                        f"Não foi possível navegar para o menu '{menu_path_or_url}'. "
                        f"Verifique se o menu existe e está acessível."
                    )
                logger.info(f"Navegação pelo menu Odoo concluída: {menu_path_or_url}")
            
            # Check if URL changed
            new_url = self.page.url
            if new_url != current_url:
                logger.info(f"Navegação Odoo bem-sucedida: {current_url} -> {new_url}")
            else:
                logger.debug(
                    f"URL não mudou após navegação Odoo (pode ser SPA): {menu_path_or_url} "
                    f"(URL atual: {new_url})"
                )
        except Exception as e:
            logger.error(f"Falha na navegação Odoo para '{menu_path_or_url}': {e}", exc_info=True)
            raise
        
        # Wait for Odoo to be ready after navigation (fast)
        await self.wait_until_ready(timeout=3000)  # 3s instead of 5s default
        return self
    
    async def go_to_dashboard(self) -> 'OdooNavigationMixin':
        """
        Navigate to Odoo dashboard/home page.
        
        Returns:
            Self for method chaining
        """
        await self.menu.go_to_dashboard()
        return self
    
    async def go_to_home(self) -> 'OdooNavigationMixin':
        """
        Navigate to home page (alias for go_to_dashboard).
        
        Returns:
            Self for method chaining
        """
        await self.menu.go_to_home()
        return self
    
    async def go_to_model(self, model_name: str, view_type: str = "list") -> 'OdooNavigationMixin':
        """
        Navigate directly to a model.
        
        Args:
            model_name: Odoo model name (e.g., "sale.order", "res.partner")
            view_type: View type ("list", "kanban", "form")
            
        Returns:
            Self for method chaining
        """
        base_url = self.config.base_url.rstrip('/')
        url = f"{base_url}/web#model={model_name}&view_type={view_type}"
        await self.go_to(url)
        await asyncio.sleep(0.05)
        return self

