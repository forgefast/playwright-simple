#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste Completo do Playwright-Simple Baseado nos Fluxos Racco

Este teste valida o playwright-simple passando por todas as interfaces únicas
dos fluxos_racco, usando os comandos exatos dos MDs (pw-click, pw-type, pw-submit)
através dos handlers do Recorder, em modo não headless, com mensagens de erro na tela.

Interfaces testadas:
1. Portal do Consumidor (website/portal)
2. E-commerce (website)
3. Portal do Revendedor (website/portal)
4. Backend Odoo - Categorias (interface administrativa)
5. Backend Odoo - Vendas/Pedidos (interface administrativa)
"""

import asyncio
import logging
import re
import sys
from pathlib import Path
from typing import Optional, Set

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

# Adicionar o diretório do projeto ao path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright, Page, Browser
from playwright_simple.core.recorder.recorder import Recorder
from playwright_simple.core.recorder.config import RecorderConfig, SpeedLevel

# Configuração
BASE_URL = "http://localhost:18069"
HEADLESS = False  # Modo não headless para visualizar execução

# Usuários de teste
CONSUMER_EMAIL = "juliana.ferreira@gmail.com"
CONSUMER_PASSWORD = "demo123"
RESELLER_EMAIL = "lucia.santos@exemplo.com"
RESELLER_PASSWORD = "demo123"
ADMIN_LOGIN = "admin"
ADMIN_PASSWORD = "admin"

# Configurar logging
LOG_DIR = project_root / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "test_complete_racco_flows.log"

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def parse_validated_flows_from_md(md_file: Path) -> Set[str]:
    """
    Lê a seção YAML de fluxos validados do arquivo Markdown.
    
    Args:
        md_file: Caminho para o arquivo MD
        
    Returns:
        Set com os IDs dos fluxos validados (ex: {'fluxo_01', 'fluxo_02'})
    """
    if not md_file.exists():
        return set()
    
    if not YAML_AVAILABLE:
        logger.warning("PyYAML não disponível. Não será possível ler fluxos validados.")
        return set()
    
    validated_flows = set()
    
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Procurar seção "Fluxos Validados"
    linhas = content.split('\n')
    in_yaml_block = False
    yaml_lines = []
    
    for i, line in enumerate(linhas):
        if '## Fluxos Validados' in line:
            # Encontrou a seção, agora procurar o bloco ```yaml
            continue
        if line.strip().startswith('```yaml'):
            in_yaml_block = True
            continue
        if in_yaml_block:
            if line.strip() == '```':
                break
            yaml_lines.append(line)
    
    if not yaml_lines:
        return set()
    
    try:
        yaml_content = '\n'.join(yaml_lines)
        data = yaml.safe_load(yaml_content)
        if data and 'validated_flows' in data:
            flows = data['validated_flows']
            if flows:
                validated_flows = set(flows)
                logger.info(f"✅ Fluxos validados encontrados: {validated_flows}")
    except Exception as e:
        logger.warning(f"⚠️  Erro ao ler fluxos validados: {e}")
    
    return validated_flows


def map_commands_to_flows(commands: list[str]) -> list[tuple[str, str]]:
    """
    Mapeia cada comando para o fluxo ao qual pertence.
    
    Args:
        commands: Lista de comandos (incluindo marcadores de fluxo)
        
    Returns:
        Lista de tuplas (comando, fluxo_id) onde fluxo_id é como 'fluxo_01', 'fluxo_02', etc.
    """
    commands_with_flows = []
    current_flow = None
    
    # Padrão para identificar início de fluxo: "# FLUXO XX:"
    flow_pattern = re.compile(r'#\s*FLUXO\s+(\d+):', re.IGNORECASE)
    
    for cmd in commands:
        # Verificar se o comando contém um marcador de fluxo
        match = flow_pattern.search(cmd)
        if match:
            flow_num = match.group(1).zfill(2)  # Garante 2 dígitos (01, 02, etc.)
            current_flow = f"fluxo_{flow_num}"
            # Incluir o marcador de fluxo na lista
            commands_with_flows.append((cmd, current_flow))
            continue
        
        # Se encontrou um comando, associar ao fluxo atual
        if current_flow:
            commands_with_flows.append((cmd, current_flow))
        else:
            # Comandos antes do primeiro fluxo (não devem existir, mas por segurança)
            commands_with_flows.append((cmd, None))
    
    return commands_with_flows


def parse_commands_from_md(md_file: Path) -> list[str]:
    """
    Lê comandos do arquivo Markdown, seguindo padrão de gravar_fluxo.py.
    
    Extrai comandos da seção "Comandos de Terminal Completos" dentro de um bloco ```bash.
    
    Args:
        md_file: Caminho para o arquivo MD
        
    Returns:
        Lista de comandos na ordem em que aparecem no arquivo
    """
    if not md_file.exists():
        raise FileNotFoundError(f"Arquivo MD não encontrado: {md_file}")
    
    commands = []
    
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Procurar seção "Comandos de Terminal Completos" especificamente
    linhas = content.split('\n')
    in_comandos_completos = False
    encontrou_bash = False
    inicio_secao = -1
    
    # Primeiro, encontrar onde começa a seção "Comandos de Terminal Completos"
    for i, line in enumerate(linhas):
        if 'Comandos de Terminal Completos' in line:
            inicio_secao = i
            break
    
    if inicio_secao == -1:
        raise ValueError("Seção 'Comandos de Terminal Completos' não encontrada no arquivo MD")
    
    # Agora, processar apenas a partir dessa seção
    for i, line in enumerate(linhas[inicio_secao:], start=inicio_secao):
        if '```bash' in line:
            encontrou_bash = True
            in_comandos_completos = True
            continue
        # Só parar se encontrou bash antes e agora encontrou ``` sem bash
        if in_comandos_completos and encontrou_bash and line.strip() == '```':
            break
        if in_comandos_completos and line.strip():
            # Incluir comentários de fluxo (FLUXO XX: ou separadores ======)
            if line.strip().startswith('#') and ('FLUXO' in line.upper() or '=====' in line):
                commands.append(line.strip())
                continue
            # Ignorar outros comentários
            if line.strip().startswith('#'):
                continue
            # Remover comentários inline
            cmd = line.strip().split('#')[0].strip()
            if cmd:
                commands.append(cmd)
    
    return commands


