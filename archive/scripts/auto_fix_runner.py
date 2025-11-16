#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto-fix Test Runner - Executa testes em background e corrige YAML automaticamente.

Este script:
1. Executa o teste em background
2. Monitora a saída para detectar erros
3. Analisa erros e corrige o YAML automaticamente
4. Usa hot-reload para aplicar correções sem reiniciar
"""

import os
import sys
import re
import subprocess
import signal
import time
import json
import queue
import threading
import logging
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from datetime import datetime
import yaml
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger(__name__)

# Cores para output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class YAMLFileWatcher(FileSystemEventHandler):
    """Monitora mudanças no arquivo YAML."""
    
    def __init__(self, yaml_file: Path, callback):
        self.yaml_file = yaml_file
        self.callback = callback
        self.last_modified = yaml_file.stat().st_mtime if yaml_file.exists() else 0
    
    def on_modified(self, event):
        if event.src_path == str(self.yaml_file):
            current_mtime = self.yaml_file.stat().st_mtime
            if current_mtime > self.last_modified:
                self.last_modified = current_mtime
                print(f"{Colors.CYAN}📝 YAML modificado detectado!{Colors.RESET}")
                if self.callback:
                    self.callback()


class ErrorAnalyzer:
    """Analisa erros e sugere correções."""
    
    # Padrões de erro comuns
    ERROR_PATTERNS = [
        # Elemento não encontrado
        (r"Element.*not found|ElementNotFoundError|Timeout.*waiting for selector",
         "element_not_found"),
        # Seletor inválido
        (r"Invalid selector|Selector.*not found|Malformed selector",
         "invalid_selector"),
        # Ação não suportada
        (r"Action.*not supported|Unknown action|Action.*not found",
         "unknown_action"),
        # Erro de navegação
        (r"Navigation.*failed|NavigationError|Page.*not found",
         "navigation_error"),
        # Erro de timeout
        (r"Timeout.*exceeded|TimeoutError|waiting for.*timeout",
         "timeout_error"),
        # Erro de login
        (r"Login.*failed|Authentication.*failed|Invalid.*credentials",
         "login_error"),
        # Erro de YAML
        (r"YAML.*error|Invalid YAML|YAML.*parse.*error",
         "yaml_error"),
    ]
    
    @staticmethod
    def analyze_error(error_text: str) -> Optional[Dict]:
        """Analisa erro e retorna sugestão de correção."""
        error_text_lower = error_text.lower()
        
        for pattern, error_type in ErrorAnalyzer.ERROR_PATTERNS:
            if re.search(pattern, error_text, re.IGNORECASE):
                return {
                    "type": error_type,
                    "message": error_text,
                    "pattern": pattern
                }
        
        return None


class YAMLFixer:
    """Corrige arquivos YAML automaticamente."""
    
    def __init__(self, yaml_file: Path):
        self.yaml_file = yaml_file
        self.backup_dir = yaml_file.parent / ".auto_fix_backups"
        self.backup_dir.mkdir(exist_ok=True)
    
    def backup(self) -> Path:
        """Cria backup do YAML antes de modificar."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"{self.yaml_file.stem}_{timestamp}.yaml"
        
        if self.yaml_file.exists():
            import shutil
            shutil.copy2(self.yaml_file, backup_file)
            print(f"{Colors.YELLOW}💾 Backup criado: {backup_file}{Colors.RESET}")
        
        return backup_file
    
    def load_yaml(self) -> Dict:
        """Carrega YAML."""
        with open(self.yaml_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    
    def save_yaml(self, data: Dict):
        """Salva YAML."""
        self.backup()
        with open(self.yaml_file, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        print(f"{Colors.GREEN}✅ YAML salvo: {self.yaml_file}{Colors.RESET}")
    
    def fix_element_not_found(self, error_info: Dict, yaml_data: Dict) -> bool:
        """Tenta corrigir erro de elemento não encontrado."""
        # Extrair seletor do erro se possível
        error_msg = error_info.get("message", "")
        
        # Procurar por seletores no erro
        selector_match = re.search(r"selector[:\s]+['\"]([^'\"]+)['\"]", error_msg, re.IGNORECASE)
        if selector_match:
            selector = selector_match.group(1)
            print(f"{Colors.YELLOW}🔍 Seletor problemático encontrado: {selector}{Colors.RESET}")
            
            # Tentar encontrar e corrigir no YAML
            steps = yaml_data.get("steps", [])
            for i, step in enumerate(steps):
                if step.get("selector") == selector or step.get("text") == selector:
                    # Adicionar wait antes do elemento
                    print(f"{Colors.BLUE}🔧 Adicionando wait antes do step {i+1}{Colors.RESET}")
                    
                    # Inserir wait antes
                    wait_step = {
                        "action": "wait",
                        "seconds": 2,
                        "description": "Aguardando elemento aparecer"
                    }
                    steps.insert(i, wait_step)
                    yaml_data["steps"] = steps
                    return True
        
        return False
    
    def fix_timeout_error(self, error_info: Dict, yaml_data: Dict) -> bool:
        """Aumenta timeouts para steps problemáticos."""
        steps = yaml_data.get("steps", [])
        
        # Adicionar timeout aos steps que não têm
        modified = False
        for step in steps:
            if "timeout" not in step and step.get("action") not in ["wait", "screenshot"]:
                step["timeout"] = 10  # Aumentar timeout padrão
                modified = True
        
        if modified:
            print(f"{Colors.BLUE}🔧 Timeouts aumentados nos steps{Colors.RESET}")
            return True
        
        return False
    
    def fix_unknown_action(self, error_info: Dict, yaml_data: Dict) -> bool:
        """Tenta corrigir ação desconhecida."""
        error_msg = error_info.get("message", "")
        
        # Extrair nome da ação
        action_match = re.search(r"action[:\s]+['\"]?([^'\"]+)['\"]?", error_msg, re.IGNORECASE)
        if action_match:
            unknown_action = action_match.group(1)
            print(f"{Colors.YELLOW}⚠️  Ação desconhecida: {unknown_action}{Colors.RESET}")
            
            # Mapear ações comuns
            action_mapping = {
                "click_button": "click",
                "fill_field": "fill",
                "navigate": "go_to",
            }
            
            if unknown_action in action_mapping:
                mapped_action = action_mapping[unknown_action]
                print(f"{Colors.BLUE}🔧 Mapeando '{unknown_action}' para '{mapped_action}'{Colors.RESET}")
                
                # Substituir no YAML
                steps = yaml_data.get("steps", [])
                for step in steps:
                    if step.get("action") == unknown_action:
                        step["action"] = mapped_action
                        return True
        
        return False
    
    def fix_error(self, error_info: Dict) -> bool:
        """Tenta corrigir erro no YAML."""
        error_type = error_info.get("type")
        
        if not error_type:
            return False
        
        try:
            yaml_data = self.load_yaml()
            
            fixed = False
            if error_type == "element_not_found":
                fixed = self.fix_element_not_found(error_info, yaml_data)
            elif error_type == "timeout_error":
                fixed = self.fix_timeout_error(error_info, yaml_data)
            elif error_type == "unknown_action":
                fixed = self.fix_unknown_action(error_info, yaml_data)
            
            if fixed:
                self.save_yaml(yaml_data)
                return True
            else:
                print(f"{Colors.YELLOW}⚠️  Não foi possível corrigir automaticamente{Colors.RESET}")
                return False
                
        except Exception as e:
            print(f"{Colors.RED}❌ Erro ao corrigir YAML: {e}{Colors.RESET}")
            return False


class AutoFixRunner:
    """Runner que executa testes e corrige automaticamente."""
    
    def __init__(self, yaml_file: Path, base_url: str = None, max_fixes: int = 10, headless: bool = True):
        """
        Inicializa runner.
        
        Args:
            yaml_file: Caminho para arquivo YAML do teste
            base_url: URL base (opcional)
            max_fixes: Número máximo de correções automáticas
            headless: Executar em modo headless (sem abrir navegador)
        """
        self.yaml_file = Path(yaml_file).absolute()
        self.base_url = base_url
        self.max_fixes = max_fixes
        self.headless = headless
        self.fix_count = 0
        self.process: Optional[subprocess.Popen] = None
        self.error_analyzer = ErrorAnalyzer()
        self.yaml_fixer = YAMLFixer(self.yaml_file)
        self.observer: Optional[Observer] = None
        self.build_command()
    
    def _kill_existing_processes(self):
        """Encerra processos existentes de playwright antes de iniciar novo."""
        try:
            # Encontrar processos relacionados
            import psutil
            killed = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info.get('cmdline', [])
                    if not cmdline:
                        continue
                    cmdline_str = ' '.join(cmdline)
                    # Verificar se é processo do playwright-simple
                    if 'playwright_simple.cli' in cmdline_str or 'auto_fix_runner' in cmdline_str:
                        # Não matar o próprio processo
                        if proc.pid != os.getpid():
                            proc.terminate()
                            try:
                                proc.wait(timeout=3)
                            except psutil.TimeoutExpired:
                                proc.kill()
                            killed.append(proc.pid)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            if killed:
                print(f"{Colors.YELLOW}⚠️  Encerrados {len(killed)} processo(s) antigo(s): {killed}{Colors.RESET}")
                time.sleep(1)  # Aguardar processos encerrarem
        except ImportError:
            # psutil não disponível, usar pkill
            import subprocess
            try:
                subprocess.run(['pkill', '-f', 'playwright_simple.cli'], 
                             capture_output=True, timeout=5)
                subprocess.run(['pkill', '-f', 'auto_fix_runner'], 
                             capture_output=True, timeout=5)
                time.sleep(1)
            except:
                pass
        except Exception as e:
            logger.debug(f"Erro ao encerrar processos: {e}")
    
    def build_command(self):
        """Constrói comando para executar teste."""
        # Construir comando
        self.command = [
            "python3", "-m", "playwright_simple.cli",
            "--log-level", "INFO",
            "run", str(self.yaml_file.absolute()),
        ]
        
        if self.base_url:
            self.command.extend(["--base-url", self.base_url])
        
        # Adicionar flags de debug e hot-reload
        if not self.headless:
            self.command.append("--no-headless")
        
        self.command.extend([
            "--video",
            "--audio",
            "--subtitles",
            "--debug",
            "--interactive",
            "--hot-reload",
            "--step-timeout", "0.1"
        ])
        
    def start_file_watcher(self):
        """Inicia monitoramento do arquivo YAML."""
        event_handler = YAMLFileWatcher(self.yaml_file, self.on_yaml_changed)
        self.observer = Observer()
        self.observer.schedule(event_handler, str(self.yaml_file.parent), recursive=False)
        self.observer.start()
        print(f"{Colors.CYAN}👀 Monitorando: {self.yaml_file}{Colors.RESET}")
    
    def on_yaml_changed(self):
        """Callback quando YAML é modificado."""
        print(f"{Colors.GREEN}🔄 YAML modificado - hot reload deve recarregar{Colors.RESET}")
    
    def parse_output_line(self, line: str) -> Optional[Dict]:
        """Analisa linha de output para detectar erros."""
        line_lower = line.lower()
        
        # Detectar erros comuns
        if any(keyword in line_lower for keyword in ["error", "failed", "exception", "traceback"]):
            error_info = self.error_analyzer.analyze_error(line)
            if error_info:
                return error_info
        
        return None
    
    def handle_error(self, error_info: Dict):
        """Trata erro detectado - mostra informações e permite correção manual."""
        error_type = error_info.get("type")
        print(f"\n{Colors.RED}{'='*80}{Colors.RESET}")
        print(f"{Colors.RED}❌ ERRO DETECTADO: {error_type}{Colors.RESET}")
        print(f"{Colors.YELLOW}📋 Mensagem: {error_info.get('message', '')[:200]}{Colors.RESET}")
        
        # Obter informações detalhadas do passo atual
        step_state = self.get_current_step_state()
        if step_state:
            print(f"\n{Colors.CYAN}📍 INFORMAÇÕES DO PASSO ATUAL:{Colors.RESET}")
            print(f"   Passo: {step_state.get('step_number', '?')}")
            print(f"   Ação: {step_state.get('action', '?')}")
            print(f"   URL: {step_state.get('url', '?')}")
            step_data = step_state.get('step_data', {})
            if step_data:
                print(f"   Dados do passo:")
                for key, value in step_data.items():
                    if key != 'action':
                        print(f"     - {key}: {value}")
        
        # Verificar se há erro salvo pelo processo
        error_data = self.get_error_from_process()
        if error_data:
            print(f"\n{Colors.YELLOW}📋 ERRO DO PROCESSO:{Colors.RESET}")
            print(f"   Tipo: {error_data.get('error_type', '?')}")
            print(f"   Mensagem: {error_data.get('error_message', '?')}")
            print(f"   Passo: {error_data.get('step_number', '?')}")
        
        # Mostrar conteúdo do passo atual para análise
        if step_state and step_data:
            print(f"\n{Colors.BLUE}📝 CONTEÚDO DO PASSO (YAML):{Colors.RESET}")
            import yaml
            step_yaml = yaml.dump(step_data, default_flow_style=False, allow_unicode=True)
            print(f"   {step_yaml.replace(chr(10), chr(10) + '   ')}")
        
        print(f"\n{Colors.BLUE}💡 CORREÇÃO MANUAL:{Colors.RESET}")
        print(f"   Arquivo: {self.yaml_file}")
        print(f"   Passo: {step_state.get('step_number', '?') if step_state else '?'}")
        print(f"\n{Colors.CYAN}⏳ Aguardando correção do YAML...{Colors.RESET}")
        print(f"{Colors.RED}{'='*80}{Colors.RESET}\n")
        
        # Retornar informações para correção
        return {
            "error_type": error_type,
            "error_message": error_info.get('message', ''),
            "step_state": step_state,
            "error_data": error_data,
            "yaml_file": str(self.yaml_file)
        }
    
    def get_current_step_state(self) -> Optional[Dict]:
        """Obtém estado completo do passo atual via control interface."""
        # Tentar via control interface (arquivo JSON)
        control_dir = Path("/tmp/playwright_control")
        if control_dir.exists():
            # Procurar arquivo de estado do teste
            test_name = self.yaml_file.stem
            state_file = control_dir / f"{test_name}_state.json"
            if state_file.exists():
                try:
                    import json
                    return json.loads(state_file.read_text(encoding='utf-8'))
                except Exception as e:
                    pass
        
        # Fallback: verificar debug states
        debug_state_dir = Path(self.yaml_file.parent) / "debug_states"
        if debug_state_dir.exists():
            state_files = sorted(debug_state_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
            if state_files:
                try:
                    import json
                    state_data = json.loads(state_files[0].read_text())
                    return {
                        "step_number": state_data.get("step_number"),
                        "action": state_data.get("action"),
                        "url": state_data.get("url"),
                        "step_data": state_data.get("step_data", {})
                    }
                except:
                    pass
        return None
    
    def get_error_from_process(self) -> Optional[Dict]:
        """Obtém erro salvo pelo processo via control interface."""
        control_dir = Path("/tmp/playwright_control")
        if control_dir.exists():
            test_name = self.yaml_file.stem
            error_file = control_dir / f"{test_name}_error.json"
            if error_file.exists():
                try:
                    import json
                    return json.loads(error_file.read_text(encoding='utf-8'))
                except:
                    pass
        return None
    
    def send_reload_command(self) -> None:
        """Envia comando de reload para o processo."""
        control_dir = Path("/tmp/playwright_control")
        control_dir.mkdir(parents=True, exist_ok=True)
        test_name = self.yaml_file.stem
        command_file = control_dir / f"{test_name}_command.json"
        
        import json
        from datetime import datetime
        cmd_data = {
            "command": "reload",
            "params": {},
            "timestamp": datetime.now().isoformat()
        }
        command_file.write_text(json.dumps(cmd_data, indent=2), encoding='utf-8')
        print(f"{Colors.GREEN}✅ Comando de reload enviado{Colors.RESET}")
    
    def run(self):
        """Executa o teste em background e monitora via comunicação."""
        # Encerrar processos antigos antes de iniciar novo
        self._kill_existing_processes()
        
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}🚀 Auto-Fix Test Runner (Modo Interativo){Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}")
        print(f"{Colors.CYAN}📄 YAML: {self.yaml_file}{Colors.RESET}")
        print(f"{Colors.CYAN}🔧 Comando: {' '.join(self.command)}{Colors.RESET}")
        print(f"{Colors.CYAN}💡 Modo: Processo em background + Comunicação via arquivos{Colors.RESET}")
        print(f"{Colors.CYAN}🖥️  Headless: {'Sim' if self.headless else 'Não'}{Colors.RESET}")
        print()
        
        # Determinar diretório do projeto
        project_dir = self.yaml_file.parent.parent
        if not (project_dir / "playwright_simple").exists():
            current = Path.cwd()
            if (current / "playwright_simple").exists():
                project_dir = current
            else:
                for parent in current.parents:
                    if (parent / "playwright_simple").exists():
                        project_dir = parent
                        break
        
        # Preparar ambiente
        env = os.environ.copy()
        pythonpath = env.get('PYTHONPATH', '')
        if pythonpath:
            env['PYTHONPATH'] = f"{project_dir}:{pythonpath}"
        else:
            env['PYTHONPATH'] = str(project_dir)
        
        print(f"{Colors.GREEN}▶️  Iniciando processo em background...{Colors.RESET}\n")
        
        # Executar processo capturando stdout para ler eventos JSON
        self.process = subprocess.Popen(
            self.command,
            stdout=subprocess.PIPE,  # Capturar para ler eventos
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1,  # Line buffered
            cwd=project_dir,
            env=env
        )
        
        print(f"{Colors.GREEN}✅ Processo iniciado (PID: {self.process.pid}){Colors.RESET}")
        print(f"{Colors.CYAN}💡 Monitorando via arquivos de controle...{Colors.RESET}\n")
        
        # Nome do teste para arquivos de controle
        test_name = self.yaml_file.stem
        control_dir = Path("/tmp/playwright_control")
        control_dir.mkdir(parents=True, exist_ok=True)
        
        state_file = control_dir / f"{test_name}_state.json"
        error_file = control_dir / f"{test_name}_error.json"
        
        # Ler eventos JSON do stdout em tempo real (muito mais eficiente que polling)
        import sys
        import threading
        if str(project_dir) not in sys.path:
            sys.path.insert(0, str(project_dir))
        
        from playwright_simple.core.control_interface import ControlInterface
        control_interface = ControlInterface(test_name, control_dir)
        
        last_processed_error = None
        
        def read_events():
            """Thread para ler eventos do stdout em tempo real."""
            nonlocal last_processed_error
            try:
                for line in iter(self.process.stdout.readline, ''):
                    if not line:
                        break
                    
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Tentar parsear como JSON event
                    try:
                        event = json.loads(line)
                        event_type = event.get('type')
                        
                        if event_type == 'error':
                            error_data = {k: v for k, v in event.items() if k != 'type'}
                            if error_data != last_processed_error:
                                last_processed_error = error_data
                                
                                # Obter estado atual
                                step_state = self.get_current_step_state()
                                
                                # Mostrar informações
                                self.show_error_info(error_data, step_state)
                                
                                # Corrigir automaticamente
                                fixed = self.auto_fix_error(error_data, step_state)
                                
                                if fixed:
                                    print(f"{Colors.GREEN}✅ Correção aplicada!{Colors.RESET}")
                                    time.sleep(2)  # Aguardar hot reload
                        elif event_type == 'state':
                            # Estado atualizado (pode usar para contexto)
                            pass
                    except json.JSONDecodeError:
                        # Não é JSON, pode ser log normal - ignorar
                        pass
            except Exception as e:
                logger.debug(f"Error reading events: {e}")
        
        # Iniciar thread de leitura
        reader_thread = threading.Thread(target=read_events, daemon=True)
        reader_thread.start()
        
        try:
            # Loop de monitoramento
            while True:
                # Verificar se processo ainda está rodando
                if self.process.poll() is not None:
                    return_code = self.process.returncode
                    print(f"\n{Colors.CYAN}📊 Processo terminou com código: {return_code}{Colors.RESET}")
                    break
                
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}⚠️  Interrompido pelo usuário{Colors.RESET}")
            if self.process:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
            return 130
        finally:
            if self.observer:
                self.observer.stop()
                self.observer.join()
            print(f"\n{Colors.CYAN}👋 Monitoramento encerrado{Colors.RESET}")
    
    def auto_fix_error(self, error_data: Dict, step_state: Optional[Dict]) -> bool:
        """Corrige erro automaticamente usando HTML se disponível."""
        # Tentar ler HTML se disponível
        html_info = None
        if Path("/tmp/playwright_html_simplified.json").exists():
            try:
                html_info = json.loads(Path("/tmp/playwright_html_simplified.json").read_text(encoding='utf-8'))
            except:
                pass
        
        # Usar AutoFixer
        from playwright_simple.core.auto_fixer import AutoFixer
        fixer = AutoFixer(self.yaml_file)
        step_data = step_state.get('step_data', {}) if step_state else {}
        step_number = step_state.get('step_number') if step_state else error_data.get('step_number')
        
        if step_number:
            fix_result = fixer.fix_error(error_data, step_data, step_number)
            if fix_result.get('fixed'):
                print(f"{Colors.GREEN}🔧 {fix_result.get('message')}{Colors.RESET}")
                return True
        
        return False
    
    def show_error_info(self, error_data: Dict, step_state: Optional[Dict]):
        """Mostra informações do erro para correção."""
        print(f"\n{Colors.RED}{'='*80}{Colors.RESET}")
        print(f"{Colors.RED}❌ ERRO DETECTADO{Colors.RESET}")
        print(f"{Colors.RED}{'='*80}{Colors.RESET}")
        
        if error_data:
            print(f"{Colors.YELLOW}📋 ERRO:{Colors.RESET}")
            print(f"   Tipo: {error_data.get('error_type', '?')}")
            print(f"   Mensagem: {error_data.get('error_message', '?')}")
            print(f"   Passo: {error_data.get('step_number', '?')}")
        
        if step_state:
            print(f"\n{Colors.CYAN}📍 PASSO ATUAL:{Colors.RESET}")
            print(f"   Passo: {step_state.get('step_number', '?')}")
            print(f"   Ação: {step_state.get('action', '?')}")
            print(f"   URL: {step_state.get('url', '?')}")
            
            step_data = step_state.get('step_data', {})
            if step_data:
                print(f"\n{Colors.BLUE}📝 CONTEÚDO DO PASSO:{Colors.RESET}")
                import yaml
                step_yaml = yaml.dump(step_data, default_flow_style=False, allow_unicode=True)
                for line in step_yaml.split('\n'):
                    if line.strip():
                        print(f"   {line}")
        
        print(f"\n{Colors.BLUE}💡 CORREÇÃO:{Colors.RESET}")
        print(f"   Arquivo: {self.yaml_file}")
        print(f"   Passo: {step_state.get('step_number', '?') if step_state else error_data.get('step_number', '?')}")
        print(f"{Colors.RED}{'='*80}{Colors.RESET}\n")
    
    def wait_for_yaml_fix(self):
        """Aguarda correção do YAML (detecta mudança no arquivo)."""
        if not self.yaml_file.exists():
            return
        
        initial_mtime = self.yaml_file.stat().st_mtime
        max_wait = 300  # 5 minutos máximo
        waited = 0
        
        print(f"{Colors.CYAN}👀 Monitorando mudanças no YAML...{Colors.RESET}")
        
        while waited < max_wait:
            if self.yaml_file.exists():
                current_mtime = self.yaml_file.stat().st_mtime
                if current_mtime > initial_mtime:
                    print(f"{Colors.GREEN}✅ YAML modificado detectado!{Colors.RESET}")
                    print(f"{Colors.CYAN}💡 Hot-reload aplicará as mudanças automaticamente...{Colors.RESET}\n")
                    time.sleep(1)  # Dar tempo para hot-reload processar
                    return
            
            # Verificar se processo ainda está rodando
            if self.process.poll() is not None:
                return
            
            time.sleep(1)
            waited += 1
            
            # Mostrar progresso a cada 10 segundos
            if waited % 10 == 0:
                print(f"{Colors.CYAN}⏳ Aguardando... ({waited}s){Colors.RESET}")
        
        print(f"{Colors.YELLOW}⚠️  Timeout aguardando correção{Colors.RESET}")


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Auto-fix test runner")
    parser.add_argument("yaml_file", help="Arquivo YAML do teste")
    parser.add_argument("--base-url", default="http://localhost:18069")
    parser.add_argument("--max-fixes", type=int, default=10, help="Máximo de correções automáticas")
    parser.add_argument("--headless", action="store_true", default=True, help="Executar em modo headless (padrão: True)")
    parser.add_argument("--no-headless", dest="headless", action="store_false", help="Não executar em modo headless")
    
    args = parser.parse_args()
    
    yaml_file = Path(args.yaml_file).absolute()
    if not yaml_file.exists():
        print(f"❌ Arquivo não encontrado: {yaml_file}")
        sys.exit(1)
    
    runner = AutoFixRunner(
        yaml_file,
        base_url=args.base_url,
        max_fixes=args.max_fixes,
        headless=args.headless
    )
    sys.exit(runner.run())


if __name__ == "__main__":
    main()

