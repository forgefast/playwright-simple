# Cursor System - TDD Guidelines

## Princípios TDD

**TODAS as funcionalidades do cursor devem ser testadas ANTES de serem implementadas.**

### Regra de Ouro

> Se não está no teste, não existe. Se não passa no teste, não funciona.

## Comportamentos Críticos (Definidos por Testes)

### 1. Persistência de Posição Após Navegação

**Teste:** `test_cursor_position_saved_before_link_click`

**Comportamento Esperado:**
- Quando o cursor está em posição (x, y)
- E clica em um link que causa navegação
- A posição (x, y) deve ser salva **ANTES** da navegação acontecer
- Após navegação, o cursor deve ser restaurado na mesma posição (x, y)
- **NUNCA** deve ser criado no centro após navegação

**Implementação:**
- Salvar posição em `sessionStorage` e `window.__playwright_cursor_last_position` ANTES do clique
- Restaurar posição após evento `framenavigated`
- Usar posição salva ao criar cursor após navegação

### 2. Cursor Não no Centro Após Navegação

**Teste:** `test_cursor_not_created_at_center_after_link_navigation`

**Comportamento Esperado:**
- Cursor em posição (x, y) antes de clicar em link
- Após navegação, cursor deve ser restaurado em (x, y)
- **NUNCA** deve aparecer no centro da tela

**Implementação:**
- Verificar `sessionStorage` e `window.__playwright_cursor_last_position` ao criar cursor
- Se posição salva existe, usar ela (não centro)
- Se não existe, usar centro apenas na primeira vez

### 3. Múltiplas Navegações

**Teste:** `test_cursor_position_persisted_across_multiple_navigations`

**Comportamento Esperado:**
- Cursor mantém posição através de múltiplas navegações
- Posição persiste em `sessionStorage` (sobrevive a reloads)

**Implementação:**
- Sempre salvar posição em `sessionStorage` após cada movimento
- Sempre restaurar de `sessionStorage` após cada navegação

## Como Trabalhar com TDD

### 1. Escrever Teste Primeiro

```python
@pytest.mark.asyncio
async def test_novo_comportamento(browser_page: Page):
    """
    TDD: Descrição do comportamento esperado.
    
    Comportamento esperado:
    - Condição 1
    - Condição 2
    - Resultado esperado
    """
    # Arrange
    # Act
    # Assert
```

### 2. Teste Deve Falhar Inicialmente

- Execute o teste
- Deve falhar (comportamento ainda não implementado)
- Isso confirma que o teste está correto

### 3. Implementar Mínimo para Passar

- Implemente apenas o necessário para o teste passar
- Não adicione funcionalidades extras

### 4. Refatorar

- Após teste passar, refatore se necessário
- Teste deve continuar passando

## Checklist Antes de Commitar

- [ ] Todos os testes TDD passam
- [ ] Novo comportamento tem teste correspondente
- [ ] Testes existentes ainda passam (não quebrou nada)
- [ ] Comportamento está documentado no README

## Testes Existentes

### `tests/test_cursor_navigation.py`
- `test_cursor_position_saved_before_link_click`
- `test_cursor_not_created_at_center_after_link_navigation`
- `test_cursor_position_persisted_across_multiple_navigations`

### `tests/test_login_validation.py`
- `test_cursor_position_after_navigation`
- `test_cursor_not_created_at_center_after_navigation`

## Arquivos Relacionados

- `playwright_simple/core/cursor.py` - CursorManager
- `playwright_simple/core/cursor_elements.py` - Criação de elementos
- `playwright_simple/core/cursor_movement.py` - Movimento e persistência
- `playwright_simple/core/recorder/cursor_controller/movement.py` - Movimento no recorder
- `playwright_simple/core/playwright_commands/element_interactions/click_handler.py` - Clique em links

## Padrões de Código

### Salvar Posição

```python
await self.page.evaluate(f"""
    () => {{
        const position = {{x: {x}, y: {y}}};
        window.__playwright_cursor_last_position = position;
        try {{
            sessionStorage.setItem('__playwright_cursor_last_position', JSON.stringify(position));
        }} catch (e) {{
            // sessionStorage might not be available
        }}
    }}
""")
```

### Restaurar Posição

```python
position = await self.page.evaluate("""
    () => {{
        try {{
            const stored = sessionStorage.getItem('__playwright_cursor_last_position');
            if (stored) return JSON.parse(stored);
        }} catch (e) {{
        }}
        return window.__playwright_cursor_last_position || null;
    }}
""")
```

## Notas Importantes

1. **Sempre salvar antes de navegação**: Posição deve ser salva ANTES do clique causar navegação
2. **sessionStorage é persistente**: Sobrevive a reloads dentro da mesma sessão
3. **window property é fallback**: Usado quando sessionStorage não está disponível
4. **Centro é apenas fallback**: Usar centro apenas quando não há posição salva

