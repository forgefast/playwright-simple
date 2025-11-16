# Débito Técnico

## Captura de Eventos em Links que Causam Navegação

### Problema

Quando clicamos em um link (`<a href="...">`) via comandos CLI programáticos (`pw-click`), o evento de clique pode não ser capturado pelo `event_capture` antes que a navegação aconteça e limpe o contexto da página.

### Contexto

**IMPORTANTE**: Injetar JavaScript no navegador para capturar eventos NÃO é gambiarra - é o padrão da indústria usado por:
- Playwright Codegen (`playwright codegen`)
- Selenium IDE
- Katalon Recorder
- Extensões de navegador (content scripts)
- Ferramentas de session replay (Hotjar, FullStory, etc.)

O sistema usa dois mecanismos para capturar ações:

1. **`event_capture`**: Captura eventos DOM nativos através de listeners JavaScript injetados na página. **Este é o padrão da indústria** para gravação de testes. Funciona bem para ações do usuário na tela (cliques reais do mouse), exceto para links que causam navegação imediata.

2. **Comandos CLI programáticos** (`pw-click`, `pw-type`, etc.): Executam ações via Playwright diretamente. Agora adicionam diretamente ao YAML (não dependem mais do `event_capture`).

### Problema Específico

- Quando fazemos `element.click()` em um link via Playwright, o evento DOM é disparado
- O listener JavaScript captura o evento e adiciona ao array `window.__playwright_recording_events`
- Mas a navegação acontece imediatamente, limpando o contexto antes do polling processar o evento
- Resultado: O clique no link não aparece no YAML gerado

### Solução Atual (Temporária)

1. **Processar eventos pendentes antes da navegação**: O `_handle_navigation` em `event_capture.py` agora processa eventos pendentes antes de limpar o array.

2. **Detectar links e disparar evento manualmente**: Em `element_interactions.py`, quando detectamos que o elemento é um link, tentamos disparar manualmente um evento click via JavaScript para garantir que seja capturado.

3. **Delay após clique em links**: Adicionamos um delay (0.15s) após clicar em links para dar tempo do evento ser adicionado ao array.

4. **Links sempre são 'click'**: O `action_converter` foi ajustado para sempre tratar links como `click`, nunca como `submit`, mesmo que tenham texto como "Entrar" (do ponto de vista do usuário, links parecem botões, mas são navegação).

### Solução Implementada ✅

**Padrão Correto Implementado**: Comandos CLI programáticos agora adicionam diretamente ao YAML, não dependem do `event_capture`. Isso é o padrão correto porque:
- São ações programáticas, não ações do usuário
- Temos todas as informações necessárias (text, selector, role, index)
- Não há problema de timing com navegação
- É o padrão usado em ferramentas como Selenium IDE, Katalon, etc.

**Separação de Responsabilidades**:
- **Ações programáticas** (CLI commands: `pw-click`, `pw-type`, etc.): Adicionam diretamente ao YAML usando `action_converter`
- **Ações do usuário real** (mouse real, teclado real): Continuam usando `event_capture` para capturar eventos DOM

### Solução Ideal (Futura - se necessário)

Se ainda houver problemas com ações do usuário real em links, podemos considerar:

**Opção 2**: Melhorar o `event_capture` para processar eventos de links imediatamente, sem depender do polling. Por exemplo:
- Interceptar navegação e processar eventos pendentes antes
- Usar `beforeunload` ou similar para garantir processamento
- Processar eventos síncronamente quando detectamos que é um link

### Arquivos Envolvidos

- `playwright_simple/core/playwright_commands/element_interactions.py`: Lógica de clique
- `playwright_simple/core/recorder/event_capture.py`: Captura e processamento de eventos
- `playwright_simple/core/recorder/action_converter.py`: Conversão de eventos em ações YAML
- `playwright_simple/core/recorder/command_handlers/playwright_handlers.py`: Handlers de comandos CLI

### Status

- ✅ **Ações programáticas (CLI)**: Implementado - adicionam diretamente ao YAML
- ❌ **Ações do usuário real em links**: AINDA NÃO FUNCIONA - clique não é capturado
- ⚠️ Solução ideal ainda não implementada
- 📝 Documentado para futura refatoração

### Tentativas de Solução Implementadas (Nenhuma funcionou para usuário real)

1. **Processar eventos pendentes antes da navegação**: Implementado mas não resolve o problema
2. **Marcação de prioridade para links**: Implementado mas não resolve o problema
3. **Redução de delay no polling para links**: Implementado mas não resolve o problema
4. **preventDefault() + setTimeout para navegação**: Implementado mas não resolve o problema
   - O preventDefault() impede a navegação, mas o evento ainda não é processado a tempo
   - O setTimeout de 50ms não é suficiente para garantir processamento

### Problema Atual (Crítico)

**Quando um usuário real clica em um link (`<a href="...">`) com o mouse:**
- O evento é capturado pelo listener JavaScript ✅
- O evento é adicionado ao array `window.__playwright_recording_events` ✅
- Mas a navegação acontece ANTES do polling processar o evento ❌
- Resultado: O clique não aparece no YAML gerado ❌

**Evidência:**
- YAML gerado contém apenas `go_to` inicial
- Logs mostram "Cursor restored after navigation" (navegação aconteceu)
- Mas não há step de `click` no YAML

### Análise do Problema

O problema fundamental é que:
1. O listener JavaScript captura o clique e adiciona ao array
2. Mas o polling Python roda em um loop assíncrono com delay (0.05s - 0.1s)
3. A navegação do navegador acontece IMEDIATAMENTE após o clique
4. Quando o polling tenta processar, o contexto JavaScript já foi destruído pela navegação

**Soluções testadas que NÃO funcionaram:**
- `preventDefault()` + `setTimeout(50ms)`: Ainda não dá tempo suficiente
- Processar eventos pendentes antes da navegação: O evento já foi perdido
- Marcação de prioridade: Não ajuda se o contexto já foi destruído

### Solução Implementada ✅ RESOLVIDO

**Solução Final: Usar `page.expose_function()` para processamento imediato** ✅ IMPLEMENTADO E TESTADO
- Expõe função Python (`__playwright_process_link_click`) para JavaScript chamar diretamente
- Quando JavaScript detecta clique em link, chama função Python IMEDIATAMENTE
- Processa evento ANTES da navegação, sem depender do polling assíncrono
- Bypassa completamente o problema de timing

**Status**: ✅ **RESOLVIDO** - Testado com sucesso. Clique em link "Entrar" foi capturado antes da navegação.

**Logs de confirmação**:
```
🚨 Immediate link click processing triggered from JavaScript
Added click step: Clicar em 'Entrar'
📝 Click: Clicar em 'Entrar'
```

### Outras Opções (Se a atual não funcionar)

**Opção 1: Processamento Síncrono Imediato**
- Quando detectar clique em link, processar o evento IMEDIATAMENTE via `page.evaluate()`
- Não depender do polling assíncrono
- Processar antes de permitir a navegação

**Opção 2: Interceptar Navegação com `page.route()`**
- Usar `page.route()` do Playwright para interceptar requisições de navegação
- Verificar se há eventos pendentes antes de permitir a navegação
- Processar eventos antes de continuar

### Prioridade

🔴 **CRÍTICA** - Bloqueia funcionalidade principal (gravação de cliques do usuário em links)

### Notas

- O problema só ocorre com links que causam navegação imediata
- Botões e outros elementos não têm esse problema
- O `action_converter` já trata links corretamente quando recebe o evento