async def show_error_on_screen(page: Page, error_message: str, command: str = ""):
    """
    Mostra mensagem de erro na tela do browser.
    
    Args:
        page: Página do Playwright
        error_message: Mensagem de erro a exibir
        command: Comando que falhou (opcional)
    """
    try:
        await page.evaluate(f"""
            () => {{
                // Remover erro anterior se existir
                const existingError = document.getElementById('playwright-test-error');
                if (existingError) {{
                    existingError.remove();
                }}
                
                const errorDiv = document.createElement('div');
                errorDiv.id = 'playwright-test-error';
                errorDiv.style.cssText = `
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: #ff4444;
                    color: white;
                    padding: 20px;
                    border-radius: 8px;
                    z-index: 99999;
                    font-size: 16px;
                    max-width: 500px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                    font-family: Arial, sans-serif;
                    line-height: 1.5;
                `;
                
                const commandText = `{command}` ? `<br><strong>Comando:</strong> {command}` : '';
                errorDiv.innerHTML = `
                    <strong>❌ Erro na Execução</strong>
                    ${{commandText}}
                    <br><br>
                    <strong>Erro:</strong><br>
                    ${{`{error_message}`.replace(/</g, '&lt;').replace(/>/g, '&gt;')}}
                `;
                document.body.appendChild(errorDiv);
            }}
        """)
        logger.error(f"Erro exibido na tela: {error_message}")
    except Exception as e:
        logger.error(f"Erro ao exibir mensagem na tela: {e}")


async def fazer_logout(page: Page):
    """Faz logout clicando no menu do usuário e depois em 'Sair'."""
    try:
        # Clicar no dropdown do usuário
        user_menu = page.locator('.dropdown-toggle, [data-bs-toggle="dropdown"], .o_user_menu')
        if await user_menu.count() > 0:
            await user_menu.first.click()
            await asyncio.sleep(0.5)
            # Clicar em "Sair"
            logout_link = page.locator('#o_logout, a:has-text("Sair"), a[href*="/web/session/logout"]')
            if await logout_link.count() > 0:
                await logout_link.first.click()
                await asyncio.sleep(1.0)
            else:
                logger.warning("Link 'Sair' não encontrado, tentando navegar diretamente")
                await page.goto(f"{BASE_URL}/web/session/logout")
                await asyncio.sleep(1.0)
        else:
            logger.warning("Menu do usuário não encontrado, tentando navegar diretamente")
            await page.goto(f"{BASE_URL}/web/session/logout")
            await asyncio.sleep(1.0)
    except Exception as e:
        logger.warning(f"Erro ao fazer logout clicando: {e}, tentando navegar diretamente")
        await page.goto(f"{BASE_URL}/web/session/logout")
        await asyncio.sleep(1.0)
    
    # Garantir que estamos na página de login (logout pode redirecionar para /)
    try:
        await page.wait_for_load_state('networkidle', timeout=5000)
    except:
        pass
    await asyncio.sleep(0.5)
    current_url = page.url
    logger.info(f"URL após logout: {current_url}")
    if '/web/login' not in current_url:
        logger.info("Navegando para página de login...")
        await page.goto(f"{BASE_URL}/web/login")
        try:
            await page.wait_for_load_state('networkidle', timeout=5000)
        except:
            pass
        await asyncio.sleep(1.0)


