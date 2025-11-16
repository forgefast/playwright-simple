#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug utilities for interactive debugging during test execution.

Allows pausing test execution to inspect browser state, check elements, etc.
"""

import asyncio
import logging
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class DebugManager:
    """Manages interactive debugging during test execution."""
    
    def __init__(self, enabled: bool = False, pause_on_actions: Optional[list] = None, pause_timeout: Optional[float] = None):
        """
        Initialize debug manager.
        
        Args:
            enabled: Whether debug mode is enabled
            pause_on_actions: List of action types to pause on (e.g., ['go_to', 'click', 'fill'])
                             If None, pauses on all actions
            pause_timeout: Timeout in seconds for pause (None = wait indefinitely)
        """
        self.enabled = enabled or os.getenv('PLAYWRIGHT_DEBUG', 'false').lower() == 'true'
        self.pause_on_actions = pause_on_actions or []
        self.pause_timeout = pause_timeout
        self.step_count = 0
    
    def should_pause(self, action_type: str, force: bool = False) -> bool:
        """
        Check if should pause before this action type.
        
        Args:
            action_type: Type of action (e.g., 'go_to', 'click', 'fill')
            force: If True, always pause (breakpoint in step)
        """
        # If timeout is very short (<= 1s), never pause (for automatic execution)
        if self.pause_timeout is not None and self.pause_timeout <= 1.0:
            return False
        
        if force:
            return True  # Force pause (breakpoint in step)
        
        if not self.enabled:
            return False
        
        if not self.pause_on_actions:
            return True  # Pause on all actions if no filter
        
        return action_type in self.pause_on_actions
    
    async def pause(
        self,
        step_number: int,
        action_type: str,
        action_details: Dict[str, Any],
        page_url: str = "",
        page_title: str = "",
        force: bool = False,
        page = None
    ) -> None:
        """
        Pause execution and wait for user input.
        
        Args:
            step_number: Current step number
            action_type: Type of action (e.g., 'go_to', 'click', 'fill')
            action_details: Details about the action
            page_url: Current page URL
            page_title: Current page title
            force: If True, always pause (breakpoint in step)
            page: Playwright page object (optional, used to bring window to front)
        """
        if not self.should_pause(action_type, force=force):
            return
        
        self.step_count += 1
        
        # If this is a breakpoint (force=True), try to bring browser window to front
        if force and page:
            try:
                # Try to bring window to front using JavaScript
                await page.evaluate("""
                    () => {
                        // Try to focus the window
                        if (window.focus) {
                            window.focus();
                        }
                        // Try to bring window to front (may not work in all browsers)
                        if (window.moveTo) {
                            window.moveTo(0, 0);
                        }
                    }
                """)
                # Also try using browser context (if available)
                context = page.context
                if hasattr(context, 'pages'):
                    # Bring first page to front
                    for p in context.pages:
                        try:
                            await p.bring_to_front()
                        except:
                            pass
            except Exception as e:
                # Ignore errors - window might already be visible
                pass
        
        print("\n" + "="*80)
        if force:
            print(f"🛑 BREAKPOINT - Passo {step_number} (breakpoint definido no YAML)")
            print("   💡 Navegador deve estar visível agora - verifique a janela do navegador")
        else:
            print(f"🔍 DEBUG PAUSE - Passo {step_number}")
        print("="*80)
        print(f"📋 Ação: {action_type}")
        print(f"📄 Detalhes: {action_details}")
        if page_url:
            print(f"🌐 URL: {page_url}")
        if page_title:
            print(f"📑 Título: {page_title}")
        print("\n💡 O navegador está pausado. Você pode:")
        print("   - Inspecionar elementos no DevTools (F12)")
        print("   - Verificar o estado da página")
        print("   - Verificar se elementos estão visíveis")
        print("   - Verificar console do navegador")
        print("\n⚠️  IMPORTANTE: O navegador permanecerá aberto enquanto você não pressionar Enter")
        print("\n⌨️  Comandos disponíveis:")
        print("   [Enter] - Continuar para o próximo passo")
        print("   's' + Enter - Pular este passo (skip)")
        print("   'q' + Enter - Sair do teste (quit)")
        print("   'c' + Enter - Continuar sem mais pausas (continue)")
        print("   'r' + Enter - Recarregar módulos Python (hot reload)")
        print("="*80)
        
        # If timeout is very short (<= 1s), skip pause entirely for automatic execution
        if self.pause_timeout is not None and self.pause_timeout <= 1.0:
            # Very short timeout - just log and continue immediately (no blocking)
            logger.debug(f"Debug pause skipped (timeout={self.pause_timeout}s) - continuing automatically")
            return
        
        print("⏸️  AGUARDANDO SUA AÇÃO... (pressione Enter para continuar)")
        print("="*80)
        
        # Flush stdout to ensure message is displayed
        import sys
        sys.stdout.flush()
        sys.stderr.flush()
        
        # Use asyncio to handle input in async context
        while True:
            try:
                # Use asyncio to run input in executor (works in async context)
                # This blocks until user provides input
                loop = asyncio.get_event_loop()
                
                # If timeout is set, use asyncio.wait_for
                if self.pause_timeout is not None and self.pause_timeout > 0:
                    try:
                        user_input = await asyncio.wait_for(
                            loop.run_in_executor(None, input, "\n🔍 Debug> "),
                            timeout=self.pause_timeout
                        )
                    except asyncio.TimeoutError:
                        # Timeout reached - continue automatically
                        if self.pause_timeout > 2.0:
                            print(f"\n⏱️  Timeout de {self.pause_timeout}s atingido. Continuando automaticamente...")
                            print("💡 Dica: Use --step-timeout 0 para espera indefinida (ou Ctrl+Z para suspender)")
                        break
                else:
                    # No timeout - wait indefinitely
                    # But show message that user can use Ctrl+Z to suspend
                    print("💡 Dica: Use Ctrl+Z para suspender o processo e depois 'fg' para retomar")
                    user_input = await loop.run_in_executor(None, input, "\n🔍 Debug> ")
                
                user_input = user_input.strip().lower()
                
                if user_input == '' or user_input == 'n':
                    # Continue to next step
                    print("▶️  Continuando...")
                    break
                elif user_input == 's':
                    # Skip this step
                    print("⏭️  Pulando este passo...")
                    raise SkipStepException("Step skipped by user")
                elif user_input == 'q':
                    # Quit test
                    print("🛑 Saindo do teste...")
                    raise QuitTestException("Test quit by user")
                elif user_input == 'c':
                    # Continue without more pauses
                    print("▶️  Continuando sem mais pausas...")
                    self.enabled = False
                    break
                elif user_input == 'r':
                    # Hot reload - reload Python modules
                    print("🔄 Recarregando módulos Python...")
                    try:
                        import importlib
                        import sys
                        
                        # Modules to reload (Odoo-specific)
                        modules_to_reload = [
                            'playwright_simple.odoo.specific.filters',
                            'playwright_simple.odoo.yaml_parser.action_parser',
                            'playwright_simple.odoo.yaml_parser.action_validator',
                            'playwright_simple.odoo.yaml_parser.step_executor',
                            'playwright_simple.odoo.menus',
                            'playwright_simple.odoo.navigation',
                        ]
                        
                        reloaded = []
                        for module_name in modules_to_reload:
                            if module_name in sys.modules:
                                try:
                                    importlib.reload(sys.modules[module_name])
                                    reloaded.append(module_name)
                                except Exception as e:
                                    print(f"   ⚠️  Erro ao recarregar {module_name}: {e}")
                        
                        if reloaded:
                            print(f"   ✅ {len(reloaded)} módulo(s) recarregado(s): {', '.join(reloaded)}")
                            print("   💡 Código atualizado! Continue para aplicar as mudanças.")
                        else:
                            print("   ⚠️  Nenhum módulo foi recarregado")
                    except Exception as e:
                        print(f"   ❌ Erro ao recarregar módulos: {e}")
                    # Continue loop to wait for next command
                    continue
                else:
                    print("❌ Comando inválido. Use [Enter], 's', 'q', 'c' ou 'r'")
            except (EOFError, KeyboardInterrupt):
                print("\n🛑 Interrompido pelo usuário")
                raise QuitTestException("Test interrupted by user")
        
        print("="*80 + "\n")


class SkipStepException(Exception):
    """Exception to skip current step."""
    pass


class QuitTestException(Exception):
    """Exception to quit test execution."""
    pass

