# Composição de YAMLs - YAML-First

## Princípio: YAML-First

Extensões (como Odoo) devem implementar funcionalidades específicas como **YAMLs compostos**, não funções Python. Cada funcionalidade específica é um YAML que usa apenas ações core.

---

## Como Funciona

### 1. YAMLs de Extensão

Extensões criam YAMLs que implementam funcionalidades específicas usando apenas ações core:

**`odoo/login.yaml`**
```yaml
name: Login Odoo
description: Login específico do Odoo

steps:
  - action: click
    text: "Login"
  - action: type
    text: "{{ login }}"
  - action: click
    text: "Password"
  - action: type
    text: "{{ password }}"
  # ... etc
```

**`odoo/filter_by.yaml`**
```yaml
name: Filtrar por
description: Filtrar lista por texto

steps:
  - action: click
    text: "Filtros"
  - action: type
    text: "{{ filter_text }}"
  - action: click
    text: "{{ filter_button }}"
```

---

### 2. Composição no Teste Principal

O teste principal **compõe** esses YAMLs:

```yaml
name: Meu Teste
description: Teste que usa funcionalidades do Odoo

# Composição de YAMLs
compose:
  - file: odoo/login.yaml
    params:
      login: user@email.com
      password: senha123
      database: devel
  
  - file: odoo/filter_by.yaml
    params:
      filter_text: "Consumidor"
      filter_button: "Aplicar"

steps:
  # Ações do teste principal
  - action: click
    text: "Dashboard"
```

---

## Sintaxe de Composição

### Opção 1: `compose` (Recomendado)

```yaml
compose:
  - file: odoo/login.yaml
    params:
      login: user@email.com
      password: senha123
  
  - file: odoo/navigate.yaml
    params:
      menu: ["Vendas", "Pedidos"]
```

### Opção 2: `include` (Alternativa)

```yaml
steps:
  - include: odoo/login.yaml
    with:
      login: user@email.com
      password: senha123
  
  - action: click
    text: "Dashboard"
```

---

## Parâmetros e Variáveis

### Passar Parâmetros

```yaml
compose:
  - file: odoo/login.yaml
    params:
      login: "{{ USER_EMAIL }}"
      password: "{{ USER_PASSWORD }}"
      database: devel
      otp: null
```

### Usar no YAML Composto

```yaml
steps:
  - action: type
    text: "{{ login }}"  # Substituído pelo parâmetro
```

---

## Ações Opcionais

YAMLs compostos podem ter ações opcionais:

```yaml
steps:
  - action: click
    text: "OTP"
    optional: true
    condition: "{{ otp }}"  # Só executa se otp não for null/empty
```

---

## Exemplos de YAMLs de Extensão

### Login Odoo

```yaml
name: Login Odoo
description: Login específico do Odoo

steps:
  - action: click
    text: "Login"
  - action: type
    text: "{{ login }}"
  - action: click
    text: "Password"
  - action: type
    text: "{{ password }}"
  - action: click
    text: "Database"
    optional: true
  - action: type
    text: "{{ database }}"
    optional: true
  - action: click
    text: "Entrar"
```

### Filtrar por Texto

```yaml
name: Filtrar por
description: Filtrar lista por texto

steps:
  - action: click
    text: "Filtros"
  - action: click
    text: "Buscar"
    optional: true
  - action: type
    text: "{{ filter_text }}"
  - action: click
    text: "{{ filter_button }}"
    optional: true
    condition: "{{ filter_button }}"
  - action: press
    key: "Enter"
    optional: true
    condition: "!{{ filter_button }}"
```

### Navegar Menu

```yaml
name: Navegar Menu
description: Navegar por menu hierárquico

steps:
  # Recebe menu como array: ["Vendas", "Pedidos"]
  - action: click
    text: "{{ menu[0] }}"  # Primeiro item
  - action: click
    text: "{{ menu[1] }}"  # Segundo item
    optional: true
    condition: "{{ menu[1] }}"
```

---

## Vantagens

1. ✅ **YAML-First**: Tudo em YAML, sem código Python específico
2. ✅ **Composável**: YAMLs podem ser reutilizados
3. ✅ **Simples**: Usa apenas ações core (`click`, `type`, etc)
4. ✅ **Extensível**: Fácil criar novos YAMLs de extensão
5. ✅ **Legível**: Qualquer pessoa entende o que faz

---

## Implementação no Core

O parser YAML precisa:

1. **Suportar `compose`**: Carregar e executar YAMLs compostos
2. **Substituir variáveis**: `{{ param }}` → valor do parâmetro
3. **Ações opcionais**: `optional: true` + `condition`
4. **Resolução de caminhos**: Encontrar YAMLs em `extensions/odoo/`, etc

---

## Estrutura de Diretórios

```
playwright-simple/
├── examples/
│   ├── test_colaborador_portal.yaml  # Teste principal
│   └── odoo/
│       ├── login.yaml                 # YAML de login
│       ├── filter_by.yaml            # YAML de filtro
│       └── navigate.yaml              # YAML de navegação
```

---

## Conclusão

**YAML-First** significa:
- Extensões são YAMLs, não código Python
- Funcionalidades específicas são YAMLs compostos
- Testes principais compõem esses YAMLs
- Tudo usa apenas ações core simples


