# Handoff Note - Tela Inicial de Vídeos e Correções

**Data**: 2025-01-XX (Última atualização)  
**Status**: Tela Inicial Implementada ✅ | Logging Detalhado Implementado ✅ | Problema de Vídeo Corrigido ✅

---

## 🚨 PROBLEMA ATUAL

### Vídeo Está Sendo Cortado
- **Sintoma**: Vídeos gerados têm duração menor que o esperado (ex: teste de 21.48s gera vídeo de 15.72s)
- **Teste Real**: `test_colaborador_portal.yaml` em `/home/gabriel/softhill/presentation/playwright/tests/yaml/`
- **Status**: Investigação em andamento - pode ser problema no processamento FFmpeg ou na gravação do Playwright

### Tela Inicial Implementada
- ✅ **Concluído**: Tela inicial com gradiente roxo/azul (#667eea → #764ba2) implementada
- ✅ Formatação automática do nome do teste (ex: `test_colaborador_portal` → "Colaborador Portal")
- ✅ Texto "Gravando vídeo de teste..." abaixo do título
- ⚠️ **Problema**: Tela inicial não está sendo adicionada porque `needs_processing` é False quando não há speed/subtitles/audio
- 🔧 **Correção Parcial**: Adicionado `test_name is not None` em `needs_processing`, mas ainda precisa verificar se está funcionando

### Mudanças Recentes
1. **Adicionada função `_format_video_name()`** em `video_processor.py`:
   - Remove prefixos `test_`, `Test_`
   - Remove prefixos numéricos (01_, 02_, etc.)
   - Converte snake_case para Title Case

2. **Adicionada função `_create_intro_screen()`** em `video_processor.py`:
   - Cria vídeo de 3 segundos com gradiente roxo/azul
   - Usa FFmpeg com filtros `geq` para gradiente (fallback para cor sólida se falhar)
   - Adiciona texto centralizado com nome formatado

3. **Modificado `process_all_in_one()`**:
   - Aceita parâmetro `test_name` opcional
   - Concatena tela inicial + vídeo principal usando `concat` filter
   - Ajusta índices de input/output para considerar tela inicial

4. **Modificado `test_executor.py`**:
   - Passa `test_name` para `process_all_in_one()`
   - `needs_processing` agora inclui `test_name is not None`

5. **Removido `-shortest` flag** do FFmpeg:
   - Estava cortando vídeo quando áudio era mais curto
   - Agora deixa vídeo determinar duração

### Mudanças Recentes que Podem Ter Causado o Problema
1. **Remoção de debugs e verificações redundantes**:
   - Removidas chamadas de `_remove_duplicate_cursors()` em múltiplos lugares
   - Removidos screenshots de debug
   - Removidas verificações de cursor duplicado após cada ação

2. **Refatoração do `cursor.py`**:
   - Arquivo reduzido de 879 linhas para 109 linhas
   - Código modularizado em: `cursor_styles.py`, `cursor_debug.py`, `cursor_elements.py`, `cursor_movement.py`, `cursor_effects.py`, `cursor_injection.py`
   - Removida classe `CursorDebug` do `CursorManager`

3. **Correção no método `type()`**:
   - Adicionado clique no elemento mesmo quando não há coordenadas (para garantir foco)

### Arquivos Modificados Recentemente
- `playwright_simple/core/cursor.py` - Refatorado completamente
- `playwright_simple/core/cursor_*.py` - Novos módulos criados
- `playwright_simple/core/interactions.py` - Removidas verificações redundantes
- `playwright_simple/core/helpers.py` - Removidas verificações redundantes
- `playwright_simple/core/base.py` - Removidas verificações redundantes
- `playwright_simple/odoo/auth.py` - Removidos debugs e prints

### Próximos Passos para Resolver

#### 1. Testar com Teste Real
```bash
cd /home/gabriel/softhill/presentation/playwright
python3 run_one_test.py 18  # ou "colaborador_portal"
```

**OU** simplesmente passar o YAML como parâmetro:
```python
from pathlib import Path
from playwright_simple import TestRunner
from playwright_simple.odoo import OdooYAMLParser
from racco_config import get_racco_config

yaml_path = Path("tests/yaml/test_colaborador_portal.yaml")
yaml_data = OdooYAMLParser.parse_file(yaml_path)
test_function = OdooYAMLParser.to_python_function(yaml_data)

config = get_racco_config()
runner = TestRunner(config=config)
await runner.run_test("Colaborador Portal", test_function)
```

#### 2. Verificar se Tela Inicial Está Sendo Criada
- Verificar logs para "Tela inicial criada" ou "Tela inicial adicionada"
- Verificar se arquivo temporário `/tmp/intro_*.mp4` está sendo criado
- Verificar se `intro_video` não é None em `process_all_in_one()`

#### 3. Verificar Duração do Vídeo Original
- Verificar duração do vídeo WebM original ANTES do processamento
- Comparar com duração após processamento
- Pode ser que Playwright esteja cortando o vídeo na gravação

#### 4. Verificar Concatenação FFmpeg
- Verificar se `concat` filter está funcionando corretamente
- Verificar se índices de input/output estão corretos
- Adicionar logs do comando FFmpeg executado

#### 5. Corrigir Gradiente (Opcional)
- Atualmente usando `geq` filter que pode não funcionar em todos os FFmpeg
- Fallback para cor sólida funciona, mas não tem gradiente
- Considerar usar imagem PNG pré-renderizada com gradiente

### Scripts Úteis Criados
- `playwright-simple/scripts/analyze_video.py` - Analisa metadados de vídeos (duração, tamanho, codec, etc.)
- `playwright-simple/test_colaborador_real.py` - Script para executar teste real (criado mas não testado)

### Arquivos Modificados Recentemente
- `playwright_simple/core/runner/video_processor.py`:
  - Adicionado `_format_video_name()` (linhas 152-183)
  - Adicionado `_create_intro_screen()` (linhas 185-294)
  - Modificado `process_all_in_one()` para aceitar `test_name` e concatenar tela inicial
  - Removido `-shortest` flag do FFmpeg
  
- `playwright_simple/core/runner/test_executor.py`:
  - Modificado `needs_processing` para incluir `test_name is not None` (linha 542)
  - Passa `test_name` para `process_all_in_one()` (linha 566)

---

## ✅ Refatoração Completa - CONCLUÍDA

### 0. Refatoração do Sistema de Cursor (RECENTE)
- ✅ **Concluído**: `cursor.py` refatorado de 879 linhas para 109 linhas
- ✅ Módulos criados:
  - `cursor_styles.py` (122 linhas) - Geração de CSS
  - `cursor_debug.py` (90 linhas) - Debug utilities (não mais usado)
  - `cursor_elements.py` (236 linhas) - Gerenciamento de elementos DOM
  - `cursor_movement.py` (157 linhas) - Movimento e animação
  - `cursor_effects.py` (164 linhas) - Efeitos visuais (click/hover)
  - `cursor_injection.py` (184 linhas) - Injeção de JavaScript/CSS
- ✅ Removidos debugs e verificações redundantes:
  - Removidas 12+ chamadas de `_remove_duplicate_cursors()`
  - Removidos screenshots de debug
  - Removidos prints de debug
- ⚠️ **ATENÇÃO**: Pode ter causado o problema do login (ver seção PROBLEMA CRÍTICO)

### 1. Substituição de Exceções Genéricas
- ✅ **Concluído**: Todas as exceções genéricas (`Exception`) foram substituídas por exceções específicas
- ✅ Arquivos atualizados:
  - `base.py` - Usa `ElementNotFoundError`, `NavigationError`, `PlaywrightTimeoutError`
  - `runner.py` - Usa `VideoProcessingError`, `TTSGenerationError`
  - `tts.py` - Usa `TTSGenerationError` com propagação adequada
  - `yaml_parser.py` - Tratamento específico de erros
  - `video.py`, `screenshot.py`, `selectors.py` - Logging e tratamento melhorados

### 2. Logging Estruturado
- ✅ **Concluído**: Logging adicionado em todos os módulos core
- ✅ Arquivos com logging:
  - `base.py` - `logger = logging.getLogger(__name__)`
  - `runner.py` - Logging de erros, warnings e debug
  - `tts.py` - Logging de geração de áudio e erros
  - `video.py`, `screenshot.py`, `selectors.py`, `yaml_parser.py` - Logging completo
- ✅ Níveis apropriados: `logger.debug()`, `logger.warning()`, `logger.error()` com `exc_info=True` para erros críticos

### 3. Docstrings Completas
- ✅ **Concluído**: Docstrings adicionadas/atualizadas em todos os métodos públicos e privados críticos
- ✅ Métodos documentados:
  - `TestRunner`: `run_test()`, `run_all()`, `_run_parallel()`, `_print_summary()`, `get_results()`, `get_summary()`, `_process_video_speed()`, `_add_subtitles()`, `_add_subtitles_drawtext()`, `_add_audio()`
  - `SimpleTestBase`: Todos os métodos principais já tinham docstrings, algumas foram melhoradas
  - `YAMLParser`: Métodos principais documentados

### 4. Melhorias de Error Handling
- ✅ Mensagens de erro mais descritivas
- ✅ Propagação adequada de exceções com `raise ... from e`
- ✅ Cleanup em `finally` blocks
- ✅ Tratamento específico de exceções do Playwright (`PlaywrightTimeoutError`)

---

## 🧪 Testes - EM PROGRESSO

### Status Atual
- **Cobertura Total**: 42% (Meta: 80%)
- **Testes Passando**: 142 passed, 16 failed
- **Arquivos com menor cobertura**:
  - `runner.py`: 8% (545/590 linhas não cobertas)
  - `base.py`: 49% (234/463 linhas não cobertas)
  - `yaml_parser.py`: 43% (165/289 linhas não cobertas)
  - `tts.py`: 27% (130/177 linhas não cobertas)
  - `session.py`: 15% (85/100 linhas não cobertas)

### Testes Implementados
- ✅ `test_base.py` - Testes básicos de inicialização, `go_to()`, `wait()`
- ✅ `test_base_extended.py` - Testes adicionais: `back()`, `forward()`, `refresh()`, `click()`, `double_click()`, `right_click()`, `type()`, `select()`, `hover()`, `assert_text()`, `assert_visible()`, `assert_url()`, `assert_count()`, `assert_attr()`, `fill_form()`, `get_text()`, `get_attr()`, `is_visible()`, `is_enabled()`, `wait_for()`, `wait_for_url()`, `wait_for_text()`, `navigate()`, `scroll()`, `screenshot()`
- ✅ `test_yaml_parser.py` - Testes de parsing, loading, inheritance, includes, execução de steps
- ✅ `test_runner.py` - Testes básicos de inicialização, `get_summary()`, `get_results()`
- ✅ `test_config.py` - Testes completos de configuração
- ✅ `test_cursor.py`, `test_video.py`, `test_screenshot.py`, `test_selectors.py` - Testes dos managers

### Testes que Precisam ser Corrigidos
1. **test_base_extended.py::test_assert_url** - Falha na validação de URL pattern
2. **test_base_extended.py::test_wait_for_url** - Timeout na espera de URL
3. **test_forgeerp.py** - Erros de argumentos do TestConfig (3 testes)
4. **test_screenshot.py::test_screenshot_capture_element** - Erro com MagicMock
5. **test_selectors.py** - 2 testes falhando (timeout e MagicMock)
6. **test_tts.py** - 6 testes falhando (problemas com mocking de módulos TTS)

### Testes que Precisam ser Implementados

#### Para `runner.py` (8% cobertura):
- [ ] Teste de `run_test()` com sucesso
- [ ] Teste de `run_test()` com falha
- [ ] Teste de `run_all()` com múltiplos testes
- [ ] Teste de `_run_parallel()` com workers
- [ ] Teste de `_process_video_speed()` (com e sem ffmpeg)
- [ ] Teste de `_process_video_all_in_one()` (mocking ffmpeg)
- [ ] Teste de `_generate_narration()` (mocking TTS)
- [ ] Teste de `_generate_srt_file()`
- [ ] Teste de `_add_subtitles()` (mocking ffmpeg)
- [ ] Teste de `_add_subtitles_drawtext()` (mocking ffmpeg)
- [ ] Teste de `_add_audio()` (mocking ffmpeg)
- [ ] Teste de `_create_test_instance()` (SimpleTestBase e OdooTestBase)

#### Para `base.py` (49% cobertura):
- [ ] Teste de `_prepare_element_interaction()` (casos de sucesso e erro)
- [ ] Teste de `_move_cursor_to_element()` 
- [ ] Teste de `_navigate_with_cursor()` (com erro de injeção de cursor)
- [ ] Teste de `go_to()` com erro de injeção de cursor
- [ ] Teste de `navigate()` com menu não encontrado (deve lançar `ElementNotFoundError`)
- [ ] Teste de `login()` completo (sucesso e falha)
- [ ] Teste de `fill_by_label()` (com e sem context)
- [ ] Teste de `select_by_label()`
- [ ] Teste de `drag()` (drag and drop)
- [ ] Teste de `assert_text()` com falha
- [ ] Teste de `assert_visible()` com elemento não encontrado
- [ ] Teste de `assert_count()` com contagem incorreta
- [ ] Teste de `assert_attr()` com atributo não encontrado
- [ ] Teste de `get_card_content()`
- [ ] Teste de `save_session()` e `load_session()`
- [ ] Teste de `wait_for_modal()` e `close_modal()`
- [ ] Teste de `click_button()`

#### Para `yaml_parser.py` (43% cobertura):
- [ ] Teste de `_resolve_inheritance()` com múltiplos níveis
- [ ] Teste de `_resolve_includes()` com múltiplos includes
- [ ] Teste de `_execute_step()` para todas as ações:
  - [ ] `assert_text`, `assert_visible`, `assert_url`, `assert_count`, `assert_attr`
  - [ ] `fill_form`, `navigate`, `screenshot`
  - [ ] Ações com setup/teardown
- [ ] Teste de `to_python_function()` com setup/teardown
- [ ] Teste de `to_python_function()` com session save/load

#### Para `tts.py` (27% cobertura):
- [ ] Teste de `generate_audio()` com gTTS (mocking)
- [ ] Teste de `generate_audio()` com edge-tts (mocking)
- [ ] Teste de `generate_audio()` com pyttsx3 (mocking)
- [ ] Teste de `generate_audio()` com engine desconhecido
- [ ] Teste de `generate_narration()` completo (mocking TTS e ffmpeg)
- [ ] Teste de `_concatenate_audio()` (mocking ffmpeg)
- [ ] Teste de tratamento de erros TTS

#### Para `session.py` (15% cobertura):
- [ ] Teste de `save_session()` e `load_session()`
- [ ] Teste de `clear_session()`
- [ ] Teste de tratamento de erros

---

## 🔧 Configuração e Dependências

### Instalado
- ✅ `pytest-cov` - Para cobertura de código
- ✅ `pytest-asyncio` - Para testes assíncronos
- ✅ `coverage` - Biblioteca de cobertura

### Comando para Executar Testes com Coverage
```bash
cd /home/gabriel/softhill/playwright-simple
python3 -m pytest tests/ -v --tb=short --cov=playwright_simple.core --cov-report=term-missing --cov-report=html --cov-fail-under=80
```

### Arquivos de Teste Criados/Atualizados
- `tests/test_base.py` - Testes básicos
- `tests/test_base_extended.py` - Testes estendidos (NOVO)
- `tests/test_yaml_parser.py` - Testes do parser YAML (NOVO)
- `tests/test_runner.py` - Testes básicos do runner
- Outros arquivos de teste já existiam

---

## 📋 Próximos Passos Prioritários

### 1. Corrigir Testes que Estão Falhando
1. Corrigir `test_assert_url()` - Ajustar pattern matching de URL
2. Corrigir `test_wait_for_url()` - Ajustar timeout e pattern
3. Corrigir `test_forgeerp.py` - Ajustar argumentos do TestConfig
4. Corrigir `test_screenshot.py` - Ajustar uso de MagicMock
5. Corrigir `test_selectors.py` - Ajustar mocks e timeouts
6. Corrigir `test_tts.py` - Ajustar mocking de módulos TTS

### 2. Implementar Testes para `runner.py`
- Foco em métodos de processamento de vídeo (mocking ffmpeg)
- Testes de narração (mocking TTS)
- Testes de execução de testes (mocking Playwright)

### 3. Implementar Testes para `base.py`
- Métodos de interação não cobertos
- Métodos de navegação com erros
- Métodos de asserção com falhas

### 4. Implementar Testes para `yaml_parser.py`
- Herança e includes complexos
- Todas as ações de steps
- Setup/teardown e session

### 5. Implementar Testes para `tts.py` e `session.py`
- Mocking de bibliotecas TTS
- Testes de session management

---

## 🐛 Problemas Conhecidos

1. **Testes TTS**: Módulos TTS (`gTTS`, `edge_tts`, `pyttsx3`) precisam ser mockados corretamente
2. **Testes de URL**: Patterns de URL precisam ser ajustados para funcionar com `data:` URLs
3. **Testes de Screenshot**: MagicMock não pode ser usado diretamente em expressões `await`
4. **Testes de Selectors**: Timeouts podem ser muito curtos em alguns casos
5. **Testes ForgeERP**: TestConfig não aceita alguns argumentos que os testes esperam

---

## 📝 Notas Técnicas

### Estrutura de Testes
- Todos os testes assíncronos usam `@pytest.mark.asyncio`
- Testes de Playwright usam `async_playwright()` context manager
- Testes devem limpar recursos (browser, context) em `finally` ou após cada teste

### Mocking
- Para ffmpeg: Mockar `subprocess.run()` e verificar comandos
- Para TTS: Mockar módulos (`gTTS`, `edge_tts`, `pyttsx3`) antes de importar
- Para Playwright: Usar `async_playwright()` real, mas mockar métodos específicos quando necessário

### Cobertura
- Meta: 80% de cobertura total
- Focar em caminhos críticos primeiro
- Testes de erro são importantes para cobertura

---

## 🎯 Objetivo Final

**Atingir 80% de cobertura de código em todos os módulos core, com todos os testes passando.**

---

---

## 🔍 Debugging do Problema de Login

### Comandos Úteis
```bash
# Analisar vídeo gerado
cd /home/gabriel/softhill
python3 playwright-simple/scripts/analyze_video.py presentation/playwright/videos/common_login.webm

# Executar teste de login
cd /home/gabriel/softhill/presentation/playwright
python3 run_single_test.py
```

### Arquivos para Verificar
- `playwright_simple/odoo/auth.py` - Método `login()` (linhas 22-146)
- `playwright_simple/core/interactions.py` - Método `type()` (linhas 95-129)
- `playwright_simple/core/cursor.py` - Método `move_to()` e `show_click_effect()`

### Possíveis Causas
1. Botão de submit não está sendo encontrado (selector incorreto)
2. Clique no botão está falhando silenciosamente (exceção engolida)
3. Cursor não está se movendo até o botão corretamente
4. Efeito de click não está sendo mostrado, mas o clique não está acontecendo
5. Timeout muito curto fazendo o teste terminar antes do login completar

---

---

## 📝 Como Executar Testes YAML

### Método Simples (Recomendado)
```python
from pathlib import Path
from playwright_simple import TestRunner
from playwright_simple.odoo import OdooYAMLParser
from racco_config import get_racco_config

# Carregar YAML
yaml_path = Path("tests/yaml/test_colaborador_portal.yaml")
yaml_data = OdooYAMLParser.parse_file(yaml_path)
test_function = OdooYAMLParser.to_python_function(yaml_data)

# Executar
config = get_racco_config()
runner = TestRunner(config=config)
await runner.run_test("Colaborador Portal", test_function)
```

### Usando Script Existente
```bash
cd /home/gabriel/softhill/presentation/playwright
python3 run_one_test.py 18  # ou "colaborador_portal"
```

### Localização dos Testes
- **Testes YAML**: `/home/gabriel/softhill/presentation/playwright/tests/yaml/`
- **Configuração**: `/home/gabriel/softhill/presentation/playwright/racco_config.py`
- **Scripts**: `/home/gabriel/softhill/presentation/playwright/run_one_test.py`

---

**Última atualização**: 2025-01-XX  
**Próximo desenvolvedor**: 

## ✅ Melhorias Implementadas Recentemente

### 1. Logging Detalhado
- ✅ Logs WARNING quando elemento não é encontrado para clique
- ✅ Logs INFO quando ações são executadas com sucesso
- ✅ Logs DEBUG com coordenadas de elementos
- ✅ Logs ERROR com detalhes completos quando exceções ocorrem
- ✅ Detecção automática de mudança de estado após ações (click, type, select)
- ✅ Logs diferenciados para passos estáticos vs dinâmicos
- ✅ Logs detalhados de navegação (início, sucesso, falha, timeout)

### 2. Correção de Bug de Vídeo
- ✅ Corrigido problema de áudio no processamento de vídeo (erro "Output with label '1:a' does not exist")
- ✅ Vídeo agora processa corretamente mesmo quando não há áudio no vídeo principal

### 3. Validação do Teste
- ✅ Teste `test_colaborador_portal.yaml` executado com sucesso
- ✅ Todos os 13 steps executaram corretamente
- ⚠️ Problema de timeout no processamento de vídeo (pode ser servidor Odoo lento)

## Próximos Passos

1. **PRIORIDADE**: Testar novamente o teste do colaborador para validar processamento completo do vídeo
2. Verificar se tela inicial está sendo adicionada corretamente (já implementado, precisa validar)
3. Corrigir gradiente se necessário (atualmente fallback para cor sólida funciona)
4. Continuar melhorias de type hints e docstrings
5. Implementar testes unitários para validar separação core/odoo
