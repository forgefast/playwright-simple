# Manual do Usuário - Playwright Simple

**Versão**: 1.0.0  
**Data**: Novembro 2024

---

## 🚀 O que já está funcionando

Este manual descreve todas as funcionalidades que já estão implementadas e prontas para uso.

---

## 📦 Instalação

```bash
# Instalar dependências
cd playwright-simple
pip install -e ".[dev]"

# Instalar browsers do Playwright
playwright install chromium
```

---

## 🎬 Funcionalidade 1: Gravar Interações (RECORDER)

### O que faz
Grava suas interações no navegador e gera automaticamente um arquivo YAML com os passos.

### Como usar

```bash
# Gravar interações e gerar YAML
playwright-simple record meu_teste.yaml --url https://example.com

# Ou começar em página em branco
playwright-simple record meu_teste.yaml
```

### Durante a gravação

1. **O navegador abre** automaticamente
2. **Interaja normalmente**: clique, digite, navegue
3. **Use comandos no console**:
   - `save` - Salvar YAML sem parar (continua gravando)
   - `exit` - Sair e salvar
   - `pause` - Pausar gravação
   - `resume` - Retomar gravação
   - `caption "texto"` - Adicionar legenda
   - `audio "texto"` - Adicionar narração
   - `screenshot` - Tirar screenshot
   - `help` - Ver todos os comandos

### Exemplo de uso

```bash
# 1. Iniciar gravação
playwright-simple record login_test.yaml --url http://localhost:8069

# 2. No console, você verá:
# ✅ Recording started! Interact with the browser.
#    Type commands in the console (e.g., 'exit' to finish)

# 3. Interaja no navegador:
#    - Clique em botões
#    - Digite em campos
#    - Navegue entre páginas

# 4. Adicione legendas/áudio (opcional):
#    caption "Realizando login"
#    audio "Agora vou fazer login no sistema"

# 5. Salve e saia:
#    exit
```

### YAML gerado

O arquivo gerado será algo como:

```yaml
name: Gravação Automática
description: Gravação interativa do usuário - 2024-11-14 10:30:00
steps:
  - action: go_to
    url: http://localhost:8069
    description: Navegar para http://localhost:8069
  
  - action: click
    text: Entrar
    description: Clicar em 'Entrar'
  
  - action: type
    text: admin@example.com
    description: Campo 'E-mail'
  
  - caption: Realizando login
  
  - action: type
    text: senha123
    description: Campo 'Senha'
  
  - action: click
    text: Login
    description: Clicar em 'Login'
```

---

## ▶️ Funcionalidade 2: Executar Testes YAML

### O que faz
Executa testes definidos em YAML, com suporte a vídeo, legendas, áudio e screenshots.

### Como usar

```bash
# Executar teste básico
playwright-simple run meu_teste.yaml

# Com vídeo e legendas
playwright-simple run meu_teste.yaml --video --subtitles

# Com vídeo, legendas e áudio
playwright-simple run meu_teste.yaml --video --subtitles --audio

# Em modo não-headless (ver o browser)
playwright-simple run meu_teste.yaml --no-headless

# Com debug (pausa em erros)
playwright-simple run meu_teste.yaml --debug
```

### Exemplo de teste YAML

```yaml
name: Teste de Login
description: Teste automatizado de login

steps:
  - action: go_to
    url: http://localhost:8069
    
  - action: click
    text: Entrar
    description: Clicar em botão Entrar
    
  - action: type
    text: admin@example.com
    description: Campo 'E-mail'
    
  - action: type
    text: senha123
    description: Campo 'Senha'
    
  - action: click
    text: Login
    description: Clicar em Login
    
  - action: wait_for
    selector: .dashboard
    timeout: 5000
    description: Aguardar dashboard aparecer
    
  - action: assert_text
    selector: .welcome-message
    text: "Bem-vindo"
    description: Verificar mensagem de boas-vindas
```

### Opções disponíveis

```bash
# Ver todas as opções
playwright-simple run --help

# Opções principais:
--video              # Gravar vídeo
--audio              # Gerar áudio/narração
--subtitles          # Adicionar legendas
--screenshots        # Tirar screenshots automáticos
--no-headless        # Ver o browser (padrão)
--headless           # Executar sem ver o browser
--debug              # Modo debug (pausa em erros)
--viewport 1920x1080 # Tamanho da tela
--slow-mo 100        # Delay entre ações (ms)
```

---

## 🔧 Funcionalidade 3: Auto-Fix Inteligente

### O que faz
Tenta corrigir automaticamente erros nos testes, usando contexto completo (HTML, estado, histórico).

### Como funciona

