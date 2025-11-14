# Interface de Comunicação - Auto-Fix Runner

## Visão Geral

O sistema de comunicação permite que o `auto_fix_runner` se comunique com o processo do playwright em execução para:

1. **Obter informações** sobre o passo atual e erros
2. **Enviar comandos** (reload, continue, etc.)
3. **Corrigir erros manualmente** com base nas informações obtidas

## Como Funciona

### 1. Control Interface

O processo do playwright expõe informações via `ControlInterface`:

- **Estado do passo**: `/tmp/playwright_control/{test_name}_state.json`
- **Erros**: `/tmp/playwright_control/{test_name}_error.json`
- **Comandos**: `/tmp/playwright_control/{test_name}_command.json`

### 2. Fluxo de Comunicação

```
┌─────────────────┐         ┌──────────────────┐
│ auto_fix_runner │         │  Processo         │
│                 │         │  Playwright       │
└────────┬────────┘         └────────┬─────────┘
         │                            │
         │  1. Monitora output        │
         │───────────────────────────>│
         │                            │
         │  2. Detecta erro           │
         │<───────────────────────────│
         │                            │
         │  3. Lê estado do passo     │
         │     (state.json)           │
         │───────────────────────────>│
         │<───────────────────────────│
         │                            │
         │  4. Lê erro detalhado      │
         │     (error.json)           │
         │───────────────────────────>│
         │<───────────────────────────│
         │                            │
         │  5. Mostra informações     │
         │     para correção          │
         │                            │
         │  6. Você corrige YAML      │
         │                            │
         │  7. Hot reload detecta     │
         │     mudança automaticamente│
         │                            │
         │  8. Teste continua        │
         │<───────────────────────────│
```

## Uso

### Executar com Comunicação

```bash
python3 scripts/auto_fix_runner.py \
    examples/racco/test_simple_login.yaml \
    --base-url http://localhost:18069
```

### Quando um Erro Ocorre

O sistema mostra:

```
❌ ERRO DETECTADO: element_not_found

📍 INFORMAÇÕES DO PASSO ATUAL:
   Passo: 2
   Ação: click
   URL: http://localhost:18069/web
   Dados do passo:
     - selector: button#submit
     - text: Submit

📋 ERRO DO PROCESSO:
   Tipo: ElementNotFoundError
   Mensagem: Element not found: button#submit
   Passo: 2

📝 CONTEÚDO DO PASSO (YAML):
   action: click
   selector: button#submit
   text: Submit

💡 CORREÇÃO MANUAL:
   Arquivo: /path/to/test.yaml
   Passo: 2

⏳ Aguardando correção do YAML...
```

### Correção Manual

1. **Analise as informações** mostradas
2. **Edite o arquivo YAML** com a correção
3. **Salve o arquivo**
4. **Hot reload detecta automaticamente** e recarrega
5. **Teste continua** automaticamente

## Arquivos de Controle

### State File (`{test_name}_state.json`)

```json
{
  "test_name": "test_simple_login",
  "step_number": 2,
  "action": "click",
  "step_data": {
    "action": "click",
    "selector": "button#submit"
  },
  "url": "http://localhost:18069/web",
  "timestamp": "2025-11-14T03:33:35.867996",
  "error": null
}
```

### Error File (`{test_name}_error.json`)

```json
{
  "test_name": "test_simple_login",
  "step_number": 2,
  "error_type": "ElementNotFoundError",
  "error_message": "Element not found: button#submit",
  "timestamp": "2025-11-14T03:33:36.123456"
}
```

### Command File (`{test_name}_command.json`)

```json
{
  "command": "reload",
  "params": {},
  "timestamp": "2025-11-14T03:33:37.789012"
}
```

## Comandos Disponíveis

### reload

Força reload do YAML mesmo sem mudança de arquivo:

```python
runner.send_reload_command()
```

## Integração com Hot Reload

O hot reload funciona automaticamente:

1. **Detecção de mudança**: Compara mtime do arquivo
2. **Comando manual**: Via `command.json` com `"command": "reload"`
3. **Flag interna**: `test._yaml_reload_requested = True`

## Exemplo Completo

```python
# No auto_fix_runner
error_details = self.handle_error(error_info)

# Mostra informações
# Você analisa e corrige o YAML manualmente

# Hot reload detecta mudança automaticamente
# Teste continua
```

## Troubleshooting

### Estado não está sendo salvo

- Verifique se `ControlInterface` foi inicializado no test instance
- Verifique permissões em `/tmp/playwright_control/`

### Comandos não são recebidos

- Verifique se o arquivo `command.json` está sendo criado
- Verifique se o processo está verificando comandos (timeout de 0.1s)

### Hot reload não funciona

- Verifique se `--hot-reload` está habilitado
- Verifique se o arquivo YAML existe e é acessível
- Verifique logs para erros de parsing

