#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Authentication methods for OdooTestBase.

Contains Odoo-specific login and logout methods.
"""

import asyncio
from typing import Optional
from playwright.async_api import Page

from ..core.constants import ACTION_DELAY


class OdooAuthMixin:
    """Mixin providing Odoo-specific authentication methods.
    
    Assumes base class has: page, config, cursor_manager, go_to, type, wait_until_ready, _ensure_cursor
    """
    
    async def login(self, username: str, password: str, database: Optional[str] = None) -> 'OdooAuthMixin':
        """
        Login to Odoo with visible cursor movement.
        
        Args:
            username: Username
            password: Password
            database: Database name (optional, for multi-db setups)
            
        Returns:
            Self for method chaining
        """
        # Ensure cursor is injected and visible
        await self._ensure_cursor()
        
        # Navigate to login page
        base_url = self.config.base_url.rstrip('/')
        login_url = f"{base_url}/web/login"
        await self.go_to(login_url)
        await asyncio.sleep(ACTION_DELAY * 2)  # Reduced from 0.2s
        
        # After navigation, just ensure cursor exists (init script handles creation)
        # Don't force re-inject to avoid creating duplicate cursors
        await self.cursor_manager._ensure_cursor_exists()
        await asyncio.sleep(ACTION_DELAY)
        
        # Fill database if needed (with cursor movement)
        if database:
            db_input = self.page.locator('input[name="db"]').first
            if await db_input.count() > 0:
                await self.type('input[name="db"]', database, "Campo Database")
                # No extra delay needed - type() already has delays
        
        # Fill login (with cursor movement)
        await self.type('input[name="login"]', username, "Campo Login")
        # No extra delay needed
        
        # Fill password (with cursor movement)
        await self.type('input[name="password"]', password, "Campo Senha")
        # Small delay to ensure typing is complete
        await asyncio.sleep(ACTION_DELAY * 2)
        
        # Find submit button - try multiple selectors
        submit_selectors = [
            'button[type="submit"]',
            'button:has-text("Entrar")',
            'button:has-text("Log in")',
            'button:has-text("Login")',
            'button:has-text("Sign in")',
            'input[type="submit"]',
            'button.btn-primary',
            'button.o_primary',
            'form button[type="submit"]',
            '.o_login_form button[type="submit"]',
        ]
        
        submit_btn = None
        for selector in submit_selectors:
            try:
                btn = self.page.locator(selector).first
                count = await btn.count()
                if count > 0:
                    # Check if button is visible
                    is_visible = await btn.is_visible()
                    if is_visible:
                        submit_btn = btn
                        break
            except Exception:
                continue
        
        if not submit_btn:
            # Last resort: try to find ANY submit button
            all_buttons = self.page.locator('button, input[type="submit"]')
            count = await all_buttons.count()
            
            for i in range(min(count, 10)):  # Check first 10 buttons
                btn = all_buttons.nth(i)
                try:
                    btn_type = await btn.get_attribute("type")
                    is_visible = await btn.is_visible()
                    if btn_type == "submit" and is_visible:
                        submit_btn = btn
                        break
                except Exception:
                    continue
        
        if not submit_btn:
            raise ValueError("Botão de login não encontrado após preencher senha")
        
        # Get button position for cursor movement
        try:
            box = await submit_btn.bounding_box()
            if box:
                x = box['x'] + box['width'] / 2
                y = box['y'] + box['height'] / 2
                
                # Move cursor to button
                await self.cursor_manager.move_to(x, y)
                await asyncio.sleep(ACTION_DELAY)
                
                # Show click effect (NO hover effect)
                await self.cursor_manager.show_click_effect(x, y)
                await asyncio.sleep(ACTION_DELAY)
                
                # Click the button directly
                await submit_btn.click()
            else:
                # No bounding box, click directly
                await submit_btn.click()
        except Exception:
            # Last resort: try direct click
            await submit_btn.click()
        
        await asyncio.sleep(ACTION_DELAY * 2)
        
        # Wait for page to load (fast)
        await self.page.wait_for_load_state("load", timeout=5000)  # Reduced from 10000 to 5000
        await asyncio.sleep(ACTION_DELAY)
        
        # After login, just ensure cursor exists (init script handles creation)
        await self.cursor_manager._ensure_cursor_exists()
        
        # Wait for Odoo to be ready (with shorter timeout)
        await self.wait_until_ready(timeout=2000)  # Reduced from 5000 to 2000
        return self
    
    async def logout(self) -> 'OdooAuthMixin':
        """Logout from Odoo with visible cursor movement."""
        import asyncio
        from ..core.constants import ACTION_DELAY
        
        # Ensure cursor is visible
        await self._ensure_cursor()
        
        try:
            # Look for user menu
            user_menu_selectors = [
                '.o_user_menu',
                '.o_main_navbar .o_user_menu',
                'button[title*="Usuário"], button[title*="User"]',
                '.o_user_menu .dropdown-toggle',
                'button.o_user_menu',
            ]
            
            for selector in user_menu_selectors:
                try:
                    user_menu = self.page.locator(selector).first
                    if await user_menu.count() > 0 and await user_menu.is_visible():
                        # Move cursor to user menu
                        try:
                            box = await user_menu.bounding_box()
                            if box and self.cursor_manager:
                                x = box['x'] + box['width'] / 2
                                y = box['y'] + box['height'] / 2
                                
                                # Move cursor to user menu (with human-like speed)
                                await self.cursor_manager.move_to(x, y)
                                await asyncio.sleep(ACTION_DELAY * 2)  # Pause after movement
                                
                                # Show click effect BEFORE clicking
                                await self.cursor_manager.show_click_effect(x, y)
                                await asyncio.sleep(0.02)  # Pause to show effect
                        except Exception:
                            pass
                        
                        await user_menu.click()
                        await asyncio.sleep(ACTION_DELAY * 1)  # Wait for menu to open
                        
                        # Click logout button - wait for menu to be fully visible
                        await asyncio.sleep(ACTION_DELAY * 1)  # Wait a bit more for menu to open
                        
                        logout_selectors = [
                            'a:has-text("Sair")',
                            'a:has-text("Log out")',
                            'a:has-text("Logout")',
                            'a:has-text("Sign out")',
                            'button:has-text("Sair")',
                            'button:has-text("Log out")',
                            'button:has-text("Logout")',
                            '.o_user_menu a[href*="/web/session/logout"]',
                            '.o_user_menu button[href*="/web/session/logout"]',
                            '[role="menuitem"]:has-text("Sair")',
                            '[role="menuitem"]:has-text("Log out")',
                        ]
                        
                        logout_clicked = False
                        for logout_selector in logout_selectors:
                            try:
                                logout_btn = self.page.locator(logout_selector).first
                                count = await logout_btn.count()
                                if count > 0:
                                    # Wait for element to be visible
                                    try:
                                        await logout_btn.wait_for(state="visible", timeout=2000)
                                    except Exception:
                                        continue
                                    
                                    is_visible = await logout_btn.is_visible()
                                    if is_visible:
                                        # Move cursor to center of logout button
                                        try:
                                            box = await logout_btn.bounding_box()
                                            if box and self.cursor_manager:
                                                x = box['x'] + box['width'] / 2
                                                y = box['y'] + box['height'] / 2
                                                
                                                # Move cursor to center of logout button
                                                await self.cursor_manager.move_to(x, y)
                                                await asyncio.sleep(ACTION_DELAY * 1)  # Pause after movement
                                                
                                                # Show click effect BEFORE clicking
                                                await self.cursor_manager.show_click_effect(x, y)
                                                await asyncio.sleep(0.02)  # Pause to show effect
                                        except Exception:
                                            pass
                                        
                                        # Click the logout button
                                        await logout_btn.click()
                                        logout_clicked = True
                                        await asyncio.sleep(ACTION_DELAY * 2)  # Wait for logout to complete
                                        
                                        # Wait for login page to load
                                        await self.page.wait_for_load_state("load", timeout=10000)
                                        await asyncio.sleep(ACTION_DELAY * 1)  # Additional delay to show login page
                                        return self
                            except Exception:
                                continue
                        
                        if not logout_clicked:
                            # If no logout button found, try to find any clickable element in the menu
                            logger.warning("Logout button not found, trying alternative methods")
                            # Try clicking on the menu area where logout should be
                            try:
                                menu_area = self.page.locator('.o_user_menu .dropdown-menu, .o_user_menu [role="menu"]').first
                                if await menu_area.count() > 0:
                                    box = await menu_area.bounding_box()
                                    if box:
                                        # Click in the lower part of the menu (where logout usually is)
                                        x = box['x'] + box['width'] / 2
                                        y = box['y'] + box['height'] * 0.8  # Lower part of menu
                                        await self.cursor_manager.move_to(x, y)
                                        await asyncio.sleep(ACTION_DELAY * 1)
                                        await self.cursor_manager.show_click_effect(x, y)
                                        await asyncio.sleep(0.02)
                                        await menu_area.click()
                                        await asyncio.sleep(ACTION_DELAY * 2)
                            except Exception:
                                pass
                except Exception:
                    continue
        except Exception:
            pass
        
        return self

