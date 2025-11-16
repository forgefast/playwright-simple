# Requisitos de Migração - Funcionalidades Antigas para Nova Estrutura

## Contexto

A estrutura antiga (`presentation/playwright/`) tinha funcionalidades avançadas que precisam ser migradas para a nova estrutura do `playwright-simple`. Este documento lista os requisitos e o plano de implementação incremental.

## Funcionalidades da Estrutura Antiga

### 1. Passos Estáticos vs Dinâmicos

**Conceito:**
- **Passo Estático** (`static: true`): Passo que fica visível por mais tempo no vídeo (ex: screenshots para demonstração)
- **Passo Dinâmico**: Passo normal que executa rapidamente

**Implementação Antiga:**
```yaml
- screenshot: 01_dashboard
  description: Dashboard
  static: true  # Fica visível por mais tempo
```

**Requisito:**
- Suportar flag `static: true` em steps
- Passos estáticos devem ter duração mínima configurável (ex: 3-5 segundos)
- Passos dinâmicos executam normalmente

**Prioridade:** Alta

---

### 2. Máquina de Estados

**Conceito:**
- Cada passo conhece seu estado anterior e próximo
- Estado capturado antes e depois de cada passo
- Permite continuar de um checkpoint específico

**Implementação Antiga:**
- `WebState` capturado antes e depois de cada step
- Estado inclui: URL, HTML snapshot, timestamp, step_number

**Requisito:**
- Manter sistema de `WebState` atual (já existe em `playwright_simple/core/state.py`)
- Melhorar captura de estado para incluir mais informações
- Permitir salvar/restaurar estado em checkpoints

**Prioridade:** Média (já parcialmente implementado)

---

### 3. Timing de Passos (Start Time, Duration, End Time)

**Conceito:**
- Cada passo tem:
  - **Start Time**: Quando o passo começou (em tempo de vídeo)
  - **Duration**: Quanto tempo o passo durou
  - **End Time**: Quando o passo terminou
- Esses dados servem como baliza para:
  - Legendas (quando mostrar/esconder)
  - Áudio (quando tocar narração)
  - Sincronização de vídeo

**Implementação Antiga:**
- Timestamps capturados durante execução
- Dados salvos em metadados do step

**Requisito:**
- Capturar timestamps de início/fim de cada step
- Calcular duração de cada step
- Armazenar em `TestStep` ou metadados
- Usar para sincronização de legendas e áudio

**Prioridade:** Alta

---

### 4. Legendas Embutidas no Vídeo (Hard Subtitles)

**Conceito:**
- Legendas podem ser:
  - **Soft Subtitles**: Arquivo SRT separado (já implementado)
  - **Hard Subtitles**: Legendas embutidas no vídeo (não implementado)

**Implementação Antiga:**
```yaml
config:
  video:
    hard_subtitles: true  # Legendas embutidas no vídeo
```

**Requisito:**
- Suportar `hard_subtitles: true` na configuração
- Usar ffmpeg para embutir legendas no vídeo
- Manter compatibilidade com soft subtitles

**Prioridade:** Média

---

### 5. Vídeo Acelerado e Desacelerado (Performance)

**Conceito:**
- Gravar vídeo em velocidade acelerada (ex: 2x) para performance
- Desacelerar depois no processamento final (ex: 0.5x)
- Resultado: Vídeo final em velocidade normal, mas gravação mais rápida

**Implementação Antiga:**
- Gravação com `slow_mo: 0` (rápido)
- Processamento com `ffmpeg` para ajustar velocidade

**Requisito:**
- Suportar `video.record_speed` (ex: 2.0 = 2x mais rápido)
- Suportar `video.playback_speed` (ex: 0.5 = metade da velocidade)
- Processar vídeo com ffmpeg para ajustar velocidade final

**Prioridade:** Média

---

### 6. Hot Reload

**Conceito:**
- Monitorar mudanças em arquivos YAML
- Recarregar YAML sem reiniciar o teste
- Continuar execução do ponto onde parou

**Implementação Antiga:**
- `hot_reload_enabled: true` na config
- Monitoramento de arquivos (watchdog ou similar)

**Requisito:**
- Implementar monitoramento de arquivos YAML
- Recarregar YAML quando detectar mudança
- Continuar execução sem perder estado

**Prioridade:** Alta (já parcialmente implementado)

---

### 7. Debugging Avançado

**Conceito:**
- Pausa em erros
- Modo interativo (shell Python)
- HTML snapshots salvos
- Estado JSON salvo
- Breakpoints em passos específicos

**Implementação Antiga:**
```yaml
config:
  debug:
    enabled: true
    pause_on_error: true
    interactive_mode: true
    fast_mode: true  # Ignora delays em passos static
```

**Requisito:**
- Melhorar extensão de debug existente
- Implementar `fast_mode` (ignora delays em passos static)
- Melhorar modo interativo
- Adicionar breakpoints (`breakpoint: true` no step)

**Prioridade:** Alta (já parcialmente implementado)

---

### 8. Espera por Carregamento da Tela (Não Hardcoded)

**Conceito:**
- Cada passo espera a tela carregar antes de continuar
- Não usa `wait: 0.2` hardcoded
- Usa `wait_for_load_state("load")` ou `wait_for_load_state("networkidle")`

**Implementação Antiga:**
```python
await page.wait_for_load_state("load", timeout=10000)
```

**Requisito:**
- Implementar espera automática por carregamento após cada ação
- Usar `wait_for_load_state` do Playwright
- Configurável: `load`, `domcontentloaded`, `networkidle`
- Timeout configurável

