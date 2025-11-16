# Análise de Código Antigo

## Código que NÃO está na Stack Funcional

### ⚠️ Código Antigo (Não Testado)

Estes arquivos existem mas **NÃO** são usados pela stack funcional do `test_full_cycle.py`:

#### 1. SimpleTestBase e Base Classes
- **Arquivo**: `playwright_simple/core/base.py`
- **Classe**: `SimpleTestBase`
- **Status**: ⚠️ Código antigo, não usado pela stack funcional
- **Uso**: Pode ser usado em outros lugares, mas não está na stack testada
- **Ação**: Verificar se precisa ser atualizado ou se pode ser removido

#### 2. TestRunner (Runner Antigo)
- **Arquivo**: `playwright_simple/core/runner/test_runner.py`
- **Classe**: `TestRunner`
- **Status**: ⚠️ Código antigo, não usado pela stack funcional
- **Uso**: Parece ser um runner diferente do Recorder
- **Ação**: Verificar se precisa ser integrado ou se pode ser removido

#### 3. TestExecutor
- **Arquivo**: `playwright_simple/core/runner/test_executor.py`
- **Status**: ⚠️ Código antigo, não usado pela stack funcional
- **Ação**: Verificar se precisa ser integrado

#### 4. Interactions Base
- **Arquivo**: `playwright_simple/core/interactions/base.py`
- **Status**: ⚠️ Código antigo, não usado pela stack funcional
- **Ação**: Verificar se precisa ser atualizado para usar stack do recorder

#### 5. Runner.py (Legacy)
- **Arquivo**: `playwright_simple/core/runner.py`
- **Status**: ⚠️ Código antigo, não usado pela stack funcional
- **Ação**: Verificar se precisa ser removido ou integrado

### ✅ Código Legacy Mantido (Backward Compatibility)

#### command_handlers.py (Legacy Wrapper)
- **Arquivo**: `playwright_simple/core/recorder/command_handlers.py`
- **Status**: ✅ Mantido para backward compatibility
- **Função**: Redireciona para estrutura modular
- **Ação**: Manter como está

### 📋 Resumo

**Código Funcional (Stack do test_full_cycle.py)**:
- ✅ Recorder e todos os seus componentes
- ✅ Command handlers modulares
- ✅ Event capture e handlers
- ✅ YAML writer e reader

**Código Antigo (Não na Stack)**:
- ⚠️ SimpleTestBase
- ⚠️ TestRunner antigo
- ⚠️ TestExecutor antigo
- ⚠️ Interactions base antigo
- ⚠️ Runner.py legacy

**Estratégia**:
1. Usar apenas código da stack funcional como base
2. Código antigo pode ser usado como referência/ideias
3. Atualizar código antigo para usar stack funcional quando necessário