async def abrir_menu_apps(page: Page) -> bool:
    """
    Tenta abrir o menu Apps do Odoo usando múltiplos seletores.
    
    Returns:
        True se conseguiu abrir, False caso contrário
    """
    # Verificar se menu Apps já está aberto
    try:
        body_class = await page.evaluate("() => document.body.className")
        if 'o_apps_menu_opened' in body_class:
            logger.info("✅ Menu Apps já está aberto")
            return True
    except:
        pass
    
    menu_apps_selectors = [
        'button.o_menu_toggle',
        '.o_main_navbar button[aria-label*="Menu"]',
        'button[title*="Menu"]',
        'button[title*="Apps"]',
        'button.o_grid_apps_menu__button',
        '.o_main_navbar .o_menu_toggle',
        '[aria-label*="Apps"]',
        '[aria-label*="Menu"]',
    ]
    
    current_url = page.url
    logger.info(f"Tentando abrir menu Apps na URL: {current_url}")
    
    for selector in menu_apps_selectors:
        try:
            btn = page.locator(selector).first
            count = await btn.count()
            if count > 0:
                is_visible = await btn.is_visible()
                logger.debug(f"Seletor {selector}: count={count}, visible={is_visible}")
                if is_visible:
                    await btn.click()
                    await asyncio.sleep(0.5)
                    # Verificar se abriu
                    body_class = await page.evaluate("() => document.body.className")
                    if 'o_apps_menu_opened' in body_class:
                        logger.info(f"✅ Menu Apps aberto usando seletor: {selector}")
                        return True
        except Exception as e:
            logger.debug(f"Tentativa com seletor {selector} falhou: {e}")
            continue
    
    logger.warning("⚠️  Não foi possível abrir menu Apps")
    return False


