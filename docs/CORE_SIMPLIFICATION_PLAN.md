# Plano de Simplificação do Core

## Princípio: Ações de Usuário Típico

O core deve ter apenas ações que um **usuário típico** faz no dia-a-dia:
- ✅ Clica em links, botões, menus
- ✅ Digita em campos
- ✅ Passa mouse (hover) - opcional
- ❌ NÃO edita URL diretamente
- ❌ NÃO usa seletores CSS complexos (a menos que necessário)

---

## Ações Core (Simplificadas)

### 1. `click` - Clicar em qualquer coisa
```yaml
- action: click
  text: "Login"  # Texto visível (preferido)
  # ou
  selector: "#login-btn"  # Seletor CSS (fallback)
  description: "Botão de login"
```

**Comportamento:**
- Tenta encontrar por texto primeiro (mais user-friendly)
- Se não encontrar, tenta seletor CSS
- Move cursor, mostra efeito, clica

---

### 2. `type` - Digitar em campos
```yaml
- action: type
  text: "usuario@email.com"
  description: "Campo de email"
  # ou com seletor específico
  selector: input[name="email"]
```

**Comportamento:**
- Se não tem `selector`, tenta encontrar campo focado ou primeiro campo de texto
- Move cursor, digita com delay humano

---

### 3. `hover` - Passar mouse (opcional)
```yaml
- action: hover
  text: "Menu"
  description: "Passar mouse no menu"
```

**Comportamento:**
- Move cursor para elemento
- Mostra hover effect
- Útil para menus dropdown

---

### 4. `screenshot` - Tirar screenshot
```yaml
- action: screenshot
  name: "login_success"
  description: "Tela após login"
```

---

## Remover do Core

### ❌ `go_to(url)` - Ninguém edita URL
**Motivo:** Usuário típico não edita URL, ele clica em links/menus.

**Substituir por:**
```yaml
# ❌ ANTES (técnico)
- action: go_to
  url: /dashboard

# ✅ DEPOIS (user-friendly)
- action: click
  text: "Dashboard"
```

---

### ❌ `navigate(menu_path)` - Muito técnico
**Motivo:** Usuário clica em menus um por vez, não passa array.

**Substituir por:**
```yaml
# ❌ ANTES (técnico)
- action: navigate
  menu_path: ["Vendas", "Pedidos"]

# ✅ DEPOIS (user-friendly)
- action: click
  text: "Vendas"
- action: click
  text: "Pedidos"
```

---

### ❌ `login()` genérico - Muito complexo
**Motivo:** Cada app tem login diferente. Melhor usar `click` + `type`.

**Substituir por:**
```yaml
# ❌ ANTES (tenta adivinhar campos)
- action: login
  username: user
  password: pass

# ✅ DEPOIS (explícito, user-friendly)
- action: click
  text: "Login"
- action: type
  text: user@email.com
  description: "Campo de email"
- action: type
  text: senha123
  description: "Campo de senha"
- action: click
  text: "Entrar"
```

---

## Simplificações no Código

### 1. Melhorar `click()` para aceitar texto primeiro

```python
async def click(self, text_or_selector: str, description: str = "") -> 'InteractionMixin':
    """
    Click on element by text (preferred) or selector.
    
    Tries to find element by visible text first (user-friendly),
    then falls back to CSS selector if text not found.
    
    Args:
        text_or_selector: Visible text or CSS selector
        description: Optional description
    """
    # Try text first (user-friendly)
    selectors = [
        f'button:has-text("{text_or_selector}")',
        f'a:has-text("{text_or_selector}")',
        f'[role="button"]:has-text("{text_or_selector}")',
        f'*:has-text("{text_or_selector}")',  # Any element with text
    ]
    
    element = None
    for selector in selectors:
        try:
            locator = self.page.locator(selector).first
            if await locator.count() > 0 and await locator.is_visible():
                element = locator
                break
        except:
            continue
    
    # Fallback to CSS selector
    if not element:
        try:
            element = self.page.locator(text_or_selector).first
        except:
            raise ElementNotFoundError(f"Element not found: {text_or_selector}")
    
    # ... resto do código ...
```

---

### 2. Melhorar `type()` para encontrar campo automaticamente

```python
async def type(self, text: str, description: str = "", selector: Optional[str] = None) -> 'InteractionMixin':
    """
    Type text into field.
    
    If no selector provided, tries to find focused field or first text input.
    
    Args:
        text: Text to type
        description: Description of field
        selector: Optional CSS selector (if not provided, tries to find field)
    """
    if not selector:
        # Try focused field first
        focused = await self.page.evaluate("() => document.activeElement")
        if focused and focused.tagName in ['INPUT', 'TEXTAREA']:
            element = self.page.locator(':focus')
        else:
            # Try first visible text input
            element = self.page.locator('input[type="text"], input[type="email"], textarea').first
    else:
        element = self.page.locator(selector).first
    
    # ... resto do código ...
```

---

### 3. Remover `go_to()` ou simplificar drasticamente

**Opção 1: Remover completamente**
- Usuário sempre usa `click` em links

**Opção 2: Manter apenas para casos especiais**
- Apenas se realmente necessário (ex: teste de URL direta)
- Documentar como "avançado"

---

## Exemplo de Teste Simplificado

### Antes (Complexo)
```yaml
steps:
  - action: login
    username: user
    password: pass
    database: db
  
  - action: go_to
    url: /dashboard
  
  - action: navigate
    menu_path: ["Vendas", "Pedidos"]
  
  - action: open_filters
```

### Depois (Simples)
```yaml
steps:
  - action: click
    text: "Login"
  
  - action: type
    text: user@email.com
    description: "Email"
  
  - action: type
    text: senha123
    description: "Senha"
  
  - action: type
    text: db
    description: "Database"
  
  - action: click
    text: "Entrar"
  
  - action: click
    text: "Dashboard"
  
  - action: click
    text: "Vendas"
  
  - action: click
    text: "Pedidos"
  
  - action: click
    text: "Filtros"
```

---

## Checklist de Implementação

- [ ] Melhorar `click()` para aceitar texto primeiro
- [ ] Melhorar `type()` para encontrar campo automaticamente
- [ ] Remover ou simplificar `go_to()`
- [ ] Remover `navigate()` (ou tornar muito simples)
- [ ] Simplificar `login()` ou remover
- [ ] Atualizar YAML parser
- [ ] Atualizar documentação
- [ ] Testar com teste simplificado

---

## Benefícios

1. ✅ **Mais user-friendly**: Testes leem como ações de usuário
2. ✅ **Mais simples**: Menos ações para aprender
3. ✅ **Mais genérico**: Funciona para qualquer app web
4. ✅ **Mais intuitivo**: Qualquer pessoa entende o teste

---

## Conclusão

O core deve ser **mínimo** e **baseado em ações de usuário típico**:
- `click` - clicar em qualquer coisa
- `type` - digitar em campos
- `hover` - passar mouse (opcional)
- `screenshot` - tirar screenshot

Tudo mais deve ser feito com essas ações básicas ou ficar em extensões.


