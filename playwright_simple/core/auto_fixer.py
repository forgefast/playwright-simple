#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto Fixer - Corrige erros automaticamente e faz rollback de passos.

Detecta erros, corrige YAML/código automaticamente, faz rollback e re-executa.
"""

import logging
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
import re

logger = logging.getLogger(__name__)


class AutoFixer:
    """Corrige erros automaticamente em YAML e código Python."""
    
    def __init__(self, yaml_file: Path):
        """
        Inicializa auto-fixer.
        
        Args:
            yaml_file: Arquivo YAML do teste
        """
        self.yaml_file = Path(yaml_file)
        self.fix_count = 0
        self.max_fixes_per_step = 5  # Máximo de tentativas por passo
    
    def fix_error(
        self, 
        error_data: Dict, 
        step_data: Dict, 
        step_number: int,
        page_state: Optional[Dict[str, Any]] = None,
        html_analyzer: Optional[Any] = None,
        action_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Tenta corrigir erro automaticamente com contexto completo.
        
        Args:
            error_data: Dados do erro
            step_data: Dados do passo atual
            step_number: Número do passo
            page_state: Estado atual da página (URL, título, etc.)
            html_analyzer: Instância de HTMLAnalyzer para analisar HTML
            action_history: Histórico de ações executadas anteriormente
            
        Returns:
            Dict com informações da correção:
            - fixed: bool - Se foi corrigido
            - fix_type: str - Tipo de correção ('yaml', 'code', 'none')
            - message: str - Mensagem da correção
        """
        error_type = error_data.get('error_type', '')
        error_message = error_data.get('error_message', '')
        action = step_data.get('action', '')
        
        # Coletar contexto adicional
        context = {
            'error_type': error_type,
            'error_message': error_message,
            'action': action,
            'step_number': step_number,
            'page_state': page_state or {},
            'action_history': action_history or []
        }
        
        # Analisar HTML se disponível
        if html_analyzer:
            try:
                html_info = html_analyzer.analyze()
                context['html_info'] = html_info
                logger.debug(f"HTML analisado: {len(html_info.get('buttons', []))} botões, {len(html_info.get('inputs', []))} inputs")
            except Exception as e:
                logger.debug(f"Erro ao analisar HTML: {e}")
        
        # Tentar corrigir YAML primeiro (com contexto)
        yaml_fix = self._fix_yaml_error_with_context(error_type, error_message, step_data, step_number, context)
        if yaml_fix['fixed']:
            return {
                'fixed': True,
                'fix_type': 'yaml',
                'message': yaml_fix['message'],
                'yaml_file': str(self.yaml_file)
            }
        
        # Tentar corrigir código Python
        code_fix = self._fix_code_error(error_type, error_message, step_data)
        if code_fix['fixed']:
            return {
                'fixed': True,
                'fix_type': 'code',
                'message': code_fix['message'],
                'code_file': code_fix.get('file')
            }
        
        return {
            'fixed': False,
            'fix_type': 'none',
            'message': 'Não foi possível corrigir automaticamente'
        }
    
    def _fix_yaml_error_with_context(
        self, 
        error_type: str, 
        error_message: str, 
        step_data: Dict, 
        step_number: int,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Corrige erro no YAML usando contexto completo."""
        # Primeiro tenta a correção básica
        basic_fix = self._fix_yaml_error(error_type, error_message, step_data, step_number)
        if basic_fix['fixed']:
            return basic_fix
        
        # Se não funcionou, tenta correção com contexto
        html_info = context.get('html_info', {})
        action_history = context.get('action_history', [])
        
        # ElementNotFoundError com análise de HTML
        if 'ElementNotFoundError' in error_type or 'not found' in error_message.lower():
            # Tentar encontrar elemento similar no HTML
            if html_info:
                buttons = html_info.get('buttons', [])
                inputs = html_info.get('inputs', [])
                
                # Extrair texto procurado do erro ou step
                searched_text = step_data.get('text', '') or step_data.get('selector', '')
                if not searched_text and error_message:
                    # Tentar extrair do erro
                    import re
                    match = re.search(r"['\"]([^'\"]+)['\"]", error_message)
                    if match:
                        searched_text = match.group(1)
                
                # Procurar elemento similar
                if searched_text:
                    # Procurar em botões
                    for button in buttons:
                        button_text = button.get('text', '').lower()
                        searched_lower = searched_text.lower()
                        if searched_lower in button_text or button_text in searched_lower:
                            # Encontrou botão similar
                            return self._apply_fix_suggestion(
                                step_data, 
                                step_number,
                                f"Elemento '{searched_text}' não encontrado, mas encontrado botão similar: '{button.get('text', '')}'",
                                {'text': button.get('text', '')}
                            )
                    
                    # Procurar em inputs
                    for input_field in inputs:
                        input_name = (input_field.get('name', '') or input_field.get('placeholder', '') or input_field.get('id', '')).lower()
                        searched_lower = searched_text.lower()
                        if searched_lower in input_name or input_name in searched_lower:
                            # Encontrou input similar
                            return self._apply_fix_suggestion(
                                step_data,
                                step_number,
                                f"Campo '{searched_text}' não encontrado, mas encontrado campo similar: '{input_field.get('name') or input_field.get('placeholder', '')}'",
                                {'selector': f"input[name='{input_field.get('name')}']" if input_field.get('name') else f"#{input_field.get('id')}"}
                            )
        
        return {'fixed': False, 'message': 'Nenhuma correção com contexto aplicada'}
    
    def _apply_fix_suggestion(self, step_data: Dict, step_number: int, message: str, fix_data: Dict[str, Any]) -> Dict[str, Any]:
        """Aplica sugestão de correção ao YAML."""
        if not self.yaml_file.exists():
            return {'fixed': False, 'message': 'Arquivo YAML não encontrado'}
        
        try:
            import yaml
            with open(self.yaml_file, 'r', encoding='utf-8') as f:
                yaml_data = yaml.safe_load(f) or {}
            
            steps = yaml_data.get('steps', [])
            if step_number < 1 or step_number > len(steps):
                return {'fixed': False, 'message': 'Passo inválido'}
            
            step_index = step_number - 1
            step = steps[step_index]
            
            # Aplicar correção
            step.update(fix_data)
            
            # Salvar YAML corrigido
            yaml_data['steps'] = steps
            with open(self.yaml_file, 'w', encoding='utf-8') as f:
                yaml.dump(yaml_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            
            self.fix_count += 1
            return {
                'fixed': True,
                'message': message
            }
        except Exception as e:
            logger.error(f"Erro ao aplicar correção: {e}")
            return {'fixed': False, 'message': f'Erro ao aplicar correção: {e}'}
    
    def _fix_yaml_error(self, error_type: str, error_message: str, step_data: Dict, step_number: int) -> Dict[str, Any]:
        """Corrige erro no YAML."""
        if not self.yaml_file.exists():
            return {'fixed': False, 'message': 'Arquivo YAML não encontrado'}
        
        try:
            # Carregar YAML
            with open(self.yaml_file, 'r', encoding='utf-8') as f:
                yaml_data = yaml.safe_load(f) or {}
            
            steps = yaml_data.get('steps', [])
            if step_number < 1 or step_number > len(steps):
                return {'fixed': False, 'message': 'Passo inválido'}
            
            step_index = step_number - 1
            step = steps[step_index]
            original_step = step.copy()
            
            fixed = False
            fix_messages = []
            
            # 1. ElementNotFoundError - Adicionar wait ou timeout
            if 'ElementNotFoundError' in error_type or 'not found' in error_message.lower() or 'element' in error_message.lower():
                if 'wait' not in step and 'timeout' not in step:
                    # Adicionar wait antes do passo
                    wait_step = {
                        'action': 'wait',
                        'seconds': 2,
                        'description': 'Aguardando elemento aparecer'
                    }
                    steps.insert(step_index, wait_step)
                    fixed = True
                    fix_messages.append("Adicionado wait antes do passo")
                    step_number += 1  # Passo foi inserido
                    step_index += 1
                    step = steps[step_index]
                
                # Aumentar timeout se não tiver
                if 'timeout' not in step:
                    step['timeout'] = 10
                    fixed = True
                    fix_messages.append("Aumentado timeout para 10s")
            
            # 2. TimeoutError - Aumentar timeout
            elif 'Timeout' in error_type or 'timeout' in error_message.lower():
                current_timeout = step.get('timeout', 5)
                new_timeout = max(current_timeout * 2, 10)
                step['timeout'] = new_timeout
                fixed = True
                fix_messages.append(f"Aumentado timeout de {current_timeout}s para {new_timeout}s")
            
            # 3. Unknown action - Tentar mapear ou adicionar action genérica
            elif 'Unknown action' in error_message or 'unknown action' in error_message.lower():
                action = step.get('action', '')
                action_mapping = {
                    'click_button': 'click',
                    'fill_field': 'type',
                    'fill': 'type',
                    'navigate': 'go_to',
                    'goto': 'go_to',
                    'press_key': 'press',
                    'select_option': 'select',
                    'hover_element': 'hover'
                }
                if action in action_mapping:
                    step['action'] = action_mapping[action]
                    fixed = True
                    fix_messages.append(f"Mapeado '{action}' para '{action_mapping[action]}'")
                elif not action:
                    # Se não tem action, tentar inferir
                    if 'text' in step or 'selector' in step:
                        if 'click' in str(step).lower() or 'button' in str(step).lower():
                            step['action'] = 'click'
                            fixed = True
                            fix_messages.append("Inferido action='click'")
                        elif 'type' in str(step).lower() or 'input' in str(step).lower():
                            step['action'] = 'type'
                            fixed = True
                            fix_messages.append("Inferido action='type'")
            
            # 4. Missing required fields
            elif 'missing' in error_message.lower() or 'required' in error_message.lower():
                # Tentar adicionar campos faltantes baseado na action
                action = step.get('action', '')
                if action == 'click' and 'text' not in step and 'selector' not in step:
                    # Tentar usar description como text
                    if 'description' in step:
                        step['text'] = step['description']
                        fixed = True
                        fix_messages.append("Usado description como text para click")
                elif action == 'type' and 'text' not in step:
                    step['text'] = ''
                    fixed = True
                    fix_messages.append("Adicionado campo 'text' vazio para type")
                elif action == 'go_to' and 'url' not in step:
                    # Tentar usar base_url ou inferir
                    step['url'] = '/'
                    fixed = True
                    fix_messages.append("Adicionado url='/' para go_to")
            
            # 5. TypeError com argumentos faltantes
            elif 'TypeError' in error_type and 'missing' in error_message.lower():
                # Extrair nome do argumento faltante
                match = re.search(r"missing.*?argument.*?'(\w+)'", error_message)
                if match:
                    missing_arg = match.group(1)
                    # Tentar adicionar argumento baseado no contexto
                    if missing_arg == 'element' and action in ['click', 'type', 'hover']:
                        if 'text' in step:
                            step['element'] = step['text']
                        elif 'selector' in step:
                            step['element'] = step['selector']
                        fixed = True
                        fix_messages.append(f"Adicionado argumento '{missing_arg}'")
            
            # 6. NavigationError - Adicionar wait após navegação
            elif 'NavigationError' in error_type or 'navigation' in error_message.lower():
                if action == 'go_to' and 'wait' not in step:
                    step['wait'] = True
                    fixed = True
                    fix_messages.append("Adicionado wait após navegação")
            
            if fixed:
                # Salvar YAML corrigido
                yaml_data['steps'] = steps
                with open(self.yaml_file, 'w', encoding='utf-8') as f:
                    yaml.dump(yaml_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
                
                self.fix_count += 1
                return {
                    'fixed': True,
                    'message': '; '.join(fix_messages)
                }
            
        except Exception as e:
            logger.error(f"Erro ao corrigir YAML: {e}")
            return {'fixed': False, 'message': f'Erro ao corrigir: {e}'}
        
        return {'fixed': False, 'message': 'Nenhuma correção aplicada'}
    
    def _fix_code_error(self, error_type: str, error_message: str, step_data: Dict) -> Dict[str, Any]:
        """Corrige erro no código Python."""
        # Por enquanto, apenas detecta problemas conhecidos
        # A correção real é feita manualmente ou via hot reload
        
        if 'TypeError' in error_type and 'missing' in error_message.lower():
            # Extrair informações do erro
            match = re.search(r"(\w+)\(\) missing.*?argument.*?'(\w+)'", error_message)
            if match:
                function_name = match.group(1)
                missing_arg = match.group(2)
                
                # Tentar encontrar arquivo
                code_file = self._find_code_file(function_name)
                if code_file:
                    return {
                        'fixed': False,  # Não corrige automaticamente código Python
                        'message': f"Erro em {code_file}: {function_name}() precisa do argumento '{missing_arg}'",
                        'file': str(code_file),
                        'suggestion': f"Adicione o argumento '{missing_arg}' na chamada de {function_name}()"
                    }
        
        return {'fixed': False, 'message': 'Correção de código requer intervenção manual'}
    
    def _find_code_file(self, function_name: str) -> Optional[Path]:
        """Tenta encontrar arquivo onde função está definida."""
        # Procurar em playwright_simple
        project_root = self.yaml_file.parent.parent
        playwright_dir = project_root / "playwright_simple"
        
        if not playwright_dir.exists():
            return None
        
        # Procurar por function_name em arquivos .py
        for py_file in playwright_dir.rglob("*.py"):
            try:
                content = py_file.read_text(encoding='utf-8')
                # Procurar definição da função
                if f"def {function_name}(" in content or f".{function_name}(" in content:
                    return py_file
            except:
                pass
        
        return None

