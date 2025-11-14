# Plano de Melhorias - Funcionalidades de Vídeo, Legendas e Áudio

## Estado Atual

### ✅ Funcionalidades Implementadas

1. **Gravação de Vídeo**
   - Playwright grava automaticamente em `.webm`
   - Suporte para conversão para `.mp4`
   - Configuração de qualidade (low, medium, high)
   - Suporte para viewport customizado

2. **Legendas (Subtitles)**
   - Geração de arquivo SRT a partir de test_steps
   - Soft subtitles (faixa separada - rápido, sem re-encode)
   - Hard subtitles (embutidas no vídeo - lento, requer re-encode)
   - Sincronização com timestamps dos steps

3. **Áudio/Narração**
   - Geração de TTS (gTTS, edge-tts, pyttsx3)
   - Embutimento de áudio de fundo
   - Mixagem de narração + áudio de fundo
   - Sincronização com steps

4. **Processamento de Vídeo**
   - Ajuste de velocidade (speed)
   - Tela inicial (intro screen) - temporariamente desabilitada
   - Processamento tudo-em-um (process_all_in_one)
   - Fast path para casos sem filtros

### ⚠️ Problemas Conhecidos

1. **Hard Subtitles são Lentos**
   - Filtro `subtitles` do FFmpeg força re-encode completo
   - Tempo: 30-300s dependendo do tamanho do vídeo
   - Soft subtitles são muito mais rápidos (sem re-encode)

2. **Tela Inicial Desabilitada**
   - Temporariamente desabilitada para focar em correções
   - Precisa ser reativada e testada

3. **Sincronização de Timestamps**
   - Pode precisar melhorias na precisão
   - Timestamps dos steps podem não estar perfeitos

## Plano de Melhorias

### Fase 1: Testes e Validação (Prioridade: ALTA)

**Objetivo**: Garantir que todas as funcionalidades básicas estão funcionando

1. **Teste de Gravação Básica**
   - ✅ Gravação de vídeo funcionando
   - Testar diferentes qualidades
   - Testar diferentes codecs (webm, mp4)

2. **Teste de Legendas**
   - Testar geração de SRT
   - Testar soft subtitles (sem re-encode)
   - Testar hard subtitles (com re-encode)
   - Validar sincronização

3. **Teste de Áudio**
   - Testar geração de TTS
   - Testar embutimento de áudio
   - Testar mixagem de narração + áudio de fundo
   - Validar sincronização

### Fase 2: Otimizações (Prioridade: MÉDIA)

**Objetivo**: Melhorar performance e qualidade

1. **Otimizar Hard Subtitles**
   - Investigar alternativas ao filtro `subtitles`
   - Considerar `drawtext` (mais rápido, menos flexível)
   - Considerar hardware acceleration (nvenc, etc)
   - Melhorar preset FFmpeg (ultrafast já usado)

2. **Melhorar Sincronização**
   - Garantir timestamps precisos nos steps
   - Melhorar cálculo de duração de legendas
   - Sincronizar áudio com legendas

3. **Reativar Tela Inicial**
   - Reativar criação de intro screen
   - Testar e validar funcionamento
   - Otimizar criação (já é rápida: ~0.1-0.5s)

### Fase 3: Funcionalidades Avançadas (Prioridade: BAIXA)

**Objetivo**: Adicionar funcionalidades extras

1. **Múltiplas Faixas de Áudio**
   - Suporte para múltiplas narrações
   - Mixagem avançada de áudio

2. **Legendas Customizáveis**
   - Estilos personalizados
   - Posicionamento customizado
   - Múltiplas faixas de legendas

3. **Efeitos de Vídeo**
   - Transições
   - Overlays
   - Animações

## Arquivos Principais

- `playwright_simple/core/runner/video_processor.py` - Processamento de vídeo
- `playwright_simple/core/runner/subtitle_generator.py` - Geração de legendas
- `playwright_simple/core/runner/audio_processor.py` - Processamento de áudio
- `playwright_simple/core/runner/test_executor.py` - Orquestração
- `playwright_simple/core/tts.py` - TTS (Text-to-Speech)
- `playwright_simple/extensions/video/config.py` - Configuração

## Próximos Passos

1. Criar testes para validar funcionalidades
2. Testar cada funcionalidade isoladamente
3. Identificar problemas específicos
4. Implementar melhorias incrementais
5. Validar com testes reais

