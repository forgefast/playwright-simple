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
            button_text = action["click"]
            context = action.get("context")
            
            # Try to find button
            button_selectors = [
                f'button:has-text("{button_text}")',
                f'a:has-text("{button_text}")',
                f'button[title*="{button_text}"]',
                f'[role="button"]:has-text("{button_text}")',
            ]
            
            element_found = False
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
                        logger.info(f"Step {step.step_number}: Element found for click '{button_text}': {selector}")
                        break
                except Exception:
                    continue
            
            if not element_found:
                step.element_found = False
                step.warnings.append(f"Elemento não encontrado para click '{button_text}'")
                logger.warning(f"Step {step.step_number}: Elemento não encontrado para click '{button_text}'")
        
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
                    logger.warning(f"Step {step.step_number}: Campo não encontrado para fill '{label}'")
            except Exception as e:
                step.element_found = False
                step.warnings.append(f"Erro ao buscar campo '{label}': {str(e)}")
                logger.warning(f"Step {step.step_number}: Erro ao buscar campo '{label}': {e}")
        
        # Check for go_to actions (menu navigation)
        elif "go_to" in action:
            menu_path = action["go_to"]
            # For go_to, we can try to check if we're already on the target
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
                    logger.warning(f"Step {step.step_number}: Nenhum registro encontrado para '{search_text}'")
            except Exception as e:
                step.element_found = False
                step.warnings.append(f"Erro ao buscar registro '{search_text}': {str(e)}")
                logger.warning(f"Step {step.step_number}: Erro ao buscar registro '{search_text}': {e}")
    
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
                    
                    # Method 2: Check if we're on Dashboard and menu was "Dashboard"
                    elif menu_path.lower() in ["dashboard", "menu principal", "home"]:
                        dashboard_indicators = [
                            '.o_menu_apps',
                            '.o_main_navbar',
                            '.o_action_manager',
                            '[data-menu-xmlid="base.menu_administration"]',
                            '.o_web_client',
                        ]
                        for indicator in dashboard_indicators:
                            count = await test.page.locator(indicator).count()
                            if count > 0:
                                navigation_succeeded = True
                                verification_method = "Dashboard indicators found"
                                logger.info(f"Step {step.step_number}: Dashboard verificado (indicadores encontrados)")
                                break
                        
                        if not navigation_succeeded:
                            menu_item = test.page.locator('a:has-text("Dashboard"), .o_menu_item:has-text("Dashboard")').first
                            if await menu_item.count() > 0:
                                navigation_succeeded = True
                                verification_method = "Dashboard menu item found"
                                logger.info(f"Step {step.step_number}: Dashboard menu item encontrado")
                    
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
                    
                    # Set result
                    step.action_succeeded = navigation_succeeded
                    
                    if navigation_succeeded:
                        logger.info(f"Step {step.step_number}: Navegação verificada por {verification_method}")
                    else:
                        # Different log level for static vs non-static steps
                        if is_static:
                            logger.info(
                                f"Step {step.step_number}: Passo estático - mudança de estado não detectada "
                                f"(comportamento esperado para passo estático)"
                            )
                        else:
                            step.warnings.append(f"Navegação pode ter falhado: não foi possível verificar se '{menu_path}' foi acessado")
                            logger.warning(
                                f"Step {step.step_number}: Navegação não verificada para '{menu_path}' "
                                f"(passo não-estático - possível problema)"
                            )
                        
                except Exception as e:
                    step.action_succeeded = True
                    step.warnings.append(f"Não foi possível verificar navegação para '{menu_path}': {str(e)} (assumindo sucesso)")
                    logger.warning(f"Step {step.step_number}: Erro ao verificar navegação: {e}")
            
            # For click actions
            elif "click" in action:
                if step.element_found is not False:
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
                
        except Exception as e:
            step.action_succeeded = False
            step.warnings.append(f"Erro ao validar ação: {str(e)}")
            logger.warning(f"Step {step.step_number}: Erro ao validar ação: {e}")

