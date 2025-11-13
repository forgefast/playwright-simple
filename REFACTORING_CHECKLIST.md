# Checklist de Refatoração Arquitetural - playwright-simple

**Última atualização**: 2025-01-XX  
**Versão**: 2.0

## 📋 Checklist de Separação Core vs Extensões

### Core (`playwright_simple/core/`)
- [x] `core/auth.py` - Sem lógica Odoo-específica
- [x] `core/forms.py` - Sem lógica Odoo-específica
- [x] `core/wait.py` - Sem lógica Odoo-específica
- [x] `core/navigation.py` - Sem lógica Odoo-específica
- [x] `core/interactions.py` - Genérico
- [x] `core/assertions.py` - Genérico
- [x] `core/extensions/` - Interfaces criadas

### Odoo (`playwright_simple/odoo/`)
- [x] `odoo/auth.py` - Completo e específico
- [x] `odoo/wait.py` - Completo e específico
- [x] `odoo/navigation.py` - Completo e específico
- [x] `odoo/specific/` - Módulo criado para ações muito específicas
  - [x] `logo.py` - LogoNavigator
  - [x] `filters.py` - FilterHelper

### Dependency Injection
- [x] `SimpleTestBase` - Aceita managers e helpers opcionais
- [x] `OdooTestBase` - Aceita managers e helpers opcionais

## 📋 Checklist Rápido por Arquivo

### `core/base.py`
- [ ] Verificar se métodos seguem SRP
- [ ] Extrair constantes (magic numbers/strings)
- [ ] Adicionar type hints completos
- [ ] Melhorar docstrings
- [ ] Verificar error handling
- [ ] Reduzir complexidade ciclomática
- [ ] Verificar se helpers são reutilizáveis

### `core/cursor.py`
- [ ] Separar lógica de injeção de lógica de animação
- [ ] Extrair código JavaScript para arquivos separados
- [ ] Adicionar type hints
- [ ] Melhorar error handling
- [ ] Reduzir duplicação de código JS
- [ ] Adicionar logging apropriado

### `core/runner.py`
- [ ] Separar lógica de processamento de vídeo
- [ ] Aplicar Strategy Pattern para processamento
- [ ] Melhorar error handling e logging
- [ ] Adicionar type hints
- [ ] Reduzir complexidade do método `run_test`
- [ ] Extrair métodos menores

### `core/config.py`
- [ ] Validar valores no `__post_init__`
- [ ] Adicionar type hints
- [ ] Melhorar documentação
- [ ] Adicionar métodos de validação

### `core/video.py`
- [ ] Adicionar type hints
- [ ] Melhorar error handling
- [ ] Adicionar logging

### `core/screenshot.py`
- [ ] Adicionar type hints
- [ ] Melhorar error handling
- [ ] Adatorar logging

### `core/selectors.py`
- [ ] Adicionar type hints
- [ ] Melhorar error handling
- [ ] Adicionar logging

### `core/yaml_parser.py`
- [ ] Separar parsing de execução
- [ ] Adicionar type hints
- [ ] Melhorar error handling
- [ ] Adicionar validação de schema

---

## 🔍 Code Smells a Verificar

### Duplicação
- [ ] Código duplicado entre métodos
- [ ] Lógica repetida em múltiplos arquivos
- [ ] Strings/valores hardcoded repetidos

### Complexidade
- [ ] Métodos com >50 linhas
- [ ] Classes com >300 linhas
- [ ] Níveis de aninhamento >3
- [ ] Complexidade ciclomática >10

### Nomenclatura
- [ ] Nomes não descritivos
- [ ] Abreviações desnecessárias
- [ ] Inconsistência de nomenclatura
- [ ] Nomes genéricos (data, info, temp)

### Estrutura
- [ ] Muitos parâmetros (>5)
- [ ] Long parameter lists
- [ ] Feature envy (acesso excessivo a outros objetos)
- [ ] Data clumps (grupos de dados relacionados)

