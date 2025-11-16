# YAML Language Features - playwright-simple

## Status: Linguagem de Programação Completa ✅

O core do playwright-simple define uma **linguagem YAML completa e extensível** para testes. Este documento lista todas as features disponíveis.

---

## ✅ FEATURES IMPLEMENTADAS

### 1. **Composição e Reutilização**
```yaml
# Compor YAMLs (importar funcionalidades)
compose:
  - file: odoo/login.yaml
    params:
      login: user@email.com
      password: senha123

# Ou dentro de steps
steps:
  - compose: odoo/filter_by.yaml
    params:
      filter_text: "Consumidor"
```

### 2. **Variáveis e Parâmetros**
```yaml
# Passar parâmetros
params:
  login: "{{ USER_EMAIL }}"
  password: "{{ USER_PASSWORD }}"

# Usar variáveis
steps:
  - action: type
    text: "{{ login }}"  # Substituído pelo parâmetro
  
  - action: click
    text: "{{ menu[0] }}"  # Array access
  
  - action: type
    text: "{{ user.name }}"  # Nested object access
```

### 3. **Ações Opcionais e Condições**
```yaml
steps:
  - action: click
    text: "OTP"
    optional: true
    condition: "{{ otp }}"  # Só executa se otp não for null/empty
```

### 4. **Herança (extends)**
```yaml
# base_test.yaml
name: Teste Base
steps:
  - action: click
    text: "Dashboard"

# meu_teste.yaml
extends: base_test.yaml
steps:
  - action: click
    text: "Contatos"  # Adiciona aos steps do base
```

### 5. **Includes**
```yaml
include:
  - common/setup.yaml
  - common/teardown.yaml
```

### 6. **Setup e Teardown**
```yaml
setup:
  - action: click
    text: "Login"

steps:
  - action: click
    text: "Dashboard"

teardown:
  - action: click
    text: "Logout"
```

### 7. **Busca Automática de Ações**
```yaml
steps:
  - action: login  # Busca automaticamente login.yaml
    login: user@email.com
    password: senha123
  
  - action: filter_by  # Busca filter_by.yaml
    filter_text: "Consumidor"
```

### 8. **Todas as Ações Básicas de Interação**
- `click`, `double_click`, `right_click`, `middle_click`
- `type`, `insert_text`, `clear`
- `press`, `keydown`, `keyup`, `keypress`
- `focus`, `blur`
- `hover`, `drag`, `scroll`
- `select`, `select_all`
- `copy`, `paste`
- `wait`, `wait_for`, `wait_for_text`, `wait_for_url`
- `assert_text`, `assert_visible`, `assert_url`, `assert_count`, `assert_attr`
- `screenshot`, `fill_form`

---

## ✅ FEATURES AVANÇADAS IMPLEMENTADAS

### 9. **Loops (for/foreach)**
```yaml
steps:
  - set: menu_items = ["Vendas", "Pedidos", "Produtos"]
  - for: item in menu_items
    steps:
      - action: click
        text: "{{ item }}"
      - action: screenshot
        name: "screenshot_{{ item }}"
```

**Suporta:**
- Listas: `for: item in items`
- Dicionários: `for: key in dict` (acessa `key.key` e `key.value`)
- Expressões: `for: item in {{ menu_items }}`

### 10. **Condicionais Complexas (if/else/elif)**
```yaml
steps:
  - set: user_role = "admin"
  - if: "{{ user_role }} == 'admin'"
    then:
      - action: click
        text: "Admin Panel"
  - elif:
      - if: "{{ user_role }} == 'user'"
        then:
          - action: click
            text: "User Panel"
  - else:
      - action: click
        text: "Guest Panel"
```

**Suporta:**
- Expressões: `{{ a == b }}`, `{{ x > 10 }}`, `{{ a and b }}`
- Múltiplos elif
- Else opcional

### 11. **Variáveis e Contexto (set)**
```yaml
steps:
  - set: current_url = "https://example.com"
  - set: counter = 0
  - set: total = "{{ counter + 10 }}"
  - action: click
    text: "{{ current_url }}"
```

