# Debugging Avançado

O playwright-simple fornece um sistema completo de debugging com logging avançado e uma extensão de debug interativa.

## Logging Avançado

### Configuração

O sistema de logging está integrado no core e pode ser configurado via YAML:

```yaml
config:
  logging:
    level: DEBUG  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    log_file: logs/test.log
    json_log: false  # true para formato JSON
    console_output: true
```

### Níveis de Log

- **DEBUG**: Informações detalhadas para debugging
- **INFO**: Informações gerais sobre execução
- **WARNING**: Avisos (ações deprecated, etc.)
- **ERROR**: Erros que não interrompem execução
- **CRITICAL**: Erros críticos
- **ACTION**: Ações do usuário (click, type, etc.)
- **STATE**: Mudanças de estado
- **ELEMENT**: Operações com elementos

### Exemplo de Log

```
🎬 [ACTION] | Test: login_test | Step: 1 | Action: click | Element: Login | Message: Clicking on element: Login
🎯 [ELEMENT] | Test: login_test | Step: 1 | Selector: button:has-text("Login") | Message: Element found
✅ [INFO] | Test: login_test | Step: 1 | Duration: 0.234s | Message: Click completed successfully
```

## Extensão de Debug

### Instalação

A extensão de debug está disponível automaticamente. Para habilitar:

```yaml
config:
  debug:
    enabled: true
    pause_on_error: true
    pause_on_element_not_found: true
    interactive_mode: true
    hot_reload_enabled: true
```

### Funcionalidades

#### 1. Pausa em Erros

Quando um erro ocorre, a extensão pausa a execução e entra em modo interativo:

```
================================================================================
🐛 DEBUG MODE - Interactive Debugging
================================================================================
Error: ElementNotFoundError: Element not found: "Submit"
Step: 5
Action: click
URL: https://example.com/form

Available commands:
  [h] - Show HTML snapshot
  [s] - Save HTML to file
  [c] - Continue execution
  [r] - Hot reload YAML and continue
  [q] - Quit and save checkpoint
  [i] - Inspect element (enter selector)
================================================================================

Debug> 
```

#### 2. Inspeção de HTML

Comando `h` - Mostra snapshot do HTML atual:
```
Debug> h

HTML Snapshot:
--------------------------------------------------------------------------------
<!DOCTYPE html>
<html>
<head>
  <title>Form Page</title>
</head>
<body>
  <form>
    <button id="submit-btn">Submit</button>
  </form>
</body>
</html>
--------------------------------------------------------------------------------
```

#### 3. Salvar HTML

Comando `s` - Salva HTML para arquivo:
```
Debug> s
HTML saved to: debug_html/snapshot_20240101_120000.html
```

#### 4. Inspecionar Elemento

Comando `i` - Inspeciona elemento específico:
```
Debug> i
Enter selector or text to find: submit-btn

Element found:
  Tag: BUTTON
  Text: Submit
  Position: {'x': 100, 'y': 200, 'width': 80, 'height': 30}
  Attributes: {
    "id": "submit-btn",
    "class": "btn-primary"
  }
```

#### 5. Hot Reload

Comando `r` - Recarrega YAML e continua:
```
Debug> r
Hot reload: YAML file will be reloaded on next step.
Note: You may need to restart the test for a clean video.
```

#### 6. Checkpoint

Comando `q` - Salva checkpoint e sai:
```
Debug> q
Checkpoint saved to: debug_checkpoints/checkpoint_20240101_120000.json
```

### Continuar de Checkpoint

Para continuar de um checkpoint salvo:

```python
from playwright_simple.extensions.debug import DebugExtension
from pathlib import Path
import json

# Carregar checkpoint
checkpoint_file = Path("debug_checkpoints/checkpoint_20240101_120000.json")
checkpoint = json.loads(checkpoint_file.read_text())

# Continuar execução
debug_ext = test.extensions.get('debug')
if debug_ext:
    await debug_ext.resume_from_checkpoint(checkpoint, page)
```

## Logging em Ações Core

Todas as ações core agora têm logging detalhado:

### Click

```python
# Log automático:
🎬 [ACTION] | Action: click | Element: Submit | Message: Clicking on element: Submit
🎯 [ELEMENT] | Element: Submit | Selector: button:has-text("Submit") | Message: Element found
✅ [INFO] | Duration: 0.234s | Message: Click completed successfully
```

### Type

```python
# Log automático:
🎬 [ACTION] | Action: type | Element: email | Message: Typing in element: email
✅ [INFO] | Duration: 0.456s | Message: Type completed successfully
```

### Navigate

```python
# Log automático:
🔄 [STATE] | Action: navigate | URL: https://example.com | Message: Navigating to URL
✅ [INFO] | Duration: 1.234s | Message: Navigation completed
```

## Configuração Completa

```yaml
name: Teste com Debug
description: Teste com logging e debug avançado

config:
  logging:
    level: DEBUG
    log_file: logs/test.log
    json_log: false
    console_output: true
  
  debug:
    enabled: true
    pause_on_error: true
    pause_on_element_not_found: true
    pause_on_navigation_error: true
    interactive_mode: true
    save_state_on_error: true
    state_dir: debug_states
    html_snapshot_dir: debug_html
    checkpoint_dir: debug_checkpoints
    hot_reload_enabled: true
    yaml_watch_enabled: true

steps:
  - action: click
    text: "Login"
    description: "Clicar em Login"
```

## Estrutura de Arquivos de Debug

```
debug_states/
  ├── error_20240101_120000.html
  ├── error_20240101_120000.json
  └── ...

debug_html/
  ├── snapshot_20240101_120000.html
  └── ...

debug_checkpoints/
  ├── checkpoint_20240101_120000.html
  ├── checkpoint_20240101_120000.json
  └── ...
```

## Dicas

1. **Use DEBUG level** durante desenvolvimento para ver todos os detalhes
2. **Salve HTML** quando encontrar erros para inspecionar depois
3. **Use checkpoints** para pausar e continuar testes longos
4. **Hot reload** permite iterar rapidamente sem reiniciar tudo
5. **JSON logs** são úteis para análise programática

## Integração com Testes

O debug extension é automaticamente integrado quando habilitado. Não precisa fazer nada especial - apenas configure no YAML e use!