Quando um teste falha, o sistema:
1. **Analisa o erro** (tipo, mensagem, contexto)
2. **Captura estado da página** (URL, título, HTML)
3. **Analisa HTML disponível** (botões, inputs, links)
4. **Sugere correções** (elementos similares, timeouts, etc.)
5. **Aplica correção automaticamente** (se possível)
6. **Tenta novamente**

### Exemplo

```yaml
steps:
  - action: click
    text: Entrar  # Se este botão não existir...
```

**Auto-fix detecta:**
- Botão "Entrar" não encontrado
- Mas encontrou botão "Login" similar
- **Corrige automaticamente**: `text: Login`
- **Tenta novamente**: ✅ Passa!

### Quando é ativado

- Automaticamente durante execução de testes
- Funciona com testes YAML
- Usa contexto completo para melhor precisão

---

## 📸 Funcionalidade 4: Comparação Visual de Screenshots

### O que faz
Compara screenshots entre execuções para detectar regressões visuais.

### Como usar

```python
from playwright_simple.core.visual_comparison import VisualComparison
from pathlib import Path

# Configurar
comparison = VisualComparison(
    baseline_dir=Path("screenshots/baseline"),
    current_dir=Path("screenshots/current"),
    diff_dir=Path("screenshots/diffs")
)

# Comparar um screenshot
result = comparison.compare_screenshot("login_page.png", threshold=0.01)

if result['match']:
    print("✅ Screenshots são idênticos")
else:
    print(f"❌ Diferença detectada: {result['difference']*100:.2f}%")
    print(f"   Diff salvo em: {result['diff_path']}")

# Comparar todos os screenshots
results = comparison.compare_all_screenshots(threshold=0.01)
print(f"Total: {results['summary']['total']}")
print(f"Match: {results['summary']['matches']}")
print(f"Diferenças: {results['summary']['differences']}")
```

### Atualizar baseline

```python
# Atualizar baseline (copiar current para baseline)
comparison.compare_screenshot("login_page.png", update_baseline=True)
```

---

## 🎯 Funcionalidade 5: Testes Genéricos (Core)

### Ações disponíveis

Todas estas ações funcionam para **qualquer aplicação web**:

#### Navegação
```yaml
- action: go_to
  url: /dashboard
  
- action: go_to
  url: http://example.com/page
```

#### Interações
```yaml
- action: click
  text: "Botão"  # Por texto (preferido)
  
- action: click
  selector: "#button-id"  # Por seletor CSS
  
- action: type
  text: "valor"
  selector: "input[name='email']"
  
- action: fill
  selector: "input[name='name']"
  text: "João Silva"
  
- action: select
  selector: "select[name='country']"
  value: "BR"
```

#### Esperas
```yaml
- action: wait
  seconds: 2
  
- action: wait_for
  selector: ".loading"
  timeout: 5000
  
- action: wait_for_text
  text: "Carregado"
  timeout: 10000
```

#### Assertions
```yaml
- action: assert_text
  selector: ".message"
  text: "Sucesso"
  
- action: assert_visible
  selector: ".dashboard"
  
- action: assert_url
  url: "/dashboard"
```

---

## 🔌 Funcionalidade 6: Extensão Odoo

### O que faz
Ações específicas para Odoo, usando sintaxe amigável.

### Ações Odoo disponíveis

#### Login
```yaml
- action: login
  login: admin
  password: admin
  database: devel  # Opcional
```

#### Navegação
```yaml
- action: go_to
  go_to: "Vendas > Pedidos"  # Navegação por menu
  
- action: go_to
  go_to: "Dashboard"  # Vai para dashboard
```

#### Preencher campos
```yaml
- action: fill
  fill: "Cliente = João Silva"  # Formato "Label = Valor"
  
- action: fill
  fill: "Data = 01/01/2024"
```

#### Clicar
```yaml
- action: click
  click: "Criar"  # Por texto do botão
  
- action: click
  click: "Salvar"
```

### Exemplo completo Odoo

```yaml
name: Criar Pedido de Venda
description: Teste de criação de pedido no Odoo

steps:
  - action: login
    login: admin
    password: admin
    database: devel
    
  - action: go_to
    go_to: "Vendas > Pedidos"
    
  - action: click
    click: "Criar"
    
  - action: fill
    fill: "Cliente = João Silva"
    
  - action: fill
    fill: "Data = 01/01/2024"
    
  - action: click
    click: "Salvar"
    
  - action: assert_text
    selector: ".o_notification"
    text: "Pedido criado"
```

---

## 📝 Funcionalidade 7: YAML Avançado

