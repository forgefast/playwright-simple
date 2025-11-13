# Handoff Note - Processamento de Vídeo e Legendas

**Data**: 2025-11-13  
**Status**: 🔧 Em Progresso - Problema Principal Identificado e Parcialmente Corrigido

---

## 🎯 OBJETIVO

Corrigir o processamento de vídeo que estava falhando silenciosamente. O vídeo webm era gravado, mas o processamento para MP4 com tela inicial e legendas não estava sendo executado.

---

## 🔍 PROBLEMA IDENTIFICADO

### Sintoma Principal
- Vídeo webm era gravado com sucesso
- Processamento para MP4 não ocorria
- Erro: `RuntimeError: Vídeo deveria ser MP4 mas é .webm`
- `process_all_in_one` estava sendo chamado, mas retornava o vídeo original sem processar

### Causa Raiz
1. **Lógica de `use_fast_path` incorreta**: Não verificava `has_video_filters`, permitindo usar fast path mesmo com legendas
2. **Falta de `-y` no comando FFmpeg**: Quando `use_fast_path=True`, o comando não tinha `-y` para sobrescrever arquivo de saída
3. **Early return no bloco `else`**: Quando não havia `filter_complex_parts` e não estava usando fast path, o código retornava o vídeo original sem processar

---

## ✅ CORREÇÕES APLICADAS

### 1. Correção da Lógica `use_fast_path`
**Arquivo**: `playwright_simple/core/runner/video_processor.py` (linha ~451)

```python
# ANTES (ERRADO):
use_fast_path = (has_intro and not audio_filters and 
               self.config.video.speed == 1.0 and not has_audio_input)

# DEPOIS (CORRETO):
use_fast_path = (has_intro and not audio_filters and 
               self.config.video.speed == 1.0 and not has_audio_input and
               not has_video_filters)  # NO VIDEO FILTERS for fast path!
```

### 2. Adição de `-y` no Bloco `use_fast_path`
**Arquivo**: `playwright_simple/core/runner/video_processor.py` (linhas ~471, ~482, ~503)

Adicionado `cmd.extend(['-y', str(output_path)])` em todos os caminhos do `use_fast_path` para garantir que FFmpeg sobrescreva o arquivo de saída.

### 3. Logs de Debug Adicionados
Adicionados prints detalhados para rastrear a execução:
- `🔍 DEBUG: needs_processing=...`
- `🔍 DEBUG: process_all_in_one chamado: ...`
- `🔍 DEBUG: FFmpeg disponível`
- `🔍 DEBUG: Tela inicial criada: ...`
- `🔍 DEBUG: Legendas geradas: ...`
- `🔍 DEBUG: filter_complex_parts=..., use_fast_path=...`
- `🔍 DEBUG: Processando vídeo: ...`
- `🔍 DEBUG: Iniciando processamento FFmpeg...`

---

## 📊 STATUS ATUAL

### ✅ Funcionando
- ✅ Tela inicial sendo criada corretamente (corrigido erro de sintaxe do `drawtext`)
- ✅ Legendas sendo geradas (arquivo SRT criado)
- ✅ FFmpeg sendo executado quando `use_fast_path=False` (com legendas)
- ✅ Vídeo `_processed.mp4` sendo gerado (confirmado: arquivos de 1.6MB e 3.1MB encontrados)

### ⚠️ Pendências
- ⚠️ Vídeo final não está sendo renomeado de `*_processed.mp4` para `{test_name}.mp4`
- ⚠️ Processamento está demorando muito (timeout após 120s, mas vídeo é gerado)
- ⚠️ Teste simples (`test_simple_login.yaml`) criado para debug rápido, mas ainda precisa ser validado completamente

---

## 🔧 PRÓXIMOS PASSOS

### 1. Verificar Renomeação do Vídeo Final
**Arquivo**: `playwright_simple/core/runner/test_executor.py` (linhas ~580-590)

Verificar se o código que renomeia `*_processed.mp4` para `{test_name}.mp4` está sendo executado. O vídeo está sendo gerado, mas não está sendo renomeado.

```python
if needs_conversion and final_path.suffix == ".mp4":
    if expected_path.exists():
        expected_path.unlink()
    final_path.rename(expected_path)
    final_path = expected_path
```

### 2. Otimizar Performance do Processamento
O processamento está demorando muito. Possíveis otimizações:
- Verificar se o preset `ultrafast` está sendo usado corretamente
- Considerar processar legendas de forma assíncrona
- Verificar se há algum bloqueio no FFmpeg

### 3. Validar Teste Completo
Executar o teste completo `test_colaborador_portal.yaml` (ID 18) para validar que tudo está funcionando end-to-end.

### 4. Remover Logs de Debug
Após validação completa, remover os prints de debug (`🔍 DEBUG:`) para limpar a saída.

---

## 📝 ARQUIVOS MODIFICADOS

1. **`playwright_simple/core/runner/video_processor.py`**
   - Corrigida lógica de `use_fast_path` (linha ~451)
   - Adicionado `-y` nos comandos FFmpeg do fast path (linhas ~471, ~482, ~503)
   - Corrigida sintaxe do `drawtext` para tela inicial (linha ~226 - vírgula entre dois drawtext)
   - Melhorados logs de erro do FFmpeg (linhas ~594-613)
   - Adicionados prints de debug extensivos