**Prioridade:** Alta

---

### 9. Fast Mode (Ignora Delays em Passos Static)

**Conceito:**
- Quando `fast_mode: true`, ignora delays extras em passos `static: true`
- Útil para debug rápido (chegar rápido onde está o problema)

**Implementação Antiga:**
```yaml
config:
  debug:
    fast_mode: true  # Ignora delays em passos static
```

**Requisito:**
- Implementar `fast_mode` na config de debug
- Quando ativo, ignora duração extra de passos static
- Mantém comportamento normal quando desativado

**Prioridade:** Média

---

### 10. Breakpoints em Passos Específicos

**Conceito:**
- Pausar execução em passos específicos
- Útil para inspeção manual

**Implementação Antiga:**
```yaml
- go_to: "Vendas > Produtos"
  breakpoint: true  # Pausa aqui
```

**Requisito:**
- Suportar `breakpoint: true` em steps
- Pausar execução quando encontrar breakpoint
- Abrir modo interativo se `interactive_mode: true`

**Prioridade:** Média

---

## Plano de Implementação Incremental

### Fase 1: Básico (Começar Simples)
1. ✅ Executar teste simples e gerar vídeo (sem áudio/legendas)
2. ⏳ Implementar espera por carregamento da tela
3. ⏳ Capturar timestamps de início/fim de cada step

### Fase 2: Timing e Sincronização
4. ⏳ Implementar passos estáticos (`static: true`)
5. ⏳ Usar timestamps para sincronização de legendas
6. ⏳ Usar timestamps para sincronização de áudio

### Fase 3: Performance e Otimização
7. ⏳ Implementar vídeo acelerado/desacelerado
8. ⏳ Implementar `fast_mode` para debug

### Fase 4: Debugging Avançado
9. ⏳ Melhorar hot reload (monitoramento de arquivos)
10. ⏳ Implementar breakpoints
11. ⏳ Melhorar modo interativo

### Fase 5: Legendas e Áudio
12. ⏳ Implementar hard subtitles
13. ⏳ Sincronizar áudio com timestamps de steps
14. ⏳ Melhorar qualidade de legendas e áudio

---

## Exemplo de Teste com Todas as Funcionalidades

```yaml
name: Teste Completo
description: Teste com todas as funcionalidades

config:
  video:
    enabled: true
    record_speed: 2.0  # Grava 2x mais rápido
    playback_speed: 0.5  # Reproduz em 0.5x (resultado: velocidade normal)
    subtitles: true
    hard_subtitles: true  # Legendas embutidas
    audio: true
  debug:
    enabled: true
    pause_on_error: true
    interactive_mode: true
    hot_reload_enabled: true
    fast_mode: false  # Respeita delays de passos static
  browser:
    wait_for_load: "networkidle"  # Espera carregamento completo
    wait_timeout: 10000

steps:
  - action: login
    login: admin
    password: admin
    database: devel
    subtitle: "Realizando login"
    audio: "Realizando login no sistema"
    # Timestamps serão capturados automaticamente
  
  - action: navigate_menu
    menu_path: ["Dashboard"]
    subtitle: "Acessando Dashboard"
    breakpoint: false  # Pode pausar aqui se true
  
  - action: screenshot
    name: dashboard
    description: "Dashboard"
    subtitle: "Visualizando Dashboard"
    static: true  # Fica visível por mais tempo (3-5s)
    # Em fast_mode, ignora delay extra
```

---

## Status Atual

### ✅ Concluído

1. **✅ Gerar vídeo de teste simples** (sem áudio/legendas)
   - Vídeo gerado com sucesso: `videos/Teste Simples Login.webm` (32KB)
   - Teste executado via CLI Python direto
   - Vídeo processado e validado

2. **✅ Lista de requisitos criada**
   - Documento completo com todas as funcionalidades antigas
   - Plano de implementação incremental definido
   - Prioridades estabelecidas

### ✅ Fase 1 Concluída

3. **✅ Implementar espera por carregamento** automática
   - Adicionado `wait_for_load_state` após cada ação no `StepExecutor`
   - Configurável via `browser.wait_for_load` (load/domcontentloaded/networkidle)
   - Timeout configurável via `browser.wait_timeout`
   - Método genérico `wait_until_ready()` adicionado ao `SimpleTestBase`

4. **✅ Capturar timestamps** de início/fim de cada step
   - Timestamps já existem em `TestStep` (start_time, execute_time, wait_load_time, end_time)
   - Melhorado cálculo de duração para passos estáticos

5. **✅ Implementar passos estáticos** (`static: true`) com duração mínima
   - Suporte a `static: true` em steps
   - Duração mínima configurável via `step.static_min_duration` (padrão: 3.0s)
   - Cálculo preciso baseado em timestamps reais

6. **✅ Implementar fast_mode** (ignora delays em passos static)
   - Configurável via `step.fast_mode`
   - Quando ativo, ignora duração extra de passos static

### 📋 Próximos Passos (Fase 2)

1. **Implementar breakpoints** (`breakpoint: true`)
2. **Implementar vídeo acelerado/desacelerado** (record_speed/playback_speed)
3. **Implementar hard subtitles** (legendas embutidas no vídeo)
4. **Melhorar hot reload** (monitoramento de arquivos)

---

## Notas Técnicas

- A estrutura antiga usava `wait_for_load_state("load")` após cada ação
- Passos static tinham duração mínima de ~3-5 segundos
- Fast mode ignorava essa duração extra
- Timestamps eram usados para sincronizar legendas e áudio no processamento final do vídeo