### Variáveis
```yaml
variables:
  email: admin@example.com
  password: senha123

steps:
  - action: type
    text: "{{ email }}"
    description: Campo 'E-mail'
```

### Loops
```yaml
steps:
  - for:
      var: user
      in: ["admin@example.com", "user@example.com"]
    steps:
      - action: click
        text: "Login"
      - action: type
        text: "{{ user }}"
```

### Condicionais
```yaml
steps:
  - if:
      condition: "{{ user_type }} == 'admin'"
    then:
      - action: go_to
        url: /admin
    else:
      - action: go_to
        url: /user
```

### Setup e Teardown
```yaml
setup:
  - action: login
    login: admin
    password: admin

steps:
  - action: go_to
    url: /dashboard

teardown:
  - action: logout
```

### Herança
```yaml
# common_login.yaml
steps:
  - action: login
    login: admin
    password: admin

# meu_teste.yaml
extends: common_login.yaml
steps:
  - action: go_to
    url: /dashboard
```

---

## 🎥 Funcionalidade 8: Vídeo, Legendas e Áudio

### Vídeo
```bash
# Gravar vídeo automaticamente
playwright-simple run teste.yaml --video
```

O vídeo será salvo em `videos/` com o nome do teste.

### Legendas
```yaml
steps:
  - action: click
    text: "Login"
    subtitle: "Clicando em Login"  # Legenda para este passo
```

Ou adicione legendas separadas:
```yaml
steps:
  - caption: "Iniciando processo de login"
  - action: click
    text: "Login"
```

### Áudio/Narração
```yaml
steps:
  - action: click
    text: "Login"
    audio: "Agora vou clicar no botão de login"  # Narração
```

### Executar com tudo
```bash
playwright-simple run teste.yaml --video --subtitles --audio
```

---

## 🐛 Funcionalidade 9: Debug e Hot Reload

### Modo Debug
```bash
# Pausa em erros para inspecionar
playwright-simple run teste.yaml --debug

# Pausa em breakpoints
playwright-simple run teste.yaml --debug --pause-on-error
```

### Breakpoints no YAML
```yaml
steps:
  - action: click
    text: "Login"
    breakpoint: true  # Pausa aqui
```

### Hot Reload
Durante a execução, você pode editar o YAML e o teste será recarregado automaticamente:

```bash
playwright-simple run teste.yaml --hot-reload
```

**Como funciona:**
1. Teste executa normalmente
2. Você edita o YAML
3. Sistema detecta mudança
4. Recarrega automaticamente
5. Continua de onde parou (ou reinicia, conforme configuração)

---

## 📊 Funcionalidade 10: Relatórios e Resultados

### Screenshots
```bash
# Screenshots automáticos
playwright-simple run teste.yaml --screenshots

# Screenshots salvos em: screenshots/{test_name}/
```

### Vídeo
```bash
# Vídeo salvo em: videos/{test_name}.mp4
playwright-simple run teste.yaml --video
```

### Logs
```bash
# Logs detalhados
playwright-simple run teste.yaml --log-level DEBUG

# Salvar logs em arquivo
playwright-simple run teste.yaml --log-file logs/teste.log
```

---

## 🎓 Exemplos Práticos

### Exemplo 1: Teste Simples de Login

```yaml
name: Login Simples
description: Teste básico de login

steps:
  - action: go_to
    url: http://localhost:8069
    
  - action: click
    text: Entrar
    
  - action: type
    text: admin@example.com
    selector: input[name="login"]
    
  - action: type
    text: senha123
    selector: input[name="password"]
    
  - action: click
    text: Login
    
  - action: wait_for
    selector: .dashboard
    timeout: 5000
```

**Executar:**
```bash
playwright-simple run login_simples.yaml --video
```

### Exemplo 2: Teste Odoo Completo

```yaml
name: Criar Pedido Odoo
description: Criar pedido de venda no Odoo

setup:
  - action: login
    login: admin
    password: admin
    database: devel

steps:
  - caption: "Acessando módulo de Vendas"
  - action: go_to
    go_to: "Vendas > Pedidos"
    
  - caption: "Criando novo pedido"
  - action: click
    click: "Criar"
    
  - audio: "Preenchendo dados do cliente"
  - action: fill
    fill: "Cliente = João Silva"
    
  - action: fill
    fill: "Data = 01/01/2024"
    
  - caption: "Salvando pedido"
  - action: click
    click: "Salvar"
    
  - action: assert_text
    selector: .o_notification
    text: "Pedido criado"

teardown:
  - action: logout
```

**Executar:**
```bash
playwright-simple run criar_pedido.yaml --video --subtitles --audio
```

### Exemplo 3: Teste com Loop

