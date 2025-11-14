#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Monitor and Fix - Monitora processo e corrige erros automaticamente.

Este script:
1. Monitora arquivos de controle do processo
2. Detecta erros
3. Corrige YAMLs e código Python automaticamente
4. Envia comandos de reload
"""

import sys
import time
import json
from pathlib import Path
from typing import Optional, Dict, Any
import yaml

# Adicionar projeto ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playwright_simple.core.control_interface import ControlInterface

# Cores
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class AutoFixer:
    """Corrige erros automaticamente."""
    
    def __init__(self, test_name: str, yaml_file: Path):
        self.test_name = test_name
        self.yaml_file = yaml_file
        self.control_dir = Path("/tmp/playwright_control")
        self.fix_count = 0
    
    def get_error(self) -> Optional[Dict]:
        """Obtém erro do processo."""
        error_file = self.control_dir / f"{self.test_name}_error.json"
        if error_file.exists():
            try:
                return json.loads(error_file.read_text(encoding='utf-8'))
            except:
                pass
        return None
    
    def get_state(self) -> Optional[Dict]:
        """Obtém estado do processo."""
        state_file = self.control_dir / f"{self.test_name}_state.json"
        if state_file.exists():
            try:
                return json.loads(state_file.read_text(encoding='utf-8'))
            except:
                pass
        return None
    
    def fix_yaml(self, error_data: Dict, step_state: Optional[Dict]) -> bool:
        """Corrige YAML baseado no erro."""
        if not self.yaml_file.exists():
            return False
        
        try:
            # Carregar YAML
            with open(self.yaml_file, 'r', encoding='utf-8') as f:
                yaml_data = yaml.safe_load(f) or {}
            
            steps = yaml_data.get('steps', [])
            step_number = error_data.get('step_number') or (step_state.get('step_number') if step_state else None)
            
            if not step_number or step_number < 1 or step_number > len(steps):
                return False
            
            step_index = step_number - 1
            step = steps[step_index]
            
            error_type = error_data.get('error_type', '')
            error_msg = error_data.get('error_message', '')
            
            # Corrigir baseado no tipo de erro
            fixed = False
            
            if 'ElementNotFoundError' in error_type or 'not found' in error_msg.lower():
                # Adicionar wait antes do step
                wait_step = {
                    'action': 'wait',
                    'seconds': 2,
                    'description': 'Aguardando elemento aparecer'
                }
                steps.insert(step_index, wait_step)
                fixed = True
                print(f"{Colors.BLUE}🔧 Adicionado wait antes do passo {step_number}{Colors.RESET}")
            
            elif 'Timeout' in error_type or 'timeout' in error_msg.lower():
                # Aumentar timeout
                if 'timeout' not in step:
                    step['timeout'] = 10
                    fixed = True
                    print(f"{Colors.BLUE}🔧 Aumentado timeout do passo {step_number}{Colors.RESET}")
            
            elif 'Unknown action' in error_msg or 'action' in error_msg.lower():
                # Tentar mapear ação
                action = step.get('action', '')
                action_mapping = {
                    'click_button': 'click',
                    'fill_field': 'fill',
                    'navigate': 'go_to'
                }
                if action in action_mapping:
                    step['action'] = action_mapping[action]
                    fixed = True
                    print(f"{Colors.BLUE}🔧 Mapeado '{action}' para '{action_mapping[action]}'{Colors.RESET}")
            
            if fixed:
                # Salvar YAML
                yaml_data['steps'] = steps
                with open(self.yaml_file, 'w', encoding='utf-8') as f:
                    yaml.dump(yaml_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
                print(f"{Colors.GREEN}✅ YAML corrigido e salvo{Colors.RESET}")
                return True
            
        except Exception as e:
            print(f"{Colors.RED}❌ Erro ao corrigir YAML: {e}{Colors.RESET}")
        
        return False
    
    def fix_code(self, error_data: Dict) -> bool:
        """Corrige código Python da biblioteca se necessário."""
        error_type = error_data.get('error_type', '')
        error_msg = error_data.get('error_message', '')
        
        # Aqui você pode adicionar lógica para corrigir código Python
        # Por enquanto, apenas detecta problemas conhecidos
        
        if 'ImportError' in error_type or 'ModuleNotFoundError' in error_type:
            print(f"{Colors.YELLOW}⚠️  Erro de importação detectado: {error_msg}{Colors.RESET}")
            print(f"{Colors.CYAN}💡 Verifique se o módulo está no PYTHONPATH{Colors.RESET}")
            return False
        
        return False
    
    def send_reload(self):
        """Envia comando de reload."""
        command_file = self.control_dir / f"{self.test_name}_command.json"
        cmd_data = {
            "command": "reload",
            "params": {},
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        }
        command_file.write_text(json.dumps(cmd_data, indent=2), encoding='utf-8')
        print(f"{Colors.GREEN}✅ Comando de reload enviado{Colors.RESET}")


def main():
    """Monitora e corrige erros."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor and fix errors")
    parser.add_argument("yaml_file", help="Arquivo YAML do teste")
    parser.add_argument("--test-name", help="Nome do teste (default: stem do arquivo)")
    
    args = parser.parse_args()
    
    yaml_file = Path(args.yaml_file).absolute()
    test_name = args.test_name or yaml_file.stem
    
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}🔍 Monitor and Fix{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}")
    print(f"{Colors.CYAN}📄 YAML: {yaml_file}{Colors.RESET}")
    print(f"{Colors.CYAN}🧪 Teste: {test_name}{Colors.RESET}")
    print()
    
    fixer = AutoFixer(test_name, yaml_file)
    control_interface = ControlInterface(test_name)
    
    last_error = None
    error_detected = False
    
    def on_error_changed(path: Path):
        """Callback quando arquivo de erro muda."""
        nonlocal error_detected
        error_detected = True
    
    # Monitorar arquivo de erro
    error_file = Path("/tmp/playwright_control") / f"{test_name}_error.json"
    control_interface.watch_file(error_file, on_error_changed)
    
    print(f"{Colors.GREEN}✅ Monitoramento iniciado{Colors.RESET}")
    print(f"{Colors.CYAN}💡 Aguardando erros...{Colors.RESET}\n")
    
    try:
        while True:
            if error_detected:
                error_detected = False
                
                error_data = fixer.get_error()
                if error_data and error_data != last_error:
                    last_error = error_data
                    
                    print(f"\n{Colors.RED}{'='*80}{Colors.RESET}")
                    print(f"{Colors.RED}❌ ERRO DETECTADO{Colors.RESET}")
                    print(f"{Colors.RED}{'='*80}{Colors.RESET}")
                    print(f"{Colors.YELLOW}Tipo: {error_data.get('error_type', '?')}{Colors.RESET}")
                    print(f"{Colors.YELLOW}Mensagem: {error_data.get('error_message', '?')[:200]}{Colors.RESET}")
                    print(f"{Colors.YELLOW}Passo: {error_data.get('step_number', '?')}{Colors.RESET}")
                    
                    # Obter estado
                    step_state = fixer.get_state()
                    
                    # Tentar corrigir YAML
                    print(f"\n{Colors.BLUE}🔧 Tentando corrigir YAML...{Colors.RESET}")
                    if fixer.fix_yaml(error_data, step_state):
                        fixer.fix_count += 1
                        time.sleep(1)  # Dar tempo para hot-reload
                    else:
                        print(f"{Colors.YELLOW}⚠️  Não foi possível corrigir YAML automaticamente{Colors.RESET}")
                    
                    # Tentar corrigir código
                    print(f"{Colors.BLUE}🔧 Verificando código Python...{Colors.RESET}")
                    fixer.fix_code(error_data)
                    
                    print(f"{Colors.RED}{'='*80}{Colors.RESET}\n")
            
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️  Interrompido{Colors.RESET}")
    finally:
        control_interface.stop_watching()
        print(f"\n{Colors.CYAN}📊 Total de correções: {fixer.fix_count}{Colors.RESET}")
        print(f"{Colors.CYAN}👋 Monitoramento encerrado{Colors.RESET}")


if __name__ == "__main__":
    main()

