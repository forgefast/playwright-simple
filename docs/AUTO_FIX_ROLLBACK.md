# Auto-Fix com Rollback de Passos

## Visão Geral

O sistema agora implementa **rollback automático de passos** com **correção automática**, permitindo que todos os problemas sejam corrigidos em uma única execução.

## Como Funciona

### 1. Execução com Retry

Quando um passo falha:
1. **Captura o estado antes do passo** (URL, scroll, cursor, etc.)
2. **Detecta o erro** e tenta corrigir automaticamente
3. **Faz rollback** para o estado anterior
4. **Re-executa o passo** com a correção aplicada
5. **Repete até 5 vezes** ou até o passo passar

### 2. Correção Automática

O `AutoFixer` tenta corrigir:

#### Erros de YAML:
- **ElementNotFoundError**: Adiciona `wait` antes do passo e aumenta `timeout`
- **TimeoutError**: Aumenta o `timeout` progressivamente
- **Unknown action**: Mapeia ações conhecidas (ex: `click_button` → `click`)
- **Missing fields**: Adiciona campos faltantes baseado na action
- **TypeError com argumentos**: Adiciona argumentos faltantes

#### Erros de Código Python:
- Detecta problemas e sugere correções
- Hot reload aplica correções automaticamente

### 3. Rollback de Estado

O sistema restaura:
- **URL**: Navega de volta se necessário
- **Scroll**: Restaura posição de scroll
- **Cursor**: Restaura posição do cursor (se disponível)
- **Estado da página**: Aguarda página estabilizar

## Exemplo de Fluxo

```
Passo 1: ✅ Sucesso
Passo 2: ✅ Sucesso
Passo 3: ❌ Erro (ElementNotFoundError)
  → 🔧 Correção: Adiciona wait + timeout
  → 🔄 Rollback para estado do Passo 2
  → 🔄 Re-executa Passo 3
  → ✅ Sucesso!
Passo 4: ✅ Sucesso
```

## Configuração

### Máximo de Tentativas

Por padrão, cada passo tem **5 tentativas**:

```python
max_retries = 5  # Em yaml_parser.py
```

### Desabilitar Auto-Fix

Para desabilitar correção automática, remova o bloco de auto-fix em `yaml_parser.py`.

## Logs

O sistema mostra:
- `⚠️  Erro no passo X`: Erro detectado
- `🔧 Correção automática aplicada`: Correção bem-sucedida
- `🔄 Rollback`: Estado restaurado
- `❌ Máximo de tentativas atingido`: Falha após todas as tentativas

## Limitações

1. **Estado do navegador**: Alguns estados podem não ser totalmente restaurados (ex: JavaScript executado)
2. **Sessão**: Cookies e localStorage são preservados, mas ações JavaScript podem ter efeitos colaterais
3. **Timeout**: Se o problema for fundamental (ex: elemento não existe), pode não ser corrigível automaticamente

## Benefícios

✅ **Uma execução corrige tudo**: Não precisa reiniciar o teste  
✅ **Rollback seguro**: Volta para estado conhecido antes de tentar novamente  
✅ **Correção inteligente**: Aplica correções baseadas no tipo de erro  
✅ **Feedback claro**: Mostra o que está sendo corrigido  
✅ **Produtividade**: Desenvolve e corrige ao mesmo tempo

