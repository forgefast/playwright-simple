# Análise de Funcionalidades - Presentation vs Extensão Odoo

## Objetivo
Revisar funcionalidades usadas nos testes do `presentation/` e decidir quais implementar/melhorar na extensão Odoo.

---

## Funcionalidades Identificadas nos Testes do Presentation

### 1. Autenticação
**YAML:**
```yaml
- login: admin
  password: admin
  database: devel
- logout:
```

**Status na Extensão:** ✅ **IMPLEMENTADO**
- `OdooAuthMixin.login()` - Implementado
- `OdooAuthMixin.logout()` - Implementado
- Suporta database opcional
- Suporta cursor visual

**Ação:** Manter como está

---

### 2. Navegação
**YAML:**
```yaml
- go_to: "Dashboard"
- go_to: "Vendas > Pedidos"
- go_to: "Vendas > Configuração"
```

**Status na Extensão:** ✅ **IMPLEMENTADO**
- `OdooNavigationMixin.go_to()` - Implementado
- `OdooNavigationMixin.go_to_menu()` - Implementado
- `OdooNavigationMixin.go_to_dashboard()` - Implementado
- Suporta menu path com `>`

**Ação:** Manter como está

---

### 3. Interações Básicas
**YAML:**
```yaml
- click: "Criar"
- click: "Salvar"
- click: "Confirmar"
```

**Status na Extensão:** ✅ **IMPLEMENTADO**
- `OdooFormsMixin.click()` - Implementado
- `OdooFormsMixin.click_button()` - Implementado
- Suporta texto e CSS selectors
- Suporta contexto (wizard/form)

**Ação:** Manter como está

---

### 4. Preenchimento de Campos
**YAML:**
```yaml
- fill: "Cliente = João Silva"
- fill: "Quantidade = 10"
- fill: "Produto = Batom"
```

**Status na Extensão:** ✅ **IMPLEMENTADO**
- `OdooFormsMixin.fill()` - Implementado
- Suporta sintaxe `"Label = Valor"`
- Suporta argumentos separados: `fill("Label", "Valor")`
- Suporta contexto opcional

**Ação:** Manter como está

---

### 5. Adicionar Linhas (One2many)
**YAML:**
```yaml
- add_line: "Adicionar linha"
```

**Status na Extensão:** ✅ **IMPLEMENTADO**
- `OdooCRUDMixin.add_line()` - Implementado
- Suporta texto do botão customizado

**Ação:** Manter como está

---

### 6. Busca
**YAML:**
```yaml
- search: "Revendedor"
- search: "Bronze"
- search: "Rascunho"
```

**Status na Extensão:** ⚠️ **PARCIALMENTE IMPLEMENTADO**
- `OdooCRUDMixin.search_and_open()` - Existe mas é para abrir registro
- Não há método específico para apenas buscar/filtrar na lista

**Ação:** 
- ✅ Implementar `search()` ou `filter()` para buscar na lista atual
- Pode usar campo de busca genérico do Odoo

---

### 7. Abrir Registro
**YAML:**
```yaml
- open_record: "Pedido"
  position: primeiro
- open_record: "João Silva"
  position: último
```

**Status na Extensão:** ✅ **IMPLEMENTADO**
- `OdooCRUDMixin.open_record()` - Implementado
- Suporta position: "primeiro", "segundo", "último"

**Ação:** Manter como está

---

### 8. Abrir Filtros
**YAML:**
```yaml
- open_filters: true
```

**Status na Extensão:** ✅ **IMPLEMENTADO**
- `ActionParser` suporta `open_filters`
- Usa `FilterHelper.open_filter_menu()`

**Ação:** Manter como está

---

### 9. Wait/Delay
**YAML:**
```yaml
- wait: 0.2
- wait: 1.0
```

**Status na Extensão:** ✅ **IMPLEMENTADO (via SimpleTestBase)**
- `SimpleTestBase.wait()` - Herdado
- `OdooWaitMixin.wait_until_ready()` - Específico Odoo

**Ação:** Manter como está

---

### 10. Screenshot
**YAML:**
```yaml
- screenshot: login_success
  description: Tela após login
```

**Status na Extensão:** ✅ **IMPLEMENTADO (via SimpleTestBase)**
- `SimpleTestBase.screenshot()` - Herdado
- Suporta descrição

**Ação:** Manter como está

---

### 11. Criar Registro (CRUD)
**YAML:**
```yaml
# Não encontrado nos YAMLs do presentation, mas seria útil:
- create:
    model: sale.order
    fields:
      partner_id: "Cliente Teste"
      order_line:
        - product_id: "Produto 1"
          quantity: 10
```

**Status na Extensão:** ✅ **IMPLEMENTADO**
- `OdooCRUDMixin.create_record()` - Implementado
- Suporta model e fields dict

