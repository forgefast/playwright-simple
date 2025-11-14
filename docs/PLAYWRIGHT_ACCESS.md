# Acesso Direto ao Playwright

## Princípio: Não Travar o Usuário

O playwright-simple **facilita** o uso do Playwright, mas **não remove** funcionalidades. Você sempre pode usar Playwright diretamente quando necessário.

---

## Acesso ao Page

O objeto `page` do Playwright está sempre disponível:

### Em Python
```python
async def test_example(page, test):
    # Usar métodos do playwright-simple
    await test.click("Botão")
    
    # OU usar Playwright diretamente
    await page.evaluate("() => console.log('Hello')")
    await page.locator('.my-class').click()
    await page.route('**/api/**', lambda route: route.fulfill(status=200))
```

### Em YAML
```yaml
steps:
  # Usar ações do playwright-simple
  - action: click
    text: "Botão"
  
  # OU usar Playwright diretamente
  - action: evaluate
    code: "() => console.log('Hello')"
  
  - action: locator
    selector: ".my-class"
    # Retorna locator (pode ser usado em evaluate)
```

---

## Ações Playwright Disponíveis no YAML

### 1. **evaluate** - Executar JavaScript
```yaml
steps:
  - action: evaluate
    code: |
      () => {
        document.querySelector('.my-element').style.display = 'none';
        return document.title;
      }
```

### 2. **evaluate_handle** - Executar e retornar JSHandle
```yaml
steps:
  - action: evaluate_handle
    code: "() => document.body"
```

### 3. **locator** - Obter Locator
```yaml
# Nota: locator() retorna um objeto, melhor usar em Python
# Em YAML, use action: click que já usa locator internamente
```

### 4. **query_selector** / **query_selector_all**
```yaml
# Nota: Melhor usar em Python para acessar o elemento retornado
# Em YAML, use action: click ou action: evaluate
```

### 5. **add_init_script** - Adicionar script na inicialização
```yaml
steps:
  - action: add_init_script
    script: |
      window.myCustomFunction = () => {
        console.log('Custom function');
      };
```

### 6. **route** / **unroute** - Interceptar requisições
```yaml
steps:
  - action: route
    url: "**/api/users"
    handler: |
      async (route) => {
        await route.fulfill({
          status: 200,
          body: JSON.stringify({ users: [] })
        });
      }
  
  - action: unroute
    url: "**/api/users"
```

### 7. **set_extra_http_headers** - Headers HTTP
```yaml
steps:
  - action: set_extra_http_headers
    headers:
      Authorization: "Bearer token123"
      X-Custom-Header: "value"
```

### 8. **set_viewport_size** - Tamanho do viewport
```yaml
steps:
  - action: set_viewport_size
    width: 1920
    height: 1080
```

### 9. **add_script_tag** / **add_style_tag**
```yaml
steps:
  - action: add_script_tag
    url: "https://cdn.example.com/script.js"
  
  - action: add_style_tag
    content: |
      .my-class { color: red; }
```

### 10. **expose_function** - Expor função Python
```yaml
# Nota: Requer callback Python, melhor usar em código Python
# Exemplo em Python:
# await test.page.expose_function('myFunc', lambda x: x * 2)
```

### 11. **request** - Fazer requisições HTTP
```yaml
steps:
  - action: request
    method: GET
    url: "https://api.example.com/data"
  
  - action: request
    method: POST
    url: "https://api.example.com/data"
    data:
      key: "value"
```

---

## Funcionalidades Avançadas do Playwright

### Interceptação de Rede
```yaml
steps:
  # Interceptar e modificar requisições
  - action: route
    url: "**/api/**"
    handler: |
      async (route) => {
        const request = route.request();
        if (request.url().includes('/users')) {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ users: [] })
          });
        } else {
          await route.continue();
        }
      }
```

### Executar JavaScript Complexo
```yaml
steps:
  - action: evaluate
    code: |
      () => {
        // Acessar window, document, etc.
        window.myData = { count: 0 };
        document.querySelector('.counter').textContent = '0';
        return window.location.href;
      }
```

