# Servidor de Comandos para Processos em Background

Este documento explica como enviar comandos para um processo em background usando named pipes (FIFOs).

## Método 1: Named Pipes (FIFOs) - Recomendado

### Como Funciona

1. **Servidor cria pipes**: O processo em background cria dois pipes (comandos e respostas)
2. **Cliente escreve no pipe de comandos**: Você envia comandos escrevendo no pipe
3. **Servidor lê e processa**: O servidor lê o comando e executa a ação
4. **Servidor escreve resposta**: O servidor escreve a resposta no pipe de respostas

### Exemplo Prático

#### 1. Iniciar o Servidor

```bash
# Em background
python3 scripts/command_server.py &

# Ou com nohup para persistir após logout
nohup python3 scripts/command_server.py > /tmp/command_server.log 2>&1 &
```

#### 2. Enviar Comandos

```bash
# Método 1: Usando o script helper
./scripts/send_command.sh reload
./scripts/send_command.sh pause
./scripts/send_command.sh status

# Método 2: Diretamente via echo
echo "reload" > /tmp/playwright_commands
echo "pause" > /tmp/playwright_commands
echo "continue" > /tmp/playwright_commands
echo "status" > /tmp/playwright_commands
echo "quit" > /tmp/playwright_commands
```

#### 3. Ler Respostas

```bash
# Ler resposta (bloqueia até receber)
cat /tmp/playwright_responses

# Ou em background
tail -f /tmp/playwright_responses
```

### Comandos Disponíveis

- `reload` - Recarrega configuração/código
- `pause` - Pausa execução
- `continue` - Continua execução
- `status` - Mostra status do servidor
- `quit` / `exit` - Encerra o servidor

## Método 2: Socket TCP (Mais Avançado)

Para comunicação entre máquinas diferentes ou mais robustez:

```python
# Servidor
import socket

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('localhost', 9999))
server.listen(1)

while True:
    conn, addr = server.accept()
    command = conn.recv(1024).decode()
    # Processar comando
    response = process_command(command)
    conn.send(response.encode())
    conn.close()
```

```bash
# Cliente
echo "reload" | nc localhost 9999
```

## Método 3: Arquivo de Controle

Mais simples, mas menos eficiente:

```bash
# Servidor monitora arquivo
while true; do
    if [ -f /tmp/control.txt ]; then
        command=$(cat /tmp/control.txt)
        rm /tmp/control.txt
        # Processar comando
    fi
    sleep 1
done

# Cliente envia comando
echo "reload" > /tmp/control.txt
```

## Método 4: Signals (Limitado)

Apenas para comandos simples:

```python
import signal
import sys

def signal_handler(sig, frame):
    if sig == signal.SIGUSR1:
        print("Reload!")
    elif sig == signal.SIGUSR2:
        print("Pause!")

signal.signal(signal.SIGUSR1, signal_handler)
signal.signal(signal.SIGUSR2, signal_handler)
```

```bash
# Enviar signal
kill -USR1 <PID>
kill -USR2 <PID>
```

## Integração com Playwright Simple

Para integrar com o hot reload do playwright-simple:

```python
# No seu processo principal
from scripts.command_server import register_command, setup_pipes

def handle_reload_yaml():
    # Lógica de reload do YAML
    reload_yaml_file()
    return "YAML recarregado"

register_command("reload_yaml", handle_reload_yaml)

# Iniciar servidor em thread separada
import threading
threading.Thread(target=lambda: asyncio.run(command_server()), daemon=True).start()
```

## Exemplo Completo de Uso

```bash
# Terminal 1: Iniciar servidor
cd /home/gabriel/softhill/playwright-simple
python3 scripts/command_server.py

# Terminal 2: Enviar comandos
./scripts/send_command.sh status
./scripts/send_command.sh reload
./scripts/send_command.sh pause
./scripts/send_command.sh continue

# Terminal 3: Monitorar respostas
tail -f /tmp/playwright_responses
```

## Vantagens de Cada Método

| Método | Vantagens | Desvantagens |
|--------|-----------|--------------|
| **Named Pipes** | Simples, rápido, local | Apenas mesma máquina |
| **TCP Socket** | Rede, robusto | Mais complexo |
| **Arquivo** | Muito simples | Ineficiente, polling |
| **Signals** | Nativo do sistema | Limitado a sinais |

## Recomendação

Para o playwright-simple, use **Named Pipes** (Método 1) porque:
- ✅ Simples de implementar
- ✅ Rápido e eficiente
- ✅ Permite comunicação bidirecional
- ✅ Funciona bem para processos locais

