#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ForgeERP-specific selectors.

Provides selectors for common ForgeERP UI elements including navigation,
forms, buttons, modals, and HTMX containers.
"""

from typing import List, Optional


class ForgeERPSelectors:
    """Selectors for ForgeERP UI elements."""
    
    # Navigation
    NAV_HOME = 'a[href="/"]'
    NAV_SETUP = 'a[href="/setup"]'
    NAV_PROVISION = 'a[href="/provision"]'
    NAV_STATUS = 'a[href="/status"]'
    NAV_DEPLOY = 'a[href="/deploy"]'
    NAV_DIAGNOSTICS = 'a[href="/diagnostics"]'
    
    # Form fields (common names)
    FIELD_CLIENT_NAME = 'input[name="client_name"]'
    FIELD_ENVIRONMENT = 'select[name="environment"], input[name="environment"]'
    FIELD_DATABASE_TYPE = 'select[name="database_type"]'
    FIELD_NAMESPACE = 'input[name="namespace"]'
    FIELD_CHART_NAME = 'input[name="chart_name"]'
    FIELD_CHART_VERSION = 'input[name="chart_version"]'
    
    # Buttons
    BUTTON_SUBMIT = 'button[type="submit"]'
    BUTTON_PROVISION = 'button:has-text("Provision"), button:has-text("Provision Client")'
    BUTTON_DEPLOY = 'button:has-text("Deploy")'
    BUTTON_CHECK_STATUS = 'button:has-text("Check Status")'
    BUTTON_RUN_DIAGNOSTICS = 'button:has-text("Run Diagnostics"), button:has-text("Run Summary Diagnostics")'
    
    # HTMX containers
    HTMX_PROVISION_RESULT = '#provision-result'
    HTMX_DEPLOY_RESULT = '#deploy-result'
    HTMX_STATUS_RESULT = '#status-result'
    HTMX_DIAGNOSTICS_SUMMARY = '#diagnostics-summary'
    HTMX_CLIENT_DIAGNOSTICS = '#client-diagnostics'
    HTMX_SETUP_RESULT = '#setup-result'
    
    # Loading indicators
    LOADING_PROVISION = '#provision-loading'
    LOADING_DEPLOY = '#deploy-loading'
    LOADING_STATUS = '#status-loading'
    LOADING_SUMMARY = '#summary-loading'
    LOADING_CLIENT = '#client-loading'
    LOADING_SETUP = '#setup-loading'
    
    # Toast notifications
    TOAST_CONTAINER = '.toast'
    TOAST_ERROR = '.toast:has-text("Error"), .toast:has-text("Failed")'
    TOAST_SUCCESS = '.toast:has-text("Success")'
    
    # Cards and containers
    CARD_WHITE = '.bg-white.shadow-xl'
    CARD_STATUS = '.status-card, [class*="status"]'
    
    # Modals and dialogs
    MODAL = '.modal, [role="dialog"], .o_dialog'
    MODAL_CLOSE = 'button[aria-label*="Close"], button:has-text("Close")'
    
    # Setup page
    SETUP_BACKEND_K8S = 'input[value="k8s"]'
    SETUP_BACKEND_SWARM = 'input[value="swarm"]'
    SETUP_BACKEND_NOMAD = 'input[value="nomad"]'
    SETUP_KUBECONFIG_PATH = 'input[name="kubeconfig_path"], input[id="kubeconfig_path"]'
    SETUP_NOMAD_ADDR = 'input[name="nomad_addr"], input[id="nomad_addr"]'
    SETUP_SAVE_BUTTON = 'button:has-text("Save Configuration")'
    SETUP_CURRENT_CONFIG = '#current-config'
    
    @staticmethod
    def get_nav_link(page: str) -> str:
        """
        Get navigation link selector for a page.
        
        Args:
            page: Page name (home, setup, provision, status, deploy, diagnostics)
            
        Returns:
            Selector string
        """
        nav_map = {
            'home': ForgeERPSelectors.NAV_HOME,
            'setup': ForgeERPSelectors.NAV_SETUP,
            'provision': ForgeERPSelectors.NAV_PROVISION,
            'status': ForgeERPSelectors.NAV_STATUS,
            'deploy': ForgeERPSelectors.NAV_DEPLOY,
            'diagnostics': ForgeERPSelectors.NAV_DIAGNOSTICS,
        }
        return nav_map.get(page.lower(), f'a[href="/{page}"]')
    
    @staticmethod
    def get_htmx_result_container(page: str) -> str:
        """
        Get HTMX result container selector for a page.
        
        Args:
            page: Page name (provision, deploy, status, diagnostics)
            
        Returns:
            Selector string
        """
        container_map = {
            'provision': ForgeERPSelectors.HTMX_PROVISION_RESULT,
            'deploy': ForgeERPSelectors.HTMX_DEPLOY_RESULT,
            'status': ForgeERPSelectors.HTMX_STATUS_RESULT,
            'diagnostics': ForgeERPSelectors.HTMX_DIAGNOSTICS_SUMMARY,
            'client-diagnostics': ForgeERPSelectors.HTMX_CLIENT_DIAGNOSTICS,
            'setup': ForgeERPSelectors.HTMX_SETUP_RESULT,
        }
        return container_map.get(page.lower(), f'#{page}-result')
    
    @staticmethod
    def get_loading_indicator(page: str) -> str:
        """
        Get loading indicator selector for a page.
        
        Args:
            page: Page name (provision, deploy, status, diagnostics, setup)
            
        Returns:
            Selector string
        """
        loading_map = {
            'provision': ForgeERPSelectors.LOADING_PROVISION,
            'deploy': ForgeERPSelectors.LOADING_DEPLOY,
            'status': ForgeERPSelectors.LOADING_STATUS,
            'summary': ForgeERPSelectors.LOADING_SUMMARY,
            'client': ForgeERPSelectors.LOADING_CLIENT,
            'setup': ForgeERPSelectors.LOADING_SETUP,
        }
        return loading_map.get(page.lower(), f'#{page}-loading')
    
    @staticmethod
    def get_form_field_selector(field_name: str) -> List[str]:
        """
        Get selectors for a form field by name.
        
        Args:
            field_name: Name of the field
            
        Returns:
            List of selector strings to try
        """
        selectors = [
            f'input[name="{field_name}"]',
            f'select[name="{field_name}"]',
            f'textarea[name="{field_name}"]',
            f'[name="{field_name}"]',
            f'#{field_name}',
            f'input[id="{field_name}"]',
            f'select[id="{field_name}"]',
        ]
        return selectors

