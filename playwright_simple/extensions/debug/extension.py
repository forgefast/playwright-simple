#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug extension for playwright-simple.

Provides advanced debugging capabilities with hot reload and interactive debugging.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from playwright.async_api import Page

from ...extensions import Extension
from .config import DebugConfig
from ...core.logger import get_logger, LogContext

logger = logging.getLogger(__name__)
structured_logger = get_logger()


class DebugExtension(Extension):
    """Extension for advanced debugging."""
    
    def __init__(self, config: DebugConfig):
        """
        Initialize debug extension.
        
        Args:
            config: Debug configuration
        """
        super().__init__('debug', {
            'enabled': config.enabled,
            'pause_on_error': config.pause_on_error,
            'interactive_mode': config.interactive_mode
        })
        self.debug_config = config
        self._test_instance: Optional[Any] = None
        self._current_checkpoint: Optional[Dict[str, Any]] = None
        self._checkpoints: List[Dict[str, Any]] = []
        self._error_state: Optional[Dict[str, Any]] = None
    
    async def initialize(self, test_instance: Any) -> None:
        """Initialize extension with test instance."""
        self._test_instance = test_instance
        structured_logger.info("Debug extension initialized", action="debug_init")
    
    async def on_error(
        self,
        error: Exception,
        page: Page,
        step_number: Optional[int] = None,
        action: Optional[str] = None,
        context: Optional[LogContext] = None
    ) -> bool:
        """
        Handle error with interactive debugging.
        
        Args:
            error: The exception that occurred
            page: Playwright page instance
            step_number: Current step number
            action: Current action
            context: Log context
            
        Returns:
            True if should continue, False if should stop
        """
        if not self.debug_config.enabled or not self.debug_config.pause_on_error:
            return False
        
        structured_logger.error(
            f"Error occurred: {error}",
            action=action or "unknown",
            step_number=step_number,
            error_type=type(error).__name__,
            error_message=str(error)
        )
        
        # Save error state
        if self.debug_config.save_state_on_error:
            await self._save_error_state(page, error, step_number, action)
        
        # Interactive debugging
        if self.debug_config.interactive_mode:
            test = self._test_instance
            return await self._interactive_debug(page, error, step_number, action, test=test)
        
        return False
    
    async def _save_error_state(
        self,
        page: Page,
        error: Exception,
        step_number: Optional[int],
        action: Optional[str]
    ) -> None:
        """Save error state for inspection."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        state_dir = Path(self.debug_config.state_dir)
        
        # Save HTML
        html_content = await page.content()
        html_file = state_dir / f"error_{timestamp}.html"
        html_file.write_text(html_content, encoding='utf-8')
        structured_logger.info(f"HTML saved to {html_file}", action="save_state")
        
        # Save state JSON
        state_data = {
            'timestamp': timestamp,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'step_number': step_number,
            'action': action,
            'url': page.url,
            'html_file': str(html_file),
            'screenshot': None  # Will be set if screenshot is taken
        }
        
        state_file = state_dir / f"error_{timestamp}.json"
        state_file.write_text(json.dumps(state_data, indent=2), encoding='utf-8')
        
        self._error_state = state_data
        structured_logger.info(f"Error state saved to {state_file}", action="save_state")
    
    async def _interactive_debug(
        self,
        page: Page,
        error: Exception,
        step_number: Optional[int],
        action: Optional[str],
        test=None
    ) -> bool:
        """
        Interactive debugging session.
        
        Returns:
            True if should continue, False if should stop
        """
        print("\n" + "="*80)
        print("🐛 DEBUG MODE - Interactive Debugging")
        print("="*80)
        print(f"Error: {type(error).__name__}: {error}")
        print(f"Step: {step_number}")
        print(f"Action: {action}")
        print(f"URL: {page.url}")
        print("\n📋 Comandos Disponíveis:")
        print("  [h] - Mostrar HTML snapshot")
        print("  [s] - Salvar HTML em arquivo")
        print("  [g] - Salvar HTML para análise da IA (/tmp/playwright_html.html)")
        print("  [e] - Listar elementos disponíveis (botões, inputs)")
        print("  [m] - Mover cursor para elemento (seletor ou texto)")
        print("  [c] - Clicar em elemento (seletor ou texto)")
        print("  [t] - Digitar texto em campo (seletor + texto)")
        print("  [w] - Aguardar X segundos")
        print("  [n] - Navegar para URL")
        print("  [b] - Rollback para passo anterior (voltar estado)")
        print("  [j] - Pular para próximo passo")
        print("  [r] - Hot reload YAML e continuar")
        print("  [u] - Mostrar URL atual")
        print("  [i] - Inspecionar elemento (seletor)")
        print("  [v] - Mostrar estado atual (step, action, URL)")
        print("  [q] - Sair e salvar checkpoint")
        print("  [x] - Continuar execução")
        print("="*80)
        
        # Salvar referência do test para comandos (usar _test_instance se test não fornecido)
        if test:
            self._test = test
        elif self._test_instance:
            self._test = self._test_instance
        else:
            self._test = None
        
        # Salvar estado atual para rollback
        saved_state = None
        if test:
            from playwright_simple.core.state import WebState
            try:
                saved_state = await WebState.capture(page, step_number=step_number, action_type=action)
                if not hasattr(test, '_saved_states'):
                    test._saved_states = []
                test._saved_states.append(saved_state)
            except:
                pass
        
        while True:
            try:
                command = input("\n🔍 Debug> ").strip().lower()
                
                if command == 'h':
                    await self._show_html_snapshot(page)
                elif command == 's':
                    await self._save_html_snapshot(page)
                elif command == 'g':
                    await self._get_html_for_ai(page)
                elif command == 'e':
                    await self._list_elements(page)
                elif command == 'm':
                    await self._move_cursor_to_element(page)
                elif command == 'c':
                    await self._click_element_interactive(page)
                elif command == 't':
                    await self._type_text_interactive(page)
                elif command == 'w':
                    await self._wait_interactive()
                elif command == 'n':
                    await self._navigate_interactive(page)
                elif command == 'b':
                    if saved_state and hasattr(self, '_test'):
                        await self._rollback_step(page, saved_state)
                    else:
                        print("⚠️  Estado anterior não disponível para rollback")
                elif command == 'j':
                    print("⏭️  Pulando para próximo passo...")
                    return True
                elif command == 'r':
                    return await self._hot_reload_yaml()
                elif command == 'u':
                    print(f"🌐 URL atual: {page.url}")
                    print(f"📄 Título: {await page.title()}")
                elif command == 'i':
                    await self._inspect_element(page)
                elif command == 'v':
                    print(f"📍 Passo: {step_number}")
                    print(f"🎬 Ação: {action}")
                    print(f"🌐 URL: {page.url}")
                    print(f"📄 Título: {await page.title()}")
                elif command == 'q':
                    await self._save_checkpoint(page, step_number)
                    return False
                elif command == 'x' or command == '':
                    print("▶️  Continuando execução...")
                    return True
                else:
                    print("❌ Comando desconhecido. Digite 'h' para ajuda.")
            except KeyboardInterrupt:
                print("\nExiting debug mode...")
                return False
            except Exception as e:
                print(f"Error in debug command: {e}")
    
    async def _show_html_snapshot(self, page: Page) -> None:
        """Show HTML snapshot in browser."""
        html_content = await page.content()
        print("\nHTML Snapshot:")
        print("-" * 80)
        print(html_content[:2000])  # First 2000 chars
        if len(html_content) > 2000:
            print(f"\n... ({len(html_content) - 2000} more characters)")
        print("-" * 80)
    
    async def _get_html_for_ai(self, page: Page) -> None:
        """Get HTML for AI analysis - saves to /tmp/playwright_html.html."""
        try:
            html = await page.content()
            html_file = Path("/tmp/playwright_html.html")
            html_file.write_text(html, encoding='utf-8')
            
            # Also save metadata
            metadata = {
                "url": page.url,
                "title": await page.title(),
                "timestamp": datetime.now().isoformat(),
                "html_file": str(html_file)
            }
            metadata_file = Path("/tmp/playwright_html_metadata.json")
            metadata_file.write_text(json.dumps(metadata, indent=2), encoding='utf-8')
            
            print(f"✅ HTML salvo em: {html_file}")
            print(f"✅ Metadata salvo em: {metadata_file}")
            print(f"📄 URL: {page.url}")
            print(f"📄 Título: {await page.title()}")
            print(f"📊 Tamanho do HTML: {len(html)} caracteres")
            
            # Also save a simplified version with just visible text and buttons
            try:
                simplified = await page.evaluate("""
                    () => {
                        const buttons = Array.from(document.querySelectorAll('button, a[role="button"], input[type="submit"], input[type="button"]'))
                            .map(btn => ({
                                text: btn.textContent?.trim() || btn.value || btn.getAttribute('aria-label') || '',
                                tag: btn.tagName.toLowerCase(),
                                id: btn.id || '',
                                class: btn.className || '',
                                visible: btn.offsetParent !== null
                            }))
                            .filter(btn => btn.visible && btn.text);
                        
                        const inputs = Array.from(document.querySelectorAll('input[type="text"], input[type="email"], input[type="password"], textarea'))
                            .map(inp => ({
                                type: inp.type,
                                placeholder: inp.placeholder || '',
                                name: inp.name || '',
                                id: inp.id || '',
                                label: inp.labels?.[0]?.textContent?.trim() || ''
                            }));
                        
                        return JSON.stringify({
                            buttons: buttons,
                            inputs: inputs,
                            url: window.location.href,
                            title: document.title
                        }, null, 2);
                    }
                """)
                simplified_file = Path("/tmp/playwright_html_simplified.json")
                simplified_file.write_text(simplified, encoding='utf-8')
                print(f"✅ Versão simplificada salva em: {simplified_file}")
            except Exception as e:
                logger.debug(f"Erro ao criar versão simplificada: {e}")
                
        except Exception as e:
            print(f"❌ Erro ao capturar HTML: {e}")
            logger.error(f"Error getting HTML for AI: {e}")
    
    async def _save_html_snapshot(self, page: Page) -> None:
        """Save HTML snapshot to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_dir = Path(self.debug_config.html_snapshot_dir)
        html_file = html_dir / f"snapshot_{timestamp}.html"
        
        html_content = await page.content()
        html_file.write_text(html_content, encoding='utf-8')
        
        print(f"HTML saved to: {html_file}")
        structured_logger.info(f"HTML snapshot saved to {html_file}", action="save_html")
    
    async def _hot_reload_yaml(self) -> bool:
        """Hot reload YAML and continue."""
        if not self.debug_config.hot_reload_enabled:
            print("Hot reload is disabled in config.")
            return False
        
        # Get test instance
        test = self._test_instance
        
        if test:
            # Set reload flag
            test._yaml_reload_requested = True
            print("✅ Hot reload: Flag definido, YAML será recarregado no próximo step.")
            logger.info("Hot reload requested", action="hot_reload")
            return True
        else:
            print("⚠️  Hot reload: Não foi possível encontrar instância do test.")
            print("   O YAML será recarregado automaticamente se for modificado.")
            return True
    
    async def _save_checkpoint(
        self,
        page: Page,
        step_number: Optional[int]
    ) -> None:
        """Save checkpoint for resuming later."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        checkpoint_dir = Path(self.debug_config.checkpoint_dir)
        
        checkpoint = {
            'timestamp': timestamp,
            'step_number': step_number,
            'url': page.url,
            'html_file': None,
            'state': await self._capture_page_state(page)
        }
        
        # Save HTML
        html_content = await page.content()
        html_file = checkpoint_dir / f"checkpoint_{timestamp}.html"
        html_file.write_text(html_content, encoding='utf-8')
        checkpoint['html_file'] = str(html_file)
        
        # Save checkpoint JSON
        checkpoint_file = checkpoint_dir / f"checkpoint_{timestamp}.json"
        checkpoint_file.write_text(json.dumps(checkpoint, indent=2), encoding='utf-8')
        
        self._current_checkpoint = checkpoint
        print(f"Checkpoint saved to: {checkpoint_file}")
        structured_logger.info(f"Checkpoint saved to {checkpoint_file}", action="save_checkpoint")
    
    async def _list_elements(self, page: Page) -> None:
        """Lista elementos disponíveis na página."""
        try:
            elements = await page.evaluate("""
                () => {
                    const buttons = Array.from(document.querySelectorAll('button, a[role="button"], input[type="submit"], input[type="button"]'))
                        .map(btn => ({
                            text: btn.textContent?.trim() || btn.value || btn.getAttribute('aria-label') || '',
                            tag: btn.tagName.toLowerCase(),
                            id: btn.id || '',
                            class: btn.className || '',
                            visible: btn.offsetParent !== null
                        }))
                        .filter(btn => btn.visible && btn.text);
                    
                    const inputs = Array.from(document.querySelectorAll('input[type="text"], input[type="email"], input[type="password"], textarea'))
                        .map(inp => ({
                            type: inp.type,
                            placeholder: inp.placeholder || '',
                            name: inp.name || '',
                            id: inp.id || '',
                            label: inp.labels?.[0]?.textContent?.trim() || '',
                            visible: inp.offsetParent !== null
                        }))
                        .filter(inp => inp.visible);
                    
                    return { buttons: buttons, inputs: inputs };
                }
            """)
            
            print(f"\n🔘 Botões disponíveis ({len(elements.get('buttons', []))}):")
            for i, btn in enumerate(elements.get('buttons', [])[:20], 1):
                selector = btn.get('id') and f"#{btn['id']}" or (btn.get('class') and f".{btn['class'].split(' ')[0]}" or btn.get('tag'))
                print(f"  {i}. '{btn.get('text')}' - {selector}")
            
            print(f"\n📝 Inputs disponíveis ({len(elements.get('inputs', []))}):")
            for i, inp in enumerate(elements.get('inputs', [])[:20], 1):
                selector = inp.get('id') and f"#{inp['id']}" or (inp.get('name') and f"[name='{inp['name']}']" or 'input')
                label = inp.get('label') or inp.get('placeholder') or 'sem label'
                print(f"  {i}. {inp.get('type')} - {selector} ({label})")
                
        except Exception as e:
            print(f"❌ Erro ao listar elementos: {e}")
    
    async def _move_cursor_to_element(self, page: Page) -> None:
        """Move cursor para um elemento."""
        try:
            selector_or_text = input("  Seletor ou texto do elemento: ").strip()
            if not selector_or_text:
                print("  ⚠️  Seletor vazio")
                return
            
            # Tentar encontrar elemento
            if selector_or_text.startswith(('/', '#', '.', '[')):
                element = page.locator(selector_or_text).first
            else:
                element = page.locator(f'text="{selector_or_text}"').first
            
            if await element.count() == 0:
                print(f"  ❌ Elemento não encontrado: {selector_or_text}")
                return
            
            if not await element.is_visible():
                print(f"  ⚠️  Elemento não está visível: {selector_or_text}")
                return
            
            box = await element.bounding_box()
            if not box:
                print(f"  ❌ Não foi possível obter posição do elemento")
                return
            
            x = box['x'] + box['width'] / 2
            y = box['y'] + box['height'] / 2
            
            # Mover cursor se test tem cursor_manager
            if hasattr(self, '_test') and self._test and hasattr(self._test, 'cursor_manager'):
                await self._test.cursor_manager.move_to(x, y)
                print(f"  ✅ Cursor movido para ({x:.0f}, {y:.0f})")
            else:
                print(f"  ⚠️  cursor_manager não disponível")
                print(f"  📍 Posição do elemento: ({x:.0f}, {y:.0f})")
                
        except Exception as e:
            print(f"  ❌ Erro: {e}")
    
    async def _click_element_interactive(self, page: Page) -> None:
        """Clica em um elemento interativamente."""
        try:
            selector_or_text = input("  Seletor ou texto do elemento: ").strip()
            if not selector_or_text:
                print("  ⚠️  Seletor vazio")
                return
            
            # Tentar encontrar elemento
            if selector_or_text.startswith(('/', '#', '.', '[')):
                element = page.locator(selector_or_text).first
            else:
                element = page.locator(f'text="{selector_or_text}"').first
            
            if await element.count() == 0:
                print(f"  ❌ Elemento não encontrado: {selector_or_text}")
                return
            
            if not await element.is_visible():
                print(f"  ⚠️  Elemento não está visível: {selector_or_text}")
                return
            
            box = await element.bounding_box()
            if box and hasattr(self, '_test') and self._test and hasattr(self._test, 'cursor_manager'):
                x = box['x'] + box['width'] / 2
                y = box['y'] + box['height'] / 2
                await self._test.cursor_manager.move_to(x, y)
                await asyncio.sleep(0.3)
                await self._test.cursor_manager.show_click_effect(x, y)
                await asyncio.sleep(0.1)
                await page.mouse.click(x, y)
            else:
                await element.click()
            
            print(f"  ✅ Clique executado em: {selector_or_text}")
            await asyncio.sleep(0.5)
            
        except Exception as e:
            print(f"  ❌ Erro: {e}")
    
    async def _type_text_interactive(self, page: Page) -> None:
        """Digita texto em um campo interativamente."""
        try:
            selector = input("  Seletor do campo: ").strip()
            if not selector:
                print("  ⚠️  Seletor vazio")
                return
            
            text = input("  Texto para digitar: ").strip()
            if not text:
                print("  ⚠️  Texto vazio")
                return
            
            element = page.locator(selector).first
            if await element.count() == 0:
                print(f"  ❌ Campo não encontrado: {selector}")
                return
            
            # Mover cursor se disponível
            box = await element.bounding_box()
            if box and hasattr(self, '_test') and self._test and hasattr(self._test, 'cursor_manager'):
                x = box['x'] + box['width'] / 2
                y = box['y'] + box['height'] / 2
                await self._test.cursor_manager.move_to(x, y)
                await asyncio.sleep(0.2)
            
            await element.click()
            await asyncio.sleep(0.2)
            await element.fill('')
            await element.type(text, delay=50)
            
            print(f"  ✅ Texto '{text}' digitado em: {selector}")
            
        except Exception as e:
            print(f"  ❌ Erro: {e}")
    
    async def _wait_interactive(self) -> None:
        """Aguarda um tempo interativamente."""
        try:
            seconds = float(input("  Segundos para aguardar: ").strip() or "1")
            print(f"  ⏳ Aguardando {seconds}s...")
            await asyncio.sleep(seconds)
            print(f"  ✅ Aguardou {seconds}s")
        except ValueError:
            print("  ❌ Valor inválido")
        except Exception as e:
            print(f"  ❌ Erro: {e}")
    
    async def _navigate_interactive(self, page: Page) -> None:
        """Navega para uma URL interativamente."""
        try:
            url = input("  URL para navegar: ").strip()
            if not url:
                print("  ⚠️  URL vazia")
                return
            
            print(f"  🌐 Navegando para: {url}")
            await page.goto(url, wait_until='domcontentloaded', timeout=10000)
            await asyncio.sleep(1)
            print(f"  ✅ Navegou para: {page.url}")
            
        except Exception as e:
            print(f"  ❌ Erro: {e}")
    
    async def _rollback_step(self, page: Page, target_state) -> None:
        """Faz rollback para um estado anterior."""
        try:
            if not target_state:
                print("  ❌ Estado alvo não disponível")
                return
            
            # Restore URL if different
            if hasattr(target_state, 'url') and target_state.url and page.url != target_state.url:
                print(f"  🌐 Restaurando URL: {target_state.url}")
                await page.goto(target_state.url, wait_until='domcontentloaded', timeout=10000)
            
            # Restore scroll position
            if hasattr(target_state, 'scroll_x') and hasattr(target_state, 'scroll_y'):
                await page.evaluate(f"window.scrollTo({target_state.scroll_x}, {target_state.scroll_y})")
            
            print(f"  ✅ Rollback executado - estado restaurado")
            
        except Exception as e:
            print(f"  ❌ Erro no rollback: {e}")
    
    async def _inspect_element(self, page: Page) -> None:
        """Inspect element interactively."""
        selector = input("  Seletor ou texto para encontrar: ").strip()
        if not selector:
            return
        
        try:
            # Try to find element
            if selector.startswith(('/', '#', '.', '[')):
                element = await page.query_selector(selector)
            else:
                element = await page.query_selector(f'text="{selector}"')
            
            if element:
                # Get element info
                box = await element.bounding_box()
                text = await element.text_content()
                tag = await element.evaluate("el => el.tagName")
                attributes = await element.evaluate("""
                    el => {
                        const attrs = {};
                        for (let attr of el.attributes) {
                            attrs[attr.name] = attr.value;
                        }
                        return attrs;
                    }
                """)
                
                print(f"\n✅ Elemento encontrado:")
                print(f"  Tag: {tag}")
                print(f"  Texto: {text[:100] if text else 'N/A'}")
                print(f"  Posição: {box}")
                print(f"  Atributos: {json.dumps(attributes, indent=2)}")
            else:
                print(f"❌ Elemento não encontrado: {selector}")
        except Exception as e:
            print(f"❌ Erro ao inspecionar elemento: {e}")
    
    async def _capture_page_state(self, page: Page) -> Dict[str, Any]:
        """Capture current page state."""
        return {
            'url': page.url,
            'title': await page.title(),
            'viewport': page.viewport_size,
            'cookies': await page.context.cookies()
        }
    
    async def create_checkpoint(
        self,
        page: Page,
        step_number: int,
        action: str
    ) -> Dict[str, Any]:
        """
        Create a checkpoint for resuming later.
        
        Args:
            page: Playwright page instance
            step_number: Current step number
            action: Current action
            
        Returns:
            Checkpoint data
        """
        checkpoint = {
            'step_number': step_number,
            'action': action,
            'timestamp': datetime.now().isoformat(),
            'state': await self._capture_page_state(page)
        }
        
        self._checkpoints.append(checkpoint)
        self._current_checkpoint = checkpoint
        
        structured_logger.state(
            f"Checkpoint created at step {step_number}",
            step_number=step_number,
            action=action
        )
        
        return checkpoint
    
    async def resume_from_checkpoint(
        self,
        checkpoint: Dict[str, Any],
        page: Page
    ) -> bool:
        """
        Resume execution from a checkpoint.
        
        Args:
            checkpoint: Checkpoint data
            page: Playwright page instance
            
        Returns:
            True if resumed successfully
        """
        try:
            # Navigate to checkpoint URL
            await page.goto(checkpoint['state']['url'])
            
            # Restore state if possible
            # (This is a simplified version - full implementation would restore more state)
            
            structured_logger.state(
                f"Resumed from checkpoint at step {checkpoint['step_number']}",
                step_number=checkpoint['step_number'],
                action=checkpoint['action']
            )
            
            return True
        except Exception as e:
            structured_logger.error(f"Failed to resume from checkpoint: {e}")
            return False

