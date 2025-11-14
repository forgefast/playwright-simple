# Opções de Comunicação - Análise

## Situação Atual: Arquivos JSON + Polling

**Problemas:**
- ❌ Polling ineficiente (verifica arquivos a cada 0.5s)
- ❌ Race conditions possíveis
- ❌ Overhead de I/O de disco
- ❌ Não é real-time

## Opções Melhores

### 1. **stdin/stdout com JSON Lines** ⭐ RECOMENDADO

**Como funciona:**
- Processo escreve eventos em stdout (JSON lines)
- Monitor lê stdout em tempo real
- Zero overhead, comunicação direta

**Vantagens:**
- ✅ Real-time (sem polling)
- ✅ Simples de implementar
- ✅ Sem arquivos temporários
- ✅ Funciona bem com subprocess
- ✅ Padrão da indústria (JSON Lines)

**Exemplo:**
```python
# Processo escreve:
{"type": "error", "error_type": "ElementNotFoundError", ...}
{"type": "state", "step_number": 1, ...}

# Monitor lê linha por linha
for line in process.stdout:
    event = json.loads(line)
    if event['type'] == 'error':
        fix_error(event)
```

### 2. **Unix Domain Sockets** (já implementado)

**Vantagens:**
- ✅ Muito rápido (kernel-level)
- ✅ Bidirecional
- ✅ Sem overhead de rede
- ✅ Já temos `ipc_server.py`

**Desvantagens:**
- ⚠️ Mais complexo que stdin/stdout
- ⚠️ Precisa gerenciar conexões

### 3. **Named Pipes (FIFOs)**

**Vantagens:**
- ✅ Simples
- ✅ Eficiente

**Desvantagens:**
- ⚠️ Unidirecional (precisa 2 pipes)
- ⚠️ Menos flexível

### 4. **HTTP/WebSocket**

**Vantagens:**
- ✅ Padrão web
- ✅ Bidirecional
- ✅ Funciona em rede

**Desvantagens:**
- ❌ Overhead desnecessário para local
- ❌ Mais complexo

## Recomendação: stdin/stdout com JSON Lines

**Por quê:**
1. **Mais simples**: Apenas redirecionar stdout
2. **Real-time**: Eventos chegam instantaneamente
3. **Padrão**: JSON Lines é usado por muitas ferramentas (jq, etc)
4. **Sem overhead**: Comunicação direta via pipe
5. **Fácil de debugar**: Pode fazer `tee` para ver logs

**Implementação:**
- Processo escreve eventos JSON em stdout
- Monitor lê linha por linha
- Zero polling necessário

