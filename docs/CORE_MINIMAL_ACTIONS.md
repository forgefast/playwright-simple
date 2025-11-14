# Ações YAML Core Mínimas

## Objetivo

Definir as ações YAML mínimas que o core deve suportar. Apenas funcionalidades genéricas para qualquer aplicação web.

---

## Ações Core (Mínimas)

### 1. Navegação
```yaml
- action: go_to
  url: "/path"

- action: navigate
  menu_path: ["Menu", "Submenu"]

- action: go_to_url
  url: "https://example.com"

- action: back

- action: forward

- action: refresh
```

### 2. Interações
```yaml
- action: click
  selector: "button"
  description: "Botão submit"

- action: type
  selector: "input"
  text: "texto"

- action: fill
  value: "Campo = Valor"

- action: select
  selector: "select"
  option: "opção"

- action: hover
  selector: "element"

- action: drag
  source: ".draggable"
  target: ".dropzone"

- action: scroll
  direction: "down"
  amount: 500
```

### 3. Autenticação
```yaml
- action: login
  username: "user"
  password: "pass"
  url: "/login"

- action: logout
```

### 4. Esperas
```yaml
- action: wait
  seconds: 1.0

- action: wait_for
  selector: ".element"
  timeout: 5000

- action: wait_for_url
  url: "/dashboard"
  timeout: 5000

- action: wait_for_text
  selector: ".message"
  text: "Sucesso"
  timeout: 5000
```

### 5. Assertions
```yaml
- action: assert_text
  selector: ".message"
  expected: "Sucesso"

- action: assert_visible
  selector: ".element"

- action: assert_count
  selector: ".items"
  expected: 5

- action: assert_attr
  selector: "input"
  attribute: "disabled"
  expected: "true"

- action: assert_url
  expected: "/dashboard"
```

### 6. Screenshot
```yaml
- action: screenshot
  name: "tela-inicial"
  full_page: false
  element: ".container"  # opcional
```

### 7. Queries (leitura)
```yaml
- action: get_text
  selector: ".message"
  # Retorna texto (não é ação YAML, mas método disponível)

- action: get_attr
  selector: "input"
  attribute: "value"
  # Retorna atributo
```

---

## Ações que NÃO são Core (devem ser extensões)

### ❌ Vídeo
```yaml
- action: video.start_recording
- action: video.stop_recording
- action: video.pause
- action: video.resume
```

### ❌ Áudio
```yaml
- action: audio.speak
  text: "Texto para narração"
```

### ❌ Legendas
```yaml
- action: subtitles.generate
- action: subtitles.embed
```

### ❌ Acessibilidade
```yaml
- action: accessibility.check
- action: accessibility.report
```

### ❌ Performance
```yaml
- action: performance.metrics
- action: performance.report
```

### ❌ Odoo Específico
```yaml
- action: go_to
  value: "Vendas > Pedidos"  # Formato específico Odoo

- action: open_filters

- action: filter_by
  value: "Consumidor"

- action: add_line
  value: "Adicionar linha"
```

### ❌ ForgeERP Específico
```yaml
- action: go_to_provision
- action: fill_provision_form
- action: provision_client
```

---

## Estrutura YAML Core

```yaml
name: "Teste Básico"
description: "Teste genérico para qualquer aplicação web"

steps:
  - action: go_to
    url: "/login"
  
  - action: login
    username: "admin"
    password: "senha123"
  
  - action: go_to
    url: "/dashboard"
  
  - action: click
    selector: "button:has-text('Criar')"
    description: "Botão criar"
  
  - action: type
    selector: "input[name='name']"
    text: "Item Teste"
  
  - action: assert_text
    selector: ".success-message"
    expected: "Item criado"
  
  - action: screenshot
    name: "resultado-final"
```

---

## Princípios

1. **Genérico**: Funciona para qualquer aplicação web
2. **Simples**: Fácil de entender e usar
3. **Mínimo**: Apenas o essencial
4. **Extensível**: Extensões podem adicionar ações

---

## Implementação no YAML Parser

O parser core deve:
1. Suportar apenas ações core listadas acima
2. Permitir que extensões registrem suas ações
3. Executar ações de extensões se registradas
4. Falhar graciosamente se ação não for encontrada (core ou extensão)

