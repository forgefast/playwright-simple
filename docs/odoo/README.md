# Playwright Simple - Odoo Extra

O extra `playwright-simple[odoo]` fornece funcionalidades específicas para testar aplicações Odoo de forma **extremamente simples e intuitiva**, permitindo que QAs sem experiência em programação escrevam testes usando apenas o que veem na tela.

## Instalação

```bash
pip install playwright-simple[odoo]
```

## Características Principais

- **User-Friendly**: Use apenas labels visíveis e textos de botões
- **Detecção Automática**: Detecta automaticamente tipos de campos, wizards e contextos
- **Sem Seletores CSS**: Não precisa conhecer seletores técnicos
- **YAML Simples**: Escreva testes em YAML sem estruturas complexas
- **Mensagens de Erro Claras**: Erros explicam o que fazer

## Início Rápido

### Python - API User-Friendly

```python
from playwright_simple.odoo import OdooTestBase

async def test_sale_order(page, test: OdooTestBase):
    # Login
    await test.login("admin", "admin", database="devel")
    
    # Navegar (formato simples)
    await test.go_to("Vendas > Pedidos")
    
    # Clicar botão (apenas texto)
    await test.click("Criar")
    
    # Preencher campos (usando labels visíveis)
    await test.fill("Cliente = João Silva")
    await test.fill("Data", "01/01/2024")
    
    # Adicionar linha de produto
    await test.add_line("Adicionar linha")
    await test.fill("Produto", "Batom")
    await test.fill("Quantidade", "10")
    
    # Salvar
    await test.click("Salvar")
```

### YAML - Sintaxe User-Friendly

```yaml
name: Criar Pedido de Venda
steps:
  - login: admin
    password: admin
    database: devel
  
  - go_to: "Vendas > Pedidos"
  
  - click: "Criar"
  
  - fill: "Cliente = João Silva"
  
  - add_line: "Adicionar linha"
  
  - fill: "Produto = Batom"
  - fill: "Quantidade = 10"
  
  - click: "Salvar"
```

## API User-Friendly

### Navegação

```python
# Formato 1: String única com separador
await test.go_to("Vendas > Pedidos")

# Formato 2: Argumentos separados (compatibilidade)
await test.go_to_menu("Vendas", "Pedidos")

# Navegação User-Friendly (sem URLs técnicas)
await test.go_to("Dashboard")      # Vai para dashboard/home
await test.go_to("Menu principal") # Alias para Dashboard
await test.go_to("Portal")         # Vai para /my (portal do cliente)
await test.go_to("Loja")           # Vai para /shop (e-commerce)
await test.go_to("E-commerce")     # Alias para Loja

# Métodos específicos
await test.go_to_dashboard()       # Vai para dashboard
await test.go_to_home()            # Alias para go_to_dashboard()
```

### Clicar em Botões

```python
# Apenas texto do botão (detecção automática de wizard/form)
await test.click("Salvar")
await test.click("Confirmar")

# Especificar contexto se necessário
await test.click("Salvar", context="wizard")  # Apenas em wizard
await test.click("Salvar", context="form")    # Apenas em formulário
```

### Preencher Campos

```python
# Formato 1: "Label = Valor"
await test.fill("Cliente = João Silva")
await test.fill("Data = 01/01/2024")

# Formato 2: Label e valor separados
await test.fill("Cliente", "João Silva")
await test.fill("Quantidade", "10")

# Com contexto (quando há campos duplicados)
await test.fill("Nome", "João", context="Seção Cliente")
```

**Tipos de Campo Detectados Automaticamente:**
- Many2one (busca automática)
- Char/Text
- Integer/Float
- Date/Datetime
- Boolean (toggle automático)
- Selection (dropdown)
- HTML

### Adicionar Linhas em Tabelas

```python
# Auto-detecta botão de adicionar linha
await test.add_line()

# Ou especificar texto do botão
await test.add_line("Adicionar linha")
```

### Buscar e Abrir Registros

```python
# Busca e abre automaticamente (usa primeiro resultado)
await test.open_record("João Silva")

# Especificar posição se houver múltiplos
await test.open_record("João", position="primeiro")
await test.open_record("João", position="segundo")
await test.open_record("João", position="último")
```

### Wizards (Detecção Automática)

```python
# Clicar em botão que abre wizard
await test.click("Processar")

# Próximas operações são automaticamente no wizard
await test.fill("Data", "01/01/2024")
await test.click("Confirmar")  # Fecha wizard automaticamente
```

### Ações da Tela (User-Friendly)

```python
# Scroll
await test.scroll_down()        # Scroll para baixo (500px)
await test.scroll_down(1000)    # Scroll para baixo (1000px)
await test.scroll_up()          # Scroll para cima (500px)
await test.scroll_up(1000)      # Scroll para cima (1000px)

# Hover (passar mouse sobre elemento)
await test.hover("Produto")     # Hover em elemento com texto "Produto"

# Double Click
await test.double_click("Editar")  # Duplo clique em elemento

# Right Click
await test.right_click("Item")     # Clique direito em elemento

# Drag and Drop
await test.drag_and_drop("Item A", "Item B")  # Arrasta Item A para Item B
```