```yaml
name: Teste Múltiplos Usuários
description: Testar login com vários usuários

variables:
  password: senha123

steps:
  - for:
      var: user
      in: ["admin@example.com", "user@example.com", "guest@example.com"]
    steps:
      - action: go_to
        url: /login
        
      - action: type
        text: "{{ user }}"
        selector: input[name="email"]
        
      - action: type
        text: "{{ password }}"
        selector: input[name="password"]
        
      - action: click
        text: Login
        
      - action: wait_for
        selector: .dashboard
        timeout: 5000
        
      - action: click
        text: Logout
```

---

## 🔍 Troubleshooting

### Problema: "Element not found"

**Solução 1**: Adicionar wait
```yaml
- action: wait_for
  selector: .elemento
  timeout: 5000
- action: click
  text: "Botão"
```

**Solução 2**: Auto-fix tenta corrigir automaticamente
- Sistema detecta elemento similar
- Sugere correção
- Aplica automaticamente

### Problema: "Timeout"

**Solução**: Aumentar timeout
```yaml
- action: wait_for
  selector: .elemento
  timeout: 10000  # 10 segundos
```

### Problema: Vídeo não gerado

**Verificar:**
1. `--video` flag está presente?
2. Diretório `videos/` existe?
3. Permissões de escrita?

**Solução:**
```bash
mkdir -p videos
playwright-simple run teste.yaml --video
```

### Problema: Legendas não aparecem

**Verificar:**
1. `--subtitles` flag está presente?
2. Legendas definidas no YAML?

**Solução:**
```yaml
steps:
  - action: click
    text: "Login"
    subtitle: "Clicando em Login"  # Adicionar subtitle
```

---

## 📚 Recursos Adicionais

### Documentação
- `HYBRID_WORKFLOW.md` - Fluxo completo: gravar → editar → executar
- `IMPLEMENTATION_PLAN.md` - Plano de implementação completo
- `docs/` - Documentação técnica detalhada

### Exemplos
- `examples/` - Exemplos de testes YAML
- `examples/odoo/` - Exemplos específicos para Odoo

### Scripts Úteis
- `scripts/auto_fix_direct.py` - Auto-fix com IA
- `scripts/analyze_video.py` - Análise de vídeos gerados

---

## 🎯 Checklist de Teste

Use este checklist para testar as funcionalidades:

### Recorder
- [ ] Gravar interações básicas (clique, digite)
- [ ] Adicionar legendas durante gravação
- [ ] Adicionar áudio durante gravação
- [ ] Salvar YAML gerado
- [ ] Verificar YAML gerado está correto

### Execução
- [ ] Executar teste YAML básico
- [ ] Executar com vídeo
- [ ] Executar com legendas
- [ ] Executar com áudio
- [ ] Verificar vídeo gerado
- [ ] Verificar legendas no vídeo

### Auto-Fix
- [ ] Criar teste com elemento que não existe
- [ ] Verificar se auto-fix sugere correção
- [ ] Verificar se auto-fix aplica correção
- [ ] Verificar se teste passa após correção

### Odoo
- [ ] Login no Odoo
- [ ] Navegação por menu
- [ ] Preencher campos Odoo
- [ ] Clicar em botões Odoo
- [ ] Criar registro Odoo

### YAML Avançado
- [ ] Usar variáveis
- [ ] Usar loops
- [ ] Usar condicionais
- [ ] Usar setup/teardown
- [ ] Usar herança

---

## 💡 Dicas e Boas Práticas

1. **Sempre adicione descrições**: Facilita entender o que o teste faz
2. **Use legendas**: Melhoram muito a compreensão do vídeo
3. **Adicione waits**: Evita falhas por timing
4. **Use variáveis**: Facilita manutenção
5. **Teste incrementalmente**: Comece simples, depois adicione complexidade
6. **Use hot reload**: Durante desenvolvimento, facilita iteração rápida

---

## 🐛 Reportar Problemas

Ao encontrar problemas ou ter sugestões:

1. **Descreva o problema**: O que aconteceu vs o que esperava
2. **Inclua o YAML**: Se possível, compartilhe o YAML que causou o problema
3. **Inclua logs**: Use `--log-level DEBUG` e compartilhe os logs
4. **Sugestões**: O que você acha que poderia melhorar?

---

## 🚀 Próximos Passos

Conforme você testa, anote:
- ✅ O que funciona bem
- ⚠️ O que precisa melhorar
- 💡 Ideias para novas funcionalidades
- 🐛 Problemas encontrados

Essas informações serão usadas para:
- Melhorar funcionalidades existentes
- Planejar próximas fases
- Priorizar melhorias

---

**Última Atualização**: Novembro 2024

