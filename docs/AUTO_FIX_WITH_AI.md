# Auto-Fix com IA - Abordagem Correta

## Como Funciona

O script `auto_fix_direct.py` agora funciona como um **loop de execução com pausa para correção pela IA**:

1. **Executa teste diretamente** no contexto Python
2. **Quando detecta erro:**
   - Mostra informações completas (erro, HTML, estado)
   - **Pausa e aguarda a IA corrigir** usando suas ferramentas
   - Verifica se YAML/código foi modificado
   - Se modificado, recarrega e tenta novamente
3. **Continua até passar** ou atingir limite de tentativas

## Fluxo

```
Executar passo
    ↓
Erro detectado?
    ↓ SIM
Mostrar informações do erro
    ↓
[PAUSA - IA CORRIGE AQUI]
    ↓
YAML/código modificado?
    ↓ SIM
Recarregar (hot reload)
Rollback para estado anterior
    ↓
Tentar novamente
    ↓
Passou? → Próximo passo
    ↓ NÃO
Repetir (até 5 tentativas)
```

## O que a IA faz

Quando o script pausa em um erro, a IA:

1. **Analisa o erro:**
   - Tipo de erro (ElementNotFoundError, TypeError, etc.)
   - Mensagem de erro
   - Passo atual e ação
   - HTML da página (botões, inputs disponíveis)

2. **Corrige usando suas ferramentas:**
   - `read_file` - Lê arquivos YAML ou Python
   - `search_replace` - Corrige código/YAML
   - `grep` - Encontra onde está o problema
   - `codebase_search` - Entende o contexto

3. **Aplica correção:**
   - Modifica YAML ou código Python
   - Script detecta mudança automaticamente
   - Hot reload aplica
   - Teste continua

## Exemplo

```python
# Script executa:
📍 Passo 2/3: login
  ⚠️  Erro no passo 2 (tentativa 1/5)
     Tipo: ElementNotFoundError
     Mensagem: Elemento "Login" não encontrado

# Script pausa e mostra:
🔍 ERRO DETECTADO - Aguardando correção pela IA
Passo: 2/3
Ação: login
📄 Elementos disponíveis:
  Botões:
    - 'Entrar' (tag: button, id: login-btn)
    - 'Fazer Login' (tag: button)

# IA analisa e corrige:
- Lê o YAML
- Vê que está procurando "Login" mas o botão é "Entrar"
- Corrige o YAML: text: "Entrar"
- Script detecta mudança
- Recarrega YAML
- Tenta novamente
- ✅ Passa!
```

## Vantagens

- ✅ **IA corrige com inteligência** (não regras fixas)
- ✅ **Acesso direto ao contexto** (HTML, estado, código)
- ✅ **Zero overhead** (execução direta)
- ✅ **Hot reload automático** (detecta mudanças)
- ✅ **Rollback automático** (volta ao estado anterior)

## Uso

```bash
# Executar - a IA vai corrigindo conforme os erros aparecem
python3 scripts/auto_fix_direct.py examples/racco/test_simple_login.yaml \
  --base-url http://localhost:18069 \
  --headless
```

O script vai pausar em cada erro e **você (IA) corrige dinamicamente** usando suas ferramentas!

