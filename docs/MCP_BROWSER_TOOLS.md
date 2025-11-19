# Ferramentas MCP de Navegação Web no Playwright-Simple

**Versão**: 1.0.0  
**Data**: Novembro 2024

---

## 📚 Índice

- [Visão Geral](#visão-geral)
- [Ferramentas Disponíveis](#ferramentas-disponíveis)
- [Comparação com Playwright-Simple](#comparação-com-playwright-simple)
- [Casos de Uso](#casos-de-uso)
- [Exemplos Práticos](#exemplos-práticos)
- [Integração com Playwright-Simple](#integração-com-playwright-simple)

---

## Visão Geral

As **Ferramentas MCP (Model Context Protocol) de Navegação Web** são um conjunto de ferramentas que permitem interagir com páginas web de forma programática através de uma interface padronizada. Essas ferramentas são especialmente úteis para:

- **Testes automatizados** - Verificar comportamento de páginas web
- **Debugging interativo** - Inspecionar páginas em tempo real
- **Automação de tarefas** - Preencher formulários, clicar em elementos, etc.
- **Análise de páginas** - Capturar snapshots, screenshots, logs do console

### Diferença entre MCP Browser Tools e Playwright-Simple

| Aspecto | MCP Browser Tools | Playwright-Simple |
|---------|-------------------|------------------|
| **Interface** | Protocolo MCP (Model Context Protocol) | API Python/YAML |
| **Uso** | Via ferramentas MCP (Cursor AI) | Via código Python ou arquivos YAML |
| **Snapshot** | Formato YAML estruturado | HTML completo + estado da página |
| **Gravação** | Não suporta gravação | Suporta gravação interativa |
| **Execução** | Interativa (via AI) | Automatizada (scripts/testes) |
| **Melhor para** | Debugging rápido, testes exploratórios | Testes regressivos, CI/CD |

---

## Ferramentas Disponíveis

### 1. Navegação

#### `browser_navigate`
Navega para uma URL específica.

**Uso MCP:**
```json
{
  "url": "http://localhost:18069/cadastro-revendedor"
}
```

**Equivalente Playwright-Simple:**
```yaml
steps:
  - action: go_to
    url: http://localhost:18069/cadastro-revendedor
```

```python
await test.go_to("http://localhost:18069/cadastro-revendedor")
```

#### `browser_navigate_back`
Volta para a página anterior no histórico.

**Equivalente Playwright-Simple:**
```yaml
steps:
  - action: back
```

```python
await test.back()
```

#### `browser_resize`
Redimensiona a janela do navegador.

**Uso MCP:**
```json
{
  "width": 1920,
  "height": 1080
}
```

**Equivalente Playwright-Simple:**
```python
await page.set_viewport_size({"width": 1920, "height": 1080})
```

---

### 2. Inspeção e Análise

#### `browser_snapshot`
Captura um snapshot de acessibilidade da página em formato YAML estruturado.

**Exemplo de saída:**
```yaml
- generic [ref=e2]:
  - link "Pular para o conteúdo" [ref=e3] [cursor=pointer]:
    - /url: "#wrap"
  - main [ref=e18]:
    - textbox "000.000.000-00" [ref=e36]
```

**Equivalente Playwright-Simple:**
```python
# Capturar HTML completo
html = await page.content()

# Capturar estado estruturado
state = await WebState.capture(page)
```

#### `browser_take_screenshot`
Tira uma screenshot da página ou de um elemento específico.

**Uso MCP:**
```json
{
  "filename": "screenshot.png",
  "fullPage": true
}
```

**Equivalente Playwright-Simple:**
```yaml
steps:
  - action: screenshot
    path: screenshot.png
    full_page: true
```

```python
await page.screenshot(path="screenshot.png", full_page=True)
```

#### `browser_console_messages`
Lê todas as mensagens do console do navegador.

**Equivalente Playwright-Simple:**
```python
# Capturar logs do console
console_messages = []
page.on("console", lambda msg: console_messages.append(msg.text))
```

#### `browser_network_requests`
Lista todas as requisições de rede desde o carregamento da página.

**Equivalente Playwright-Simple:**
```python
# Interceptar requisições
requests = []
page.on("request", lambda req: requests.append(req.url))
page.on("response", lambda res: print(f"{res.status} {res.url}"))
```

---

### 3. Interações com Elementos

#### `browser_click`
Clica em um elemento usando referência ou descrição.

**Uso MCP:**
```json
{
  "element": "Campo CPF",
  "ref": "e36"
}
```

**Equivalente Playwright-Simple:**
```yaml
steps:
  - action: click
    text: "Campo CPF"
    # ou
    selector: "input[name='cnpj_cpf']"
```

```python
await test.click("Campo CPF")
# ou
await test.click("input[name='cnpj_cpf']")
```

#### `browser_type`
Digita texto em um campo editável.

**Uso MCP:**
```json
{
  "element": "Campo CPF",
  "ref": "e36",
  "text": "12345678901",
  "slowly": false
}
```

**Equivalente Playwright-Simple:**
```yaml
steps:
  - action: type
    text: "12345678901"
    selector: "input[name='cnpj_cpf']"
```

```python
await test.type("12345678901", selector="input[name='cnpj_cpf']")
```

#### `browser_fill_form`
Preenche múltiplos campos de formulário de uma vez.

**Uso MCP:**
```json
{
  "fields": [
    {
      "name": "CPF",
      "ref": "input[name='cnpj_cpf']",
      "type": "textbox",
      "value": "123.456.789-01"
    },
    {
      "name": "Email",
      "ref": "input[name='email']",
      "type": "textbox",
      "value": "teste@example.com"
    }
  ]
}
```

**Equivalente Playwright-Simple:**
```yaml
steps:
  - action: fill_form
    fields:
      - selector: "input[name='cnpj_cpf']"
        value: "123.456.789-01"
      - selector: "input[name='email']"
        value: "teste@example.com"
```

```python
await test.fill_form({
    "input[name='cnpj_cpf']": "123.456.789-01",
    "input[name='email']": "teste@example.com"
})
```

#### `browser_select_option`
Seleciona opções em dropdowns.

**Uso MCP:**
```json
{
  "element": "Estado",
  "ref": "select[name='state_id']",
  "values": ["SP"]
}
```

**Equivalente Playwright-Simple:**
```yaml
steps:
  - action: select
    selector: "select[name='state_id']"
    value: "SP"
```

```python
await test.select("select[name='state_id']", "SP")
```

#### `browser_hover`
Passa o mouse sobre um elemento.

**Equivalente Playwright-Simple:**
```python
await test.hover("button.menu-item")
```

#### `browser_drag`
Arrasta um elemento para outro.

**Equivalente Playwright-Simple:**
```python
await test.drag("source-element", "target-element")
```

---

### 4. Ferramentas Avançadas

#### `browser_evaluate`
Executa JavaScript na página.

**Uso MCP:**
```json
{
  "function": "() => { return document.title; }"
}
```

**Equivalente Playwright-Simple:**
```yaml
steps:
  - action: evaluate
    code: |
      () => {
        return document.title;
      }
```

```python
title = await page.evaluate("() => document.title")
```

#### `browser_wait_for`
Aguarda texto aparecer/desaparecer ou um tempo específico.

**Uso MCP:**
```json
{
  "text": "Carregando...",
  "textGone": true,
  "time": 5
}
```

**Equivalente Playwright-Simple:**
```yaml
steps:
  - action: wait_for
    text: "Carregando..."
    timeout: 5000
```

```python
await test.wait_for_text("Carregando...", timeout=5000)
```

#### `browser_handle_dialog`
Lida com diálogos (alert, confirm, prompt).

**Uso MCP:**
```json
{
  "accept": true,
  "promptText": "resposta"
}
```

**Equivalente Playwright-Simple:**
```python
page.on("dialog", lambda dialog: dialog.accept("resposta"))
```

---

## Casos de Uso

### 1. Debugging Interativo

**Cenário:** Você está desenvolvendo um formulário e quer testar rapidamente se as máscaras estão funcionando.

**Com MCP Browser Tools:**
1. Navegar para a página
2. Capturar snapshot para ver estrutura
3. Clicar no campo CPF
4. Digitar números
5. Verificar se a máscara foi aplicada

**Com Playwright-Simple:**
```yaml
name: Teste Máscara CPF
steps:
  - action: go_to
    url: http://localhost:18069/cadastro-revendedor
  
  - action: click
    selector: "input[name='cnpj_cpf']"
  
  - action: type
    text: "12345678901"
    selector: "input[name='cnpj_cpf']"
  
  - action: assert
    selector: "input[name='cnpj_cpf']"
    attribute: value
    expected: "123.456.789-01"
```

### 2. Testes Exploratórios

**Cenário:** Você quer explorar uma nova funcionalidade sem escrever código.

**Com MCP Browser Tools:**
- Navegar pela aplicação interativamente
- Capturar snapshots para entender a estrutura
- Testar diferentes fluxos rapidamente

**Com Playwright-Simple:**
- Usar o modo de gravação interativa:
```bash
playwright-simple record teste_exploratorio.yaml --url http://localhost:18069
```

### 3. Validação de Regressão

**Cenário:** Você quer garantir que uma funcionalidade continua funcionando após mudanças.

**Com Playwright-Simple (recomendado):**
```yaml
name: Validação Formulário Revendedor
steps:
  - action: go_to
    url: http://localhost:18069/cadastro-revendedor
  
  - action: fill_form
    fields:
      - selector: "input[name='name']"
        value: "João Silva"
      - selector: "input[name='cnpj_cpf']"
        value: "12345678901"
      - selector: "input[name='email']"
        value: "joao@example.com"
  
  - action: assert_text
    text: "123.456.789-01"
    selector: "input[name='cnpj_cpf']"
```

---

## Exemplos Práticos

### Exemplo 1: Teste de Máscara de CPF

**Objetivo:** Verificar se a máscara de CPF formata corretamente durante a digitação.

**Com MCP Browser Tools:**
```python
# Executado via ferramentas MCP
1. browser_navigate(url="http://localhost:18069/cadastro-revendedor")
2. browser_snapshot()  # Ver estrutura da página
3. browser_click(element="Campo CPF", ref="e36")
4. browser_type(element="Campo CPF", ref="e36", text="12345678901")
5. browser_evaluate(function="() => document.querySelector('input[name=\"cnpj_cpf\"]').value")
   # Retorna: "123.456.789-01" se funcionou
```

**Com Playwright-Simple:**
```yaml
name: Teste Máscara CPF
steps:
  - action: go_to
    url: http://localhost:18069/cadastro-revendedor
  
  - action: click
    selector: "input[name='cnpj_cpf']"
  
  - action: type
    text: "12345678901"
    selector: "input[name='cnpj_cpf']"
  
  - action: assert
    selector: "input[name='cnpj_cpf']"
    attribute: value
    expected: "123.456.789-01"
```

### Exemplo 2: Verificar Console para Erros

**Objetivo:** Verificar se há erros JavaScript no console.

**Com MCP Browser Tools:**
```python
# Executado via ferramentas MCP
1. browser_navigate(url="http://localhost:18069/cadastro-revendedor")
2. browser_wait_for(time=2)  # Aguardar carregamento
3. browser_console_messages()  # Retorna lista de erros/warnings
```

**Com Playwright-Simple:**
```python
async def test_console_errors(page, test):
    console_errors = []
    
    def handle_console(msg):
        if msg.type == "error":
            console_errors.append(msg.text)
    
    page.on("console", handle_console)
    
    await test.go_to("http://localhost:18069/cadastro-revendedor")
    await test.wait(2)
    
    assert len(console_errors) == 0, f"Erros no console: {console_errors}"
```

### Exemplo 3: Preencher Formulário Completo

**Objetivo:** Preencher todos os campos do formulário de cadastro.

**Com MCP Browser Tools:**
```python
# Executado via ferramentas MCP
1. browser_navigate(url="http://localhost:18069/cadastro-revendedor")
2. browser_fill_form(fields=[
    {"name": "Nome", "ref": "input[name='name']", "type": "textbox", "value": "João Silva"},
    {"name": "CPF", "ref": "input[name='cnpj_cpf']", "type": "textbox", "value": "12345678901"},
    {"name": "Email", "ref": "input[name='email']", "type": "textbox", "value": "joao@example.com"},
    {"name": "Telefone", "ref": "input[name='phone']", "type": "textbox", "value": "11987654321"},
    {"name": "CEP", "ref": "input[name='zip']", "type": "textbox", "value": "12345678"},
])
```

**Com Playwright-Simple:**
```yaml
name: Preencher Formulário Completo
steps:
  - action: go_to
    url: http://localhost:18069/cadastro-revendedor
  
  - action: fill_form
    fields:
      - selector: "input[name='name']"
        value: "João Silva"
      - selector: "input[name='cnpj_cpf']"
        value: "12345678901"
      - selector: "input[name='email']"
        value: "joao@example.com"
      - selector: "input[name='phone']"
        value: "11987654321"
      - selector: "input[name='zip']"
        value: "12345678"
  
  - action: click
    text: "Enviar Cadastro"
```

---

## Integração com Playwright-Simple

### Quando Usar Cada Ferramenta

| Situação | Ferramenta Recomendada |
|----------|----------------------|
| **Testes regressivos** | Playwright-Simple (YAML/Python) |
| **Debugging rápido** | MCP Browser Tools |
| **Exploração de funcionalidades** | MCP Browser Tools ou Gravação do Playwright-Simple |
| **CI/CD** | Playwright-Simple |
| **Testes interativos com AI** | MCP Browser Tools |
| **Documentação de fluxos** | Playwright-Simple (gravação) |

### Convertendo Entre Formatos

#### De MCP Browser Tools para Playwright-Simple YAML

**MCP:**
```python
browser_navigate(url="http://example.com")
browser_click(element="Botão", ref="e1")
browser_type(element="Campo", ref="e2", text="valor")
```

**Playwright-Simple YAML:**
```yaml
steps:
  - action: go_to
    url: http://example.com
  
  - action: click
    selector: "#button-id"  # ou text: "Botão"
  
  - action: type
    text: "valor"
    selector: "#field-id"  # ou text: "Campo"
```

#### De Playwright-Simple para MCP Browser Tools

**Playwright-Simple:**
```yaml
steps:
  - action: go_to
    url: http://example.com
  
  - action: click
    text: "Botão"
  
  - action: assert_text
    text: "Sucesso"
```

**MCP (conceitual):**
```python
1. browser_navigate(url="http://example.com")
2. browser_snapshot()  # Encontrar elemento
3. browser_click(element="Botão", ref="e1")
4. browser_snapshot()  # Verificar resultado
5. browser_evaluate(function="() => document.body.textContent.includes('Sucesso')")
```

---

## Dicas e Boas Práticas

### 1. Usar Snapshots para Entender Estrutura

**MCP Browser Tools:**
- Use `browser_snapshot()` para entender a estrutura da página antes de interagir
- Os refs (referências) dos elementos podem mudar entre carregamentos

**Playwright-Simple:**
- Use seletores estáveis (IDs, data-attributes) ao invés de refs
- Capture estado com `WebState.capture()` para debugging

### 2. Aguardar Carregamento

**MCP Browser Tools:**
```python
browser_navigate(url="...")
browser_wait_for(time=2)  # Aguardar carregamento
browser_snapshot()  # Verificar se carregou
```

**Playwright-Simple:**
```yaml
steps:
  - action: go_to
    url: ...
  
  - action: wait_for
    selector: "input[name='cnpj_cpf']"
    state: visible
```

### 3. Verificar Console para Debugging

**MCP Browser Tools:**
```python
browser_console_messages()  # Ver erros JavaScript
browser_network_requests()  # Ver requisições falhadas
```

**Playwright-Simple:**
```python
page.on("console", lambda msg: print(f"Console: {msg.text}"))
page.on("response", lambda res: print(f"Response: {res.status} {res.url}"))
```

### 4. Capturar Screenshots para Documentação

**MCP Browser Tools:**
```python
browser_take_screenshot(filename="antes.png")
# ... interação ...
browser_take_screenshot(filename="depois.png")
```

**Playwright-Simple:**
```yaml
steps:
  - action: screenshot
    path: antes.png
  
  # ... outras ações ...
  
  - action: screenshot
    path: depois.png
```

---

## Conclusão

As **Ferramentas MCP de Navegação Web** e o **Playwright-Simple** são complementares:

- **MCP Browser Tools**: Melhor para debugging interativo, testes exploratórios e uso com AI
- **Playwright-Simple**: Melhor para testes regressivos, CI/CD e documentação de fluxos

Ambos permitem automação web poderosa, mas com diferentes interfaces e casos de uso ideais. Escolha a ferramenta certa para cada situação!

---

**Última Atualização**: Novembro 2024  
**Autor**: Documentação Playwright-Simple

