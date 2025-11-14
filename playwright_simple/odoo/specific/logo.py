#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Odoo logo navigation.

Handles clicking the Odoo logo in the top-left corner to navigate to dashboard.
"""

import asyncio
import logging
from typing import Optional
from playwright.async_api import Page

from ...core.constants import ACTION_DELAY

logger = logging.getLogger(__name__)


class LogoNavigator:
    """Helper for navigating via Odoo logo."""
    
    def __init__(self, page: Page, cursor_manager=None):
        """
        Initialize logo navigator.
        
        Args:
            page: Playwright page instance
            cursor_manager: Optional cursor manager for visual cursor movement
        """
        self.page = page
        self.cursor_manager = cursor_manager
    
    async def _is_on_dashboard(self) -> bool:
        """
        Check if we're already on the dashboard.
        
        Returns:
            True if we're on dashboard, False otherwise
        """
        try:
            current_url = self.page.url.lower()
            
            # If we're on /discuss, check if menu is closed and no app content visible
            # If menu is closed, we might be on dashboard (even if URL still says /discuss)
            if '/discuss' in current_url:
                # Check if menu is closed (not opened)
                menu_is_open = await self.page.evaluate("""
                    () => {
                        return document.body.classList.contains('o_apps_menu_opened') ||
                               document.querySelector('.o-app-menu-list') !== null;
                    }
                """)
                
                if not menu_is_open:
                    # Menu is closed - check if we have app content visible
                    discuss_content = await self.page.locator('.o-mail-Discuss, .o-mail-DiscussSidebar').count()
                    if discuss_content == 0:
                        # No discuss content visible and menu is closed - might be on dashboard
                        logger.debug("Menu fechado e sem conteúdo de discuss - assumindo Dashboard")
                        return True
                
                logger.debug("Não está no dashboard: URL contém /discuss e menu está aberto ou conteúdo visível")
                return False
            
            # Check for dashboard indicators (more comprehensive)
            dashboard_indicators = [
                '.o_menu_apps',
                '.o_action_manager',
                '[data-menu-xmlid="base.menu_administration"]',
                '.o_web_client',  # Main web client container
                '.o_main_navbar',  # Main navbar
            ]
            
            found_indicators = []
            for indicator in dashboard_indicators:
                count = await self.page.locator(indicator).count()
                if count > 0:
                    # Check if it's visible
                    is_visible = await self.page.locator(indicator).first.is_visible()
                    if is_visible:
                        found_indicators.append(indicator)
            
            if found_indicators:
                logger.debug(f"Dashboard detectado: indicadores encontrados: {found_indicators}")
                return True
            
            # Check URL patterns - dashboard URLs typically don't have /discuss, /contacts, etc.
            # and might be just /web or /web#home
            if '/web#' in current_url or current_url.endswith('/web') or current_url.endswith('/web#'):
                # Check if it's a dashboard URL (not a specific app)
                app_indicators = ['/contacts', '/sales', '/crm', '/project', '/stock', '/purchase', '/account', '/hr']
                if not any(indicator in current_url for indicator in app_indicators):
                    # Might be dashboard
                    logger.debug(f"Dashboard detectado: URL parece ser dashboard: {current_url}")
                    return True
            
            # Additional check: if we have the apps menu button visible AND we're NOT in a specific app
            apps_button = self.page.locator('button.o_grid_apps_menu__button, button.o_menu_toggle').first
            if await apps_button.count() > 0:
                is_visible = await apps_button.is_visible()
                if is_visible:
                    # Check if we're NOT in a specific app
                    # If we're in an app, we'll have breadcrumbs or app-specific content
                    breadcrumbs = await self.page.locator('.breadcrumb, .o_breadcrumb, .o_control_panel_breadcrumbs').count()
                    # Also check if we're in discuss (which is NOT dashboard)
                    in_discuss = '/discuss' in current_url or 'discuss' in current_url
                    # Check if we have app-specific action manager content
                    action_manager = self.page.locator('.o_action_manager')
                    has_app_content = False
                    if await action_manager.count() > 0:
                        # Check if action manager has app-specific content (not just empty)
                        children_count = await action_manager.locator('> *').count()
                        if children_count > 0:
                            # Check if it's discuss or another app
                            discuss_content = await self.page.locator('.o-mail-Discuss, .o-mail-DiscussSidebar').count()
                            if discuss_content > 0:
                                has_app_content = True
                            elif breadcrumbs > 0:
                                has_app_content = True
                    
                    # We're on dashboard if: button visible, no breadcrumbs, not in discuss, no app content
                    if breadcrumbs == 0 and not in_discuss and not has_app_content:
                        logger.debug("Dashboard detectado: botão de apps visível, sem breadcrumbs, sem discuss, sem conteúdo de app")
                        return True
            
            logger.debug(f"Não está no dashboard: URL={current_url}, indicadores={found_indicators}")
            return False
        except Exception as e:
            logger.debug(f"Erro ao verificar dashboard: {e}")
            return False
    
    async def click_logo(self) -> bool:
        """
        Click the Odoo logo in the top-left corner to navigate to dashboard.
        
        Specifically targets the Odoo logo, avoiding other clickable elements
        like "Discussões" or "Mensagens".
        
        Returns:
            True if logo was clicked successfully or already on dashboard, False otherwise
        """
        # Check if we're already on dashboard - if so, no need to navigate
        if await self._is_on_dashboard():
            print(f"  ✅ Já estamos no Dashboard - não precisa navegar")
            logger.info("Já estamos no Dashboard - não precisa navegar")
            return True
        
        # Priority 1: Odoo logo/brand in top-left corner (most specific)
        # These selectors target the actual logo, not other menu items
        logo_selectors = [
            # Odoo logo/brand element (most specific - top-left corner)
            # Try navbar-brand first (Bootstrap navbar logo)
            '.navbar-brand.logo',
            'a.navbar-brand.logo',
            '.o_main_navbar .navbar-brand',
            '.o_main_navbar a.navbar-brand',
            # Odoo-specific logo selectors
            '.o_main_navbar .o_menu_brand:first-child',
            '.o_main_navbar > .o_menu_brand',
            'a.o_menu_brand:first-child',
            '.o_main_navbar a.o_menu_brand[href*="#home"]',
            '.o_main_navbar a.o_menu_brand[href="#"]',
            '.o_main_navbar a.o_menu_brand[href="/"]',
            '.o_main_navbar a.o_menu_brand[href="/web"]',
            '.o_main_navbar a.o_menu_brand[href*="web#"]',
            # Try first link in navbar that goes to home/dashboard
            '.o_main_navbar > a:first-child[href*="#home"]',
            '.o_main_navbar > a:first-child[href="/"]',
            '.o_main_navbar > a:first-child[href="/web"]',
            # Fallback: any logo/brand in navbar (but exclude if it has text "Mensagens" or "Discuss")
            '.o_main_navbar .o_menu_brand',
            'a.o_menu_brand',
        ]
        
        for selector in logo_selectors:
            try:
                logo_link = self.page.locator(selector).first
                count = await logo_link.count()
                logger.debug(f"Tentando selector '{selector}': encontrados {count} elementos")
                
                if count > 0:
                    # Verify it's actually visible
                    is_visible = await logo_link.is_visible()
                    logger.debug(f"Elemento visível: {is_visible}")
                    if not is_visible:
                        continue
                    
                    # Verify it's in the navbar and is one of the first children (logo position)
                    is_in_navbar = await logo_link.evaluate("""
                        (el) => {
                            const navbar = el.closest('.o_main_navbar');
                            if (!navbar) return false;
                            
                            // Check if it's the first child or early in the navbar (logo position)
                            const children = Array.from(navbar.children);
                            const index = children.indexOf(el);
                            return index < 3; // Logo should be in first 3 children
                        }
                    """)
                    
                    logger.debug(f"Elemento está na navbar (primeiros 3): {is_in_navbar}")
                    if not is_in_navbar:
                        continue
                    
                    # Get text content to exclude "Discuss" or "Mensagens"
                    text_content = await logo_link.text_content() or ""
                    text_lower = text_content.lower()
                    logger.debug(f"Conteúdo do texto: '{text_content}'")
                    
                    # Exclude elements that contain "Discuss", "Mensagens", or menu-related text
                    exclude_keywords = ["discuss", "mensagens", "menu", "apps", "aplicativos"]
                    if any(keyword in text_lower for keyword in exclude_keywords):
                        logger.debug(f"Elemento excluído (contém palavras-chave excluídas: {text_lower})")
                        continue
                    
                    # Also check aria-label and title attributes
                    aria_label = await logo_link.get_attribute('aria-label') or ""
                    title = await logo_link.get_attribute('title') or ""
                    if any(keyword in (aria_label + " " + title).lower() for keyword in exclude_keywords):
                        logger.debug(f"Elemento excluído (aria-label ou title contém palavras-chave: {aria_label}, {title})")
                        continue
                    
                    # Move cursor to logo if cursor_manager is available
                    logger.debug(f"Cursor manager disponível: {self.cursor_manager is not None}")
                    if self.cursor_manager:
                        try:
                            box = await logo_link.bounding_box()
                            logger.debug(f"Bounding box do logo: {box}")
                            if box:
                                x = box['x'] + box['width'] / 2
                                y = box['y'] + box['height'] / 2
                                logger.info(f"🖱️  Movendo cursor para logo em ({x:.1f}, {y:.1f})")
                                await self.cursor_manager.move_to(x, y)
                                await asyncio.sleep(ACTION_DELAY * 2)
                                logger.info(f"🖱️  Mostrando efeito de clique no logo")
                                await self.cursor_manager.show_click_effect(x, y)
                                await asyncio.sleep(0.05)
                        except Exception as e:
                            logger.error(f"Erro ao mover cursor para logo: {e}", exc_info=True)
                    else:
                        logger.warning("⚠️  Cursor manager não disponível - cursor não será movido")
                    
                    # Click the logo
                    logger.info(f"🖱️  Clicando no logo (selector: {selector})")
                    url_before = self.page.url
                    await logo_link.click()
                    await asyncio.sleep(ACTION_DELAY * 2)
                    
                    # Wait a bit more for navigation to complete
                    await asyncio.sleep(ACTION_DELAY * 1)
                    
                    # Verify navigation succeeded by checking URL or page content
                    url_after = self.page.url
                    if url_before != url_after:
                        logger.info(f"✅ Logo clicado com sucesso - URL mudou: {url_before} -> {url_after}")
                        return True
                    else:
                        # URL didn't change (SPA), but check if we're on dashboard by content
                        try:
                            # Check for dashboard indicators
                            dashboard_indicators = [
                                '.o_menu_apps',
                                '.o_action_manager',
                                '[data-menu-xmlid="base.menu_administration"]',
                            ]
                            for indicator in dashboard_indicators:
                                count = await self.page.locator(indicator).count()
                                if count > 0:
                                    logger.info(f"✅ Logo clicado com sucesso - Dashboard detectado (indicador: {indicator})")
                                    return True
                            
                            # If still on discuss page, navigation didn't work
                            if '/discuss' in url_after:
                                logger.warning(f"⚠️  Logo clicado mas ainda em /discuss - navegação falhou")
                                # Don't use direct navigation - cursor must be the protagonist
                                # Return False so caller can handle the failure
                                return False
                        except Exception as e:
                            logger.warning(f"Erro ao verificar navegação: {e}")
                    
                    logger.info(f"✅ Logo clicado (assumindo sucesso)")
                    return True
            except Exception as e:
                logger.debug(f"Logo selector '{selector}' falhou: {e}")
                continue
        
        # Fallback: try home link selectors
        home_selectors = [
            'a[href="#home"]',
            'a[href="/web"]',
            '.o_main_navbar a[href*="home"]',
        ]
        
        for selector in home_selectors:
            try:
                home_link = self.page.locator(selector).first
                if await home_link.count() > 0:
                    # Verify it's in navbar and not a menu item
                    is_menu_item = await home_link.evaluate("""
                        (el) => {
                            return el.closest('.o_menu_item, .dropdown-menu') !== null;
                        }
                    """)
                    if not is_menu_item:
                        if self.cursor_manager:
                            try:
                                box = await home_link.bounding_box()
                                if box:
                                    x = box['x'] + box['width'] / 2
                                    y = box['y'] + box['height'] / 2
                                    await self.cursor_manager.move_to(x, y)
                                    await asyncio.sleep(ACTION_DELAY * 2)
                                    await self.cursor_manager.show_click_effect(x, y)
                                    await asyncio.sleep(0.05)
                            except Exception:
                                pass
                        await home_link.click()
                        await asyncio.sleep(ACTION_DELAY * 2)
                        return True
            except Exception:
                continue
        
        # Last resort: try to find any clickable element in the very top-left corner
        # But be more specific - look for elements that are likely the logo
        logger.warning("Odoo logo não encontrado com seletores. Tentando encontrar elemento no canto superior esquerdo...")
        print(f"  ⚠️  Logo não encontrado, tentando encontrar elemento no canto superior esquerdo")
        
        if self.cursor_manager:
            try:
                # Try to find logo image or navbar-brand in top-left
                # Look for elements that are likely the logo (images, navbar-brand)
                fallback_selectors = [
                    # Try to find logo image first
                    '.o_main_navbar img[alt*="Logo"], .o_main_navbar img[title*="Logo"]',
                    '.navbar-brand img',
                    '.o_main_navbar .navbar-brand img',
                    # Then try links with specific hrefs
                    '.o_main_navbar a.navbar-brand[href="/"]',
                    '.o_main_navbar a.navbar-brand[href="#home"]',
                    '.navbar-brand[href="/"]',
                    '.navbar-brand[href="#home"]',
                    # Then try first link in navbar (but verify it's not menu/mensagens)
                    '.o_main_navbar > a:first-child',
                ]
                
                for selector in fallback_selectors:
                    try:
                        element = self.page.locator(selector).first
                        if await element.count() > 0:
                            is_visible = await element.is_visible()
                            if is_visible:
                                # Get position
                                box = await element.bounding_box()
                                if box:
                                    x = box['x'] + box['width'] / 2
                                    y = box['y'] + box['height'] / 2
                                    
                                    # Verify it's in the top-left area (first 80px horizontally to avoid menu)
                                    if x < 80:
                                        # Double-check it's not menu or mensagens
                                        text_content = await element.text_content() or ""
                                        aria_label = await element.get_attribute('aria-label') or ""
                                        title = await element.get_attribute('title') or ""
                                        all_text = (text_content + " " + aria_label + " " + title).lower()
                                        
                                        if any(kw in all_text for kw in ["mensagens", "discuss", "menu", "apps"]):
                                            continue
                                        
                                        print(f"  🖱️  Encontrado elemento no canto superior esquerdo em ({x:.1f}, {y:.1f})")
                                        logger.info(f"🖱️  Encontrado elemento no canto superior esquerdo em ({x:.1f}, {y:.1f})")
                                        await self.cursor_manager.move_to(x, y)
                                        await asyncio.sleep(ACTION_DELAY * 2)
                                        
                                        print(f"  🖱️  Mostrando efeito de clique")
                                        logger.info(f"🖱️  Mostrando efeito de clique")
                                        await self.cursor_manager.show_click_effect(x, y)
                                        await asyncio.sleep(0.05)
                                        
                                        # Click the element directly (not page.mouse to avoid clicking wrong element)
                                        # Note: OK aqui porque cursor já foi movido acima
                                        print(f"  🖱️  Clicando no elemento")
                                        logger.info(f"🖱️  Clicando no elemento")
                                        await element.click()
                                        await asyncio.sleep(ACTION_DELAY * 2)
                                        
                                        print(f"  ✅ Clique executado")
                                        logger.info(f"✅ Clique executado")
                                        return True
                    except Exception:
                        continue
                
                # Alternative approach: try to find navbar and get first link
                try:
                    # Try to find first link in navbar that goes to home/web
                    navbar_link = await self.page.evaluate("""
                        () => {
                            const navbar = document.querySelector('.o_main_navbar');
                            if (!navbar) return null;
                            
                            // Get all links in navbar, sorted by position
                            const links = Array.from(navbar.querySelectorAll('a'));
                            const linksWithPos = links.map(link => {
                                const rect = link.getBoundingClientRect();
                                return {
                                    element: link,
                                    x: rect.x,
                                    y: rect.y,
                                    href: link.getAttribute('href') || '',
                                    text: link.textContent?.trim() || '',
                                    className: link.className || ''
                                };
                            }).filter(l => l.x < 150 && l.y < 80); // Top-left area
                            
                            // Sort by x position (leftmost first)
                            linksWithPos.sort((a, b) => {
                                if (Math.abs(a.x - b.x) < 10) return a.y - b.y;
                                return a.x - b.x;
                            });
                            
                            // Find first link that goes to home/web/dashboard
                            // First, filter out menu items
                            const filteredLinks = linksWithPos.filter(linkInfo => {
                                const href = linkInfo.href.toLowerCase();
                                const text = linkInfo.text.toLowerCase();
                                const allText = (text + ' ' + linkInfo.className).toLowerCase();
                                
                                // Exclude menu items - be more strict
                                if (allText.includes('mensagens') || 
                                    allText.includes('discuss') || 
                                    allText.includes('menu') || 
                                    allText.includes('apps') ||
                                    allText.includes('o_mail_systray') ||
                                    href.includes('/discuss') ||
                                    href.includes('/mail')) {
                                    return false;
                                }
                                return true;
                            });
                            
                            // Try links to home/web first
                            for (const linkInfo of filteredLinks) {
                                const href = linkInfo.href.toLowerCase();
                                if (href.includes('/web') || 
                                    href.includes('#home') || 
                                    href === '/' ||
                                    href.includes('web#')) {
                                    return {
                                        x: linkInfo.x + (linkInfo.element.getBoundingClientRect().width / 2),
                                        y: linkInfo.y + (linkInfo.element.getBoundingClientRect().height / 2),
                                        href: linkInfo.href,
                                        text: linkInfo.text
                                    };
                                }
                            }
                            
                            // If no home link found, return leftmost filtered link (x < 60 to avoid menu)
                            const leftmostFiltered = filteredLinks.filter(l => l.x < 60);
                            if (leftmostFiltered.length > 0) {
                                const first = leftmostFiltered[0];
                                return {
                                    x: first.x + (first.element.getBoundingClientRect().width / 2),
                                    y: first.y + (first.element.getBoundingClientRect().height / 2),
                                    href: first.href,
                                    text: first.text
                                };
                            }
                            
                            return null;
                        }
                    """)
                    
                    if navbar_link:
                        x = navbar_link['x']
                        y = navbar_link['y']
                        href = navbar_link.get('href', '')
                        print(f"  🖱️  Encontrado link no navbar em ({x:.1f}, {y:.1f}) - href: {href or 'N/A'}, text: '{navbar_link.get('text', '')[:30]}'")
                        logger.info(f"Link encontrado no navbar: {navbar_link}")
                        
                        # Move cursor and click
                        await self.cursor_manager.move_to(x, y)
                        await asyncio.sleep(ACTION_DELAY * 2)
                        await self.cursor_manager.show_click_effect(x, y)
                        await asyncio.sleep(0.05)
                        
                        url_before = self.page.url
                        await self.page.mouse.click(x, y)
                        await asyncio.sleep(ACTION_DELAY * 2)
                        await asyncio.sleep(ACTION_DELAY * 1)
                        
                        url_after = self.page.url
                        if url_before != url_after:
                            print(f"  ✅ Clique no link do navbar - URL mudou: {url_before} -> {url_after}")
                            logger.info(f"✅ Clique no link do navbar executado - URL mudou")
                            return True
                        elif '/discuss' not in url_after:
                            print(f"  ✅ Clique no link do navbar - não está mais em /discuss")
                            logger.info(f"✅ Clique no link do navbar executado - não está mais em /discuss")
                            return True
                    else:
                        # No link found in navbar - try to find ANY clickable element in very top-left
                        print(f"  🔍 Nenhum link encontrado no navbar, buscando qualquer elemento clicável no topo esquerdo...")
                        logger.info("Nenhum link encontrado no navbar, buscando qualquer elemento clicável")
                        
                        # Try to find first child of navbar that's clickable
                        first_navbar_element = await self.page.evaluate("""
                            () => {
                                const navbar = document.querySelector('.o_main_navbar');
                                if (!navbar) return null;
                                
                                // Get first few children of navbar
                                const children = Array.from(navbar.children);
                                for (let i = 0; i < Math.min(5, children.length); i++) {
                                    const child = children[i];
                                    const rect = child.getBoundingClientRect();
                                    
                                    // Check if it's in top-left and is clickable
                                    if (rect.x < 80 && rect.y < 60 && rect.width > 0 && rect.height > 0) {
                                        const text = child.textContent?.trim() || '';
                                        const href = child.getAttribute('href') || '';
                                        const allText = (text + ' ' + child.className).toLowerCase();
                                        
                                        // Exclude menu items
                                        if (!allText.includes('mensagens') && 
                                            !allText.includes('discuss') && 
                                            !allText.includes('menu') && 
                                            !allText.includes('apps') &&
                                            !allText.includes('o_mail_systray')) {
                                            return {
                                                x: rect.x + rect.width / 2,
                                                y: rect.y + rect.height / 2,
                                                tagName: child.tagName,
                                                href: href,
                                                text: text.substring(0, 30)
                                            };
                                        }
                                    }
                                }
                                return null;
                            }
                        """)
                        
                        if first_navbar_element:
                            x = first_navbar_element['x']
                            y = first_navbar_element['y']
                            print(f"  🖱️  Encontrado elemento do navbar em ({x:.1f}, {y:.1f}) - tag: {first_navbar_element.get('tagName')}, text: '{first_navbar_element.get('text', '')[:30]}'")
                            logger.info(f"Elemento encontrado no navbar: {first_navbar_element}")
                            
                            await self.cursor_manager.move_to(x, y)
                            await asyncio.sleep(ACTION_DELAY * 2)
                            await self.cursor_manager.show_click_effect(x, y)
                            await asyncio.sleep(0.05)
                            
                            url_before = self.page.url
                            await self.page.mouse.click(x, y)
                            await asyncio.sleep(ACTION_DELAY * 2)
                            await asyncio.sleep(ACTION_DELAY * 1)
                            
                            url_after = self.page.url
                            if url_before != url_after:
                                print(f"  ✅ Clique no elemento do navbar - URL mudou: {url_before} -> {url_after}")
                                logger.info(f"✅ Clique no elemento do navbar executado - URL mudou")
                                return True
                            elif '/discuss' not in url_after:
                                print(f"  ✅ Clique no elemento do navbar - não está mais em /discuss")
                                logger.info(f"✅ Clique no elemento do navbar executado - não está mais em /discuss")
                                return True
                except Exception as e:
                    logger.debug(f"Erro ao buscar link no navbar: {e}")
                
                # If no element found, try to find ANY clickable element in top-left
                # that might be the logo (more aggressive search)
                try:
                    # Get all elements in top-left area (expanded: first 150px horizontally, first 80px vertically)
                    elements_in_area = await self.page.evaluate("""
                        () => {
                            const elements = [];
                            // Try to find navbar first
                            const navbar = document.querySelector('.o_main_navbar');
                            const searchArea = navbar || document;
                            
                            const allElements = searchArea.querySelectorAll('a, button, [role="button"], .o_menu_brand, .navbar-brand, [onclick], [href]');
                            for (const el of allElements) {
                                const rect = el.getBoundingClientRect();
                                // Check if element is in top-left area (expanded search)
                                if (rect.x < 150 && rect.y < 80 && rect.width > 0 && rect.height > 0) {
                                    const text = el.textContent?.trim() || '';
                                    const ariaLabel = el.getAttribute('aria-label') || '';
                                    const title = el.getAttribute('title') || '';
                                    const href = el.getAttribute('href') || '';
                                    const className = el.className || '';
                                    const id = el.id || '';
                                    const allText = (text + ' ' + ariaLabel + ' ' + title + ' ' + className + ' ' + id).toLowerCase();
                                    
                                    // Exclude menu items
                                    if (!allText.includes('mensagens') && 
                                        !allText.includes('discuss') && 
                                        !allText.includes('menu') && 
                                        !allText.includes('apps') &&
                                        !allText.includes('o_mail_systray')) {
                                        // Get computed style to check if visible
                                        const style = window.getComputedStyle(el);
                                        const isVisible = style.display !== 'none' && 
                                                         style.visibility !== 'hidden' && 
                                                         style.opacity !== '0';
                                        
                                        if (isVisible) {
                                            elements.push({
                                                x: rect.x,
                                                y: rect.y,
                                                width: rect.width,
                                                height: rect.height,
                                                href: href,
                                                text: text.substring(0, 50),
                                                tagName: el.tagName,
                                                className: className.substring(0, 100)
                                            });
                                        }
                                    }
                                }
                            }
                            // Sort by x position (leftmost first), then by y (topmost first)
                            return elements.sort((a, b) => {
                                if (Math.abs(a.x - b.x) < 10) return a.y - b.y;
                                return a.x - b.x;
                            });
                        }
                    """)
                    
                    logger.info(f"Elementos encontrados no topo esquerdo: {len(elements_in_area) if elements_in_area else 0}")
                    if elements_in_area:
                        print(f"  📋 Encontrados {len(elements_in_area)} elementos no topo esquerdo:")
                        for i, elem_info in enumerate(elements_in_area[:5], 1):
                            print(f"    {i}. {elem_info.get('tagName')} em ({elem_info.get('x'):.0f}, {elem_info.get('y'):.0f}) href='{elem_info.get('href')}' text='{elem_info.get('text')[:30]}'")
                            logger.debug(f"  - {elem_info.get('tagName')} em ({elem_info.get('x')}, {elem_info.get('y')}) href={elem_info.get('href')} text='{elem_info.get('text')}'")
                    else:
                        print(f"  ⚠️  Nenhum elemento encontrado no topo esquerdo")
                        logger.warning("Nenhum elemento encontrado no topo esquerdo")
                    
                    if elements_in_area and len(elements_in_area) > 0:
                        # Try the leftmost element that looks like a logo (has href to home/web or is very left)
                        for elem_info in elements_in_area[:5]:  # Try first 5 leftmost elements
                            x = elem_info['x'] + elem_info['width'] / 2
                            y = elem_info['y'] + elem_info['height'] / 2
                            
                            # Prefer elements with href to home/web, but try all if needed
                            href = elem_info.get('href', '')
                            is_home_link = '/web' in href or '#home' in href or href == '/' or 'web#' in href
                            
                            # Try home links first, then any leftmost element
                            if is_home_link or elem_info['x'] < 50:
                                print(f"  🖱️  Tentando elemento em ({x:.1f}, {y:.1f}) - tag: {elem_info.get('tagName')}, href: {href or 'N/A'}")
                                logger.info(f"🖱️  Tentando elemento: {elem_info}")
                                
                                # Try to click the element directly using JavaScript
                                try:
                                    # Use JavaScript to find and click the element at this position
                                    clicked = await self.page.evaluate("""
                                        (targetX, targetY) => {
                                            const el = document.elementFromPoint(targetX, targetY);
                                            if (el) {
                                                // Walk up the DOM to find clickable parent
                                                let clickable = el;
                                                while (clickable && clickable !== document.body) {
                                                    if (clickable.tagName === 'A' || 
                                                        clickable.tagName === 'BUTTON' || 
                                                        clickable.onclick || 
                                                        clickable.getAttribute('role') === 'button' ||
                                                        clickable.classList.contains('o_menu_brand') ||
                                                        clickable.classList.contains('navbar-brand')) {
                                                        // Click it
                                                        clickable.click();
                                                        return true;
                                                    }
                                                    clickable = clickable.parentElement;
                                                }
                                            }
                                            return false;
                                        }
                                    """, x, y)
                                    
                                    if clicked:
                                        logger.info(f"Elemento clicado via JavaScript na posição ({x}, {y})")
                                        await asyncio.sleep(ACTION_DELAY * 2)
                                        await asyncio.sleep(ACTION_DELAY * 1)
                                        
                                        url_after = self.page.url
                                        if '/discuss' not in url_after:
                                            print(f"  ✅ Clique via JS executado - não está mais em /discuss (URL: {url_after})")
                                            logger.info(f"✅ Clique via JS executado - não está mais em /discuss")
                                            return True
                                        else:
                                            print(f"  ⚠️  Clique via JS mas ainda em /discuss, tentando próximo elemento")
                                            continue
                                    
                                    # Fallback: use cursor and mouse click
                                    await self.cursor_manager.move_to(x, y)
                                    await asyncio.sleep(ACTION_DELAY * 2)
                                    await self.cursor_manager.show_click_effect(x, y)
                                    await asyncio.sleep(0.05)
                                    
                                    url_before = self.page.url
                                    await self.page.mouse.click(x, y)
                                    await asyncio.sleep(ACTION_DELAY * 2)
                                    await asyncio.sleep(ACTION_DELAY * 1)
                                    
                                    url_after = self.page.url
                                    if url_before != url_after:
                                        print(f"  ✅ Clique executado - URL mudou: {url_before} -> {url_after}")
                                        logger.info(f"✅ Clique no elemento executado - URL mudou")
                                        return True
                                    elif '/discuss' not in url_after:
                                        # Not on discuss anymore, might have worked
                                        print(f"  ✅ Clique executado - não está mais em /discuss")
                                        logger.info(f"✅ Clique no elemento executado - não está mais em /discuss")
                                        return True
                                    # If still on discuss, try next element
                                    print(f"  ⚠️  Clique não mudou URL (ainda em {url_after}), tentando próximo elemento")
                                    continue
                                except Exception as e:
                                    logger.debug(f"Erro ao clicar no elemento: {e}")
                                    continue
                except Exception as e:
                    logger.debug(f"Erro ao buscar elementos no topo esquerdo: {e}")
                
                # Last resort: try clicking at very specific top-left coordinates
                # But first, find what element is actually at that position
                x = 30  # Left area, but not too left to avoid edge
                y = 20  # Top area, avoiding menu items below
                
                print(f"  🔍 Verificando elemento na posição ({x}, {y})...")
                logger.info(f"Verificando elemento na posição ({x}, {y})")
                
                # Find what element is at this position
                element_at_point = await self.page.evaluate(f"""
                    (() => {{
                        const targetX = {x};
                        const targetY = {y};
                        const el = document.elementFromPoint(targetX, targetY);
                        if (!el) return null;
                        
                        // Walk up to find clickable parent
                        let clickable = el;
                        while (clickable && clickable !== document.body) {{
                            const tag = clickable.tagName;
                            const hasHref = clickable.getAttribute('href');
                            const hasOnClick = clickable.onclick;
                            const role = clickable.getAttribute('role');
                            const className = clickable.className || '';
                            
                            if (tag === 'A' || tag === 'BUTTON' || hasOnClick || role === 'button' ||
                                className.includes('o_menu_brand') || className.includes('navbar-brand')) {{
                                const rect = clickable.getBoundingClientRect();
                                return {{
                                    tagName: tag,
                                    href: hasHref || '',
                                    className: className.substring(0, 100),
                                    text: clickable.textContent?.trim().substring(0, 50) || '',
                                    x: rect.x,
                                    y: rect.y,
                                    width: rect.width,
                                    height: rect.height
                                }};
                            }}
                            clickable = clickable.parentElement;
                        }}
                        return null;
                    }})()
                """)
                
                if element_at_point:
                    print(f"  📋 Elemento encontrado na posição: {element_at_point.get('tagName')} - text: '{element_at_point.get('text', '')[:30]}' - className: '{element_at_point.get('className', '')[:50]}'")
                    logger.info(f"Elemento encontrado na posição: {element_at_point}")
                    
                    # Use center of element for click
                    elem_x = element_at_point['x'] + element_at_point['width'] / 2
                    elem_y = element_at_point['y'] + element_at_point['height'] / 2
                    
                    print(f"  🖱️  Clicando no elemento em ({elem_x:.1f}, {elem_y:.1f})")
                    logger.info(f"Clicando no elemento em ({elem_x}, {elem_y})")
                    
                    await self.cursor_manager.move_to(elem_x, elem_y)
                    await asyncio.sleep(ACTION_DELAY * 2)
                    await self.cursor_manager.show_click_effect(elem_x, elem_y)
                    await asyncio.sleep(0.05)
                    
                    url_before = self.page.url
                    await self.page.mouse.click(elem_x, elem_y)
                    await asyncio.sleep(ACTION_DELAY * 2)
                    await asyncio.sleep(ACTION_DELAY * 1)
                    
                    url_after = self.page.url
                    if url_before != url_after:
                        print(f"  ✅ Clique executado - URL mudou: {url_before} -> {url_after}")
                        logger.info(f"✅ Clique no elemento executado - URL mudou")
                        return True
                    elif '/discuss' not in url_after:
                        print(f"  ✅ Clique executado - não está mais em /discuss")
                        logger.info(f"✅ Clique no elemento executado - não está mais em /discuss")
                        return True
                    else:
                        print(f"  ⚠️  Clique executado mas ainda em /discuss - navegação falhou")
                        logger.warning(f"Clique no elemento executado mas navegação falhou (ainda em /discuss)")
                        return False
                else:
                    print(f"  ⚠️  Nenhum elemento clicável encontrado na posição ({x}, {y})")
                    logger.warning(f"Nenhum elemento clicável encontrado na posição ({x}, {y})")
                    return False
            except Exception as e:
                print(f"  ❌ Erro ao clicar no canto superior esquerdo: {e}")
                logger.error(f"Erro ao clicar no canto superior esquerdo: {e}", exc_info=True)
        else:
            print(f"  ⚠️  Cursor manager não disponível - não é possível mover cursor")
            logger.warning("⚠️  Cursor manager não disponível - não é possível mover cursor")
        
        logger.warning("Odoo logo not found. Cannot navigate to dashboard.")
        return False

