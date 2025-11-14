#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step execution for YAML parser.

Handles execution of individual steps including:
- Loops (for)
- Conditionals (if/else/elif)
- Variable assignment (set)
- Try/catch/finally
- Compose
- Core actions
- Playwright actions
- Generic YAML actions
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

from .base import SimpleTestBase
from .state import WebState
from .yaml_expressions import ExpressionEvaluator
from .yaml_resolver import YAMLResolver
from .yaml_actions import ActionMapper

logger = logging.getLogger(__name__)


class StepExecutor:
    """Executes YAML steps with state tracking."""
    
    @staticmethod
    async def _rollback_state(test: SimpleTestBase, target_state: 'WebState') -> 'WebState':
        """
        Faz rollback para um estado anterior.
        
        Args:
            test: Instância do teste
            target_state: Estado para o qual fazer rollback
            
        Returns:
            Estado restaurado
        """
        try:
            # Navegar para URL se diferente
            if target_state.url and test.page.url != target_state.url:
                await test.page.goto(target_state.url, wait_until='domcontentloaded')
            
            # Restaurar scroll
            if target_state.scroll_x != 0 or target_state.scroll_y != 0:
                await test.page.evaluate(f"""
                    window.scrollTo({target_state.scroll_x}, {target_state.scroll_y});
                """)
            
            # Restaurar cursor (se possível)
            if target_state.cursor_x is not None and target_state.cursor_y is not None:
                cursor_manager = getattr(test.page, '_cursor_manager', None)
                if cursor_manager and hasattr(cursor_manager, 'set_position'):
                    try:
                        cursor_manager.set_position(target_state.cursor_x, target_state.cursor_y)
                    except:
                        pass
            
            # Aguardar página estabilizar
            await asyncio.sleep(0.3)
            
            # Capturar novo estado
            return await WebState.capture(test.page, target_state.step_number, target_state.action_type)
        except Exception as e:
            logger.warning(f"Erro ao fazer rollback: {e}")
            # Se rollback falhar, apenas capturar estado atual
            return await WebState.capture(test.page)
    
    @staticmethod
    async def execute_step(
        step: Dict[str, Any],
        test: SimpleTestBase,
        base_dir: Optional[Path] = None,
        context: Optional[Dict[str, Any]] = None,
        previous_state: Optional[WebState] = None
    ) -> WebState:
        """
        Execute a single step from YAML with state tracking.
        
        Each step:
        - Knows where it came from (previous_state)
        - Executes its action
        - Returns where it goes (new_state)
        
        Args:
            step: Step dictionary
            test: Test base instance
            base_dir: Base directory for resolving YAML paths (optional)
            context: Context dictionary with vars and params (optional)
            previous_state: State before this step (optional)
            
        Returns:
            WebState after step execution
        """
        if context is None:
            context = {'vars': {}, 'params': {}}
        
        # Capture state before step
        if previous_state is None:
            previous_state = await WebState.capture(test.page)
        
        # Store previous state in context
        context['previous_state'] = previous_state
        
        # Determine action type
        action_type = step.get('action') or list(step.keys())[0] if step else 'unknown'
        
        # DEBUG: Pause before step if debug is enabled (only if timeout > 1s)
        # Check if test has debug_manager or debug extension
        debug_manager = None
        step_timeout = getattr(test, '_debug_step_timeout', 1.0)  # Default 1 second for automatic execution
        
        # Only enable debug pause if timeout is > 1s (for interactive mode)
        # For automatic execution (timeout <= 1s), skip pause entirely
        if step_timeout is None or step_timeout > 1.0:
            if hasattr(test, 'debug_manager'):
                debug_manager = test.debug_manager
                # Update timeout if set
                if step_timeout is not None:
                    debug_manager.pause_timeout = step_timeout
            elif hasattr(test, 'extensions') and test.extensions.has('debug'):
                # Get debug extension and create a debug manager wrapper
                debug_ext = test.extensions.get('debug')
                if hasattr(debug_ext, 'debug_config') and debug_ext.debug_config.interactive_mode:
                    from .debug import DebugManager
                    debug_manager = DebugManager(enabled=True, pause_on_actions=[], pause_timeout=step_timeout)
        
        # Get step number from context or previous_state
        step_number = context.get('step_number', 0) if context else 0
        if not step_number and previous_state and previous_state.step_number:
            step_number = previous_state.step_number
        
        # Salvar estado do passo para controle externo
        if hasattr(test, '_control_interface'):
            try:
                url = test.page.url if hasattr(test, 'page') and test.page else None
                test._control_interface.save_step_state(
                    step_number=step_number,
                    action=action_type,
                    step_data=step,
                    url=url
                )
            except Exception as e:
                logger.debug(f"Error saving step state: {e}")
        
        # Pause before step if debug is enabled (and timeout allows it)
        if debug_manager:
            try:
                has_breakpoint = step.get('breakpoint', False) or step.get('debug', False)
                page_url = test.page.url if hasattr(test, 'page') else ''
                page_title = await test.page.title() if hasattr(test, 'page') else ''
                
                print(f"\n🔍 DEBUG: Pausando antes do passo {step_number} - Ação: {action_type}")
                
                await debug_manager.pause(
                    step_number=step_number,
                    action_type=action_type,
                    action_details=step,
                    page_url=page_url,
                    page_title=page_title,
                    force=has_breakpoint,
                    page=test.page if hasattr(test, 'page') else None
                )
            except Exception as e:
                # If SkipStepException or QuitTestException, re-raise
                from .debug import SkipStepException, QuitTestException
                if isinstance(e, (SkipStepException, QuitTestException)):
                    raise
                logger.debug(f"Debug pause error (ignoring): {e}")
        else:
            # Log step for debugging (non-blocking)
            logger.debug(f"Step {step_number}: {action_type} - {step}")
        
        # Merge compose params into context if present
        if '_compose_params' in step:
            context['params'].update(step['_compose_params'])
            step = {k: v for k, v in step.items() if k != '_compose_params'}
        
        # Substitute variables in step
        step = ExpressionEvaluator.substitute_variables(step, context)
        
        # Handle compose (within steps)
        if 'compose' in step:
            return await StepExecutor._handle_compose(step, test, base_dir, context, previous_state, action_type)
        
        # Handle loops
        if 'for' in step:
            return await StepExecutor._handle_loop(step, test, base_dir, context, previous_state)
        
        # Handle conditionals
        if 'if' in step:
            return await StepExecutor._handle_conditional(step, test, base_dir, context, previous_state)
        
        # Handle variable assignment
        if 'set' in step:
            return await StepExecutor._handle_set(step, context, previous_state)
        
        # Handle try/catch
        if 'try' in step:
            return await StepExecutor._handle_try_catch(step, test, base_dir, context, previous_state)
        
        # Handle optional steps (legacy)
        if step.get('optional', False):
            if not StepExecutor._should_execute_optional(step, context):
                return previous_state
        
        # Handle direct method calls
        if len(step) == 1:
            method_name = list(step.keys())[0]
            if method_name != 'action' and hasattr(test, method_name):
                return await StepExecutor._handle_method_call(test, method_name, previous_state)
        
        # Handle standard actions
        action = step.get('action')
        if not action:
            return previous_state
        
        # Handle Playwright actions (special async handling)
        playwright_state = await StepExecutor._handle_playwright_actions(action, step, test, context, previous_state)
        if playwright_state is not None:
            new_state = playwright_state
        else:
            # Handle core actions
            core_actions = ActionMapper.get_core_actions(step, test)
            if action in core_actions:
                if ActionMapper.is_deprecated(action):
                    logger.warning(ActionMapper.get_deprecation_warning(action))
                await core_actions[action]()
                new_state = await WebState.capture(test.page, step_number=previous_state.step_number, action_type=action_type)
            # Handle deprecated navigate
            elif action == 'navigate':
                logger.warning(ActionMapper.get_deprecation_warning(action))
                menu_path = step.get('menu_path', [])
                await test.navigate(menu_path)
                new_state = await WebState.capture(test.page, step_number=previous_state.step_number, action_type=action_type)
            # Try to find action as YAML file (generic action)
            elif base_dir:
                action_yaml = YAMLResolver.find_action_yaml(action, base_dir)
                if action_yaml:
                    new_state = await StepExecutor._handle_yaml_action(action_yaml, step, test, base_dir, context, previous_state)
                else:
                    # Try to find action in extensions
                    extension_actions = test.extensions.get_all_yaml_actions()
                    if action in extension_actions:
                        handler = extension_actions[action]
                        action_data = {k: v for k, v in step.items() if k != 'action'}
                        await handler(test, action_data)
                        new_state = await WebState.capture(test.page, step_number=previous_state.step_number, action_type=action_type)
                    else:
                        # Unknown action
                        logger.warning(f"Unknown action: {action}. Se for uma ação genérica, crie um YAML em examples/ (ex: {action}.yaml)")
                        print(f"  ⚠️  Unknown action: {action}")
                        return previous_state
            else:
                # Try to find action in extensions
                extension_actions = test.extensions.get_all_yaml_actions()
                if action in extension_actions:
                    handler = extension_actions[action]
                    action_data = {k: v for k, v in step.items() if k != 'action'}
                    await handler(test, action_data)
                    new_state = await WebState.capture(test.page, step_number=previous_state.step_number, action_type=action_type)
                else:
                    # Unknown action
                    logger.warning(f"Unknown action: {action}. Se for uma ação genérica, crie um YAML em examples/ (ex: {action}.yaml)")
                    print(f"  ⚠️  Unknown action: {action}")
                    return previous_state
        
        # Wait for page to load after action (unless explicitly disabled)
        step_start_time = time.time()
        if step.get('wait', True) is not False:
            # Check if test has wait_until_ready method (OdooTestBase has it)
            if hasattr(test, 'wait_until_ready'):
                await test.wait_until_ready()
            else:
                # Generic wait for load state
                try:
                    load_state = test.config.browser.wait_for_load
                    timeout = test.config.browser.wait_timeout
                    if load_state in ["load", "domcontentloaded", "networkidle"]:
                        await test.page.wait_for_load_state(load_state, timeout=timeout)
                except Exception:
                    pass  # Don't fail if wait times out
        
        # Handle static steps (minimum duration)
        is_static = step.get('static', False)
        if is_static and not test.config.step.fast_mode:
            min_duration = test.config.step.static_min_duration
            # Calculate elapsed time since step start
            elapsed = time.time() - step_start_time
            remaining = max(0, min_duration - elapsed)
            if remaining > 0:
                await asyncio.sleep(remaining)
        
        return new_state
    
    @staticmethod
    async def _handle_compose(step: Dict[str, Any], test: SimpleTestBase, base_dir: Optional[Path], 
                             context: Dict[str, Any], previous_state: WebState, action_type: str) -> WebState:
        """Handle compose step."""
        compose_file = step.get('compose')
        params = step.get('params', {})
        
        if compose_file:
            yaml_path = YAMLResolver.resolve_yaml_path(compose_file, base_dir) if base_dir else None
            if yaml_path:
                with open(yaml_path, 'r', encoding='utf-8') as f:
                    composed_data = yaml.safe_load(f)
                
                composed_data = YAMLResolver.resolve_inheritance(composed_data, yaml_path.parent)
                composed_data = YAMLResolver.resolve_includes(composed_data, yaml_path.parent)
                composed_data = YAMLResolver.resolve_compose(composed_data, yaml_path.parent)
                
                context['params'].update(params)
                
                composed_steps_list = composed_data.get('steps', [])
                current_state = previous_state
                for composed_step in composed_steps_list:
                    current_state = await StepExecutor.execute_step(composed_step, test, base_dir, context, current_state)
                return current_state
            else:
                logger.warning(f"Compose YAML not found in step: {compose_file}")
        
        return await WebState.capture(test.page, step_number=previous_state.step_number, action_type=action_type)
    
    @staticmethod
    async def _handle_loop(step: Dict[str, Any], test: SimpleTestBase, base_dir: Optional[Path],
                          context: Dict[str, Any], previous_state: WebState) -> WebState:
        """Handle for loop."""
        loop_var, _, iterable_expr = step['for'].partition(' in ')
        loop_var = loop_var.strip()
        iterable_expr = iterable_expr.strip()
        
        iterable = ExpressionEvaluator.evaluate(f"{{{{ {iterable_expr} }}}}", context) if '{{' in iterable_expr else context.get('vars', {}).get(iterable_expr) or context.get('params', {}).get(iterable_expr)
        
        if not iterable:
            logger.warning(f"Loop iterable not found: {iterable_expr}")
            return previous_state
        
        if not isinstance(iterable, (list, tuple, dict)):
            logger.warning(f"Loop iterable is not iterable: {iterable_expr}")
            return previous_state
        
        loop_steps = step.get('steps', [])
        current_state = previous_state
        if isinstance(iterable, dict):
            for key, value in iterable.items():
                context['vars'][loop_var] = {'key': key, 'value': value}
                for loop_step in loop_steps:
                    current_state = await StepExecutor.execute_step(loop_step, test, base_dir, context, current_state)
        else:
            for item in iterable:
                context['vars'][loop_var] = item
                for loop_step in loop_steps:
                    current_state = await StepExecutor.execute_step(loop_step, test, base_dir, context, current_state)
        
        if loop_var in context['vars']:
            del context['vars'][loop_var]
        
        return current_state
    
    @staticmethod
    async def _handle_conditional(step: Dict[str, Any], test: SimpleTestBase, base_dir: Optional[Path],
                                 context: Dict[str, Any], previous_state: WebState) -> WebState:
        """Handle if/else/elif conditional."""
        condition_expr = step['if']
        condition_result = ExpressionEvaluator.evaluate(f"{{{{ {condition_expr} }}}}", context) if isinstance(condition_expr, str) else condition_expr
        
        current_state = previous_state
        if condition_result:
            if_steps = step.get('then', step.get('steps', []))
            for if_step in if_steps:
                current_state = await StepExecutor.execute_step(if_step, test, base_dir, context, current_state)
        else:
            elif_branches = step.get('elif', [])
            for elif_branch in elif_branches:
                elif_condition = elif_branch.get('if')
                if elif_condition:
                    elif_result = ExpressionEvaluator.evaluate(f"{{{{ {elif_condition} }}}}", context) if isinstance(elif_condition, str) else elif_condition
                    if elif_result:
                        elif_steps = elif_branch.get('then', elif_branch.get('steps', []))
                        for elif_step in elif_steps:
                            current_state = await StepExecutor.execute_step(elif_step, test, base_dir, context, current_state)
                        return current_state
            
            else_steps = step.get('else', [])
            for else_step in else_steps:
                current_state = await StepExecutor.execute_step(else_step, test, base_dir, context, current_state)
        
        return current_state
    
    @staticmethod
    async def _handle_set(step: Dict[str, Any], context: Dict[str, Any], previous_state: WebState) -> WebState:
        """Handle variable assignment."""
        set_expr = step['set']
        if '=' in set_expr:
            var_name, value_expr = set_expr.split('=', 1)
            var_name = var_name.strip()
            value_expr = value_expr.strip()
            
            value = ExpressionEvaluator.evaluate(f"{{{{ {value_expr} }}}}", context) if '{{' in value_expr or any(op in value_expr for op in ['+', '-', '*', '/']) else value_expr
            
            context['vars'][var_name] = value
            logger.debug(f"Set variable '{var_name}' = {value}")
        
        return previous_state
    
    @staticmethod
    async def _handle_try_catch(step: Dict[str, Any], test: SimpleTestBase, base_dir: Optional[Path],
                               context: Dict[str, Any], previous_state: WebState) -> WebState:
        """Handle try/catch/finally."""
        try_steps = step.get('try', [])
        catch_steps = step.get('catch', [])
        finally_steps = step.get('finally', [])
        
        current_state = previous_state
        try:
            for try_step in try_steps:
                current_state = await StepExecutor.execute_step(try_step, test, base_dir, context, current_state)
        except Exception as e:
            logger.info(f"Try block failed, executing catch: {e}")
            context['vars']['__error__'] = str(e)
            context['vars']['__error_type__'] = type(e).__name__
            for catch_step in catch_steps:
                current_state = await StepExecutor.execute_step(catch_step, test, base_dir, context, current_state)
        finally:
            if finally_steps:
                for finally_step in finally_steps:
                    try:
                        current_state = await StepExecutor.execute_step(finally_step, test, base_dir, context, current_state)
                    except Exception as e:
                        logger.warning(f"Finally block failed: {e}")
        
        return current_state
    
    @staticmethod
    def _should_execute_optional(step: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Check if optional step should execute."""
        condition = step.get('condition')
        if condition:
            condition_value = ExpressionEvaluator.evaluate(f"{{{{ {condition} }}}}", context) if isinstance(condition, str) and ('{{' in condition or any(op in condition for op in ['==', '!=', '<', '>', 'and', 'or'])) else condition
            return bool(condition_value)
        return True
    
    @staticmethod
    async def _handle_method_call(test: SimpleTestBase, method_name: str, previous_state: WebState) -> WebState:
        """Handle direct method call."""
        method = getattr(test, method_name)
        if callable(method):
            if asyncio.iscoroutinefunction(method):
                await method()
            else:
                method()
            return await WebState.capture(test.page, step_number=previous_state.step_number, action_type=method_name)
        return previous_state
    
    @staticmethod
    async def _handle_playwright_actions(action: str, step: Dict[str, Any], test: SimpleTestBase,
                                        context: Dict[str, Any], previous_state: WebState) -> Optional[WebState]:
        """Handle Playwright-specific actions that need async/await."""
        if action == 'evaluate':
            code = step.get('code', '')
            if code:
                result = await test.page.evaluate(code)
                if step.get('store_result'):
                    context['vars'][step.get('store_result')] = result
            return await WebState.capture(test.page, step_number=previous_state.step_number, action_type=action)
        
        if action == 'evaluate_handle':
            code = step.get('code', '')
            if code:
                result = await test.page.evaluate_handle(code)
                if step.get('store_result'):
                    context['vars'][step.get('store_result')] = result
            return await WebState.capture(test.page, step_number=previous_state.step_number, action_type=action)
        
        if action == 'route':
            url = step.get('url', '')
            handler_code = step.get('handler', '')
            if url and handler_code:
                async def route_handler(route):
                    await test.page.evaluate(f"""
                        async () => {{
                            {handler_code}
                        }}
                    """)
                    await route.continue_()
                await test.page.route(url, route_handler)
            return await WebState.capture(test.page, step_number=previous_state.step_number, action_type=action)
        
        if action == 'unroute':
            url = step.get('url', '')
            handler = step.get('handler')
            if handler:
                await test.page.unroute(url, handler)
            else:
                await test.page.unroute(url)
            return await WebState.capture(test.page, step_number=previous_state.step_number, action_type=action)
        
        if action == 'add_init_script':
            script = step.get('script', '')
            if script:
                await test.page.add_init_script(script)
            return await WebState.capture(test.page, step_number=previous_state.step_number, action_type=action)
        
        if action == 'set_extra_http_headers':
            headers = step.get('headers', {})
            if headers:
                await test.page.set_extra_http_headers(headers)
            return await WebState.capture(test.page, step_number=previous_state.step_number, action_type=action)
        
        if action == 'set_viewport_size':
            width = step.get('width', 1920)
            height = step.get('height', 1080)
            await test.page.set_viewport_size(width=width, height=height)
            return await WebState.capture(test.page, step_number=previous_state.step_number, action_type=action)
        
        if action == 'add_script_tag':
            content = step.get('content')
            url = step.get('url')
            path = step.get('path')
            await test.page.add_script_tag(content=content, url=url, path=path)
            return await WebState.capture(test.page, step_number=previous_state.step_number, action_type=action)
        
        if action == 'add_style_tag':
            content = step.get('content')
            url = step.get('url')
            path = step.get('path')
            await test.page.add_style_tag(content=content, url=url, path=path)
            return await WebState.capture(test.page, step_number=previous_state.step_number, action_type=action)
        
        if action == 'request':
            method = step.get('method', 'GET').upper()
            request_url = step.get('url', '')
            data = step.get('data')
            if method == 'GET':
                response = await test.page.request.get(request_url)
            elif method == 'POST':
                response = await test.page.request.post(request_url, data=data)
            else:
                response = await test.page.request.fetch(request_url, method=method, data=data)
            if step.get('store_result'):
                context['vars'][step.get('store_result')] = await response.json() if response.ok else None
            return await WebState.capture(test.page, step_number=previous_state.step_number, action_type=action)
        
        return None
    
    @staticmethod
    async def _handle_yaml_action(action_yaml: Path, step: Dict[str, Any], test: SimpleTestBase,
                                 base_dir: Optional[Path], context: Dict[str, Any], previous_state: WebState) -> WebState:
        """Handle generic YAML action with rollback and auto-fix support."""
        with open(action_yaml, 'r', encoding='utf-8') as f:
            action_data = yaml.safe_load(f)
        
        action_data = YAMLResolver.resolve_inheritance(action_data, action_yaml.parent)
        action_data = YAMLResolver.resolve_includes(action_data, action_yaml.parent)
        action_data = YAMLResolver.resolve_compose(action_data, action_yaml.parent)
        
        params = {k: v for k, v in step.items() if k != 'action'}
        context['params'].update(params)
        
        action_steps = action_data.get('steps', [])
        current_state = previous_state
        
        # Executar steps com rollback e auto-fix
        for step_index, action_step in enumerate(action_steps, start=1):
            state_before_step = current_state
            max_retries = 5
            retry_count = 0
            step_success = False
            
            while retry_count < max_retries and not step_success:
                try:
                    # Tentar executar passo
                    current_state = await StepExecutor.execute_step(action_step, test, action_yaml.parent, context, current_state)
                    step_success = True
                except Exception as e:
                    retry_count += 1
                    error_type = type(e).__name__
                    error_message = str(e)
                    
                    logger.warning(f"Erro no passo {step_index} de {action_yaml.name} (tentativa {retry_count}/{max_retries}): {error_type}: {error_message}")
                    print(f"  ⚠️  Erro no passo {step_index} de {action_yaml.name}: {error_type}: {error_message[:100]}")
                    
                    # Salvar erro no control interface
                    if hasattr(test, '_control_interface') and test._control_interface:
                        try:
                            test._control_interface.save_error(e, step_index)
                        except:
                            pass
                    
                    # Tentar corrigir automaticamente no arquivo YAML da action
                    from .auto_fixer import AutoFixer
                    from .html_analyzer import HTMLAnalyzer
                    
                    fixer = AutoFixer(action_yaml)
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
                        action_step, 
                        step_index,
                        page_state=page_state,
                        html_analyzer=html_analyzer,
                        action_history=action_history
                    )
                    
                    if fix_result.get('fixed'):
                        print(f"  🔧 Correção automática aplicada em {action_yaml.name}: {fix_result.get('message')}")
                        
                        # Recarregar YAML se foi corrigido
                        if fix_result.get('fix_type') == 'yaml':
                            try:
                                with open(action_yaml, 'r', encoding='utf-8') as f:
                                    reloaded_data = yaml.safe_load(f)
                                reloaded_data = YAMLResolver.resolve_inheritance(reloaded_data, action_yaml.parent)
                                reloaded_data = YAMLResolver.resolve_includes(reloaded_data, action_yaml.parent)
                                reloaded_data = YAMLResolver.resolve_compose(reloaded_data, action_yaml.parent)
                                reloaded_steps = reloaded_data.get('steps', [])
                                
                                # Atualizar step atual com versão corrigida
                                if step_index <= len(reloaded_steps):
                                    action_step = reloaded_steps[step_index - 1]
                                    action_steps[step_index - 1] = action_step
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
                        print(f"  ❌ Máximo de tentativas ({max_retries}) atingido para passo {step_index} de {action_yaml.name}")
                        raise
                    
                    # Aguardar antes de tentar novamente
                    await asyncio.sleep(1)
        
        return current_state

