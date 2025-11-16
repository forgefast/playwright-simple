# Fluxo de Processamento de Vídeo

## Visão Geral

O processamento de vídeo acontece em `test_executor.py` após a execução do teste, e delega o trabalho pesado para `video_processor.py`.

## Fluxo Completo

### 1. Execução do Teste (`test_executor.py`)

```
execute() 
  ├─ Executa o teste (grava vídeo em .webm)
  ├─ Coleta test_steps (para legendas)
  └─ Após fechar contexto:
      └─ Encontra vídeo gravado (webm)
      └─ Verifica se precisa processar (needs_processing)
      └─ Se sim, chama process_all_in_one()
```

### 2. Decisão de Processamento (`test_executor.py:554-561`)

O código decide se precisa processar baseado em:
- `test_name is not None` → precisa tela inicial
- `speed != 1.0` → precisa ajustar velocidade
- `subtitles and test_steps` → precisa adicionar legendas
- `audio_file` → precisa adicionar áudio
- `narration_audio` → precisa adicionar narração
- `needs_conversion` → precisa converter webm→mp4

### 3. Processamento (`video_processor.py:process_all_in_one`)

#### Etapa 1: Criação de Tela Inicial (linhas 331-346)
```
_se_create_intro_screen()
  └─ Executa FFmpeg para criar vídeo de 3s com texto
  └─ Salva em /tmp/intro_{name}.mp4
  └─ Tempo: ~0.1-0.5s (rápido)
```

#### Etapa 2: Geração de Legendas (linhas 401-423)
```
subtitle_generator.generate()
  └─ Cria arquivo .srt a partir de test_steps
  └─ Calcula timings baseado em start_time
  └─ Salva em videos/{video_name}.srt
  └─ Tempo: ~0.01-0.1s (muito rápido)
```

#### Etapa 3: Construção de Filtros (linhas 348-424)
```
- Monta lista de input_files: [intro_video, main_video]
- Adiciona filtros de velocidade (se speed != 1.0)
- Adiciona filtro de legendas: subtitles='{srt_path}'
- Monta filter_complex para FFmpeg
- Tempo: ~0.001s (instantâneo)
```

#### Etapa 4: Montagem do Comando FFmpeg (linhas 425-640)
```
- Adiciona inputs: -i intro.mp4 -i main.webm
- Adiciona filter_complex com concatenação + legendas
- Define codec: libx264 -preset ultrafast -crf 23 -threads 0
- Define output: videos/{name}_processed.mp4
- Tempo: ~0.005s (muito rápido)
```

#### Etapa 5: Execução do FFmpeg (linhas 652-664)
```
subprocess.run(['ffmpeg', ...])
  └─ AQUI ESTÁ O GARGALO!
  └─ FFmpeg processa:
     1. Aplica filtro subtitles (FORÇA RE-ENCODE COMPLETO)
     2. Concatena intro + vídeo principal
     3. Converte para MP4
  └─ Tempo: 30-300s (MUITO LENTO!)
```

## O Problema: Filtro `subtitles`

O filtro `subtitles` do FFmpeg é extremamente lento porque:

1. **Força re-encode completo**: Não pode usar `-c:v copy`, precisa re-encodar cada frame
2. **Processamento frame-by-frame**: Renderiza cada legenda em cada frame
3. **Sem otimização**: Não há como acelerar significativamente

### Comando FFmpeg Gerado (exemplo):

```bash
ffmpeg \
  -i /tmp/intro_Common_Login.mp4 \
  -i videos/c2aee62dd5a1f1d5982c1547c6eed154.webm \
  -filter_complex \
    "[1:v]subtitles='/path/to/video.srt':force_style='...'[main_v]; \
     [0:v][main_v]concat=n=2:v=1:a=0[v]" \
  -map [v] \
  -c:v libx264 -preset ultrafast -crf 23 -threads 0 \
  -c:a copy \
  -y videos/c2aee62dd5a1f1d5982c1547c6eed154_processed.mp4
```

## Fast Path vs Full Path

### Fast Path (rápido - sem legendas)
- Condições: tem intro + sem filtros de vídeo + speed=1.0 + sem áudio externo
- Processo: apenas concatenação + conversão
- Tempo: ~5-15s

### Full Path (lento - com legendas)
- Condições: tem legendas OU outros filtros
- Processo: re-encode completo com filtros
- Tempo: 30-300s (depende do tamanho do vídeo)

## Onde Está a Lentidão?

Baseado no processo FFmpeg que encontramos rodando:

```
ffmpeg -i intro.mp4 -i main.webm \
  -filter_complex \
    "[1:v]subtitles='...srt'[main_v]; \
     [0:v][main_v]concat=n=2:v=1:a=0[v]" \
  -c:v libx264 -preset ultrafast ...
```

O problema é o filtro `subtitles` que está processando o vídeo inteiro frame-by-frame.

## Alternativas Possíveis

1. **Usar drawtext em vez de subtitles**: Mais rápido, mas menos flexível
2. **Processar legendas em passagem separada**: Mais controle, mas 2 passagens
3. **Desabilitar legendas quando velocidade é crítica**: Trade-off qualidade/velocidade
4. **Usar hardware acceleration**: Se disponível (nvenc, etc)

## Arquivos Principais

- `test_executor.py:528-663` - Orquestração do processamento
- `video_processor.py:279-759` - Lógica de processamento FFmpeg
- `subtitle_generator.py:41-260` - Geração de arquivo SRT

