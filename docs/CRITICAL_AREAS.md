# Áreas Críticas do Projeto - Playwright Simple

Este documento lista áreas críticas que não devem ser alteradas sem cuidado especial.

## Arquivos Críticos

### Sistema de Gravação (Recorder)
- `playwright_simple/core/recorder/event_capture.py`: Captura de eventos do DOM
- `playwright_simple/core/recorder/action_converter.py`: Conversão de eventos para ações YAML
- `playwright_simple/core/recorder/event_handlers.py`: Handlers de eventos
- **⚠️ ALERTA**: Alterações aqui podem quebrar a geração de YAML

### Sistema de Reprodução (Runner)
- `playwright_simple/core/yaml_actions.py`: Execução de ações YAML
- `playwright_simple/core/runner/test_executor.py`: Executor de testes
- **⚠️ ALERTA**: Alterações aqui podem quebrar a reprodução de YAML

### Interações com Elementos (Core)
- `playwright_simple/core/playwright_commands/element_interactions/`: Toda a pasta
  - `element_finder.py`: Busca de elementos
  - `click_handler.py`: Lógica de cliques
  - `type_handler.py`: Lógica de digitação
  - `submit_handler.py`: Lógica de submissão
- **⚠️ ALERTA**: Alterações aqui podem quebrar todas as interações

### Sistema de Cursor
- `playwright_simple/core/cursor_elements.py`: Criação de elementos de cursor
- `playwright_simple/core/cursor_movement.py`: Movimento do cursor
- `playwright_simple/core/runner/test_executor.py`: Restauração de estado do cursor
- **⚠️ ALERTA**: Alterações aqui podem quebrar feedback visual

## Padrões que Devem ser Mantidos

### Formato YAML
- **NUNCA** alterar o formato YAML sem aprovação explícita
- Usuários criam YAMLs manualmente - formato deve ser simples e legível
- Padrão atual: `action: type`, `text: "value"`, `into: "label"` (sem complexidade)
- **Regra**: Se você não está vendo problemas nos logs, os logs não são bons o suficiente

### Fluxo de Interação
- **SEMPRE** clicar antes de digitar em campos
- **SEMPRE** manter sincronização entre cursor visual e mouse do Playwright
- **SEMPRE** preservar estado do cursor após navegação

### Logging
- **SEMPRE** usar FrameworkLogger para logs padronizados
- **SEMPRE** logar movimentos de mouse, cliques e typing em modo debug
- **SEMPRE** verificar logs antes de tentar mudar coisas

## Dependências Entre Módulos

### Recorder → YAML
- `event_capture.py` → `action_converter.py` → `yaml_writer`
- Eventos do DOM são convertidos em ações YAML

### YAML → Runner
- `yaml_actions.py` → `element_interactions/` → `playwright_commands`
- Ações YAML são executadas usando element_interactions

### Cursor → Visual Feedback
- `cursor_elements.py` → `cursor_movement.py` → `test_executor.py`
- Cursor visual deve estar sincronizado com mouse do Playwright

### Element Interactions → Commands
- `element_interactions/` → `playwright_commands/commands.py`
- Todas as interações passam por PlaywrightCommands

## Anti-patterns Conhecidos

### ❌ NÃO Faça
- Alterar formato YAML sem aprovação
- Fazer await em ElementHandle diretamente (já é ElementHandle)
- Alterar código sem executar testes críticos primeiro
- Ignorar logs de debug quando há problemas
- Fazer mudanças complexas sem usar plan mode
- Alterar padrões estabelecidos sem necessidade

### ✅ Faça
- Sempre executar testes críticos antes de mudar
- Sempre testar ciclo completo após mudanças em recorder
- Sempre verificar logs antes de tentar mudar coisas
- Sempre usar plan mode para mudanças complexas
- Sempre documentar áreas críticas quando descobrir
- Sempre manter sincronização cursor/mouse

## Checklist Antes de Alterar Áreas Críticas

Antes de alterar qualquer arquivo crítico:

- [ ] Executei testes críticos e todos passaram
- [ ] Entendo completamente o código e suas dependências
- [ ] Identifiquei todos os módulos que dependem deste
- [ ] Criei testes para validar minha mudança
- [ ] Testei localmente com casos reais
- [ ] Se altero recorder: testei ciclo completo (geração + reprodução)
- [ ] Se altero yaml_actions: testei reprodução de YAML existente
- [ ] Se altero element_interactions: testei todos os tipos de interação
- [ ] Verifiquei logs de debug para entender o comportamento atual

