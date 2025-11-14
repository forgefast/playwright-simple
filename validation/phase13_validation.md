# Plano de Validação - FASE 13: Interface de Comandos CLI para Gravação Ativa

## Objetivo

Validar que os comandos CLI funcionam corretamente durante uma gravação ativa, permitindo que IAs e usuários controlem o browser programaticamente.

---

## O que Deve Funcionar

### 1. Sistema de Comunicação IPC
- `CommandServer` deve iniciar quando gravação começa
- Arquivos de comunicação devem ser criados em `/tmp/playwright-simple/`
- Lock file deve indicar sessão ativa

### 2. Comandos CLI Disponíveis
- `playwright-simple find "texto"` - Encontrar elemento
- `playwright-simple find --selector "#id"` - Encontrar por seletor
- `playwright-simple find --role button` - Encontrar por role
- `playwright-simple click "texto"` - Clicar em elemento
- `playwright-simple click --selector "#id"` - Clicar por seletor
- `playwright-simple type "texto" --into "campo"` - Digitar texto
- `playwright-simple wait "texto" --timeout 10` - Esperar elemento
- `playwright-simple info` - Informações da página
- `playwright-simple html [--selector "#id"] [--pretty] [--max-length N]` - Obter HTML da página ou elemento

### 3. Interface PlaywrightCommands
- `PlaywrightCommands` deve estar disponível
- Métodos: `find_element()`, `click()`, `type_text()`, `wait_for_element()`, `get_page_info()`, `get_html()`

### 4. Melhorias na Captura
- Links (`<a>`) devem ser sempre capturados, mesmo sem texto visível
- Cliques iniciais devem ser capturados corretamente

---

## Como Validar Manualmente

### Passo 1: Iniciar Gravação

```bash
# Terminal 1
playwright-simple record test_cli.yaml --url localhost:18069
```

**Resultado Esperado**:
- Gravação inicia
- Mensagem: "✅ Recording started! Interact with the browser."
- Mensagem: "Or use CLI commands: playwright-simple find \"text\", playwright-simple click \"text\", etc."

### Passo 2: Verificar Arquivos IPC

```bash
# Terminal 2
ls -la /tmp/playwright-simple/
```

**Resultado Esperado**:
- Arquivo `recorder_<PID>.lock` existe
- Arquivo `recorder_<PID>.commands` existe
- Arquivo `recorder_<PID>.response` existe

### Passo 3: Testar Comando `find`

```bash
# Terminal 2
playwright-simple find "Entrar"
```

**Resultado Esperado**:
- ✅ Elemento encontrado com informações (tag, texto, id, classe, visível)
- Ou ❌ Elemento não encontrado (se não existir)

### Passo 4: Testar Comando `click`

```bash
# Terminal 2
playwright-simple click "Entrar"
```

**Resultado Esperado**:
- ✅ Clicado com sucesso
- Browser deve navegar para página de login

### Passo 5: Testar Comando `wait`

```bash
# Terminal 2
playwright-simple wait "E-mail" --timeout 10
```

**Resultado Esperado**:
- ✅ Elemento apareceu
- Ou ❌ Timeout se elemento não aparecer

### Passo 6: Testar Comando `type`

```bash
# Terminal 2
playwright-simple type "admin@example.com" --into "E-mail"
```

**Resultado Esperado**:
- ✅ Texto digitado com sucesso
- Campo deve estar preenchido no browser

### Passo 7: Testar Comando `info`

```bash
# Terminal 2
playwright-simple info
```

**Resultado Esperado**:
- 📄 Informações da página (URL, título, estado)

### Passo 8: Testar Comando `html`

```bash
# Terminal 2
# HTML da página inteira
playwright-simple html

# HTML de elemento específico
playwright-simple html --selector "#login-form"

# HTML formatado
playwright-simple html --pretty

# HTML com limite
playwright-simple html --max-length 5000

# Salvar em arquivo
playwright-simple html > page.html
```

**Resultado Esperado**:
- 📄 HTML exibido ou salvo
- Se grande, sugestão de salvar em arquivo

### Passo 9: Testar Múltiplos Comandos em Sequência

```bash
# Terminal 2
playwright-simple find "Entrar"
playwright-simple click "Entrar"
playwright-simple wait "E-mail" 10
playwright-simple type "admin@example.com" --into "E-mail"
playwright-simple type "senha123" --into "Senha"
playwright-simple click "Entrar"
```

**Resultado Esperado**:
- Todos os comandos executam com sucesso
- Browser navega e preenche campos corretamente

---

## Como Validar Automaticamente

### Teste 1: Verificar Módulos Existem

```python
def test_modules_exist():
    from playwright_simple.core.playwright_commands import PlaywrightCommands
    from playwright_simple.core.recorder.command_server import CommandServer, send_command
    assert PlaywrightCommands is not None
    assert CommandServer is not None
    assert send_command is not None
```

### Teste 2: Verificar CLI Tem Comandos

```python
def test_cli_has_commands():
    import subprocess
    result = subprocess.run(
        ['playwright-simple', 'find', '--help'],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert 'find' in result.stdout.lower()
```