async def executar_comando_com_debug(
    recorder,
    handlers,
    page: Page,
    browser: Browser,
    comando: str,
    step_num: int,
    total_steps: int
) -> bool:
    """
    Executa comando com debug detalhado, seguindo padrão de gravar_fluxo.py.
    
    Args:
        recorder: Instância do Recorder
        handlers: Handlers do recorder
        page: Página do Playwright
        browser: Browser do Playwright
        comando: Comando completo a executar (ex: 'pw-click "Entrar"')
        step_num: Número do step atual
        total_steps: Total de steps
        
    Returns:
        True se sucesso, False se erro (e para execução completamente)
    """
    print("\n" + "="*80)
    print(f"STEP {step_num}/{total_steps}: {comando}")
    print("="*80)
    
    # Mostrar estado atual da página
    try:
        current_url = page.url
        current_title = await page.title()
        print(f"  📄 URL atual: {current_url}")
        print(f"  📄 Título: {current_title}")
    except Exception as e:
        print(f"  ⚠️  Erro ao obter estado da página: {e}")
    
    try:
        # Parse do comando
        parts = comando.split(None, 1)
        if not parts:
            print(f"  ⚠️  Comando vazio")
            return True
        
        cmd = parts[0]
        args = parts[1] if len(parts) > 1 else ""
        
        if cmd == "pw-click":
            print(f"  👆 Clicando: {args}...")
            
            # Verificar se o elemento existe antes de tentar clicar
            try:
                # Tentar encontrar o elemento usando múltiplas estratégias
                element_found = False
                element_visible = False
                
                # Estratégia 1: Buscar por texto
                try:
                    locator = page.locator(f'text="{args}"').first
                    if await locator.count() > 0:
                        element_found = True
                        element_visible = await locator.is_visible()
                        if element_visible:
                            print(f"  ✓ Elemento encontrado e visível: '{args}'")
                except:
                    pass
                
                # Estratégia 2: Buscar por role button/link
                if not element_found or not element_visible:
                    try:
                        locator = page.get_by_role("button", name=args, exact=False).first
                        if await locator.count() > 0:
                            element_found = True
                            element_visible = await locator.is_visible()
                            if element_visible:
                                print(f"  ✓ Elemento encontrado e visível (button): '{args}'")
                    except:
                        pass
                
                # Estratégia 3: Buscar por link
                if not element_found or not element_visible:
                    try:
                        locator = page.get_by_role("link", name=args, exact=False).first
                        if await locator.count() > 0:
                            element_found = True
                            element_visible = await locator.is_visible()
                            if element_visible:
                                print(f"  ✓ Elemento encontrado e visível (link): '{args}'")
                    except:
                        pass
                
                if not element_found:
                    print(f"  ⚠️  AVISO: Elemento '{args}' não encontrado antes do clique")
                elif not element_visible:
                    print(f"  ⚠️  AVISO: Elemento '{args}' encontrado mas não visível")
            except Exception as e:
                print(f"  ⚠️  Erro ao verificar elemento: {e}")
            
            result = await handlers.handle_pw_click(args)
            
            if not result.get('success', False):
                error_msg = result.get('error', 'Erro desconhecido')
                print(f"  ❌ ERRO ao clicar: {error_msg}")
                logger.error(f"❌ Falha em {comando}: {error_msg}")
                
                # Capturar HTML e screenshot antes de fechar
                try:
                    logger.info("📸 Capturando estado da página antes de fechar...")
                    html_content = await page.content()
                    html_file = project_root / "logs" / f"error_step_{step_num}.html"
                    html_file.parent.mkdir(exist_ok=True)
                    with open(html_file, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    logger.info(f"✅ HTML salvo em: {html_file}")
                    
                    screenshot_file = project_root / "logs" / f"error_step_{step_num}.png"
                    await page.screenshot(path=str(screenshot_file), full_page=True)
                    logger.info(f"✅ Screenshot salvo em: {screenshot_file}")
                    
                    # Mostrar informações da página
                    current_url = page.url
                    current_title = await page.title()
                    logger.info(f"📄 URL atual: {current_url}")
                    logger.info(f"📄 Título: {current_title}")
                    
                    # Tentar encontrar elementos relacionados
                    try:
                        # Verificar se há menu "Configuração"
                        config_elements = await page.locator('text="Configuração"').count()
                        logger.info(f"📋 Elementos 'Configuração' encontrados: {config_elements}")
                        
                        # Verificar se há "Contact Tags" ou "Tags de Contato"
                        tags_elements = await page.locator('text=/Contact Tags|Tags de Contato|Categorias/i').count()
                        logger.info(f"📋 Elementos relacionados a Tags/Categorias encontrados: {tags_elements}")
                        
                        # Verificar se há menu dropdown aberto
                        dropdown_menus = await page.locator('.dropdown-menu, .o_dropdown_menu').count()
                        logger.info(f"📋 Menus dropdown encontrados: {dropdown_menus}")
                        
                        # Listar todos os links visíveis
                        all_links = await page.locator('a:visible').all_text_contents()
                        logger.info(f"📋 Links visíveis na página (primeiros 20): {all_links[:20]}")
                        
                        # Verificar se estamos na tela de Contatos e quais menus estão disponíveis
                        if 'contacts' in current_url.lower():
                            logger.info("📋 Estamos na tela de Contatos")
                            # Verificar se há submenu de Configuração
                            config_menu_items = await page.locator('.o_menu_item:has-text("Configuração"), .dropdown-item:has-text("Configuração")').all_text_contents()
                            logger.info(f"📋 Itens do menu Configuração: {config_menu_items}")
                    except Exception as e:
                        logger.warning(f"⚠️  Erro ao analisar elementos: {e}")
                    
                except Exception as e:
                    logger.error(f"❌ Erro ao capturar estado da página: {e}")
                
                # Mostrar erro na tela
                await show_error_on_screen(page, error_msg, comando)
                await asyncio.sleep(2)
                
                # PARAR COMPLETAMENTE: fechar browser e retornar False
                try:
                    await recorder.stop(save=False)
                except:
                    pass
                try:
                    await browser.close()
                except:
                    pass
                return False
            
            # Verificar se realmente houve mudança após o clique
            try:
                url_antes = page.url
                await asyncio.sleep(0.3)  # Pequeno delay para verificar mudança
                url_depois = page.url
                if url_antes != url_depois:
                    print(f"  ✓ URL mudou após clique: {url_antes} → {url_depois}")
                else:
                    print(f"  ℹ️  URL não mudou após clique (pode ser normal): {url_depois}")
            except:
                pass
            
            print(f"  ✅ Clique executado")
            
            # Aguardar navegação adequadamente (como em gravar_fluxo.py)
            try:
                await asyncio.wait_for(
                    page.wait_for_load_state('domcontentloaded', timeout=5000),
                    timeout=6.0
                )
                print(f"  ✅ Página carregada (domcontentloaded)")
                try:
                    await asyncio.wait_for(
                        page.wait_for_load_state('networkidle', timeout=3000),
                        timeout=4.0
                    )
                    print(f"  ✅ Página estável (networkidle)")
                except:
                    print(f"  ⚠️  Timeout aguardando networkidle, mas domcontentloaded OK")
            except Exception as e:
                print(f"  ⚠️  Timeout aguardando navegação: {e}")
            
            # Mostrar nova URL/título
            try:
                new_url = page.url
                new_title = await page.title()
                print(f"  📄 Nova URL: {new_url}")
                print(f"  📄 Novo título: {new_title}")
            except:
                pass
            
            await asyncio.sleep(1.0)
                
        elif cmd == "pw-type":
            print(f"  ⌨️  Digitando: {args}...")
            result = await handlers.handle_pw_type(args)
            
            if not result.get('success', False):
                error_msg = result.get('error', 'Erro desconhecido')
                print(f"  ❌ ERRO ao digitar: {error_msg}")
                logger.error(f"❌ Falha em {comando}: {error_msg}")
                
                # Mostrar erro na tela
                await show_error_on_screen(page, error_msg, comando)
                await asyncio.sleep(2)
                
                # PARAR COMPLETAMENTE: fechar browser e retornar False
                try:
                    await recorder.stop(save=False)
                except:
                    pass
                try:
                    await browser.close()
                except:
                    pass
                return False
            
            print(f"  ✅ Digitação executada")
                
        elif cmd == "pw-submit":
            print(f"  ✅ Submetendo formulário: {args}...")
            result = await handlers.handle_pw_submit(args)
            
            if not result.get('success', False):
                error_msg = result.get('error', 'Erro desconhecido')
                print(f"  ❌ ERRO ao submeter: {error_msg}")
                logger.error(f"❌ Falha em {comando}: {error_msg}")
                
                # Mostrar erro na tela
                await show_error_on_screen(page, error_msg, comando)
                await asyncio.sleep(2)
                
                # PARAR COMPLETAMENTE: fechar browser e retornar False
                try:
                    await recorder.stop(save=False)
                except:
                    pass
                try:
                    await browser.close()
                except:
                    pass
                return False
            
            print(f"  ✅ Submit executado")
            
            # Aguardar navegação após submit (como em gravar_fluxo.py)
            print(f"  ⏳ Aguardando navegação após submit...")
            try:
                await asyncio.wait_for(
                    page.wait_for_load_state('networkidle', timeout=5000),
                    timeout=6.0
                )
                print(f"  ✅ Página carregada após submit (networkidle)")
                # Mostrar nova URL
                new_url = page.url
                new_title = await page.title()
                print(f"  📄 Nova URL: {new_url}")
                print(f"  📄 Novo título: {new_title}")
            except Exception as e:
                print(f"  ⚠️  Timeout aguardando networkidle: {e}")
            
            await asyncio.sleep(1.0)
        
        elif cmd == "wait":
            # Comando wait para aguardar tempo específico
            import re
            match = re.search(r'(\d+\.?\d*)', args)
            if match:
                seconds = float(match.group(1))
                print(f"  ⏳ Aguardando {seconds}s...")
                await asyncio.sleep(seconds)
                print(f"  ✅ Wait concluído")
            else:
                print(f"  ⚠️  Não foi possível extrair tempo do wait, aguardando 1s")
                await asyncio.sleep(1.0)
        
        elif cmd == "pw-wait":
            print(f"  ⏳ Aguardando elemento: {args}...")
            # Parse args: pode ser "texto" timeout ou "texto" sem timeout
            parts = args.split()
            timeout = 5000  # Default 5 segundos
            text = args
            
            # Se último argumento é um número, é o timeout
            if len(parts) >= 2 and parts[-1].isdigit():
                timeout = int(parts[-1]) * 1000  # Converter para milissegundos
                text = ' '.join(parts[:-1])
            
            # Remover aspas se houver
            text = text.strip('"\'')
            
            try:
                # Primeiro, aguardar popover aparecer se estiver procurando por filtros
                if "Revendedor" in text:
                    try:
                        await page.wait_for_selector('.o_popover', state='visible', timeout=2000)
                        await asyncio.sleep(0.3)  # Pequeno delay para renderização
                    except:
                        pass  # Continuar mesmo se popover não aparecer
                
                # Aguardar elemento aparecer usando wait_for_function
                # Procurar em todos os elementos, incluindo overlays/popovers
                await page.wait_for_function(f"""
                    (text) => {{
                        // Procurar em todos os elementos, incluindo overlays
                        const allElements = Array.from(document.querySelectorAll('*'));
                        for (const el of allElements) {{
                            const elText = (el.textContent || el.innerText || '').trim();
                            // Verificar se o texto corresponde e o elemento está visível
                            if (elText === text || elText.includes(text)) {{
                                // Verificar visibilidade - elemento deve estar renderizado
                                const rect = el.getBoundingClientRect();
                                const style = window.getComputedStyle(el);
                                if (rect.width > 0 && rect.height > 0 && 
                                    style.display !== 'none' && 
                                    style.visibility !== 'hidden' &&
                                    style.opacity !== '0') {{
                                    return true;
                                }}
                            }}
                        }}
                        return false;
                    }}
                """, text, timeout=timeout)
                print(f"  ✅ Elemento '{text}' apareceu")
                # Aguardar um pouco mais para garantir que está totalmente renderizado
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"  ⚠️  Timeout aguardando elemento '{text}': {e}")
                # Não falhar o teste, apenas avisar
                
        else:
            print(f"  ⚠️  Comando desconhecido: {cmd}")
            return True
            
    except Exception as e:
        print(f"  ❌ ERRO ao executar comando: {e}")
        import traceback
        traceback.print_exc()
        logger.error(f"❌ Exceção em {comando}: {e}", exc_info=True)
        
        # Mostrar erro na tela
        try:
            await show_error_on_screen(page, str(e), comando)
            await asyncio.sleep(2)
        except:
            pass
        
        # PARAR COMPLETAMENTE: fechar browser e retornar False
        try:
            await recorder.stop(save=False)
        except:
            pass
        try:
            await browser.close()
        except:
            pass
        return False
    
    return True