## YAML User-Friendly

### Estrutura Básica

```yaml
name: Nome do Teste
description: Descrição opcional

# Configuração opcional (cursor, vídeo, browser)
config:
  cursor:
    style: arrow
    color: "#007bff"
    size: large
    click_effect: true
    animation_speed: 0.3
  video:
    enabled: true
    quality: high
    codec: webm
  browser:
    headless: false
    slow_mo: 50

steps:
  - login: admin
    password: admin
    database: devel
  
  - go_to: "Vendas > Pedidos"
  
  - click: "Criar"
  
  - fill: "Cliente = João Silva"
  
  - click: "Salvar"
```

### Ações Suportadas

- `login`: Login no Odoo
- `go_to`: Navegar para menu (formato "Menu > Submenu") ou locais user-friendly ("Dashboard", "Portal", "Loja")
- `click`: Clicar em botão (apenas texto)
- `fill`: Preencher campo (formato "Label = Valor" ou separado)
- `add_line`: Adicionar linha em tabela
- `open_record`: Buscar e abrir registro
- `search`: Buscar registros
- `screenshot`: Tirar screenshot
- `wait`: Aguardar (segundos)
- `scroll`: Scroll da página (`down`, `up`, `baixo`, `cima`)
- `hover`: Passar mouse sobre elemento (por texto)
- `double_click`: Duplo clique (por texto)
- `right_click`: Clique direito (por texto)
- `drag`: Arrastar e soltar (formato `from: "A", to: "B"`)

### Navegação User-Friendly no YAML

```yaml
steps:
  # URLs técnicas são substituídas por comandos user-friendly
  - go_to: "Dashboard"      # Vai para /web (dashboard)
  - go_to: "Menu principal" # Alias para Dashboard
  - go_to: "Portal"         # Vai para /my (portal)
  - go_to: "Loja"           # Vai para /shop (e-commerce)
  - go_to: "E-commerce"     # Alias para Loja
  
  # Navegação por menu continua funcionando
  - go_to: "Vendas > Pedidos"
```

### Wizards em YAML

```yaml
steps:
  - click: "Processar"
    # Wizard aparece automaticamente
    wizard:
      - fill: "Data = 01/01/2024"
      - fill: "Observação = Teste"
      - click: "Confirmar"
```

### Contexto em Campos

```yaml
steps:
  - fill: "Nome = João"
    context: "Seção Cliente"
  
  - fill: "Nome = Maria"
    context: "Seção Contato"
```

### Ações da Tela no YAML

```yaml
steps:
  # Scroll
  - scroll: down        # Scroll para baixo
  - scroll: up          # Scroll para cima
  - scroll:             # Com direção e quantidade
    direction: down
    amount: 1000
  
  # Hover
  - hover: "Produto"
  
  # Double Click
  - double_click: "Editar"
  
  # Right Click
  - right_click: "Item"
  
  # Drag and Drop
  - drag:
      from: "Item A"
      to: "Item B"
```

### Configuração no YAML

```yaml
config:
  cursor:
    style: arrow              # arrow, dot, circle, custom
    color: "#007bff"          # Cor do cursor (hex)
    size: large               # small, medium, large
    click_effect: true        # Mostrar efeito de clique
    animation_speed: 0.3       # Velocidade da animação (segundos)
  
  video:
    enabled: true             # Habilitar gravação de vídeo
    quality: high             # low, medium, high
    codec: webm               # webm, mp4
  
  browser:
    headless: false           # Executar com interface gráfica
    slow_mo: 50               # Lentidão em milissegundos (para visualização)
```

## Exemplos Completos

Veja exemplos completos em:
- `examples/odoo_basic.py` - Exemplos Python
- `examples/odoo_sale_order.yaml` - Exemplo YAML

## Mensagens de Erro User-Friendly

A biblioteca fornece mensagens de erro claras e úteis:

```
Campo 'Cliente' não encontrado. Verifique se o label está correto e visível na tela.
```

```
Múltiplos campos 'Nome' encontrados. Use context para especificar (ex: context='Seção Cliente').
```

```
Botão 'Salvar' não encontrado no wizard. Verifique se o texto está correto e se está na tela correta.
```

## Compatibilidade

A biblioteca mantém compatibilidade com a API antiga (usando `field_name` técnico), mas recomenda-se usar a nova API user-friendly.

## Suporte a Versões Odoo

- Odoo 14, 15, 16, 17, 18
- Community e Enterprise
- Detecção automática de versão

## Próximos Passos

- Veja mais exemplos em `examples/`
- Consulte a documentação completa da API
- Reporte problemas ou sugestões no GitHub