**Suporta:**
- Atribuição simples: `set: var = value`
- Expressões: `set: total = {{ a + b }}`
- Variáveis disponíveis em todos os steps seguintes
- Acesso via `{{ var }}`

### 12. **Try/Catch/Error Handling**
```yaml
steps:
  - try:
      - action: click
        text: "Elemento que pode não existir"
    catch:
      - action: click
        text: "Elemento alternativo"
      - action: screenshot
        name: "error_fallback"
    finally:
      - action: click
        text: "Cleanup"
```

**Suporta:**
- Try/catch/finally
- Variáveis de erro: `{{ __error__ }}`, `{{ __error_type__ }}`
- Finally sempre executa

### 13. **Expressões e Avaliações**
```yaml
steps:
  - set: a = 10
  - set: b = 20
  - action: type
    text: "{{ a + b }}"  # Resultado: "30"
  - if: "{{ a > b }}"
    then:
      - action: click
        text: "A é maior"
```

**Suporta:**
- Matemática: `+`, `-`, `*`, `/`
- Comparações: `==`, `!=`, `<`, `>`, `<=`, `>=`
- Lógica: `and`, `or`, `not`
- Funções: `len()`, `str()`, `int()`, `float()`, `bool()`
- Arrays: `{{ items[0] }}`
- Objetos: `{{ user.name }}`

### 7. **Comentários Inline**
```yaml
# Já funciona (comentários YAML padrão)
steps:
  - action: click
    text: "Dashboard"  # Comentário inline
```

---

## 🎯 CONCLUSÃO: LINGUAGEM COMPLETA

### ✅ **SIM, é uma linguagem completa!**

Com todas as features implementadas, você pode fazer **qualquer coisa**:

1. **Reutilização:** `compose` permite importar YAMLs
2. **Parâmetros:** `{{ var }}` permite passar dados
3. **Variáveis:** `set: var = value` para contexto dinâmico
4. **Loops:** `for: item in items` para iteração
5. **Condicionais:** `if/else/elif` para lógica complexa
6. **Expressões:** `{{ a + b }}`, `{{ x > 10 }}` para cálculos
7. **Error Handling:** `try/catch/finally` para tratamento de erros
8. **Extensibilidade:** Qualquer ação pode ser um YAML (`action: login` → `login.yaml`)

---

## 💡 EXEMPLOS COMPLETOS

### Exemplo 1: Loop com Condicionais
```yaml
steps:
  - set: menu_items = ["Vendas", "Pedidos", "Produtos"]
  - for: item in menu_items
    steps:
      - action: click
        text: "{{ item }}"
      - if: "{{ item }} == 'Pedidos'"
        then:
          - action: screenshot
            name: "pedidos_page"
```

### Exemplo 2: Try/Catch com Variáveis
```yaml
steps:
  - set: attempts = 0
  - try:
      - action: click
        text: "Elemento difícil"
    catch:
      - set: attempts = "{{ attempts + 1 }}"
      - if: "{{ attempts < 3 }}"
        then:
          - action: wait
            seconds: 1
          - action: click
            text: "Elemento difícil"
```

### Exemplo 3: Expressões Complexas
```yaml
steps:
  - set: total_items = 10
  - set: current_page = 1
  - set: items_per_page = 5
  - set: total_pages = "{{ (total_items + items_per_page - 1) / items_per_page) | int }}"
  - for: page in "{{ range(1, total_pages + 1) }}"
    steps:
      - action: click
        text: "Página {{ page }}"
```

---

## 🚀 RECURSOS DA LINGUAGEM

**O core agora é uma linguagem de programação completa:**
- ✅ Variáveis e contexto
- ✅ Loops e iteração
- ✅ Condicionais complexas
- ✅ Expressões e avaliações
- ✅ Tratamento de erros
- ✅ Composição e reutilização
- ✅ Extensibilidade infinita

**Você pode criar qualquer teste sem precisar de Python!**