### Acessar Console/Network
```yaml
steps:
  - action: evaluate
    code: |
      () => {
        // Capturar console.log
        const originalLog = console.log;
        console.log = (...args) => {
          originalLog(...args);
          window._consoleMessages = window._consoleMessages || [];
          window._consoleMessages.push(args.join(' '));
        };
      }
```

### Modificar DOM
```yaml
steps:
  - action: evaluate
    code: |
      () => {
        const element = document.querySelector('.my-element');
        element.style.display = 'none';
        element.setAttribute('data-modified', 'true');
        return element.outerHTML;
      }
```

---

## Quando Usar Playwright Direto

### ✅ Use Playwright Direto Para:
1. **Interceptação de rede** - `route()`, `unroute()`
2. **JavaScript complexo** - `evaluate()` com lógica customizada
3. **Modificação de DOM** - Manipular elementos diretamente
4. **APIs específicas** - Funcionalidades não cobertas pelo core
5. **Performance** - Quando precisa de controle fino

### ✅ Use playwright-simple Para:
1. **Ações comuns** - `click()`, `type()`, `press()`
2. **Testes legíveis** - YAML mais fácil de entender
3. **Cursor visual** - Efeitos visuais automáticos
4. **Screenshots** - Captura automática
5. **Seletores inteligentes** - Busca por texto

---

## Exemplo: Combinando Ambos

```yaml
steps:
  # Setup: Interceptar API (Playwright direto)
  - action: route
    url: "**/api/**"
    handler: |
      async (route) => {
        await route.fulfill({
          status: 200,
          body: JSON.stringify({ mock: true })
        });
      }
  
  # Ações do teste (playwright-simple)
  - action: click
    text: "Login"
  
  - action: type
    text: "user@email.com"
  
  # Verificação customizada (Playwright direto)
  - action: evaluate
    code: |
      () => {
        const token = localStorage.getItem('token');
        return token !== null;
      }
  
  # Continuar com playwright-simple
  - action: click
    text: "Dashboard"
```

---

## Acesso em Python

Se você escreve testes em Python, tem acesso total:

```python
async def test_advanced(page, test):
    # playwright-simple
    await test.click("Botão")
    
    # Playwright direto
    await page.route('**/api/**', lambda route: route.fulfill(
        status=200,
        body='{"mock": true}'
    ))
    
    await page.evaluate("""
        () => {
            window.customData = { count: 0 };
        }
    """)
    
    # Continuar com playwright-simple
    await test.type("user@email.com")
    
    # Verificar resultado com Playwright
    result = await page.evaluate("() => window.customData.count")
    assert result == 0
```

---

## Funcionalidades Playwright Disponíveis

### Page Methods
- `page.evaluate()` ✅
- `page.evaluate_handle()` ✅
- `page.locator()` ✅
- `page.query_selector()` ✅
- `page.query_selector_all()` ✅
- `page.route()` ✅
- `page.unroute()` ✅
- `page.set_extra_http_headers()` ✅
- `page.set_viewport_size()` ✅
- `page.add_script_tag()` ✅
- `page.add_style_tag()` ✅
- `page.expose_function()` ✅
- `page.request` ✅
- `page.context` (acessível via `test.page.context`)
- `page.browser` (acessível via `test.page.browser`)

### Locator Methods
- `locator.click()` ✅ (via `action: click`)
- `locator.fill()` ✅ (via `action: type`)
- `locator.select_option()` ✅ (via `action: select`)
- `locator.evaluate()` ✅ (via `action: evaluate` com locator)
- `locator.wait_for()` ✅ (via `action: wait_for`)

### Network
- `page.route()` ✅
- `page.unroute()` ✅
- `page.request` ✅

---

## Conclusão

**playwright-simple não remove funcionalidades do Playwright.**

- ✅ Use YAML para ações comuns (mais fácil)
- ✅ Use Playwright direto para casos avançados (mais poder)
- ✅ Combine ambos conforme necessário
- ✅ Sempre tem acesso ao `page` do Playwright

**Você não está preso - tem o melhor dos dois mundos!**

