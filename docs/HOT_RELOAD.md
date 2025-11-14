# Hot Reload - Implementação Completa

## Visão Geral

O hot reload permite modificar o arquivo YAML durante a execução do teste, e as mudanças são aplicadas automaticamente sem reiniciar o teste.

## Como Funciona

### 1. Detecção Automática

O sistema verifica se o arquivo YAML foi modificado antes de cada step:

```python
# Em yaml_parser.py
if yaml_file_path and yaml_file_path.exists():
    current_mtime = yaml_file_path.stat().st_mtime
    if yaml_mtime and current_mtime > yaml_mtime:
        # Recarregar YAML
```

### 2. Recarregamento

Quando uma mudança é detectada:

1. O YAML é recarregado do arquivo
2. Os steps já executados são mantidos
3. Os steps restantes são substituídos pelos novos do YAML
4. A execução continua do ponto atual

### 3. Flag Manual

Você também pode forçar reload via debug extension:

```python
# No modo interativo, pressione 'r' + Enter
# Ou via código:
test._yaml_reload_requested = True
```

## Uso

### Modo Automático

Simplesmente modifique o arquivo YAML durante a execução:

```bash
# Terminal 1: Executar teste
playwright-simple run test.yaml --hot-reload

# Terminal 2: Modificar YAML
vim test.yaml  # Fazer alterações
# Salvar - o hot reload detecta automaticamente
```

### Modo Interativo

No modo interativo, você pode forçar reload:

```
🔍 DEBUG: Pausando antes do passo 3
Comandos disponíveis:
  [c] - Continuar
  [r] - Hot reload YAML and continue
  [s] - Skip step
  [q] - Quit

> r
✅ Hot reload: Flag definido, YAML será recarregado no próximo step.
🔄 Hot reload: Recarregando YAML...
✅ YAML recarregado! 5 steps disponíveis
```

## Integração com Auto-Fix Runner

O `auto_fix_runner.py` usa hot reload automaticamente:

1. Detecta erro
2. Corrige o YAML
3. Hot reload detecta a mudança
4. Teste continua com correção aplicada

```python
# Em auto_fix_runner.py
if self.yaml_fixer.fix_error(error_info):
    # YAML foi modificado
    # Hot reload detectará automaticamente na próxima iteração
    time.sleep(0.5)  # Dar tempo para detectar
```

## Detalhes Técnicos

### Armazenamento de Estado

- **YAML Path**: Armazenado na função de teste (`test_function._yaml_path`)
- **Mtime**: Timestamp da última modificação
- **Step Index**: Índice do step atual (para manter steps já executados)

### Preservação de Contexto

O hot reload preserva:
- ✅ Variáveis do contexto (`context['vars']`)
- ✅ Estado da página (`current_state`)
- ✅ Steps já executados
- ✅ Configuração do teste

### Limitações

- ⚠️ Não recarrega `setup` ou `teardown` steps
- ⚠️ Não recarrega configuração (`config`)
- ⚠️ Mudanças em `base_url` não são aplicadas
- ⚠️ Variáveis já definidas são mantidas

## Exemplo Completo

```yaml
# test.yaml
steps:
  - action: go_to
    url: /page1
  - action: click
    selector: button1  # Este step falhará
  - action: click
    selector: button2
```

**Durante execução:**

1. Step 1 executa: `/page1` carregado
2. Step 2 falha: `button1` não encontrado
3. Auto-fix corrige YAML:
   ```yaml
   steps:
     - action: go_to
       url: /page1
     - action: wait
       seconds: 2
     - action: click
       selector: button1  # Agora com wait antes
     - action: click
       selector: button2
   ```
4. Hot reload detecta mudança
5. Step 2 é recarregado (agora com wait)
6. Execução continua do step 2 corrigido

## Debug

Para ver logs de hot reload:

```bash
playwright-simple run test.yaml --hot-reload --log-level DEBUG
```

Logs esperados:
```
INFO: 🔄 Hot reload: YAML file modified, reloading...
INFO: Hot reload: 5 steps loaded
```

## Troubleshooting

### Hot reload não está funcionando

1. Verifique se `--hot-reload` está habilitado
2. Verifique se o arquivo YAML existe e é acessível
3. Verifique logs para erros de parsing

### Steps não estão sendo recarregados

- Hot reload só recarrega steps **futuros**
- Steps já executados são mantidos
- Se você quer reiniciar, pare e reinicie o teste

### Erro ao recarregar

- Verifique sintaxe YAML
- Verifique se há erros de parsing
- O sistema continua com steps antigos se reload falhar

