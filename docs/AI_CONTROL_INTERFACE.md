# AI Control Interface - Controle Direto do Navegador

## Visão Geral

Interface que permite à IA controlar diretamente o cursor e ações do Chromium através de comandos JSON.

## Como Usar

### 1. Iniciar Interface

```bash
python3 scripts/ai_control_interface.py --base-url http://localhost:18069 --no-headless
```

A interface ficará aguardando comandos em `/tmp/ai_commands.json`.

### 2. Enviar Comandos

Use o script helper:
```bash
python3 scripts/send_ai_command.py '{"command": "get_elements"}'
```

Ou escreva diretamente no arquivo:
```bash
echo '{"command": "click", "text": "Entrar"}' > /tmp/ai_commands.json
```

### 3. Ler Resposta

A resposta será salva em `/tmp/ai_response.json` e também retornada pelo script helper.

## Comandos Disponíveis

### `get_elements`
Obtém lista de botões e inputs disponíveis na página.

```json
{"command": "get_elements"}
```

**Resposta:**
```json
{
  "success": true,
  "message": "Elementos obtidos",
  "data": {
    "buttons": [
      {"text": "Entrar", "tag": "button", "id": "", "class": "btn-primary"},
      ...
    ],
    "inputs": [
      {"type": "text", "name": "login", "placeholder": "Email", ...},
      ...
    ]
  }
}
```

### `move_cursor`
Move cursor para um elemento.

```json
{"command": "move_cursor", "selector": "button[type='submit']"}
```
ou
```json
{"command": "move_cursor", "text": "Entrar"}
```

### `click`
Clica em um elemento (move cursor primeiro).

```json
{"command": "click", "text": "Entrar"}
```
ou
```json
{"command": "click", "selector": "button.btn-primary"}
```

### `type`
Digita texto em um campo.

```json
{"command": "type", "selector": "input[name='login']", "text": "admin@example.com"}
```

### `wait`
Aguarda um tempo.

```json
{"command": "wait", "seconds": 2.0}
```

### `get_html`
Obtém HTML completo e simplificado da página.

```json
{"command": "get_html"}
```

Salva em:
- `/tmp/playwright_html.html` - HTML completo
- `/tmp/playwright_html_simplified.json` - Elementos simplificados

### `navigate`
Navega para uma URL.

```json
{"command": "navigate", "url": "http://localhost:18069/web/login"}
```

## Fluxo de Trabalho

1. **Iniciar interface** em background
2. **Obter elementos** disponíveis: `get_elements`
3. **Analisar** quais elementos usar
4. **Mover cursor** para elemento: `move_cursor`
5. **Clicar** ou **digitar**: `click` / `type`
6. **Aguardar** se necessário: `wait`
7. **Repetir** até completar ação

## Exemplo Completo

```bash
# 1. Iniciar interface
python3 scripts/ai_control_interface.py --base-url http://localhost:18069 --no-headless &

# 2. Obter elementos
python3 scripts/send_ai_command.py '{"command": "get_elements"}'

# 3. Mover cursor para botão
python3 scripts/send_ai_command.py '{"command": "move_cursor", "text": "Entrar"}'

# 4. Clicar
python3 scripts/send_ai_command.py '{"command": "click", "text": "Entrar"}'
```

## Vantagens

- ✅ **Controle total** - IA decide cada ação
- ✅ **Visual** - Cursor se move na tela
- ✅ **Tempo real** - Comandos executados imediatamente
- ✅ **Feedback** - Respostas indicam sucesso/falha
- ✅ **Flexível** - Pode combinar comandos como necessário

