#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Odoo menu navigation module.

Handles navigation through Odoo menus for both Community and Enterprise editions.
"""

import asyncio
import logging
from typing import Optional, List
from playwright.async_api import Page

from .selectors import get_menu_selectors, get_selector_list
from .version_detector import detect_version, detect_edition
from .specific.logo import LogoNavigator
from ..core.constants import ACTION_DELAY

logger = logging.getLogger(__name__)


class MenuNavigator:
    """Helper class for navigating Odoo menus."""
    
    def __init__(self, page: Page, version: Optional[str] = None, cursor_manager=None):
        """
        Initialize menu navigator.
        
        Args:
            page: Playwright page instance
            version: Odoo version (auto-detected if None)
            cursor_manager: Optional cursor manager for visual cursor movement
        """
        self.page = page
        self._version = version
        self._edition = None
        self.cursor_manager = cursor_manager
    
    async def _get_version(self) -> str:
        """Get Odoo version (cached)."""
        if not self._version:
            self._version = await detect_version(self.page) or "18.0"
        return self._version
    
    async def _get_edition(self) -> str:
        """Get Odoo edition (cached)."""
        if not self._edition:
            self._edition = await detect_edition(self.page)
        return self._edition
    
    async def open_apps_menu(self) -> bool:
        """
        Open the Apps menu.
        
        Returns:
            True if menu was opened, False otherwise
        """
        # Try multiple approaches to open apps menu
        selectors = [
            'button.o_menu_toggle',
            'button[aria-label*="Menu"]',
            'button[title*="Apps"]',
            'button[title*="Menu"]',
            '.o_menu_toggle',
            '[data-bs-toggle="offcanvas"]',
            'button:has-text("Apps")',
        ]
        
        for selector in selectors:
            try:
                btn = self.page.locator(selector).first
                if await btn.count() > 0:
                    is_visible = await btn.is_visible()
                    if is_visible:
                        # Move cursor to button if cursor_manager is available
                        if self.cursor_manager:
                            try:
                                box = await btn.bounding_box()
                                if box:
                                    x = box['x'] + box['width'] / 2
                                    y = box['y'] + box['height'] / 2
                                    await self.cursor_manager.move_to(x, y)
                                    await asyncio.sleep(ACTION_DELAY * 2)  # Minimal pause
                                    await self.cursor_manager.show_click_effect(x, y)
                                    await asyncio.sleep(0.05)  # Minimal pause
                            except Exception:
                                pass
                        # Note: btn.click() aqui pode não ter cursor se cursor_manager não estiver disponível
                        # Mas é um fallback interno, então não adicionamos warning aqui
                        await btn.click()
                        await asyncio.sleep(ACTION_DELAY * 2)  # Minimal delay
                        return True
            except Exception:
                continue
        
        # Try pressing Alt key (common shortcut for apps menu)
        try:
            logger.warning(
                "DEPRECATED: page.keyboard.press() usado sem cursor. "
                "Esta ação será removida em versão futura. "
                "Use métodos que utilizam cursor_manager para melhor visualização."
            )
            await self.page.keyboard.press("Alt")
            await asyncio.sleep(ACTION_DELAY * 2)  # Reduced from 0.5s
            # Check if menu opened
            menu_visible = await self.page.locator('.o_apps_menu, .o_main_navbar').is_visible()
            if menu_visible:
                return True
        except Exception:
            pass
        
        return False
    
    async def close_apps_menu(self) -> bool:
        """Close the Apps menu."""
        try:
            logger.warning(
                "DEPRECATED: page.keyboard.press() usado sem cursor. "
                "Esta ação será removida em versão futura. "
                "Use métodos que utilizam cursor_manager para melhor visualização."
            )
            await self.page.keyboard.press("Escape")
            await asyncio.sleep(ACTION_DELAY * 2)  # Reduced from 0.3s
            return True
        except Exception:
            return False
    
    async def _is_current_app(self, app_name: str) -> bool:
        """
        Check if already in the specified app.
        
        Args:
            app_name: Name of the app to check
            
        Returns:
            True if already in the app
        """
        try:
            # First check: if menu de apps is open, we're NOT in an app yet
            menu_is_open = await self.page.evaluate("""
                () => {
                    return document.body.classList.contains('o_apps_menu_opened') ||
                           document.querySelector('.o-app-menu-list') !== null ||
                           document.querySelector('.o_apps_menu') !== null;
                }
            """)
            
            if menu_is_open:
                # Menu de apps está aberto = não estamos em nenhum app ainda
                logger.debug(f"Menu de apps está aberto - não estamos no app '{app_name}' ainda")
                return False
            
            # Check URL for app indicators
            current_url = self.page.url.lower()
            app_name_lower = app_name.lower().strip()
            
            # Check if URL contains app name or related keywords
            url_indicators = {
                "vendas": ["sale", "sales"],
                "contatos": ["contact", "partner", "res.partner"],
                "crm": ["crm"],
                "projetos": ["project"],
                "inventário": ["stock", "inventory"],
                "compras": ["purchase"],
                "contabilidade": ["account"],
                "recursos humanos": ["hr", "employee"],
                "hr": ["hr", "employee"],
                "website": ["website"],
                "ecommerce": ["shop", "ecommerce"],
            }
            
            if app_name_lower in url_indicators:
                for indicator in url_indicators[app_name_lower]:
                    if indicator in current_url:
                        return True
            
            # Check breadcrumbs or menu title
            breadcrumb_selectors = [
                '.breadcrumb',
                '.o_breadcrumb',
                '[data-breadcrumb]',
                '.o_main_navbar',
            ]
            
            for selector in breadcrumb_selectors:
                try:
                    breadcrumb = self.page.locator(selector).first
                    if await breadcrumb.count() > 0:
                        text = await breadcrumb.text_content()
                        if text and app_name_lower in text.lower():
                            return True
                except Exception:
                    continue
            
            # Check if main menu button shows the app name
            menu_button_selectors = [
                'button.o_menu_toggle',
                '.o_main_navbar .o_menu_toggle',
                '[data-bs-toggle="offcanvas"]',
            ]
            
            for selector in menu_button_selectors:
                try:
                    button = self.page.locator(selector).first
                    if await button.count() > 0:
                        # Check aria-label or title
                        aria_label = await button.get_attribute('aria-label') or ''
                        title = await button.get_attribute('title') or ''
                        if app_name_lower in aria_label.lower() or app_name_lower in title.lower():
                            return True
                except Exception:
                    continue
                    
        except Exception:
            pass
        
        return False
    
    async def go_to_app(self, app_name: str) -> bool:
        """
        Navigate to a specific app.
        
        SIMPLIFIED: Only tries to find app by exact text match. Fails immediately if not found.
        YAML should specify exact text to click.
        
        Args:
            app_name: Name of the app (e.g., "Vendas", "Contatos")
            
        Returns:
            True if navigation was successful
            
        Raises:
            RuntimeError: If app is not found
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Check if already in the app
        if await self._is_current_app(app_name):
            return True
        
        # Check if apps menu is already open
        menu_is_open = await self.page.evaluate("""
            () => {
                return document.body.classList.contains('o_apps_menu_opened') ||
                       document.querySelector('.o-app-menu-list') !== null;
            }
        """)
        
        # Open apps menu only if it's not already open
        if not menu_is_open:
            menu_opened = await self.open_apps_menu()
            if not menu_opened:
                await self._save_error_html("go_to_app", f"Menu de apps não abriu ao tentar acessar '{app_name}'")
                raise RuntimeError(
                    f"Menu de apps não abriu. Não é possível acessar '{app_name}'. "
                    f"HTML da página salvo para debug."
                )
            await asyncio.sleep(ACTION_DELAY * 2)
        else:
            logger.info(f"Menu de apps já está aberto - procurando app '{app_name}' diretamente")
            await asyncio.sleep(ACTION_DELAY * 1)  # Small delay to ensure menu is ready
        
        # Try multiple selectors to find the app in the menu
        app_selectors = [
            f'.o-app-menu-list a:has-text("{app_name}")',  # Within apps menu
            f'.o_apps_menu a:has-text("{app_name}")',  # Alternative menu container
            f'a:has-text("{app_name}")',  # Fallback: anywhere on page
        ]
        
        # Find app element
        element = None
        used_selector = None
        for app_selector in app_selectors:
            try:
                test_element = self.page.locator(app_selector).first
                if await test_element.count() > 0 and await test_element.is_visible():
                    element = test_element
                    used_selector = app_selector
                    logger.info(f"App '{app_name}' encontrado com seletor: {app_selector}")
                    break
            except Exception:
                continue
        
        try:
            if element is None:
                await self._save_error_html("go_to_app", f"App '{app_name}' não encontrado no menu")
                raise RuntimeError(
                    f"App '{app_name}' não encontrado no menu. "
                    f"Seletores tentados: {', '.join(app_selectors)}. "
                    f"HTML da página salvo para debug."
                )
            
            # Move cursor and click
            box = await element.bounding_box()
            if not box:
                await self._save_error_html("go_to_app", f"App '{app_name}' sem bounding box")
                raise RuntimeError(
                    f"Não foi possível obter posição do app '{app_name}'. "
                    f"HTML da página salvo para debug."
                )
            
            if self.cursor_manager:
                x = box['x'] + box['width'] / 2
                y = box['y'] + box['height'] / 2
                await self.cursor_manager.move_to(x, y)
                await asyncio.sleep(ACTION_DELAY * 2)
                await self.cursor_manager.show_click_effect(x, y)
                await asyncio.sleep(0.05)
                # Click using page.mouse to ensure cursor is at position
                await self.page.mouse.click(x, y)
            else:
                # Fallback: direct click if no cursor manager
                logger.warning(
                    "DEPRECATED: element.click() usado sem cursor_manager. "
                    "Esta ação será removida em versão futura. "
                    "Certifique-se de que cursor_manager está disponível."
                )
                await element.click()
            await asyncio.sleep(ACTION_DELAY * 2)
            await self.close_apps_menu()
            await asyncio.sleep(ACTION_DELAY * 1)
            
            # Verify navigation
            if await self._is_current_app(app_name):
                return True
            else:
                await self._save_error_html("go_to_app", f"Navegação para '{app_name}' falhou")
                raise RuntimeError(
                    f"Navegação para '{app_name}' falhou após clique. "
                    f"HTML da página salvo para debug."
                )
                
        except RuntimeError:
            raise
        except Exception as e:
            await self._save_error_html("go_to_app", f"Erro inesperado ao acessar '{app_name}': {str(e)}")
            raise RuntimeError(
                f"Erro ao navegar para '{app_name}': {str(e)}. "
                f"HTML da página salvo para debug."
            ) from e
    
    async def go_to_menu(
        self, 
        menu: str, 
        submenu: Optional[str] = None
    ) -> bool:
        """
        Navigate to a menu and optionally a submenu.
        
        Supports two formats:
        1. `go_to_menu("Vendas", "Pedidos")` - separate arguments
        2. `go_to_menu("Vendas > Pedidos")` - single string with separator
        
        Args:
            menu: Main menu name or full path (e.g., "Vendas" or "Vendas > Pedidos")
            submenu: Submenu name (optional, ignored if menu contains '>')
            
        Returns:
            True if navigation was successful
        """
        # Check if menu contains separator (format: "Vendas > Pedidos")
        if '>' in menu:
            parts = [p.strip() for p in menu.split('>')]
            if len(parts) >= 2:
                menu = parts[0]
                submenu = parts[1]
            elif len(parts) == 1:
                menu = parts[0]
                submenu = None
        
        # Navigate to main menu
        success = await self.go_to_app(menu)
        if not success:
            await self._save_error_html("go_to_menu", f"Navegação para menu principal '{menu}' falhou")
            return False
        
        # If submenu is specified, navigate to it
        if submenu:
            await asyncio.sleep(ACTION_DELAY * 1)  # Wait for menu to load and show cursor position
            
            submenu_selectors = [
                f'a:has-text("{submenu}")',
                f'a:has-text("{submenu}"):visible',
                f'a[title*="{submenu}"]',
                f'.o_menu_item:has-text("{submenu}")',
                f'text={submenu}',
                f'[data-menu-xmlid*="{submenu.lower()}"]',
            ]
            
            for selector in submenu_selectors:
                try:
                    element = self.page.locator(selector).first
                    if await element.count() > 0:
                        try:
                            if await element.is_visible():
                                # Get element position for cursor movement
                                try:
                                    box = await element.bounding_box()
                                    if box:
                                        x = box['x'] + box['width'] / 2
                                        y = box['y'] + box['height'] / 2
                                        
                                        # Move cursor to element if cursor_manager is available (with human-like speed)
                                        if self.cursor_manager:
                                            await self.cursor_manager.move_to(x, y)
                                            await asyncio.sleep(ACTION_DELAY * 2)  # Increased pause after movement to show cursor position clearly
                                            
                                            # Show click effect BEFORE clicking (so it's visible)
                                            await self.cursor_manager.show_click_effect(x, y)
                                            await asyncio.sleep(0.05)  # Increased pause to show effect before click
                                            
                                            # Click using page.mouse to ensure cursor is at position
                                            await self.page.mouse.click(x, y)
                                        else:
                                            # No cursor manager, just add delay and click directly
                                            logger.warning(
                                                "DEPRECATED: element.click() usado sem cursor_manager. "
                                                "Esta ação será removida em versão futura. "
                                                "Certifique-se de que cursor_manager está disponível."
                                            )
                                            await asyncio.sleep(ACTION_DELAY * 2)
                                            await element.click()
                                except Exception:
                                    # If cursor movement fails, fallback to direct click
                                    logger.warning(
                                        "DEPRECATED: element.click() usado como fallback sem cursor. "
                                        "Esta ação será removida em versão futura."
                                    )
                                    await element.click()
                                await asyncio.sleep(ACTION_DELAY * 2)  # Increased delay to show navigation result
                                return True
                        except Exception:
                            logger.warning(
                                "DEPRECATED: element.click() usado em exception handler sem cursor. "
                                "Esta ação será removida em versão futura."
                            )
                            await element.click()
                            await asyncio.sleep(ACTION_DELAY * 2)  # Increased delay to show navigation result
                            return True
                except Exception:
                    continue
            
            # If submenu not found, try with translation (Portuguese -> English)
            translations = {
                "categorias": "Categories",
                "pedidos": "Orders",
                "clientes": "Customers",
                "produtos": "Products",
                "badges": "Badges",
                "desafios": "Challenges",
                "cursos": "Courses",
            }
            
            submenu_lower = submenu.lower().strip()
            if submenu_lower in translations:
                translated_submenu = translations[submenu_lower]
                # Try again with translated name
                for selector in submenu_selectors:
                    try:
                        # Replace submenu in selector with translated version
                        translated_selector = selector.replace(f'"{submenu}"', f'"{translated_submenu}"')
                        element = self.page.locator(translated_selector).first
                        if await element.count() > 0:
                            try:
                                if await element.is_visible():
                                    logger.warning(
                                        "DEPRECATED: element.click() usado sem cursor. "
                                        "Esta ação será removida em versão futura. "
                                        "Use test.click() que utiliza cursor_manager."
                                    )
                                    await element.click()
                                    await asyncio.sleep(ACTION_DELAY * 2)  # Increased delay to show navigation
                                    return True
                            except Exception:
                                logger.warning(
                                    "DEPRECATED: element.click() usado em exception handler sem cursor. "
                                    "Esta ação será removida em versão futura."
                                )
                                await element.click()
                                await asyncio.sleep(ACTION_DELAY * 2)  # Increased delay to show navigation
                                return True
                    except Exception:
                        continue
            
            # If still not found, save HTML and return False
            await self._save_error_html("go_to_menu", f"Submenu '{submenu}' não encontrado após navegar para '{menu}'")
            logger.warning(f"Submenu '{submenu}' não encontrado após navegar para '{menu}'")
            return False
        
        return True
    
    async def search_menu(self, search_text: str) -> bool:
        """
        Search for a menu item.
        
        Args:
            search_text: Text to search for
            
        Returns:
            True if search was successful
        """
        # Open apps menu first
        await self.open_apps_menu()
        await asyncio.sleep(0.02)
        
        # Look for search input in apps menu
        search_selectors = [
            'input[placeholder*="Buscar"], input[placeholder*="Search"]',
            '.o_apps_menu input',
            '.o_searchview_input',
        ]
        
        for selector in search_selectors:
            try:
                search_input = self.page.locator(selector).first
                if await search_input.count() > 0:
                    logger.warning(
                        "DEPRECATED: search_input.fill() usado sem cursor. "
                        "Esta ação será removida em versão futura. "
                        "Use test.type() que utiliza cursor_manager."
                    )
                    await search_input.fill(search_text)
                    await asyncio.sleep(ACTION_DELAY * 2)  # Reduced from 0.5s
                    
                    # Try to click first result
                    result_selectors = [
                        '.o_apps_menu .o_app:first-child',
                        '.o_menu_item:first-child',
                    ]
                    
                    for result_sel in result_selectors:
                        try:
                            result = self.page.locator(result_sel).first
                            if await result.count() > 0:
                                logger.warning(
                                    "DEPRECATED: result.click() usado sem cursor. "
                                    "Esta ação será removida em versão futura. "
                                    "Use test.click() que utiliza cursor_manager."
                                )
                                await result.click()
                                await asyncio.sleep(ACTION_DELAY * 2)  # Reduced from 0.8s
                                await self.close_apps_menu()
                                return True
                        except Exception:
                            continue
                    break
            except Exception:
                continue
        
        await self.close_apps_menu()
        return False
    
    async def go_to_dashboard(self) -> bool:
        """
        Navigate to Odoo dashboard/home page.
        
        SIMPLIFIED: Only tries basic approach - click apps menu button, press Escape if menu opens.
        Fails immediately if element not found.
        
        Returns:
            True if navigation was successful
            
        Raises:
            RuntimeError: If required elements are not found
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Check if already on dashboard
        from .specific.logo import LogoNavigator
        logo_nav = LogoNavigator(self.page, self.cursor_manager)
        if await logo_nav._is_on_dashboard():
            return True
        
        # SIMPLIFIED: Try only the most common selector
        apps_button_selector = 'button.o_grid_apps_menu__button'
        
        try:
            btn = self.page.locator(apps_button_selector).first
            if await btn.count() == 0:
                # Save HTML before failing
                await self._save_error_html("go_to_dashboard", "Botão do menu de apps não encontrado")
                raise RuntimeError(
                    f"Elemento não encontrado: '{apps_button_selector}'. "
                    f"HTML da página salvo para debug."
                )
            
            if not await btn.is_visible():
                await self._save_error_html("go_to_dashboard", "Botão do menu de apps não visível")
                raise RuntimeError(
                    f"Elemento '{apps_button_selector}' não está visível. "
                    f"HTML da página salvo para debug."
                )
            
            # Move cursor and click
            box = await btn.bounding_box()
            if not box:
                await self._save_error_html("go_to_dashboard", "Botão do menu de apps sem bounding box")
                raise RuntimeError(
                    f"Não foi possível obter posição do elemento '{apps_button_selector}'. "
                    f"HTML da página salvo para debug."
                )
            
            if self.cursor_manager:
                x = box['x'] + box['width'] / 2
                y = box['y'] + box['height'] / 2
                await self.cursor_manager.move_to(x, y)
                await asyncio.sleep(ACTION_DELAY * 2)
                await self.cursor_manager.show_click_effect(x, y)
                await asyncio.sleep(0.05)
            
            # Note: btn.click() aqui é OK porque cursor já foi movido acima
            # Mas vamos adicionar warning se cursor_manager não estiver disponível
            if not self.cursor_manager:
                logger.warning(
                    "DEPRECATED: btn.click() usado sem cursor_manager. "
                    "Esta ação será removida em versão futura."
                )
            await btn.click()
            await asyncio.sleep(ACTION_DELAY * 2)
            
            # Check if menu opened - if so, we're on dashboard (menu IS the dashboard)
            menu_is_open = await self.page.evaluate("""
                () => {
                    return document.body.classList.contains('o_apps_menu_opened') ||
                           document.querySelector('.o-app-menu-list') !== null;
                }
            """)
            
            if menu_is_open:
                # Menu opened = we're on dashboard (menu IS the dashboard)
                logger.info("Menu de apps aberto - Dashboard acessado com sucesso")
                return True
            
            # If menu didn't open, verify we're on dashboard by other means
            if await logo_nav._is_on_dashboard():
                return True
            else:
                await self._save_error_html("go_to_dashboard", "Navegação para Dashboard falhou")
                raise RuntimeError(
                    f"Navegação para Dashboard falhou após clicar no botão. "
                    f"HTML da página salvo para debug."
                )
                
        except RuntimeError:
            raise
        except Exception as e:
            await self._save_error_html("go_to_dashboard", f"Erro inesperado: {str(e)}")
            raise RuntimeError(
                f"Erro ao navegar para Dashboard: {str(e)}. "
                f"HTML da página salvo para debug."
            ) from e
    
    async def _save_error_html(self, action_name: str, reason: str) -> None:
        """Save HTML content when an error occurs."""
        try:
            from pathlib import Path
            import datetime
            
            # Try to get test name from page context
            test_name = getattr(self, '_test_name', 'unknown')
            if hasattr(self, 'page') and hasattr(self.page, 'context'):
                # Try to get test name from browser context
                try:
                    test_name = self.page.context.extra_http_headers.get('X-Test-Name', 'unknown')
                except:
                    pass
            
            # Create error directory
            project_root = Path(__file__).parent.parent.parent.parent.parent
            error_dir = project_root / "presentation" / "playwright" / "screenshots" / test_name
            error_dir.mkdir(parents=True, exist_ok=True)
            
            # Save HTML
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            html_path = error_dir / f"error_{action_name}_{timestamp}.html"
            html_content = await self.page.content()
            html_path.write_text(html_content, encoding='utf-8')
            
            logger.error(f"HTML salvo em {html_path} - Razão: {reason}")
            print(f"  📄 HTML de erro salvo: {html_path}")
        except Exception as e:
            logger.warning(f"Erro ao salvar HTML: {e}")
    
    async def go_to_home(self) -> bool:
        """
        Navigate to home page (alias for go_to_dashboard).
        
        Returns:
            True if navigation was successful
        """
        return await self.go_to_dashboard()