---

## ✅ Padrões a Aplicar

### Factory Pattern
- [ ] `TestInstanceFactory` para criar instâncias de teste
- [ ] `VideoProcessorFactory` para diferentes estratégias de processamento

### Strategy Pattern
- [ ] Estratégias de processamento de vídeo
- [ ] Estratégias de seleção de elementos
- [ ] Estratégias de espera (wait strategies)

### Builder Pattern
- [ ] `TestConfigBuilder` para construir configurações
- [ ] `VideoProcessingBuilder` para construir comandos ffmpeg

### Observer Pattern
- [ ] Event system para notificar sobre progresso
- [ ] Logging observers

---

## 🐍 Python Best Practices

### Type Hints
- [ ] Todos os métodos públicos têm type hints
- [ ] Retornos são tipados
- [ ] Parâmetros são tipados
- [ ] Usar `Optional`, `Union` apropriadamente
- [ ] Usar `Protocol` para interfaces

### Docstrings
- [ ] Todas as classes têm docstrings
- [ ] Todos os métodos públicos têm docstrings
- [ ] Parâmetros documentados
- [ ] Retornos documentados
- [ ] Exceções documentadas
- [ ] Exemplos de uso incluídos

### Error Handling
- [ ] Exceções específicas ao invés de genéricas
- [ ] Mensagens de erro descritivas
- [ ] Logging apropriado
- [ ] Cleanup em finally blocks
- [ ] Context managers para recursos

### Async/Await
- [ ] Operações I/O são async
- [ ] Usar `asyncio.gather` para paralelismo
- [ ] Evitar `time.sleep` (usar `asyncio.sleep`)
- [ ] Context managers async quando apropriado

---

## 🏗️ Arquitetura

### Separation of Concerns
- [ ] Managers separados por responsabilidade
- [ ] Parsers separados de execução
- [ ] Configuração separada de lógica

### Dependency Injection
- [ ] Dependências injetadas via construtor
- [ ] Não criar dependências diretamente
- [ ] Usar factories quando apropriado

### Interfaces
- [ ] Interfaces definidas para contratos
- [ ] ABC para classes abstratas
- [ ] Protocol para duck typing

---

## ⚡ Performance

### Otimizações
- [ ] Processamento em lote quando possível
- [ ] Lazy loading implementado
- [ ] Caching onde apropriado
- [ ] Evitar processamento redundante

### Async
- [ ] Operações paralelas usando gather
- [ ] Sem bloqueios desnecessários
- [ ] Timeouts apropriados

---

## 🧪 Testes

### Cobertura
- [ ] Testes unitários para lógica crítica
- [ ] Testes de integração para fluxos
- [ ] Testes de regressão após refatoração

### Validação
- [ ] Todos os testes passam
- [ ] Comportamento não mudou
- [ ] Performance não degradou

---

## 📝 Documentação

### Código
- [ ] Docstrings atualizadas
- [ ] Comentários explicam "porquê"
- [ ] Type hints completos

### Externa
- [ ] README atualizado
- [ ] CHANGELOG atualizado
- [ ] Exemplos atualizados

---

## 🎯 Status Atual

### ✅ Já Implementado
- Eliminação de duplicação em métodos de interação
- Helpers reutilizáveis (`_prepare_element_interaction`, `_move_cursor_to_element`)
- Processamento de vídeo otimizado (uma única passada)
- Redução de delays desnecessários

### ⚠️ Em Progresso
- Type hints (parcial)
- Error handling (parcial)
- Documentação (parcial)

### ✅ Recém Concluído
- Logging estruturado em interações e navegação
- Detecção de mudança de estado após ações
- Logs diferenciados para passos estáticos vs dinâmicos

### ❌ Pendente
- Separar managers em módulos
- Aplicar padrões de design
- Testes unitários
- Validação de configuração

---

**Última atualização**: 2024-11-13

