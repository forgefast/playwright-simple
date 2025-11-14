#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto Debug and Fix - Monitora teste e corrige automaticamente usando HTML.

Este script:
1. Monitora o processo de teste
2. Quando detecta erro, captura HTML (se possível)
3. Analisa HTML e corrige YAML/código automaticamente
4. Continua até o teste passar
"""

import sys
import time
import json
from pathlib import Path
from typing import Optional, Dict, Any

# Adicionar projeto ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playwright_simple.core.control_interface import ControlInterface
from playwright_simple.core.html_analyzer import HTMLAnalyzer
from playwright_simple.core.auto_fixer import AutoFixer
import yaml

# Cores
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class AutoDebugFixer:
    """Monitora e corrige testes automaticamente usando HTML."""
    
    def __init__(self, test_name: str, yaml_file: Path):
        self.test_name = test_name
        self.yaml_file = yaml_file
        self.control_dir = Path("/tmp/playwright_control")
        self.fix_count = 0
        self.max_fixes = 20
        
    def run(self):
        """Monitora e corrige até o teste passar."""
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}🤖 Auto Debug and Fix{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}")
        print(f"{Colors.CYAN}🧪 Teste: {self.test_name}{Colors.RESET}")
        print(f"{Colors.CYAN}📄 YAML: {self.yaml_file}{Colors.RESET}")
        print()
        
        control_interface = ControlInterface(self.test_name)
        error_file = self.control_dir / f"{self.test_name}_error.json"
        state_file = self.control_dir / f"{self.test_name}_state.json"
        
        last_error = None
        error_detected = False
        
        def on_error_changed(path: Path):
            nonlocal error_detected
            error_detected = True
        
        control_interface.watch_file(error_file, on_error_changed)
        
        print(f"{Colors.GREEN}✅ Monitoramento iniciado{Colors.RESET}")
        print(f"{Colors.CYAN}💡 Aguardando erros para corrigir...{Colors.RESET}\n")
        
        try:
            while True:
                if error_detected:
                    error_detected = False
                    
                    error_data = self._get_error()
                    if error_data and error_data != last_error:
                        last_error = error_data
                        
                        print(f"\n{Colors.RED}{'='*80}{Colors.RESET}")
                        print(f"{Colors.RED}❌ ERRO DETECTADO{Colors.RESET}")
                        print(f"{Colors.RED}{'='*80}{Colors.RESET}")
                        print(f"{Colors.YELLOW}Tipo: {error_data.get('error_type', '?')}{Colors.RESET}")
                        print(f"{Colors.YELLOW}Mensagem: {error_data.get('error_message', '?')[:200]}{Colors.RESET}")
                        print(f"{Colors.YELLOW}Passo: {error_data.get('step_number', '?')}{Colors.RESET}")
                        
                        # Obter estado
                        step_state = self._get_state()
                        
                        # Tentar ler HTML se disponível
                        html_info = self._analyze_html()
                        
                        # Corrigir usando HTML se disponível
                        if html_info:
                            fixed = self._fix_with_html(error_data, step_state, html_info)
                        else:
                            # Corrigir sem HTML
                            fixed = self._fix_without_html(error_data, step_state)
                        
                        if fixed:
                            self.fix_count += 1
                            print(f"{Colors.GREEN}✅ Correção #{self.fix_count} aplicada!{Colors.RESET}")
                            time.sleep(2)  # Aguardar hot reload
                        else:
                            print(f"{Colors.YELLOW}⚠️  Não foi possível corrigir automaticamente{Colors.RESET}")
                        
                        print(f"{Colors.RED}{'='*80}{Colors.RESET}\n")
                        
                        if self.fix_count >= self.max_fixes:
                            print(f"{Colors.YELLOW}⚠️  Máximo de correções ({self.max_fixes}) atingido{Colors.RESET}")
                            break
                
                # Verificar se processo ainda está rodando
                import subprocess
                result = subprocess.run(['pgrep', '-f', 'playwright_simple.cli'], 
                                       capture_output=True)
                if result.returncode != 0:
                    print(f"\n{Colors.CYAN}📊 Processo terminou{Colors.RESET}")
                    break
                
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}⚠️  Interrompido{Colors.RESET}")
        finally:
            control_interface.stop_watching()
            print(f"\n{Colors.CYAN}📊 Total de correções: {self.fix_count}{Colors.RESET}")
            print(f"{Colors.CYAN}👋 Monitoramento encerrado{Colors.RESET}")
    
    def _get_error(self) -> Optional[Dict]:
        """Obtém erro do processo."""
        error_file = self.control_dir / f"{self.test_name}_error.json"
        if error_file.exists():
            try:
                return json.loads(error_file.read_text(encoding='utf-8'))
            except:
                pass
        return None
    
    def _get_state(self) -> Optional[Dict]:
        """Obtém estado do processo."""
        state_file = self.control_dir / f"{self.test_name}_state.json"
        if state_file.exists():
            try:
                return json.loads(state_file.read_text(encoding='utf-8'))
            except:
                pass
        return None
    
    def _analyze_html(self) -> Optional[Dict]:
        """Analisa HTML se disponível."""
        html_file = Path("/tmp/playwright_html.html")
        simplified_file = Path("/tmp/playwright_html_simplified.json")
        
        if simplified_file.exists():
            try:
                return json.loads(simplified_file.read_text(encoding='utf-8'))
            except:
                pass
        
        if html_file.exists():
            analyzer = HTMLAnalyzer(html_file)
            return analyzer.analyze()
        
        return None
    
    def _fix_with_html(self, error_data: Dict, step_state: Optional[Dict], html_info: Dict) -> bool:
        """Corrige usando informações do HTML."""
        error_type = error_data.get('error_type', '')
        error_message = error_data.get('error_message', '')
        step_data = step_state.get('step_data', {}) if step_state else {}
        
        # Se erro é elemento não encontrado, tentar encontrar no HTML
        if 'ElementNotFoundError' in error_type or 'not found' in error_message.lower():
            target_text = step_data.get('text') or step_data.get('selector', '')
            
            if target_text:
                # Procurar elemento similar no HTML
                buttons = html_info.get('buttons', [])
                for btn in buttons:
                    btn_text = btn.get('text', '')
                    # Verificar se é similar (case-insensitive, parcial)
                    if target_text.lower() in btn_text.lower() or btn_text.lower() in target_text.lower():
                        print(f"{Colors.BLUE}🔍 Encontrado elemento similar no HTML:{Colors.RESET}")
                        print(f"   Procurado: '{target_text}'")
                        print(f"   Encontrado: '{btn_text}'")
                        
                        # Corrigir YAML
                        return self._fix_yaml_text(step_state, target_text, btn_text)
        
        # Fallback para correção normal
        return self._fix_without_html(error_data, step_state)
    
    def _fix_yaml_text(self, step_state: Optional[Dict], old_text: str, new_text: str) -> bool:
        """Corrige texto no YAML."""
        if not step_state:
            return False
        
        step_number = step_state.get('step_number')
        if not step_number:
            return False
        
        try:
            # Carregar YAML
            with open(self.yaml_file, 'r', encoding='utf-8') as f:
                yaml_data = yaml.safe_load(f) or {}
            
            steps = yaml_data.get('steps', [])
            if step_number < 1 or step_number > len(steps):
                return False
            
            step = steps[step_number - 1]
            
            # Corrigir texto
            if step.get('text') == old_text:
                step['text'] = new_text
                print(f"{Colors.GREEN}🔧 Corrigido: '{old_text}' → '{new_text}'{Colors.RESET}")
            elif 'text' in step and old_text.lower() in step.get('text', '').lower():
                step['text'] = new_text
                print(f"{Colors.GREEN}🔧 Corrigido texto similar: '{step.get('text')}' → '{new_text}'{Colors.RESET}")
            else:
                return False
            
            # Salvar YAML
            yaml_data['steps'] = steps
            with open(self.yaml_file, 'w', encoding='utf-8') as f:
                yaml.dump(yaml_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            
            return True
        except Exception as e:
            print(f"{Colors.RED}❌ Erro ao corrigir YAML: {e}{Colors.RESET}")
            return False
    
    def _fix_without_html(self, error_data: Dict, step_state: Optional[Dict]) -> bool:
        """Corrige sem HTML usando AutoFixer."""
        fixer = AutoFixer(self.yaml_file)
        step_data = step_state.get('step_data', {}) if step_state else {}
        step_number = step_state.get('step_number') if step_state else error_data.get('step_number')
        
        if step_number:
            fix_result = fixer.fix_error(error_data, step_data, step_number)
            if fix_result.get('fixed'):
                print(f"{Colors.GREEN}🔧 {fix_result.get('message')}{Colors.RESET}")
                return True
        
        return False


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Auto debug and fix")
    parser.add_argument("yaml_file", help="Arquivo YAML do teste")
    parser.add_argument("--test-name", help="Nome do teste (default: stem do arquivo)")
    
    args = parser.parse_args()
    
    yaml_file = Path(args.yaml_file).absolute()
    test_name = args.test_name or yaml_file.stem
    
    fixer = AutoDebugFixer(test_name, yaml_file)
    fixer.run()


if __name__ == "__main__":
    main()

