#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YAML parser for playwright-simple.

Converts YAML test definitions to executable Python functions.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List, Callable, Optional, Tuple
from playwright.async_api import Page

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

from .base import SimpleTestBase
from .exceptions import ElementNotFoundError, NavigationError
from .state import WebState
from .yaml_expressions import ExpressionEvaluator
from .yaml_resolver import YAMLResolver
from .yaml_executor import StepExecutor

logger = logging.getLogger(__name__)


class YAMLParser:
    """Parser for YAML test definitions."""
    
    @staticmethod
    def parse_file(yaml_path: Path) -> Dict[str, Any]:
        """
        Parse YAML test file with support for inheritance and composition.
        
        Args:
            yaml_path: Path to YAML file
            
        Returns:
            Dictionary with test definition (with resolved inheritance/composition)
        """
        if not YAML_AVAILABLE:
            raise ImportError("PyYAML is required for YAML support. Install with: pip install pyyaml")
        
        yaml_path = Path(yaml_path)
        base_dir = yaml_path.parent
        
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # Resolve inheritance and composition
        data = YAMLResolver.resolve_inheritance(data, base_dir)
        data = YAMLResolver.resolve_includes(data, base_dir)
        data = YAMLResolver.resolve_compose(data, base_dir)
        
        return data
    
    # Note: The following methods have been moved to YAMLResolver for better organization.
    # They are kept here for backward compatibility but delegate to the new module.
    
    @staticmethod
    def _resolve_inheritance(data: Dict[str, Any], base_dir: Path) -> Dict[str, Any]:
        """Backward compatibility: delegate to YAMLResolver."""
        return YAMLResolver.resolve_inheritance(data, base_dir)
    
    @staticmethod
    def _resolve_includes(data: Dict[str, Any], base_dir: Path) -> Dict[str, Any]:
        """Backward compatibility: delegate to YAMLResolver."""
        return YAMLResolver.resolve_includes(data, base_dir)
    
    @staticmethod
    def _resolve_compose(data: Dict[str, Any], base_dir: Path) -> Dict[str, Any]:
        """Backward compatibility: delegate to YAMLResolver."""
        return YAMLResolver.resolve_compose(data, base_dir)
    
    @staticmethod
    def _substitute_variables(obj: Any, params: Dict[str, Any]) -> Any:
        """Backward compatibility: delegate to ExpressionEvaluator."""
        context = {'vars': {}, 'params': params}
        return ExpressionEvaluator.substitute_variables(obj, context)
    
    @staticmethod
    def _resolve_yaml_path(file_path: str, base_dir: Path) -> Optional[Path]:
        """Backward compatibility: delegate to YAMLResolver."""
        return YAMLResolver.resolve_yaml_path(file_path, base_dir)
    
    @staticmethod
    def _find_action_yaml(action_name: str, base_dir: Path) -> Optional[Path]:
        """Backward compatibility: delegate to YAMLResolver."""
        return YAMLResolver.find_action_yaml(action_name, base_dir)
    
    @staticmethod
    def to_python_function(yaml_data: Dict[str, Any], base_dir: Optional[Path] = None, yaml_path: Optional[Path] = None) -> Callable[..., Any]:
        """
        Convert YAML test definition to Python function.
        
        Args:
            yaml_data: YAML test data
            base_dir: Base directory for resolving YAML paths (optional)
            yaml_path: Path to YAML file (for hot reload)
            
        Returns:
            Python async function (page, test) -> None
        """
        test_name = yaml_data.get('name', 'yaml_test')
        steps = yaml_data.get('steps', [])
        setup_steps = yaml_data.get('setup', [])
        teardown_steps = yaml_data.get('teardown', [])
        base_url = yaml_data.get('base_url')
        config_data = yaml_data.get('config', {})
        save_session = yaml_data.get('save_session', False)
        load_session = yaml_data.get('load_session')
        
        # Use provided base_dir or fallback to cwd
        function_base_dir = base_dir or Path.cwd()
        
        # Store YAML path and initial mtime for hot reload
        yaml_file_path = yaml_path
        yaml_mtime = yaml_file_path.stat().st_mtime if yaml_file_path and yaml_file_path.exists() else None
        
        async def test_function(page: Page, test: SimpleTestBase) -> None:
            """Generated test function from YAML."""
            # Declare nonlocal variables that will be modified
            nonlocal steps, yaml_mtime
            
            # Initialize context for variables
            context = {
                'vars': {},
                'params': {}  # Will be populated from compose params
            }
            
            # Apply configuration from YAML if provided
            if config_data:
                from .yaml_config import YAMLConfigManager
                YAMLConfigManager.apply_config(config_data, test)
            
            # Set base URL if provided
            if base_url:
                test.config.base_url = base_url
            
            # Use base_dir from closure
            base_dir = function_base_dir
            
            # Initialize state
            current_state = None
            
            # Execute setup steps first
            if setup_steps:
                for step in setup_steps:
                    action = step.get('action')
                    if not action and 'compose' not in step and 'for' not in step and 'if' not in step and 'set' not in step and 'try' not in step:
                        continue
                    current_state = await StepExecutor.execute_step(step, test, base_dir, context, current_state)
            
            # Setup Python hot reload
            from .python_reloader import get_reloader
            python_reloader = get_reloader(auto_reload=True)
            
            # Execute main steps with hot reload support
            try:
                current_step_index = 0
                while current_step_index < len(steps):
                    # Verificar comandos externos (control interface)
                    if hasattr(test, '_control_interface') and test._control_interface:
                        try:
                            cmd = test._control_interface.wait_for_command(timeout=0.1)
                            if cmd and cmd.get('command') == 'reload':
                                test._yaml_reload_requested = True
                                logger.info("Reload command received from control interface")
                        except:
                            pass
                    
                    # Check for Python module reload (antes de verificar YAML)
                    try:
                        reloaded_count = python_reloader.check_and_reload_all()
                        if reloaded_count > 0:
                            logger.info(f"🔄 Python hot reload: {reloaded_count} módulo(s) recarregado(s)")
                            print(f"  🔄 Python hot reload: {reloaded_count} módulo(s) recarregado(s)")
                    except Exception as e:
                        logger.debug(f"Erro ao verificar reload Python: {e}")
                    
                    # Check for YAML reload before each step
                    if yaml_file_path and yaml_file_path.exists():
                        current_mtime = yaml_file_path.stat().st_mtime
                        # Check if file was modified or if reload was requested
                        reload_requested = getattr(test, '_yaml_reload_requested', False)
                        if reload_requested or (yaml_mtime and current_mtime > yaml_mtime):
                            logger.info(f"🔄 Hot reload: YAML file modified, reloading...")
                            print(f"  🔄 Hot reload: Recarregando YAML...")
                            
                            try:
                                # Reload YAML
                                reloaded_data = YAMLParser.parse_file(yaml_file_path)
                                reloaded_steps = reloaded_data.get('steps', [])
                                
                                # Update steps (keep executed ones, replace remaining)
                                steps = steps[:current_step_index] + reloaded_steps
                                
                                # Update mtime
                                yaml_mtime = current_mtime
                                
                                # Clear reload flag
                                if hasattr(test, '_yaml_reload_requested'):
                                    test._yaml_reload_requested = False
                                
                                print(f"  ✅ YAML recarregado! {len(reloaded_steps)} steps disponíveis")
                                logger.info(f"Hot reload: {len(reloaded_steps)} steps loaded")
                                
                                # If we're past the end, break
                                if current_step_index >= len(steps):
                                    break
                            except Exception as e:
                                logger.error(f"Error reloading YAML: {e}")
                                print(f"  ⚠️  Erro ao recarregar YAML: {e}")
                                # Continue with old steps
                    
                    step = steps[current_step_index]
                    current_step_index += 1
                    
                    action = step.get('action')
                    if not action and 'compose' not in step and 'for' not in step and 'if' not in step and 'set' not in step and 'try' not in step:
                        continue
                    
                    # Update step number in context for debug
                    if current_state:
                        current_state.step_number = current_step_index
                    context['step_number'] = current_step_index
                    
                    # Executar passo com rollback e auto-fix
                    state_before_step = current_state
                    max_retries = 5
                    retry_count = 0
                    step_success = False
                    
                    while retry_count < max_retries and not step_success:
                        try:
                            # Tentar executar passo
                            current_state = await StepExecutor.execute_step(step, test, base_dir, context, current_state)
                            step_success = True
                        except Exception as e:
                            retry_count += 1
                            error_type = type(e).__name__
                            error_message = str(e)
                            
                            logger.warning(f"Erro no passo {current_step_index} (tentativa {retry_count}/{max_retries}): {error_type}: {error_message}")
                            print(f"  ⚠️  Erro no passo {current_step_index}: {error_type}: {error_message[:100]}")
                            
                            # Salvar erro no control interface
                            if hasattr(test, '_control_interface') and test._control_interface:
                                try:
                                    test._control_interface.save_error(e, current_step_index)
                                except:
                                    pass
                            
                            # Tentar corrigir automaticamente
                            from .auto_fixer import AutoFixer
                            from .html_analyzer import HTMLAnalyzer
                            
                            if yaml_file_path:
                                fixer = AutoFixer(yaml_file_path)
                                error_data = {
                                    'error_type': error_type,
                                    'error_message': error_message
                                }
                                
                                # Coletar contexto adicional
                                page_state = None
                                html_analyzer = None
                                action_history = []
                                
                                # Capturar estado da página se disponível
                                if current_state:
                                    page_state = {
                                        'url': current_state.url,
                                        'title': current_state.title,
                                        'scroll_x': current_state.scroll_x,
                                        'scroll_y': current_state.scroll_y
                                    }
                                
                                # Criar HTML analyzer se HTML disponível
                                try:
                                    html_analyzer = HTMLAnalyzer()
                                except:
                                    pass
                                
                                # Coletar histórico de ações (últimos 5 passos)
                                if hasattr(test, '_action_history'):
                                    action_history = test._action_history[-5:] if len(test._action_history) > 5 else test._action_history
                                
                                fix_result = fixer.fix_error(
                                    error_data, 
                                    step, 
                                    current_step_index,
                                    page_state=page_state,
                                    html_analyzer=html_analyzer,
                                    action_history=action_history
                                )
                                
                                if fix_result.get('fixed'):
                                    print(f"  🔧 Correção automática aplicada: {fix_result.get('message')}")
                                    
                                    # Recarregar YAML se foi corrigido
                                    if fix_result.get('fix_type') == 'yaml':
                                        try:
                                            reloaded_data = YAMLParser.parse_file(yaml_file_path)
                                            reloaded_steps = reloaded_data.get('steps', [])
                                            # Atualizar step atual com versão corrigida
                                            if current_step_index <= len(reloaded_steps):
                                                step = reloaded_steps[current_step_index - 1]
                                                steps[current_step_index - 1] = step
                                        except Exception as reload_error:
                                            logger.debug(f"Erro ao recarregar YAML após correção: {reload_error}")
                                    
                                    # Aguardar um pouco para hot reload processar
                                    await asyncio.sleep(0.5)
                                    
                                    # Fazer rollback: restaurar estado antes do passo
                                    if state_before_step:
                                        current_state = await StepExecutor._rollback_state(test, state_before_step)
                                    
                                    # Tentar novamente
                                    continue
                                else:
                                    print(f"  ⚠️  Não foi possível corrigir automaticamente: {fix_result.get('message')}")
                            
                            # Se não conseguiu corrigir e esgotou tentativas, relançar erro
                            if retry_count >= max_retries:
                                print(f"  ❌ Máximo de tentativas ({max_retries}) atingido para passo {current_step_index}")
                                raise
                            
                            # Aguardar antes de tentar novamente
                            await asyncio.sleep(1)
            finally:
                # Execute teardown steps (always, even on error)
                if teardown_steps:
                    for step in teardown_steps:
                        try:
                            action = step.get('action')
                            if not action and 'compose' not in step and 'for' not in step and 'if' not in step and 'set' not in step and 'try' not in step:
                                continue
                            current_state = await StepExecutor.execute_step(step, test, base_dir, context, current_state)
                        except Exception as e:
                            # Log but don't fail on teardown errors
                            logger.warning(f"Teardown step failed: {e}")
                            print(f"  ⚠️  Teardown step failed: {e}")
        
        # Set function attributes for session management
        test_function.save_session = save_session if save_session else None
        test_function.load_session = load_session if load_session else None
        
        # Set function name for debugging
        test_function.__name__ = test_name
        return test_function
    
    # Note: _evaluate_expression, _substitute_variables_with_context, and _execute_step
    # have been moved to yaml_expressions.py, yaml_resolver.py, and yaml_executor.py respectively.
    # These methods are kept here for backward compatibility but delegate to the new modules.
    
    @staticmethod
    def _evaluate_expression(expr: str, context: Dict[str, Any]) -> Any:
        """Backward compatibility: delegate to ExpressionEvaluator."""
        return ExpressionEvaluator.evaluate(expr, context)
    
    @staticmethod
    def _substitute_variables_with_context(obj: Any, context: Dict[str, Any]) -> Any:
        """Backward compatibility: delegate to ExpressionEvaluator."""
        return ExpressionEvaluator.substitute_variables(obj, context)
    
    @staticmethod
    async def _execute_step(
        step: Dict[str, Any], 
        test: SimpleTestBase, 
        base_dir: Optional[Path] = None, 
        context: Optional[Dict[str, Any]] = None,
        previous_state: Optional[WebState] = None
    ) -> WebState:
        """Backward compatibility: delegate to StepExecutor."""
        return await StepExecutor.execute_step(step, test, base_dir, context, previous_state)
                
    
    @staticmethod
    def load_test(yaml_path: Path) -> Tuple[str, Callable[..., Any]]:
        """
        Load test from YAML file.
        
        Args:
            yaml_path: Path to YAML file
            
        Returns:
            Tuple of (test_name, test_function)
        """
        data = YAMLParser.parse_file(yaml_path)
        test_name = data.get('name', yaml_path.stem)
        
        # Pass base_dir and yaml_path to to_python_function for hot reload
        base_dir = yaml_path.parent
        test_function = YAMLParser.to_python_function(data, base_dir, yaml_path=yaml_path)
        
        # Store yaml_path in function for external access
        test_function._yaml_path = yaml_path
        
        return (test_name, test_function)
    
    @staticmethod
    def load_tests(yaml_dir: Path) -> List[Tuple[str, Callable[..., Any]]]:
        """
        Load all tests from YAML directory.
        
        Args:
            yaml_dir: Directory containing YAML test files
            
        Returns:
            List of tuples (test_name, test_function)
        """
        tests = []
        yaml_dir = Path(yaml_dir)
        
        if not yaml_dir.exists():
            return tests
        
        for yaml_file in yaml_dir.glob("*.yaml"):
            try:
                test_name, test_func = YAMLParser.load_test(yaml_file)
                tests.append((test_name, test_func))
            except Exception as e:
                print(f"  ⚠️  Error loading {yaml_file}: {e}")
        
        for yaml_file in yaml_dir.glob("*.yml"):
            try:
                test_name, test_func = YAMLParser.load_test(yaml_file)
                tests.append((test_name, test_func))
            except Exception as e:
                print(f"  ⚠️  Error loading {yaml_file}: {e}")
        
        return tests


