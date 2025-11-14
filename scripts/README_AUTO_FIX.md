# Auto-Fix Test Runner

Sistema que executa testes Playwright em background e corrige automaticamente erros no YAML durante a execução.

## Como Funciona

1. **Executa o teste** em foreground (para ver output em tempo real)
2. **Monitora a saída** para detectar erros
3. **Analisa erros** e identifica o tipo (element_not_found, timeout_error, etc.)
4. **Corrige automaticamente** o YAML quando possível
5. **Hot-reload** recarrega o YAML (quando implementado)

## Uso

### Método 1: Script Python Direto

```bash
cd /home/gabriel/softhill/playwright-simple
python3 scripts/auto_fix_runner.py \
    examples/racco/test_simple_login.yaml \
    --base-url http://localhost:18069 \
    --max-fixes 10
```

### Método 2: Script Shell Wrapper

```bash
cd /home/gabriel/softhill/playwright-simple
./scripts/run_with_auto_fix.sh \
    examples/racco/test_simple_login.yaml \
    http://localhost:18069 \
    10
```

### Método 3: Comando Original (com auto-fix)

O script usa o mesmo comando que você especificou:

```bash
python3 -m playwright_simple.cli \
    --log-level INFO \
    run examples/racco/test_simple_login.yaml \
    --base-url http://localhost:18069 \
    --no-headless \
    --video \
    --audio \
    --subtitles \
    --debug \
    --interactive \
    --hot-reload \
    --step-timeout 0.1
```

## Correções Automáticas Disponíveis

### 1. Element Not Found
- **Detecta**: Quando um elemento não é encontrado
- **Corrige**: Adiciona `wait` antes do step problemático

### 2. Timeout Error
- **Detecta**: Quando há timeout em operações
- **Corrige**: Aumenta timeouts nos steps

### 3. Unknown Action
- **Detecta**: Quando uma ação não é reconhecida
- **Corrige**: Mapeia ações comuns (ex: `click_button` → `click`)

## Exemplo de Uso

```bash
# Executar com auto-fix
python3 scripts/auto_fix_runner.py examples/racco/test_simple_login.yaml

# Output esperado:
# 🚀 Auto-Fix Test Runner
# 📄 YAML: examples/racco/test_simple_login.yaml
# 🔧 Comando: python3 -m playwright_simple.cli ...
# 💡 Correções automáticas: Ativadas (máx: 10)
# 
# ▶️  Iniciando teste...
# 
# [output do teste...]
# 
# ❌ ERRO DETECTADO: element_not_found
# 🔧 Tentando corrigir automaticamente...
# ✅ Correção aplicada! (Total: 1)
# 💡 Aguardando hot-reload recarregar o YAML...
```

## Backups

Antes de modificar o YAML, o sistema cria backups em:
```
examples/racco/.auto_fix_backups/test_simple_login_20250114_123456.yaml
```

## Limites

- **Máximo de correções**: 10 (configurável via `--max-fixes`)
- **Evita duplicatas**: Não processa o mesmo erro múltiplas vezes (janela de 2 segundos)

## Integração com Hot-Reload

O hot-reload do playwright-simple ainda não está totalmente implementado. Quando estiver:

1. O sistema corrige o YAML
2. O hot-reload detecta a mudança
3. O YAML é recarregado automaticamente
4. O teste continua sem reiniciar

Por enquanto, você pode:
- Corrigir manualmente o YAML enquanto o teste está rodando
- O sistema detectará a mudança e mostrará uma mensagem
- Reiniciar o teste para aplicar mudanças

## Troubleshooting

### O teste não está detectando erros
- Verifique se o output contém palavras-chave: "error", "failed", "exception"
- Aumente o nível de log: `--log-level DEBUG`

### Correções não estão funcionando
- Verifique os backups em `.auto_fix_backups/`
- Revise o tipo de erro (nem todos têm correção automática)
- Corrija manualmente o YAML

### Processo travado
- Use `Ctrl+C` para interromper
- O sistema limpa processos filhos automaticamente

## Próximos Passos

1. Implementar hot-reload completo no playwright-simple
2. Adicionar mais tipos de correção automática
3. Suporte a múltiplos arquivos YAML
4. Interface web para monitoramento

