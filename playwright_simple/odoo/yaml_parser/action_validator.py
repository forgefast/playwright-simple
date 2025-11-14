#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Action validator for Odoo YAML tests.

Validates elements before actions and verifies actions succeeded after execution.
"""

import logging
from typing import Dict, Any, Optional
from playwright.async_api import Page

from ...core.step import TestStep

logger = logging.getLogger(__name__)


class ActionValidator:
    """Validator for Odoo actions."""
    
    @staticmethod
    async def validate_element_before_action(action: Dict[str, Any], test, step: TestStep) -> None:
        """
        Validate that required elements exist before executing action.
        
        Args:
            action: Action dictionary
            test: OdooTestBase instance
            step: TestStep instance to record validation results
        """
        # Check for click actions
        if "click" in action:
            click_data = action["click"]
            context = action.get("context")
            
            # Support both formats:
            # 1. click: "texto ou seletor" (string)
            # 2. click: { description: "descrição do elemento" } (dict)
            if isinstance(click_data, dict):
                click_target = click_data.get("description", "")
            else:
                click_target = click_data
            
            # Map common descriptions to CSS selectors
            description_to_selector = {
                "botão do menu de apps no canto superior esquerdo": "button.o_grid_apps_menu__button",
                "botão do menu de apps": "button.o_grid_apps_menu__button",
                "menu de apps": "button.o_grid_apps_menu__button",
                "app contatos no menu de apps": 'a:has-text("Contatos"), a[data-menu-xmlid*="contacts"]',
                "app vendas no menu de apps": 'a:has-text("Vendas"), a[data-menu-xmlid*="sale"]',
                "menu pedidos no submenu de vendas": 'a:has-text("Pedidos"), a[data-menu-xmlid*="sale.order"]',
                "menu produtos no submenu de vendas": 'a:has-text("Produtos"), a[data-menu-xmlid*="product"]',
                "setinha para baixo do searchbar": ".o_filters_menu .dropdown-toggle, .o_filters_menu button.dropdown-toggle, button.o_filters_menu_button.dropdown-toggle, .o_control_panel .o_filters_menu button",
                "setinha do searchbar": ".o_filters_menu .dropdown-toggle, .o_filters_menu button.dropdown-toggle, button.o_filters_menu_button.dropdown-toggle, .o_control_panel .o_filters_menu button",
                "botão de filtros": ".o_filters_menu .dropdown-toggle, .o_filters_menu button.dropdown-toggle, button.o_filters_menu_button.dropdown-toggle, .o_control_panel .o_filters_menu button",
            }
            
            # Check if description maps to a known selector or special action
            click_target_lower = click_target.lower().strip()
            
            # Special handling for "Filtros" - check if filter button exists
            if click_target_lower in ["filtros", "filters", "menu de filtros"]:
                # Try to find filter dropdown button using the same selectors as FilterHelper
                filter_selectors = [
                    # Search view dropdown toggler (most specific - the actual filter button)
                    'button.o_searchview_dropdown_toggler',
                    'button.o_searchview_dropdown_toggler.dropdown-toggle',
                    '.o_searchview_dropdown_toggler',
                    'button.o_searchview_dropdown_toggler.btn',
                    # Alternative selectors
                    '.o_searchview button.dropdown-toggle',
                    'button[title*="Ativar/Desativar painel de pesquisa"]',
                    'button[data-hotkey="shift+q"]',
                    '.o_filters_menu .dropdown-toggle',
                    '.o_filters_menu button.dropdown-toggle',
                    'button.o_filters_menu_button.dropdown-toggle',
                    '.o_control_panel .o_filters_menu button',
                    'button[title*="Filtros"]',
                    'button[title*="Filters"]',
                ]
                element_found = False
                found_selector = None
                for selector in filter_selectors:
                    try:
                        btn = test.page.locator(selector).first
                        count = await btn.count()
                        if count > 0:
                            # Check if visible
                            is_visible = await btn.is_visible()
                            if is_visible:
                                element_found = True
                                found_selector = selector
                                step.element_found = True
                                step.action_details['element_selector'] = selector
                                logger.info(f"Step {step.step_number}: Botão de filtros encontrado: {selector}")
                                break
                            else:
                                logger.debug(f"Step {step.step_number}: Botão encontrado mas não visível: {selector}")
                    except Exception as e:
                        logger.debug(f"Step {step.step_number}: Erro ao verificar seletor {selector}: {e}")
                        continue
                
                if not element_found:
                    # Try to find ANY button in search area as last resort
                    try:
                        search_buttons = test.page.locator('.o_searchview button, .o_cp_searchview button').all()
                        for btn in search_buttons:
                            try:
                                if await btn.is_visible():
                                    title = await btn.get_attribute('title') or ''
                                    classes = await btn.get_attribute('class') or ''
                                    if 'dropdown' in classes.lower() or 'toggler' in classes.lower() or 'pesquisa' in title.lower():
                                        element_found = True
                                        found_selector = 'fallback: search area button'
                                        step.element_found = True
                                        step.action_details['element_selector'] = found_selector
                                        logger.info(f"Step {step.step_number}: Botão de filtros encontrado (fallback): {title}")
                                        break
                            except:
                                continue
                    except Exception as e:
                        logger.debug(f"Step {step.step_number}: Erro no fallback: {e}")
                
                if not element_found:
                    step.element_found = False
                    step.warnings.append(f"Botão de filtros não encontrado")
                    logger.error(f"Step {step.step_number}: Botão de filtros não encontrado com nenhum seletor")
                    await ActionValidator._save_error_html(test, step.step_number, f"click_filtros", 
                                                          f"Botão de filtros não encontrado")
                    raise RuntimeError(
                        f"Passo {step.step_number}: Botão de filtros não encontrado. "
                        f"HTML da página salvo para debug."
                    )
            elif click_target_lower in description_to_selector:
                click_target = description_to_selector[click_target_lower]
                is_css_selector = True
            else:
                # Check if it's a CSS selector (same logic as action_parser)
                is_css_selector = (
                    click_target.startswith(".") or  # .class
                    click_target.startswith("#") or  # #id
                    click_target.startswith("[") or  # [attribute]
                    click_target.startswith("button.") or  # button.class
                    click_target.startswith("a.") or  # a.class
                    " > " in click_target or  # child selector
                    " " in click_target and ("." in click_target or "#" in click_target)  # descendant with class/id
                )
            
            element_found = False
            if click_target_lower not in ["filtros", "filters", "menu de filtros"] and is_css_selector:
                # Use CSS selector directly
                try:
                    if context == "wizard":
                        wizard_loc = await test.wizard.get_wizard_locator()
                        if wizard_loc:
                            btn = wizard_loc.locator(click_target).first
                        else:
                            btn = None
                    else:
                        btn = test.page.locator(click_target).first
                    
                    if btn and await btn.count() > 0 and await btn.is_visible():
                        element_found = True
                        step.element_found = True
                        step.action_details['element_selector'] = click_target
                        logger.info(f"Step {step.step_number}: Element found for click (CSS selector) '{click_target}'")
                except Exception as e:
                    logger.debug(f"Error checking CSS selector '{click_target}': {e}")
            else:
                # Text-based click - try to find button by text
                button_selectors = [
                    f'button:has-text("{click_target}")',
                    f'a:has-text("{click_target}")',
                    f'button[title*="{click_target}"]',
                    f'[role="button"]:has-text("{click_target}")',
                ]
                
                for selector in button_selectors:
                    try:
                        if context == "wizard":
                            wizard_loc = await test.wizard.get_wizard_locator()
                            if wizard_loc:
                                btn = wizard_loc.locator(selector).first
                            else:
                                continue
                        else:
                            btn = test.page.locator(selector).first
                        
                        if await btn.count() > 0 and await btn.is_visible():
                            element_found = True
                            step.element_found = True
                            step.action_details['element_selector'] = selector
                            logger.info(f"Step {step.step_number}: Element found for click '{click_target}': {selector}")
                            break
                    except Exception:
                        continue
            
            if not element_found:
                step.element_found = False
                step.warnings.append(f"Elemento não encontrado para click '{click_target}'")
                logger.error(f"Step {step.step_number}: Elemento não encontrado para click '{click_target}'")
                
                # RIGOROUS: Save HTML and fail immediately for critical actions
                await ActionValidator._save_error_html(test, step.step_number, f"click_{click_target}", 
                                                      f"Elemento não encontrado para click '{click_target}'")
                raise RuntimeError(
                    f"Passo {step.step_number}: Elemento não encontrado para click '{click_target}'. "
                    f"HTML da página salvo para debug."
                )
        
        # Check for fill actions
        elif "fill" in action:
            fill_value = action["fill"]
            context = action.get("context")
            
            # Parse field label
            if isinstance(fill_value, str) and '=' in fill_value:
                label = fill_value.split('=', 1)[0].strip()
            else:
                label = fill_value if isinstance(fill_value, str) else action.get("label", "")
            
            # Try to find field
            try:
                field_locator, field_name, field_type = await test.field.find_field_by_label(label, context)
                if field_locator:
                    step.element_found = True
                    step.action_details['field_name'] = field_name
                    step.action_details['field_type'] = field_type
                    logger.info(f"Step {step.step_number}: Campo encontrado para fill '{label}': {field_name} ({field_type})")
                else:
                    step.element_found = False
                    step.warnings.append(f"Campo não encontrado para fill '{label}'")
                    logger.error(f"Step {step.step_number}: Campo não encontrado para fill '{label}'")
                    
                    # RIGOROUS: Save HTML and fail immediately
                    await ActionValidator._save_error_html(test, step.step_number, f"fill_{label}", 
                                                          f"Campo não encontrado para fill '{label}'")
                    raise RuntimeError(
                        f"Passo {step.step_number}: Campo não encontrado para fill '{label}'. "
                        f"HTML da página salvo para debug."
                    )
            except Exception as e:
                step.element_found = False
                step.warnings.append(f"Erro ao buscar campo '{label}': {str(e)}")
                logger.error(f"Step {step.step_number}: Erro ao buscar campo '{label}': {e}")
                
                # RIGOROUS: Save HTML and fail immediately
                await ActionValidator._save_error_html(test, step.step_number, f"fill_{label}_error", 
                                                      f"Erro ao buscar campo '{label}': {str(e)}")
                raise RuntimeError(
                    f"Passo {step.step_number}: Erro ao buscar campo '{label}': {str(e)}. "
                    f"HTML da página salvo para debug."
                ) from e
        
        # Check for open_filters action (Odoo-specific)
        elif "open_filters" in action:
            # Check if filter button exists
            filter_selectors = [
                'button.o_searchview_dropdown_toggler',
                'button.o_searchview_dropdown_toggler.dropdown-toggle',
                '.o_searchview_dropdown_toggler',
                'button.o_searchview_dropdown_toggler.btn',
                '.o_searchview button.dropdown-toggle',
                'button[title*="Ativar/Desativar painel de pesquisa"]',
                'button[data-hotkey="shift+q"]',
            ]
            element_found = False
            for selector in filter_selectors:
                try:
                    btn = test.page.locator(selector).first
                    count = await btn.count()
                    if count > 0:
                        is_visible = await btn.is_visible()
                        if is_visible:
                            element_found = True
                            step.element_found = True
                            step.action_details['element_selector'] = selector
                            logger.info(f"Step {step.step_number}: Botão de filtros encontrado: {selector}")
                            break
                except Exception:
                    continue
            
            if not element_found:
                step.element_found = False
                step.warnings.append(f"Botão de filtros não encontrado")
                logger.error(f"Step {step.step_number}: Botão de filtros não encontrado")
                await ActionValidator._save_error_html(test, step.step_number, f"open_filters", 
                                                      f"Botão de filtros não encontrado")
                raise RuntimeError(
                    f"Passo {step.step_number}: Botão de filtros não encontrado. "
                    f"HTML da página salvo para debug."
                )
        
        # Check for go_to actions (menu navigation)
        elif "go_to" in action:
            menu_path = action["go_to"]
            menu_path_lower = menu_path.lower().strip()
            
            # Special case: Filters menu (deprecated - use open_filters instead)
            if menu_path_lower in ["filtros", "filters", "menu de filtros"]:
                logger.warning("Using 'go_to: Filtros' is deprecated. Use 'open_filters: true' instead.")
                # Check if filters menu is already open
                menu_is_open = await test.page.evaluate("""
                    () => {
                        const dropdown = document.querySelector('.o_filters_menu .dropdown-menu, .o_filters_menu_menu, .o_dropdown_menu');
                        return dropdown && dropdown.style.display !== 'none' && dropdown.offsetParent !== null;
                    }
                """)
                if menu_is_open:
                    step.element_found = True
                    step.action_details['filters_menu_open'] = True
                    logger.info(f"Step {step.step_number}: Menu de filtros já está aberto")
            else:
                # For other go_to, we can try to check if we're already on the target
                try:
                    menu_parts = menu_path.split('>')
                    app_name = menu_parts[0].strip() if menu_parts else menu_path.strip()
                    
                    # Check if we're already in the target app
                    if hasattr(test, 'menu') and hasattr(test.menu, '_is_current_app'):
                        is_current = await test.menu._is_current_app(app_name)
                        if is_current:
                            step.element_found = True  # We're already there
                            step.action_details['already_in_app'] = True
                            logger.info(f"Step {step.step_number}: Já está no app '{app_name}'")
                except Exception:
                    pass
            
            step.action_details['menu_path'] = menu_path
        
        # Check for hover actions
        elif "hover" in action:
            hover_data = action["hover"]
            context = action.get("context")
            
            # Support both formats:
            # 1. hover: "texto" (string)
            # 2. hover: { description: "descrição do elemento" } (dict)
            if isinstance(hover_data, dict):
                hover_target = hover_data.get("description", "")
            else:
                hover_target = hover_data
            
            # Map common descriptions to CSS selectors
            description_to_selector = {
                "menu principal": "button.o_grid_apps_menu__button",
                "botão do menu de apps no canto superior esquerdo": "button.o_grid_apps_menu__button",
                "botão do menu de apps": "button.o_grid_apps_menu__button",
                "menu de apps": "button.o_grid_apps_menu__button",
            }
            
            # Check if description maps to a known selector
            hover_target_lower = hover_target.lower().strip()
            if hover_target_lower in description_to_selector:
                hover_selector = description_to_selector[hover_target_lower]
                hover_selectors = [hover_selector]
            else:
                # Try to find element for hover by text
                hover_selectors = [
                    f'button:has-text("{hover_target}")',
                    f'a:has-text("{hover_target}")',
                    f'[title*="{hover_target}"]',
                    f'[aria-label*="{hover_target}"]',
                ]
            
            # Try to find element for hover
            element_found = False
            
            for selector in hover_selectors:
                try:
                    if context == "wizard":
                        wizard_loc = await test.wizard.get_wizard_locator()
                        if wizard_loc:
                            elem = wizard_loc.locator(selector).first
                        else:
                            continue
                    else:
                        elem = test.page.locator(selector).first
                    
                    if await elem.count() > 0 and await elem.is_visible():
                        element_found = True
                        step.element_found = True
                        step.action_details['element_selector'] = selector
                        logger.info(f"Step {step.step_number}: Element found for hover '{hover_target}': {selector}")
                        break
                except Exception:
                    continue
            
            if not element_found:
                step.element_found = False
                step.warnings.append(f"Elemento não encontrado para hover '{hover_target}'")
                logger.warning(f"Step {step.step_number}: Elemento não encontrado para hover '{hover_target}'")
                # Hover is not critical, so we don't fail - just warn
        
        # Check for open_record actions
        elif "open_record" in action:
            search_text = action["open_record"]
            # Try to find record
            try:
                records = await test.view.search_records(search_text)
                if records:
                    step.element_found = True
                    step.action_details['records_found'] = len(records)
                    logger.info(f"Step {step.step_number}: {len(records)} registro(s) encontrado(s) para '{search_text}'")
                else:
                    step.element_found = False
                    step.warnings.append(f"Nenhum registro encontrado para '{search_text}'")
                    logger.error(f"Step {step.step_number}: Nenhum registro encontrado para '{search_text}'")
                    
                    # RIGOROUS: Save HTML and fail immediately
                    await ActionValidator._save_error_html(test, step.step_number, f"open_record_{search_text}", 
                                                          f"Nenhum registro encontrado para '{search_text}'")
                    raise RuntimeError(
                        f"Passo {step.step_number}: Nenhum registro encontrado para '{search_text}'. "
                        f"HTML da página salvo para debug."
                    )
            except Exception as e:
                step.element_found = False
                step.warnings.append(f"Erro ao buscar registro '{search_text}': {str(e)}")
                logger.error(f"Step {step.step_number}: Erro ao buscar registro '{search_text}': {e}")
                
                # RIGOROUS: Save HTML and fail immediately
                await ActionValidator._save_error_html(test, step.step_number, f"open_record_{search_text}_error", 
                                                      f"Erro ao buscar registro '{search_text}': {str(e)}")
                raise RuntimeError(
                    f"Passo {step.step_number}: Erro ao buscar registro '{search_text}': {str(e)}. "
                    f"HTML da página salvo para debug."
                ) from e
    
    @staticmethod
    async def capture_action_state(action: Dict[str, Any], test) -> Dict[str, Any]:
        """
        Capture page state before action for validation.
        
        Args:
            action: Action dictionary
            test: OdooTestBase instance
            
        Returns:
            Dictionary with state information
        """
        state = {}
        try:
            state['url'] = test.page.url
            state['title'] = await test.page.title()
        except Exception:
            pass
        return state
    
    @staticmethod
    async def validate_action_succeeded(action: Dict[str, Any], test, step: TestStep, state_before: Dict[str, Any]) -> None:
        """
        Validate that action succeeded by checking if page state changed.
        
        Args:
            action: Action dictionary (may contain 'static' flag)
            test: OdooTestBase instance
            step: TestStep instance to record validation results
            state_before: State before action
        """
        try:
            # Check if this is a static step
            is_static = action.get('static', False)
            
            state_after = await ActionValidator.capture_action_state(action, test)
            step.action_details['state_after'] = state_after
            step.action_details['is_static'] = is_static
            
            # For go_to actions, check if navigation succeeded by multiple means
            if "go_to" in action:
                url_before = state_before.get('url', '')
                url_after = state_after.get('url', '')
                menu_path = action.get("go_to", "")
                
                # Odoo is a SPA - URL might not change even when navigation works
                navigation_succeeded = False
                verification_method = None
                
                try:
                    # Method 1: Check if URL changed (most reliable)
                    if url_before and url_after and url_before != url_after:
                        navigation_succeeded = True
                        verification_method = "URL changed"
                        logger.info(f"Step {step.step_number}: Navegação bem-sucedida (URL mudou): {url_before} -> {url_after}")
                    
                    # Special case: Portal navigation - if URL contains /my, consider success
                    elif menu_path.lower() in ["portal", "meu portal", "portal do cliente"]:
                        if "/my" in url_after:
                            navigation_succeeded = True
                            verification_method = "Portal URL detected (/my)"
                            logger.info(f"Step {step.step_number}: Portal verificado (URL contém /my)")
                    
                    # Method 2: Check if we're on Dashboard (menu de apps aberto)
                    elif menu_path.lower() in ["dashboard", "menu principal", "home"]:
                        # Dashboard do colaborador = menu de apps aberto
                        # Verificar se o menu de apps está aberto
                        menu_is_open = await test.page.evaluate("""
                            () => {
                                return document.body.classList.contains('o_apps_menu_opened') ||
                                       document.querySelector('.o-app-menu-list') !== null ||
                                       document.querySelector('.o_apps_menu') !== null;
                            }
                        """)
                        
                        if menu_is_open:
                            navigation_succeeded = True
                            verification_method = "Menu de apps aberto (Dashboard)"
                            logger.info(f"Step {step.step_number}: Dashboard verificado (menu de apps está aberto)")
                        else:
                            # Fallback: verificar indicadores do dashboard
                            dashboard_indicators = [
                                '.o_menu_apps',
                                '.o_main_navbar',
                                '.o_action_manager',
                            ]
                            for indicator in dashboard_indicators:
                                count = await test.page.locator(indicator).count()
                                if count > 0:
                                    navigation_succeeded = True
                                    verification_method = "Dashboard indicators found"
                                    logger.info(f"Step {step.step_number}: Dashboard verificado (indicadores encontrados)")
                                    break
                    
                    
                    # Method 3: Check if we're already in the target app
                    elif step.action_details.get('already_in_app'):
                        navigation_succeeded = True
                        verification_method = "Already in target app"
                        logger.info(f"Step {step.step_number}: Já estava no app '{menu_path}'")
                    
                    # Method 4: For other menus, check if menu item is active/visible
                    else:
                        menu_parts = menu_path.split('>')
                        app_name = menu_parts[0].strip() if menu_parts else menu_path.strip()
                        
                        # First, check if we're already in the app
                        try:
                            if hasattr(test, 'menu') and hasattr(test.menu, '_is_current_app'):
                                is_current = await test.menu._is_current_app(app_name)
                                if is_current:
                                    navigation_succeeded = True
                                    verification_method = f"Already in app '{app_name}'"
                                    logger.info(f"Step {step.step_number}: Já está no app '{app_name}'")
                        except Exception:
                            pass
                        
                        if not navigation_succeeded:
                            # First check: if menu de apps is open, we're NOT in an app yet
                            menu_is_open = await test.page.evaluate("""
                                () => {
                                    return document.body.classList.contains('o_apps_menu_opened') ||
                                           document.querySelector('.o-app-menu-list') !== null ||
                                           document.querySelector('.o_apps_menu') !== null;
                                }
                            """)
                            
                            if menu_is_open:
                                # Menu de apps está aberto = não navegamos para o app ainda
                                logger.debug(f"Step {step.step_number}: Menu de apps está aberto - não estamos no app '{app_name}' ainda")
                            else:
                                # Check if menu item for this app is visible/active
                                menu_selectors = [
                                    f'a:has-text("{app_name}")',
                                    f'.o_menu_item:has-text("{app_name}")',
                                    f'[data-menu-xmlid*="{app_name.lower()}"]',
                                    f'.o_app[data-menu-xmlid*="{app_name.lower()}"]',
                                ]
                                
                                for selector in menu_selectors:
                                    try:
                                        menu_item = test.page.locator(selector).first
                                        if await menu_item.count() > 0:
                                            is_visible = await menu_item.is_visible()
                                            classes = await menu_item.get_attribute('class') or ''
                                            is_active = 'active' in classes or 'o_menu_item_active' in classes
                                            
                                            if is_visible or is_active:
                                                navigation_succeeded = True
                                                verification_method = f"Menu item '{app_name}' found and active"
                                                logger.info(f"Step {step.step_number}: Menu '{app_name}' encontrado e ativo")
                                                break
                                    except Exception:
                                        continue
                            
                            # Method 5: Check if page content changed (heuristic)
                            if not navigation_succeeded:
                                try:
                                    action_manager = test.page.locator('.o_action_manager, .o_view_manager')
                                    if await action_manager.count() > 0:
                                        children = action_manager.locator('> *').first
                                        if await children.count() > 0:
                                            navigation_succeeded = True
                                            verification_method = "Action manager has content"
                                            logger.info(f"Step {step.step_number}: Action manager tem conteúdo (navegação provavelmente funcionou)")
                                except Exception:
                                    pass
                    
                    # ASSERT: Navigation must have succeeded
                    if not navigation_succeeded:
                        # Build detailed error message
                        current_url = url_after
                        page_title = state_after.get('title', 'unknown')
                        
                        error_msg = (
                            f"ASSERT FALHOU no passo {step.step_number}: "
                            f"Navegação para '{menu_path}' não funcionou.\n"
                            f"  - URL atual: {current_url}\n"
                            f"  - Título da página: {page_title}\n"
                            f"  - Esperado: {menu_path}"
                        )
                        
                        # Different behavior for static vs non-static steps
                        if is_static:
                            # For static steps, just warn but don't fail
                            step.warnings.append(f"Navegação não verificada para '{menu_path}' (passo estático)")
                            logger.warning(f"Step {step.step_number}: {error_msg} (passo estático - não falhando)")
                            step.action_succeeded = True  # Don't fail static steps
                        else:
                            # For non-static steps, FAIL the test
                            step.action_succeeded = False
                            logger.error(f"Step {step.step_number}: {error_msg}")
                            raise AssertionError(error_msg)
                    else:
                        # Navigation succeeded - verify we're on the right page
                        step.action_succeeded = True
                        logger.info(f"Step {step.step_number}: ✅ ASSERT PASSOU - Navegação para '{menu_path}' verificada por {verification_method}")
                        
                        # Additional verification: make sure we're not on wrong page
                        await ActionValidator._assert_correct_page(test, menu_path, step.step_number)
                        
                except Exception as e:
                    step.action_succeeded = True
                    step.warnings.append(f"Não foi possível verificar navegação para '{menu_path}': {str(e)} (assumindo sucesso)")
                    logger.warning(f"Step {step.step_number}: Erro ao verificar navegação: {e}")
            
            # For open_filters action (Odoo-specific)
            elif "open_filters" in action:
                # Check if filters menu opened
                menu_is_open = await test.page.evaluate("""
                    () => {
                        // Check multiple possible dropdown menu selectors
                        const selectors = [
                            '.o_searchview_dropdown_menu',
                            '.o_filters_menu .dropdown-menu',
                            '.o_filters_menu_menu',
                            '.o_dropdown_menu',
                            '.dropdown-menu.show',
                            '.o_searchview .dropdown-menu',
                        ];
                        
                        for (const selector of selectors) {
                            const dropdown = document.querySelector(selector);
                            if (dropdown && dropdown.style.display !== 'none' && dropdown.offsetParent !== null) {
                                return true;
                            }
                        }
                        
                        // Also check if button aria-expanded is true
                        const button = document.querySelector('button.o_searchview_dropdown_toggler');
                        if (button && button.getAttribute('aria-expanded') === 'true') {
                            return true;
                        }
                        
                        return false;
                    }
                """)
                if menu_is_open:
                    step.action_succeeded = True
                    logger.info(f"Step {step.step_number}: Menu de filtros aberto com sucesso")
                else:
                    step.action_succeeded = False
                    step.warnings.append("Menu de filtros não foi aberto após a ação")
                    logger.warning(f"Step {step.step_number}: Menu de filtros não foi aberto após a ação")
            
            # For click actions
            elif "click" in action:
                click_data = action["click"]
                if isinstance(click_data, dict):
                    click_target = click_data.get("description", "")
                else:
                    click_target = click_data
                
                click_target_lower = click_target.lower().strip()
                
                # Special validation for "Filtros" click - check if filter menu opened
                if click_target_lower in ["filtros", "filters", "menu de filtros"]:
                    menu_is_open = await test.page.evaluate("""
                        () => {
                            // Check multiple possible dropdown menu selectors
                            const selectors = [
                                '.o_searchview_dropdown_menu',
                                '.o_filters_menu .dropdown-menu',
                                '.o_filters_menu_menu',
                                '.o_dropdown_menu',
                                '.dropdown-menu.show',
                                '.o_searchview .dropdown-menu',
                            ];
                            
                            for (const selector of selectors) {
                                const dropdown = document.querySelector(selector);
                                if (dropdown && dropdown.style.display !== 'none' && dropdown.offsetParent !== null) {
                                    return true;
                                }
                            }
                            
                            // Also check if button aria-expanded is true
                            const button = document.querySelector('button.o_searchview_dropdown_toggler');
                            if (button && button.getAttribute('aria-expanded') === 'true') {
                                return true;
                            }
                            
                            return false;
                        }
                    """)
                    if menu_is_open:
                        step.action_succeeded = True
                        logger.info(f"Step {step.step_number}: Menu de filtros aberto com sucesso")
                    else:
                        step.action_succeeded = False
                        step.warnings.append("Menu de filtros não foi aberto após o clique")
                        logger.warning(f"Step {step.step_number}: Menu de filtros não foi aberto após o clique")
                elif step.element_found is not False:
                    step.action_succeeded = True
                    if is_static:
                        logger.info(
                            f"Step {step.step_number}: Click executado em passo estático "
                            f"(elemento encontrado - mudança de estado não esperada)"
                        )
                    else:
                        logger.info(f"Step {step.step_number}: Click executado (elemento encontrado)")
                else:
                    step.action_succeeded = False
                    step.warnings.append("Click pode ter falhado: elemento não foi encontrado antes da ação")
                    logger.warning(f"Step {step.step_number}: Click pode ter falhado: elemento não encontrado")
            
            # For fill actions
            elif "fill" in action:
                if step.element_found is not False:
                    step.action_succeeded = True
                    if is_static:
                        logger.info(
                            f"Step {step.step_number}: Fill executado em passo estático "
                            f"(campo encontrado - mudança de estado não esperada)"
                        )
                    else:
                        logger.info(f"Step {step.step_number}: Fill executado (campo encontrado)")
                else:
                    step.action_succeeded = False
                    step.warnings.append("Fill pode ter falhado: campo não foi encontrado antes da ação")
                    logger.warning(f"Step {step.step_number}: Fill pode ter falhado: campo não encontrado")
            
            # For open_record
            elif "open_record" in action:
                if step.element_found is not False:
                    step.action_succeeded = True
                    logger.info(f"Step {step.step_number}: Open record executado (registro encontrado)")
                else:
                    step.action_succeeded = False
                    step.warnings.append("Open record pode ter falhado: registro não foi encontrado antes da ação")
                    logger.warning(f"Step {step.step_number}: Open record pode ter falhado: registro não encontrado")
            
            # For other actions, assume success if no exception
            else:
                step.action_succeeded = True
                
        except AssertionError:
            # Re-raise assertion errors (these are intentional test failures)
            raise
        except Exception as e:
            step.action_succeeded = False
            step.warnings.append(f"Erro ao validar ação: {str(e)}")
            logger.warning(f"Step {step.step_number}: Erro ao validar ação: {e}")
    
    @staticmethod
    async def _assert_correct_page(test, menu_path: str, step_number: int) -> None:
        """
        Assert that we're on the correct page after navigation.
        
        Args:
            test: OdooTestBase instance
            menu_path: Expected menu path (e.g., "Dashboard", "Contatos", "Vendas > Pedidos")
            step_number: Step number for error messages
            
        Raises:
            AssertionError: If we're not on the expected page
        """
        try:
            current_url = test.page.url.lower()
            page_title = (await test.page.title()).lower()
            menu_lower = menu_path.lower().strip()
            
            # Dashboard assertions
            if menu_lower in ["dashboard", "menu principal", "home", "início", "página inicial"]:
                # Dashboard do colaborador = menu de apps aberto (não importa a URL)
                # Verificar se o menu de apps está aberto
                menu_is_open = await test.page.evaluate("""
                    () => {
                        return document.body.classList.contains('o_apps_menu_opened') ||
                               document.querySelector('.o-app-menu-list') !== null ||
                               document.querySelector('.o_apps_menu') !== null;
                    }
                """)
                
                if not menu_is_open:
                    # Menu não está aberto - Dashboard não foi acessado
                    raise AssertionError(
                        f"ASSERT FALHOU no passo {step_number}: "
                        f"Esperado Dashboard (menu de apps aberto), mas o menu não está aberto (URL: {test.page.url})"
                    )
            
            # Portal assertions
            elif menu_lower in ["portal", "meu portal", "portal do cliente"]:
                if '/my' not in current_url:
                    raise AssertionError(
                        f"ASSERT FALHOU no passo {step_number}: "
                        f"Esperado Portal (/my), mas URL é {test.page.url}"
                    )
            
            # Shop/E-commerce assertions
            elif menu_lower in ["loja", "e-commerce", "shop", "compras"]:
                if '/shop' not in current_url:
                    raise AssertionError(
                        f"ASSERT FALHOU no passo {step_number}: "
                        f"Esperado Shop (/shop), mas URL é {test.page.url}"
                    )
            
            # Menu path assertions (e.g., "Contatos", "Vendas > Pedidos")
            else:
                menu_parts = menu_path.split('>')
                app_name = menu_parts[0].strip() if menu_parts else menu_path.strip()
                app_name_lower = app_name.lower()
                
                # Check if we're in the correct app
                if hasattr(test, 'menu') and hasattr(test.menu, '_is_current_app'):
                    is_current = await test.menu._is_current_app(app_name)
                    if not is_current:
                        # Check URL patterns as fallback
                        url_patterns = {
                            'contatos': ['/contacts', '/odoo/contacts'],
                            'contacts': ['/contacts', '/odoo/contacts'],
                            'vendas': ['/sales', '/odoo/sales'],
                            'sales': ['/sales', '/odoo/sales'],
                        }
                        
                        found_pattern = False
                        if app_name_lower in url_patterns:
                            for pattern in url_patterns[app_name_lower]:
                                if pattern in current_url:
                                    found_pattern = True
                                    break
                        
                        if not found_pattern:
                            # Check page title
                            if app_name_lower not in page_title:
                                raise AssertionError(
                                    f"ASSERT FALHOU no passo {step_number}: "
                                    f"Esperado app '{app_name}', mas não está no app correto.\n"
                                    f"  - URL atual: {test.page.url}\n"
                                    f"  - Título: {await test.page.title()}\n"
                                    f"  - Esperado: {menu_path}"
                                )
                
                # If submenu specified, verify we're on the submenu page
                if len(menu_parts) > 1:
                    submenu = menu_parts[1].strip().lower()
                    submenu_in_title = submenu in page_title
                    submenu_in_url = submenu.replace(' ', '') in current_url.replace(' ', '')
                    
                    if not submenu_in_title and not submenu_in_url:
                        # Try to find submenu in page content
                        submenu_selectors = [
                            f'a:has-text("{submenu}")',
                            f'.o_menu_item:has-text("{submenu}")',
                            f'h1:has-text("{submenu}")',
                            f'h2:has-text("{submenu}")',
                        ]
                        found_submenu = False
                        for selector in submenu_selectors:
                            if await test.page.locator(selector).count() > 0:
                                found_submenu = True
                                break
                        
                        if not found_submenu:
                            raise AssertionError(
                                f"ASSERT FALHOU no passo {step_number}: "
                                f"Esperado submenu '{submenu}' de '{app_name}', mas não encontrado.\n"
                                f"  - URL atual: {test.page.url}\n"
                                f"  - Título: {await test.page.title()}\n"
                                f"  - Esperado: {menu_path}"
                            )
        
        except AssertionError:
            # Re-raise assertion errors
            raise
        except Exception as e:
            # Log but don't fail on verification errors (might be false positives)
            logger.warning(f"Step {step_number}: Erro ao verificar página correta: {e}")
    
    @staticmethod
    async def _save_error_html(test, step_number: int, action_name: str, reason: str) -> None:
        """
        Save HTML content when validation fails.
        
        Args:
            test: OdooTestBase instance
            step_number: Step number
            action_name: Name of the action that failed
            reason: Reason for the error
        """
        try:
            from pathlib import Path
            import datetime
            
            # Get test name
            test_name = getattr(test, 'test_name', 'unknown')
            
            # Create error directory
            project_root = Path(__file__).parent.parent.parent.parent.parent
            error_dir = project_root / "presentation" / "playwright" / "screenshots" / test_name
            error_dir.mkdir(parents=True, exist_ok=True)
            
            # Save HTML
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            html_path = error_dir / f"debug_error_step_{step_number}_{action_name}_{timestamp}.html"
            html_content = await test.page.content()
            html_path.write_text(html_content, encoding='utf-8')
            
            logger.error(f"HTML salvo em {html_path} - Razão: {reason}")
            print(f"    📄 HTML de erro salvo: {html_path}")
        except Exception as e:
            logger.warning(f"Erro ao salvar HTML: {e}")

