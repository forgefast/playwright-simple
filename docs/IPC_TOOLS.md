# Ferramentas IPC - Não Estamos Reinventando a Roda

## Ferramentas Usadas

### 1. Watchdog (Já Instalado) ✅

**Biblioteca**: `watchdog` (já no projeto)

**Uso**: Monitoramento eficiente de mudanças em arquivos

**Vantagens**:
- ✅ Usa `inotify` no Linux (kernel-level, muito eficiente)
- ✅ Não precisa fazer polling manual
- ✅ Callbacks assíncronos quando arquivo muda
- ✅ Já está instalado no projeto

**Implementação**:
```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Monitora mudanças em arquivos
observer = Observer()
observer.schedule(handler, path, recursive=False)
observer.start()
```

### 2. Unix Domain Sockets (Padrão Python) ✅

**Biblioteca**: `socket` (built-in Python)

**Uso**: Comunicação bidirecional eficiente entre processos

**Vantagens**:
- ✅ Mais rápido que arquivos
- ✅ Comunicação bidirecional
- ✅ Sem overhead de rede
- ✅ Padrão do sistema operacional

**Implementação**:
```python
import socket
import asyncio

# Servidor
server = await asyncio.start_unix_server(handler, socket_path)

# Cliente
reader, writer = await asyncio.open_unix_connection(socket_path)
```

### 3. Named Pipes (FIFOs) ✅

**Biblioteca**: `os.mkfifo` (built-in Python)

**Uso**: Comunicação simples unidirecional

**Vantagens**:
- ✅ Muito simples
- ✅ Funciona bem para comandos simples
- ✅ Sem dependências

## Comparação com Outras Ferramentas

| Ferramenta | Complexidade | Performance | Dependências | Uso Recomendado |
|------------|--------------|------------|--------------|-----------------|
| **Watchdog** | Baixa | Alta | watchdog | Monitorar arquivos |
| **Unix Sockets** | Média | Muito Alta | Nenhuma | Comunicação bidirecional |
| **Named Pipes** | Baixa | Alta | Nenhuma | Comandos simples |
| **Redis Pub/Sub** | Alta | Alta | Redis | Sistema distribuído |
| **RabbitMQ** | Alta | Alta | RabbitMQ | Sistema complexo |
| **gRPC** | Alta | Muito Alta | gRPC | Comunicação tipo-safe |

## Nossa Implementação

### Arquitetura Atual

```
┌─────────────────┐
│ Processo        │
│ Playwright      │
│                 │
│ ControlInterface│───> Salva em arquivos JSON
│                 │     (state.json, error.json)
└─────────────────┘
         │
         │ Watchdog monitora mudanças
         ▼
┌─────────────────┐
│ auto_fix_runner │
│                 │
│ Watchdog        │───> Detecta mudanças
│ Callbacks       │     instantaneamente
└─────────────────┘
```

### Por Que Esta Abordagem?

1. **Watchdog já está instalado** - Não precisamos adicionar dependências
2. **Arquivos JSON são simples** - Fácil de debugar e inspecionar
3. **Unix Sockets disponíveis** - Podemos migrar se necessário
4. **Não reinventamos** - Usamos ferramentas padrão da indústria

## Alternativas Consideradas

### Redis Pub/Sub
- ❌ Requer Redis instalado
- ❌ Overhead desnecessário para comunicação local
- ✅ Bom para sistema distribuído

### RabbitMQ
- ❌ Requer RabbitMQ instalado
- ❌ Complexidade desnecessária
- ✅ Bom para sistema de mensageria complexo

### gRPC
- ❌ Mais complexo para este caso
- ❌ Requer definição de protobuf
- ✅ Bom para APIs estruturadas

## Conclusão

**Não estamos reinventando a roda!**

Usamos:
- ✅ **Watchdog** (biblioteca padrão da indústria)
- ✅ **Unix Sockets** (padrão do sistema operacional)
- ✅ **Named Pipes** (padrão POSIX)

Todas são ferramentas padrão e bem estabelecidas. A combinação é eficiente e não requer dependências externas pesadas.