2. **`playwright_simple/core/runner/test_executor.py`**
   - Adicionado tratamento de exceções `VideoProcessingError` (linhas ~572-587)
   - Adicionados logs de debug (linhas ~526, ~551, ~566, ~576)

3. **`presentation/playwright/tests/yaml/test_simple_login.yaml`** (NOVO)
   - Teste simples criado para debug rápido (apenas login + screenshot)

4. **`presentation/playwright/run_one_test.py`**
   - Adicionado mapeamento para teste simples (ID 99)

---

## 🧪 TESTES PARA VALIDAÇÃO

### Teste Simples (Rápido)
```bash
cd /home/gabriel/softhill/presentation/playwright
timeout 300 python3 run_one_test.py 99
```

**Esperado**:
- ✅ Vídeo gravado
- ✅ Tela inicial criada
- ✅ Legendas geradas
- ✅ Vídeo `teste_simples_login.mp4` gerado (não apenas `*_processed.mp4`)

### Teste Completo
```bash
cd /home/gabriel/softhill/presentation/playwright
timeout 600 python3 run_one_test.py 18
```

**Esperado**:
- ✅ Vídeo `portal_do_colaborador_racco.mp4` gerado
- ✅ Tela inicial incluída
- ✅ Legendas incluídas
- ✅ Processamento completo em tempo razoável (< 5 minutos)

---

## 🐛 PROBLEMAS CONHECIDOS

1. **Renomeação do Vídeo Final**
   - Vídeo `_processed.mp4` é gerado, mas não é renomeado para `{test_name}.mp4`
   - Verificar lógica de renomeação em `test_executor.py`

2. **Performance do Processamento**
   - Processamento está demorando muito (timeout após 120s)
   - Vídeo é gerado, mas processo não termina
   - Pode ser problema de timeout ou bloqueio no FFmpeg

3. **Logs Excessivos**
   - Muitos prints de debug (`🔍 DEBUG:`) foram adicionados
   - Remover após validação completa

---

## 📚 CONTEXTO TÉCNICO

### Arquitetura de Processamento
1. **Gravação**: Playwright grava vídeo em `.webm`
2. **Processamento**: `process_all_in_one()` processa o vídeo:
   - Cria tela inicial (3s)
   - Gera legendas (SRT)
   - Concatena intro + vídeo principal
   - Adiciona legendas (filtro `subtitles`)
   - Converte para MP4 (se necessário)
3. **Renomeação**: Renomeia `*_processed.mp4` para `{test_name}.mp4`

### Fast Path vs Full Path
- **Fast Path**: Quando não há filtros de vídeo, apenas concatenação + conversão
- **Full Path**: Quando há filtros (legendas), processamento completo com re-encode

### Comandos FFmpeg Principais
- **Tela Inicial**: `ffmpeg -f lavfi -i color=... -vf drawtext=...`
- **Concatenação**: `[0:v][1:v]concat=n=2:v=1:a=0[v]`
- **Legendas**: `subtitles='{srt_path}':force_style=...`
- **Conversão**: `-c:v libx264 -preset ultrafast -crf 23`

---

## 💡 DICAS PARA CONTINUAÇÃO

1. **Verificar Renomeação**: Adicionar logs antes/depois da renomeação para ver se está sendo executada
2. **Verificar Timeout**: Aumentar timeout ou verificar se FFmpeg está travando
3. **Testar com Vídeo Pequeno**: Usar teste simples para iterar mais rápido
4. **Monitorar FFmpeg**: Verificar se FFmpeg está realmente processando ou travado

---

## 📦 COMMITS REALIZADOS

1. `fix: Otimizar processamento de vídeo e criação de tela inicial`
2. `fix: Corrigir criação de tela inicial - separar drawtext filters corretamente`
3. `fix: Melhorar logs de erro do FFmpeg e tratamento de exceções`
4. `debug: Adicionar logs no início de process_all_in_one para debug`
5. `debug: Adicionar mais logs para identificar onde processamento está falhando`
6. `debug: Adicionar logs detalhados de chamada e retorno de process_all_in_one`
7. `debug: Adicionar prints para garantir que logs apareçam`
8. `debug: Adicionar mais prints para rastrear execução de process_all_in_one`
9. `debug: Adicionar prints para identificar onde process_all_in_one está retornando`
10. `fix: Corrigir lógica de use_fast_path - não usar quando há filtros de vídeo`
11. `fix: Adicionar -y e prints no bloco use_fast_path para garantir execução FFmpeg`

---

## 🎬 CONCLUSÃO

O problema principal foi identificado e corrigido:
- ✅ FFmpeg agora executa corretamente
- ✅ Vídeo `_processed.mp4` está sendo gerado
- ⚠️ Pendente: Renomeação do vídeo final e otimização de performance

**Próximo passo crítico**: Verificar por que o vídeo não está sendo renomeado de `*_processed.mp4` para `{test_name}.mp4`.
