# Máquina de Estados - Core

## Visão Geral

Cada step no playwright-simple é uma **máquina de estados** que sabe:
1. **De onde veio** (estado anterior: posição do cursor, HTML, URL, etc.)
2. **O que faz** (a ação executada)
3. **Para onde vai** (estado resultante: nova posição do cursor, novo HTML, etc.)

Isso permite que steps tomem decisões baseadas no estado anterior e que o próximo step assuma de onde o anterior parou.

---

## WebState

A classe `WebState` captura o estado completo da aplicação web:

```python
@dataclass
class WebState:
    # URL e navegação
    url: str
    title: str
    
    # Posição do cursor
    cursor_x: Optional[float]
    cursor_y: Optional[float]
    
    # Estado da página
    scroll_x: float
    scroll_y: float
    viewport_width: int
    viewport_height: int
    
    # Estado do DOM
    html_hash: Optional[str]  # Hash do HTML para comparação rápida
    dom_ready: bool
    focused_element: Optional[str]
    
    # Estado de carregamento
    load_state: str  # none, load, domcontentloaded, networkidle
    
    # Informações do step
    step_number: Optional[int]
    action_type: Optional[str]
    
    # Metadados
    metadata: Dict[str, Any]
```

---

## Como Funciona

### 1. Captura de Estado

Antes de cada step, o estado atual é capturado:

```python
previous_state = await WebState.capture(test.page)
```

### 2. Execução do Step

O step recebe o estado anterior e executa sua ação:

```python
current_state = await YAMLParser._execute_step(
    step, 
    test, 
    base_dir, 
    context, 
    previous_state  # Estado anterior
)
```

### 3. Retorno do Novo Estado

Após a execução, o novo estado é capturado e retornado:

```python
# Após ação core
return await WebState.capture(test.page, step_number=..., action_type=...)
```

### 4. Passagem para Próximo Step

O estado retornado se torna o `previous_state` do próximo step:

```python
for step in steps:
    current_state = await YAMLParser._execute_step(step, test, base_dir, context, current_state)
    # current_state agora é o previous_state do próximo step
```

---

## Informações Capturadas

### Posição do Cursor
- Coordenadas X e Y do cursor visual
- Obtido do `cursor_manager` se disponível

### URL e Título
- URL atual da página
- Título da página

### Scroll e Viewport
- Posição de scroll (X, Y)
- Tamanho do viewport (width, height)

### DOM
- Hash do HTML (para comparação rápida)
- Estado de carregamento (DOM ready)
- Elemento focado (seletor)

### Elementos Interativos
- Contagem de elementos visíveis e interagíveis
- Armazenado em `metadata`

---

## Comparação de Estados

Você pode comparar dois estados para ver o que mudou:

```python
changes = new_state.changed_from(previous_state)
# Retorna:
# {
#     'url': {'from': '...', 'to': '...'},
#     'cursor': {'from': (x1, y1), 'to': (x2, y2)},
#     'html': {'from': 'hash1', 'to': 'hash2'},
#     ...
# }
```

---

## Uso em YAML

O estado anterior está disponível no contexto:

```yaml
steps:
  - action: click
    text: "Botão"
    # previous_state está disponível em context['previous_state']
  
  - if: "{{ previous_state.url != current_state.url }}"
    then:
      - action: wait
        seconds: 1
        description: "Aguardar navegação"
```

---

## Vantagens

1. **Rastreabilidade**: Cada step sabe exatamente de onde veio
2. **Decisões Inteligentes**: Steps podem tomar decisões baseadas no estado
3. **Debugging**: Fácil ver o que mudou entre steps
4. **Recuperação**: Possível retomar de um estado específico
5. **Validação**: Verificar se estado mudou como esperado

---

## Exemplo Completo

```python
# Step 1: Click em "Login"
previous_state = WebState(url="/", cursor=(100, 200), ...)
await test.click("Login")
current_state = WebState(url="/", cursor=(150, 250), html_hash="abc123", ...)

# Step 2: Type no campo (sabe que cursor está em (150, 250))
previous_state = current_state  # Estado do step anterior
await test.type("user@email.com")
current_state = WebState(url="/", cursor=(150, 300), html_hash="abc123", ...)

# Step 3: Click em "Entrar" (sabe que cursor está em (150, 300))
previous_state = current_state
await test.click("Entrar")
current_state = WebState(url="/dashboard", cursor=(200, 400), html_hash="def456", ...)
# URL mudou! Step sabe que navegação ocorreu
```

---

## Implementação

- **`core/state.py`**: Classe `WebState` e método `capture()`
- **`core/yaml_parser.py`**: Passa estado entre steps
- **`core/interactions.py`**: Pode usar estado para decisões (futuro)

---

## Próximos Passos

1. Usar estado em `interactions.py` para decisões inteligentes
2. Permitir steps acessarem `previous_state` e `current_state` no YAML
3. Adicionar validações baseadas em mudanças de estado
4. Suporte a rollback para estados anteriores

