# Python Hot Reload

## Visão Geral

O sistema agora suporta **hot reload automático para código Python**, além do hot reload de YAML que já existia. Isso permite corrigir erros na biblioteca `playwright-simple` durante a execução dos testes, sem precisar reiniciar o processo.

## Como Funciona

### 1. Monitoramento Automático

O sistema monitora todos os arquivos `.py` no diretório `playwright_simple/` usando **watchdog** (já instalado no projeto).

### 2. Detecção de Mudanças

Antes de cada step do teste, o sistema:
- Verifica se algum arquivo Python foi modificado
- Compara timestamps (mtime) dos arquivos
- Recarrega automaticamente os módulos modificados

### 3. Recarregamento de Módulos

Usa `importlib.reload()` para recarregar:
- O módulo modificado
- Todos os submódulos relacionados (ex: `playwright_simple.core.interactions.click_interactions` recarrega também seus submódulos)

## Uso

### Automático (Recomendado)

O hot reload é **ativado automaticamente** quando você executa testes com `--hot-reload`:

```bash
python3 -m playwright_simple.cli run test.yaml --hot-reload
```

### Manual

Você também pode recarregar módulos manualmente durante o debug interativo:

```python
from playwright_simple.core.python_reloader import reload_module

# Recarregar um módulo específico
reload_module('playwright_simple.core.interactions.click_interactions')
```

## Exemplo de Uso

1. **Execute o teste em background:**
   ```bash
   python3 scripts/auto_fix_runner.py test.yaml
   ```

2. **Encontre um erro no código:**
   ```
   TypeError: StructuredLogger.element() missing 1 required positional argument: 'element'
   ```

3. **Corrija o código:**
   ```python
   # playwright_simple/core/interactions/click_interactions.py
   structured_logger.element(
       "Mensagem",
       element=text_or_selector,  # ← Adicione este argumento
       action="click"
   )
   ```

4. **Salve o arquivo** - O hot reload detecta automaticamente e recarrega!

5. **O teste continua** com o código corrigido, sem precisar reiniciar.

## Arquitetura

```
┌─────────────────────────────────┐
│  Test Execution Loop            │
│  (yaml_parser.py)               │
│                                 │
│  Antes de cada step:            │
│  1. Verifica mudanças Python    │
│  2. Recarrega módulos           │
│  3. Verifica mudanças YAML      │
│  4. Executa step                │
└─────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│  PythonModuleReloader           │
│  (python_reloader.py)           │
│                                 │
│  - Watchdog monitora .py        │
│  - Mapeia arquivos → módulos    │
│  - importlib.reload()           │
└─────────────────────────────────┘
```

## Limitações

1. **Estado do objeto**: Objetos já instanciados não são atualizados automaticamente. Novas instâncias usarão o código novo.

2. **Imports circulares**: Módulos com imports circulares podem ter problemas ao recarregar.

3. **Código em execução**: Código que está sendo executado no momento do reload pode não ser atualizado imediatamente.

## Debugging

Para ver logs do hot reload:

```bash
# Ver logs em tempo real
tail -f /tmp/playwright_runner.log | grep -i "hot reload"
```

Ou configure o nível de log:

```python
import logging
logging.getLogger('playwright_simple.core.python_reloader').setLevel(logging.DEBUG)
```

## Comparação: YAML vs Python Hot Reload

| Aspecto | YAML Hot Reload | Python Hot Reload |
|---------|----------------|-------------------|
| **Detecção** | Polling (mtime) | Watchdog (inotify) |
| **Recarregamento** | Re-parse YAML | importlib.reload() |
| **Escopo** | Apenas steps | Módulos Python |
| **Performance** | Muito rápido | Rápido |
| **Limitações** | Nenhuma | Estado de objetos |

## Benefícios

✅ **Desenvolvimento mais rápido**: Corrija erros sem reiniciar testes  
✅ **Feedback imediato**: Veja mudanças instantaneamente  
✅ **Menos interrupções**: Continue testando enquanto corrige  
✅ **Produtividade**: Especialmente útil durante desenvolvimento da biblioteca

