# Débito Técnico

## Captura de Eventos em Links que Causam Navegação

### Problema

Quando clicamos em um link (`<a href="...">`) via comandos CLI programáticos (`pw-click`), o evento de clique pode não ser capturado pelo `event_capture` antes que a navegação aconteça e limpe o contexto da página.

### Contexto

O sistema usa dois mecanismos para capturar ações:

1. **`event_capture`**: Captura eventos DOM nativos através de listeners JavaScript injetados na página. Funciona bem para ações do usuário na tela (cliques reais do mouse).

2. **Comandos CLI programáticos** (`pw-click`, `pw-type`, etc.): Executam ações via Playwright diretamente. Atualmente dependem do `event_capture` para adicionar steps ao YAML.

### Problema Específico

- Quando fazemos `element.click()` em um link via Playwright, o evento DOM é disparado
- O listener JavaScript captura o evento e adiciona ao array `window.__playwright_recording_events`
- Mas a navegação acontece imediatamente, limpando o contexto antes do polling processar o evento
- Resultado: O clique no link não aparece no YAML gerado

### Solução Atual (Temporária)

1. **Processar eventos pendentes antes da navegação**: O `_handle_navigation` em `event_capture.py` agora processa eventos pendentes antes de limpar o array.

2. **Detectar links e processar imediatamente**: Em `element_interactions.py`, quando detectamos que o elemento é um link, tentamos processar eventos imediatamente.

3. **Delay após clique em links**: Adicionamos um pequeno delay (0.05s) após clicar em links para dar tempo do evento ser adicionado ao array.

### Solução Ideal (Futura)

**Opção 1**: Comandos CLI programáticos deveriam adicionar diretamente ao YAML, não depender do `event_capture`. Isso faz sentido porque:
- São ações programáticas, não ações do usuário
- Temos todas as informações necessárias (text, selector, role, index)
- Não há problema de timing com navegação

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

- ✅ Solução temporária implementada (processar eventos pendentes antes da navegação)
- ⚠️ Solução ideal ainda não implementada
- 📝 Documentado para futura refatoração

### Notas

- O problema só ocorre com links que causam navegação imediata
- Botões e outros elementos não têm esse problema
- O `action_converter` já trata links corretamente quando recebe o evento