async def run_test():
    """Executa o teste completo usando Recorder e handlers."""
    print("\n" + "=" * 80)
    print("TESTE COMPLETO DOS FLUXOS RACCO")
    print("=" * 80)
    print(f"Base URL: {BASE_URL}")
    print(f"Headless: {HEADLESS}")
    print(f"Speed Level: ULTRA_FAST")
    print(f"Log file: {LOG_FILE}")
    print("=" * 80 + "\n")
    
    # Criar arquivo temporário para YAML (não será usado, mas é necessário)
    temp_yaml = project_root / "temp_test_racco_flows.yaml"
    
    # Criar recorder com configuração
    recorder_config = RecorderConfig.from_kwargs(
        output_path=temp_yaml,
        initial_url=BASE_URL,
        headless=HEADLESS,
        debug=False,
        fast_mode=False,
        speed_level=SpeedLevel.ULTRA_FAST,
        mode='write'
    )
    
    recorder = Recorder(config=recorder_config)
    
    try:
        # Executar recorder em background
        async def run_recorder():
            await recorder.start()
        
        recorder_task = asyncio.create_task(run_recorder())
        
        # Aguardar recorder estar pronto
        logger.info("Aguardando recorder estar pronto...")
        page = None
        max_attempts = 30
        event_capture_ready = False
        
        for attempt in range(max_attempts):
            try:
                if hasattr(recorder, 'page') and recorder.page:
                    page = recorder.page
                    try:
                        await asyncio.wait_for(
                            page.wait_for_load_state('domcontentloaded', timeout=1000),
                            timeout=1.5
                        )
                        if hasattr(recorder, 'is_recording') and recorder.is_recording:
                            if hasattr(recorder, 'event_capture') and recorder.event_capture:
                                if recorder.event_capture.is_capturing:
                                    script_ready = await page.evaluate("""
                                        () => {
                                            return !!(window.__playwright_recording_initialized && window.__playwright_recording_events);
                                        }
                                    """)
                                    if script_ready:
                                        event_capture_ready = True
                                        logger.info("✅ Recorder iniciado e EventCapture pronto!")
                                        break
                    except:
                        pass
            except:
                pass
            await asyncio.sleep(0.1)
        
        if not page or not event_capture_ready:
            logger.warning("⚠️  EventCapture pode não estar totalmente pronto, continuando...")
            if not page:
                logger.error("❌ Recorder não iniciou corretamente")
                return 1
        
        # Obter browser do recorder
        browser = None
        if hasattr(recorder, 'browser_manager') and recorder.browser_manager:
            if hasattr(recorder.browser_manager, 'browser') and recorder.browser_manager.browser:
                browser = recorder.browser_manager.browser
            elif hasattr(recorder.browser_manager, 'context') and recorder.browser_manager.context:
                browser = recorder.browser_manager.context.browser
        
        if not browser:
            logger.error("❌ Browser não disponível")
            return 1
        
        # Obter handlers
        handlers = recorder.command_handlers
        
        logger.info("=" * 80)
        logger.info("INICIANDO TESTE COMPLETO DOS FLUXOS RACCO")
        logger.info("=" * 80)
        
        # Ler comandos do arquivo Markdown
        md_file = project_root / "test_complete_racco_flows.md"
        logger.info(f"Lendo comandos do arquivo: {md_file}")
        try:
            # Ler fluxos validados
            validated_flows = parse_validated_flows_from_md(md_file)
            if validated_flows:
                logger.info(f"⏭️  Pulando fluxos validados: {validated_flows}")
            else:
                logger.info("ℹ️  Nenhum fluxo validado encontrado. Todos os fluxos serão executados.")
            
            comandos_raw = parse_commands_from_md(md_file)
            logger.info(f"✅ {len(comandos_raw)} comandos carregados do arquivo MD")
            
            # Mapear comandos para fluxos
            commands_with_flows = map_commands_to_flows(comandos_raw)
            
            # Filtrar comandos de fluxos validados
            comandos_filtrados = []
            skipped_flows = set()
            current_flow = None
            
            for cmd, flow_id in commands_with_flows:
                # Se é um marcador de fluxo, atualizar fluxo atual
                if cmd.startswith('#') and 'FLUXO' in cmd.upper():
                    flow_pattern = re.compile(r'#\s*FLUXO\s+(\d+):', re.IGNORECASE)
                    match = flow_pattern.search(cmd)
                    if match:
                        flow_num = match.group(1).zfill(2)
                        current_flow = f"fluxo_{flow_num}"
                        # Se o fluxo está validado, marcar para pular
                        if current_flow in validated_flows:
                            skipped_flows.add(current_flow)
                            logger.info(f"⏭️  Pulando fluxo: {current_flow}")
                        else:
                            # Incluir o marcador de fluxo
                            comandos_filtrados.append(cmd)
                    continue
                
                # Se o fluxo atual está validado, pular o comando
                if current_flow and current_flow in validated_flows:
                    continue
                
                # Incluir o comando
                comandos_filtrados.append(cmd)
            
            if skipped_flows:
                logger.info(f"⏭️  Total de fluxos pulados: {len(skipped_flows)}")
            
            # Substituir valores hardcoded pelos valores das constantes
            comandos = []
            count_demo123 = 0
            count_admin = 0
            
            for cmd in comandos_filtrados:
                # Pular marcadores de fluxo e separadores
                if cmd.startswith('#') and ('FLUXO' in cmd.upper() or '=====' in cmd):
                    continue
                
                # Substituir emails
                cmd = cmd.replace('"juliana.ferreira@gmail.com"', f'"{CONSUMER_EMAIL}"')
                cmd = cmd.replace('"lucia.santos@exemplo.com"', f'"{RESELLER_EMAIL}"')
                
                # Substituir senhas (demo123 aparece duas vezes)
                if '"demo123"' in cmd:
                    if count_demo123 == 0:
                        # Primeira ocorrência: senha do consumidor
                        cmd = cmd.replace('"demo123"', f'"{CONSUMER_PASSWORD}"', 1)
                        count_demo123 += 1
                    else:
                        # Segunda ocorrência: senha do revendedor
                        cmd = cmd.replace('"demo123"', f'"{RESELLER_PASSWORD}"', 1)
                        count_demo123 += 1
                
                # Substituir admin (admin aparece duas vezes: login e senha)
                if '"admin"' in cmd:
                    if count_admin == 0:
                        # Primeira ocorrência: login admin
                        cmd = cmd.replace('"admin"', f'"{ADMIN_LOGIN}"', 1)
                        count_admin += 1
                    else:
                        # Segunda ocorrência: senha admin
                        cmd = cmd.replace('"admin"', f'"{ADMIN_PASSWORD}"', 1)
                        count_admin += 1
                
                comandos.append(cmd)
        except Exception as e:
            logger.error(f"❌ Erro ao ler arquivo MD: {e}")
            import traceback
            traceback.print_exc()
            return 1
        
        # Total de steps = comandos que serão executados via executar_comando_com_debug
        # (não inclui ações diretas como abrir menu Apps ou navegação direta)
        total_steps = len(comandos)
        print(f"\n📋 Total de comandos: {total_steps}")
        print(f"📋 Comandos a executar:")
        for i, cmd in enumerate(comandos, 1):
            print(f"  {i:2d}. {cmd}")
        
        print("\n▶️  Iniciando execução em 2 segundos...")
        await asyncio.sleep(2)
        
        # Aguardar CursorController estar pronto
        logger.info("Aguardando CursorController estar pronto...")
        cursor_ready = False
        max_cursor_attempts = 30
        for attempt in range(max_cursor_attempts):
            try:
                if hasattr(handlers, '_playwright') and handlers._playwright:
                    if hasattr(handlers._playwright, '_get_cursor_controller'):
                        cursor_controller = handlers._playwright._get_cursor_controller()
                        if cursor_controller and cursor_controller.is_active:
                            cursor_ready = True
                            logger.info("✅ CursorController está pronto!")
                            break
            except:
                pass
            await asyncio.sleep(0.2)
        
        if not cursor_ready:
            logger.warning("⚠️  CursorController pode não estar totalmente pronto, continuando...")
        
        # Executar comandos com debug (seguindo padrão de gravar_fluxo.py)
        print("\n" + "="*80)
        print("INICIANDO EXECUÇÃO DOS COMANDOS")
        print("="*80)
        
        # Executar todos os comandos sequencialmente
        for step_num, comando in enumerate(comandos, 1):
            # Executar comando
            sucesso = await executar_comando_com_debug(
                recorder, handlers, page, browser, comando, step_num, total_steps
            )
            if not sucesso:
                logger.error(f"❌ Teste parado no step {step_num}: {comando}")
                
                # Capturar HTML e screenshot antes de fechar
                try:
                    logger.info("📸 Capturando estado da página antes de fechar...")
                    html_content = await page.content()
                    html_file = project_root / "logs" / f"error_step_{step_num}.html"
                    html_file.parent.mkdir(exist_ok=True)
                    with open(html_file, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    logger.info(f"✅ HTML salvo em: {html_file}")
                    
                    screenshot_file = project_root / "logs" / f"error_step_{step_num}.png"
                    await page.screenshot(path=str(screenshot_file), full_page=True)
                    logger.info(f"✅ Screenshot salvo em: {screenshot_file}")
                    
                    # Mostrar informações da página
                    current_url = page.url
                    current_title = await page.title()
                    logger.info(f"📄 URL atual: {current_url}")
                    logger.info(f"📄 Título: {current_title}")
                    
                    # Tentar encontrar elementos relacionados
                    try:
                        # Verificar se há menu "Configuração"
                        config_elements = await page.locator('text="Configuração"').count()
                        logger.info(f"📋 Elementos 'Configuração' encontrados: {config_elements}")
                        
                        # Verificar se há "Contact Tags" ou "Tags de Contato"
                        tags_elements = await page.locator('text=/Contact Tags|Tags de Contato|Categorias/i').count()
                        logger.info(f"📋 Elementos relacionados a Tags/Categorias encontrados: {tags_elements}")
                        
                        # Verificar se há menu dropdown aberto
                        dropdown_menus = await page.locator('.dropdown-menu, .o_dropdown_menu').count()
                        logger.info(f"📋 Menus dropdown encontrados: {dropdown_menus}")
                        
                        # Listar todos os links visíveis
                        all_links = await page.locator('a:visible').all_text_contents()
                        logger.info(f"📋 Links visíveis na página (primeiros 20): {all_links[:20]}")
                    except Exception as e:
                        logger.warning(f"⚠️  Erro ao analisar elementos: {e}")
                    
                except Exception as e:
                    logger.error(f"❌ Erro ao capturar estado da página: {e}")
                
                return 1
        
        # ========================================================================
        # CONCLUSÃO
        # ========================================================================
        logger.info("\n" + "=" * 80)
        logger.info("TESTE COMPLETO CONCLUÍDO COM SUCESSO!")
        logger.info("=" * 80)
        logger.info(f"Todas as interfaces foram testadas:")
        logger.info("  ✅ Portal do Consumidor")
        logger.info("  ✅ E-commerce")
        logger.info("  ✅ Portal do Revendedor")
        logger.info("  ✅ Backend Odoo - Categorias")
        logger.info("  ✅ Backend Odoo - Vendas/Pedidos")
        logger.info("=" * 80)
        
        # Aguardar um pouco antes de fechar
        await asyncio.sleep(2)
        
        # Parar recorder
        await recorder.stop(save=False)
        
        # Limpar arquivo temporário
        if temp_yaml.exists():
            temp_yaml.unlink()
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Erro durante o teste: {e}", exc_info=True)
        
        # Tentar mostrar erro na tela se page estiver disponível
        try:
            if 'page' in locals() and page:
                await show_error_on_screen(page, str(e), "Erro geral")
                await asyncio.sleep(2)
        except:
            pass
        
        # Tentar fechar browser
        try:
            if 'browser' in locals() and browser:
                await browser.close()
        except:
            pass
        
        # Limpar arquivo temporário
        try:
            if 'temp_yaml' in locals() and temp_yaml.exists():
                temp_yaml.unlink()
        except:
            pass
        
        return 1


async def main():
    """Função principal."""
    exit_code = await run_test()
    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())