**Ação:** Manter como está (não usado no presentation, mas útil)

---

### 12. Press Key
**YAML:**
```yaml
# Não encontrado nos YAMLs, mas mencionado no ActionParser:
- press: "Escape"
- press: "Enter"
- press: "Tab"
```

**Status na Extensão:** ⚠️ **DEPRECADO**
- `ActionParser` tem suporte mas marca como DEPRECATED
- Deve usar métodos com cursor_manager

**Ação:** 
- ❌ Remover do ActionParser ou manter apenas para compatibilidade
- ✅ Usar `page.keyboard.press()` diretamente quando necessário

---

## Funcionalidades NÃO Encontradas nos Testes do Presentation

### 1. Assert/Validação
**Não encontrado nos YAMLs:**
```yaml
# Seria útil mas não está sendo usado:
- assert:
    field: "Total"
    value: "R$ 1.000,00"
```

**Status na Extensão:** ❓ **NÃO IMPLEMENTADO**
- Não há método específico de assert
- Pode usar `SimpleTestBase.assert_*` herdados

**Ação:** 
- ⚠️ Avaliar se necessário
- Se sim, implementar `assert_field_value()`, `assert_record_exists()`

---

### 2. Validação de Steps
**Encontrado em `validate_step.py`:**
- `StepValidator` - Valida se steps foram executados com sucesso
- Validações específicas por ação (click, type, submit, go_to, wait, screenshot, search, login)

**Status na Extensão:** ❌ **NÃO IMPLEMENTADO**

**Ação:**
- ✅ **IMPLEMENTAR** - Muito útil para garantir que testes funcionam
- Integrar com `OdooYAMLParser` ou criar `OdooStepValidator`
- Pode ser opcional (ativar via config)

---

### 3. Action Mapper
**Encontrado em `action_mapper.py`:**
- `ActionMapper` - Converte ações Odoo para comandos básicos do recorder
- Usado para compatibilidade com recorder antigo

**Status na Extensão:** ❌ **NÃO IMPLEMENTADO**

**Ação:**
- ⚠️ **AVALIAR NECESSIDADE**
- Se o recorder já suporta ações Odoo diretamente, não é necessário
- Pode ser útil para migração de testes antigos

---

## Resumo de Decisões

### ✅ Manter/Confirmar (Já Implementado)
1. ✅ `login` / `logout`
2. ✅ `go_to` (menu navigation)
3. ✅ `click` / `click_button`
4. ✅ `fill` (com sintaxe `"Label = Valor"`)
5. ✅ `add_line`
6. ✅ `open_record` (com position)
7. ✅ `open_filters`
8. ✅ `wait`
9. ✅ `screenshot`
10. ✅ `create_record` (não usado no presentation, mas útil)

### ⚠️ Implementar/Melhorar
1. ⚠️ **`search()` / `filter()`** - Buscar/filtrar na lista atual
   - Prioridade: **ALTA** (usado em vários YAMLs)
   - Implementar em `OdooNavigationMixin` ou `OdooCRUDMixin`

2. ⚠️ **`StepValidator`** - Validação de steps após execução
   - Prioridade: **MÉDIA** (útil para garantir qualidade)
   - Criar `OdooStepValidator` baseado em `validate_step.py`

3. ⚠️ **`assert_field_value()`** - Assert de valores de campos
   - Prioridade: **BAIXA** (não usado no presentation)
   - Implementar se necessário para testes mais robustos

### ❌ Remover/Deprecar
1. ❌ **`press`** - Marcar como deprecated ou remover
   - Já está marcado como DEPRECATED no ActionParser
   - Usar `page.keyboard.press()` diretamente quando necessário

---

## Plano de Implementação

### Fase 1: Funcionalidades Críticas (Alta Prioridade)
1. ✅ Implementar `search()` / `filter()` para buscar na lista
   - Método: `async def search(self, text: str, field: Optional[str] = None)`
   - Localização: `OdooNavigationMixin` ou novo `OdooSearchMixin`

### Fase 2: Melhorias (Média Prioridade)
2. ✅ Implementar `OdooStepValidator`
   - Baseado em `validate_step.py`
   - Integrar com `OdooYAMLParser`
   - Ativar via config: `config.validate_steps = True`

### Fase 3: Opcionais (Baixa Prioridade)
3. ⚠️ Implementar asserts específicos Odoo (se necessário)
4. ⚠️ Avaliar necessidade de `ActionMapper` (provavelmente não necessário)

---

## Notas Finais

- A extensão Odoo já cobre **~90%** das funcionalidades usadas no presentation
- Principais gaps: `search()` e validação de steps
- A maioria das funcionalidades está bem implementada e funcionando
- Foco deve ser em **completar funcionalidades críticas** e **melhorar robustez**

