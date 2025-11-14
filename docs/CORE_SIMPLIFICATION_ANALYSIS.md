# Análise de Simplificação - Teste Core vs Odoo

## Objetivo

Reescrever um teste YAML do Odoo usando apenas ações core para identificar:
1. O que funciona
2. O que precisa ser simplificado
3. O que precisa ser adicionado ao core
4. O que deve permanecer como extensão

---

## Teste Original (Odoo)

```yaml
steps:
  - login: maria.santos@racco.com.br
    password: demo123
    database: devel
  
  - go_to: "Dashboard"
  - go_to: "Contatos"
  - open_filters: true
  - go_to: "Vendas > Pedidos"
  - go_to: "Vendas > Produtos"
  - go_to: "Portal"
```

---

## Teste Reescrito (Core Only)

```yaml
steps:
  # PROBLEMA 1: Login não suporta "database"
  - action: go_to
    url: /web/login
  - action: type
    selector: input[name="login"]
    text: maria.santos@racco.com.br
  - action: type
    selector: input[name="password"]
    text: demo123
  - action: type
    selector: input[name="db"]
    text: devel
  - action: click
    selector: button[type="submit"]
  
  # PROBLEMA 2: go_to não entende "Dashboard"
  - action: navigate
    menu_path: ["Dashboard"]
  
  # PROBLEMA 3: go_to não entende "Contatos"
  - action: navigate
    menu_path: ["Contatos"]
  
  # PROBLEMA 4: open_filters não existe
  - action: click
    selector: ".o_filters_menu button"
  
  # PROBLEMA 5: go_to não entende "Vendas > Pedidos"
  - action: navigate
    menu_path: ["Vendas", "Pedidos"]
```

---

## Problemas Identificados

### 1. Login não suporta parâmetros específicos do Odoo

**Problema:**
- Core `login()` aceita apenas `username`, `password`, `login_url`
- Odoo precisa de `database` também

**Solução Atual:**
- Preencher campos manualmente com `type()`

**Solução Proposta:**
- Adicionar suporte a `**kwargs` no `login()` core
- Ou criar extensão Odoo que sobrescreve `login()`

**Decisão:**
- ✅ **Manter no core genérico**: `login()` com `**kwargs` para parâmetros extras
- ✅ **Extensão Odoo**: Usa `login()` core com `database` em kwargs

---

### 2. Navegação por menu não é user-friendly

**Problema:**
- Core `go_to()` aceita apenas URLs
- Odoo usa `go_to: "Vendas > Pedidos"` (user-friendly)
- Core tem `navigate()` com array, mas não é tão user-friendly

**Solução Atual:**
- Usar `navigate(menu_path: ["Vendas", "Pedidos"])`

**Solução Proposta:**
- Adicionar suporte a string com `>` no `go_to()` core
- Ou melhorar `navigate()` para aceitar string também

**Decisão:**
- ✅ **Melhorar core**: `go_to()` deve tentar detectar se é menu path (contém `>`)
- ✅ **Se for menu path**: Delegar para `navigate()` automaticamente
- ✅ **Mantém genérico**: Funciona para qualquer app com menus hierárquicos

---

### 3. Ações específicas do Odoo não existem

**Problema:**
- `open_filters` é específico do Odoo
- Não faz sentido adicionar ao core

**Solução:**
- ✅ **Manter como extensão Odoo**: `open_filters` permanece específico
- ✅ **Core genérico**: Usar `click()` com seletor CSS quando necessário

**Decisão:**
- ✅ **Correto**: Ações muito específicas devem ficar em extensões

---

### 4. Navegação user-friendly não funciona

**Problema:**
- `go_to: "Dashboard"` não funciona no core
- Precisa usar `navigate(["Dashboard"])` ou URL direta

**Solução Proposta:**
- Adicionar mapeamento de termos user-friendly no core
- Exemplo: "Dashboard" → tenta encontrar link/logo para home

**Decisão:**
- ⚠️ **Avaliar**: Pode ser muito específico para core
- ✅ **Alternativa**: Extensão pode adicionar mapeamentos
- ✅ **Core mínimo**: Manter apenas URLs e arrays de menu

---

## Simplificações Propostas

### 1. Melhorar `login()` para aceitar kwargs

```python
async def login(
    self,
    username: str,
    password: str,
    login_url: str = "/login",
    **kwargs  # Para parâmetros extras (database, etc)
) -> 'AuthMixin':
    # ... código atual ...
    
    # Preencher campos extras de kwargs
    for field_name, field_value in kwargs.items():
        selectors = [
            f'input[name="{field_name}"]',
            f'input[id="{field_name}"]',
            f'#{field_name}',
        ]
        for selector in selectors:
            try:
                await self.type(selector, str(field_value), f"{field_name} field")
                break
            except:
                continue
```

**Benefício:**
- ✅ Core genérico funciona com qualquer app
- ✅ Extensões podem passar parâmetros extras
- ✅ Não quebra compatibilidade

---

### 2. Melhorar `go_to()` para detectar menu paths

```python
async def go_to(self, url_or_path: str) -> 'NavigationMixin':
    # Se contém ">", tratar como menu path
    if ">" in url_or_path:
        menu_path = [item.strip() for item in url_or_path.split(">")]
        return await self.navigate(menu_path)
    
    # Caso contrário, tratar como URL
    # ... código atual ...
```

**Benefício:**
- ✅ User-friendly: `go_to: "Vendas > Pedidos"` funciona
- ✅ Genérico: Funciona para qualquer app com menus
- ✅ Não quebra compatibilidade: URLs continuam funcionando

---

### 3. Melhorar `navigate()` para aceitar string ou array

```python
async def navigate(self, menu_path: Union[str, List[str]]) -> 'NavigationMixin':
    # Se string, converter para array
    if isinstance(menu_path, str):
        if ">" in menu_path:
            menu_path = [item.strip() for item in menu_path.split(">")]
        else:
            menu_path = [menu_path]
    
    # ... código atual ...
```

**Benefício:**
- ✅ Mais flexível
- ✅ User-friendly
- ✅ Não quebra compatibilidade

---

## Checklist de Implementação

- [ ] Adicionar `**kwargs` ao `login()` core
- [ ] Melhorar `go_to()` para detectar menu paths
- [ ] Melhorar `navigate()` para aceitar string
- [ ] Testar com teste reescrito
- [ ] Documentar mudanças

---

## Conclusão

### O que funciona bem no core:
- ✅ `click()`, `type()`, `screenshot()` - genéricos e funcionam
- ✅ `go_to()` com URLs - funciona perfeitamente
- ✅ `navigate()` com arrays - funciona, mas pode ser melhorado

### O que precisa ser melhorado:
- ⚠️ `login()` - adicionar suporte a kwargs
- ⚠️ `go_to()` - detectar menu paths automaticamente
- ⚠️ `navigate()` - aceitar string além de array

### O que deve permanecer em extensões:
- ✅ `open_filters` - muito específico do Odoo
- ✅ Navegação específica do Odoo (se houver)
- ✅ Formulários específicos do Odoo

---

## Próximos Passos

1. Implementar melhorias no core
2. Testar com teste reescrito
3. Atualizar documentação
4. Criar exemplos de uso