### Teste 3: Verificar CommandServer Cria Arquivos

```python
def test_command_server_creates_files():
    from playwright_simple.core.recorder.command_server import CommandServer
    from playwright_simple.core.recorder.recorder import Recorder
    from pathlib import Path
    import tempfile
    
    # Mock recorder
    recorder = Recorder(Path('test.yaml'))
    server = CommandServer(recorder, session_id='test_session')
    
    # Verificar que arquivos seriam criados
    temp_dir = Path(tempfile.gettempdir()) / "playwright-simple"
    assert server.command_file.parent == temp_dir
    assert server.response_file.parent == temp_dir
    assert server.lock_file.parent == temp_dir
```

### Teste 4: Verificar PlaywrightCommands Interface

```python
def test_playwright_commands_interface():
    from playwright_simple.core.playwright_commands import PlaywrightCommands
    
    # Verificar que métodos existem
    assert hasattr(PlaywrightCommands, 'find_element')
    assert hasattr(PlaywrightCommands, 'find_all_elements')
    assert hasattr(PlaywrightCommands, 'click')
    assert hasattr(PlaywrightCommands, 'type_text')
    assert hasattr(PlaywrightCommands, 'wait_for_element')
    assert hasattr(PlaywrightCommands, 'get_page_info')
    assert hasattr(PlaywrightCommands, 'get_html')
    assert hasattr(PlaywrightCommands, 'navigate')
    assert hasattr(PlaywrightCommands, 'take_screenshot')
```

### Teste 5: Verificar Captura de Links

```python
def test_link_capture_improvement():
    # Verificar que event_capture.py tem lógica especial para links
    from pathlib import Path
    event_capture_file = Path("playwright_simple/core/recorder/event_capture.py")
    content = event_capture_file.read_text()
    
    # Verificar que links são sempre capturados
    assert "tag === 'A' && hasHref" in content
    assert "Always capture links" in content or "capture links" in content.lower()
```

---

## Como Garantir Compatibilidade Futura

### 1. Testes de Regressão

Criar testes que verificam:
- Comandos CLI ainda funcionam após mudanças
- Comunicação IPC não quebrou
- Interface `PlaywrightCommands` mantém compatibilidade

### 2. Documentação de API

Manter documentação atualizada:
- `docs/CLI_COMMANDS.md` - Comandos CLI
- `docs/PLAYWRIGHT_COMMANDS.md` - Interface programática

### 3. Versionamento

Se a interface mudar:
- Manter compatibilidade retroativa
- Adicionar warnings para APIs deprecadas
- Documentar mudanças em CHANGELOG

---

## Checklist de Validação

### Funcionalidades
- [ ] `CommandServer` inicia com gravação
- [ ] Arquivos IPC são criados corretamente
- [ ] Comando `find` funciona
- [ ] Comando `click` funciona
- [ ] Comando `type` funciona
- [ ] Comando `wait` funciona
- [ ] Comando `info` funciona
- [ ] Comando `html` funciona
- [ ] Comando `html` com `--selector` funciona
- [ ] Comando `html` com `--pretty` funciona
- [ ] Comando `html` com `--max-length` funciona
- [ ] Múltiplos comandos em sequência funcionam

### Interface Programática
- [ ] `PlaywrightCommands` está disponível
- [ ] Todos os métodos existem (incluindo `get_html`)
- [ ] Métodos retornam resultados corretos
- [ ] `get_html()` retorna HTML da página
- [ ] `get_html(selector="...")` retorna HTML do elemento
- [ ] `get_html(pretty=True)` formata HTML
- [ ] `get_html(max_length=N)` limita tamanho

### Melhorias
- [ ] Links são sempre capturados
- [ ] Cliques iniciais são capturados

### Documentação
- [ ] `CLI_COMMANDS.md` existe e está completo
- [ ] `PLAYWRIGHT_COMMANDS.md` existe e está completo
- [ ] Exemplos funcionam

### Testes
- [ ] Testes unitários passam
- [ ] Testes de integração passam
- [ ] Testes E2E passam (se aplicável)

---

## Problemas Conhecidos e Soluções

### Problema: "No active recording session found"

**Causa**: Gravação não está ativa ou processo morreu

**Solução**:
- Verificar se gravação está rodando
- Verificar se lock file existe em `/tmp/playwright-simple/`
- Reiniciar gravação se necessário

### Problema: Comandos não executam

**Causa**: Comunicação IPC quebrada

**Solução**:
- Verificar permissões em `/tmp/playwright-simple/`
- Verificar se arquivos de comando/resposta existem
- Verificar logs da gravação

### Problema: Timeout em comandos

**Causa**: Gravação não está processando comandos

**Solução**:
- Verificar se `CommandServer` está rodando
- Verificar logs da gravação
- Aumentar timeout se necessário

---

## Métricas de Sucesso

- ✅ Todos os comandos CLI funcionam
- ✅ Comunicação IPC estável
- ✅ Interface programática completa
- ✅ Documentação completa
- ✅ Testes passando
- ✅ Captura de cliques melhorada

---

**Última Atualização**: Janeiro 2025

