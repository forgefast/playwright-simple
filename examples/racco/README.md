# Testes Odoo Racco

Esta pasta contém todos os testes do sistema Racco migrados para a nova estrutura do playwright-simple.

## Estrutura

Todos os testes foram migrados de `presentation/playwright/tests/yaml/` e adaptados para usar:
- Sintaxe moderna do playwright-simple
- Vídeo, áudio e legendas habilitados
- Debugging avançado com hot reload
- Logging estruturado

## Configuração Padrão

Todos os testes incluem:
- **Vídeo**: Habilitado com qualidade alta
- **Áudio/Narração**: Habilitado em pt-BR
- **Legendas**: Habilitadas (soft subtitles)
- **Debug**: Habilitado com pause on error e interactive mode
- **Hot Reload**: Habilitado para iteração rápida
- **Logging**: Nível DEBUG com console output

## Como Executar

### Teste Individual com Debug Completo

```bash
cd /home/gabriel/softhill/playwright-simple
timeout 300 playwright-simple run examples/racco/test_XXX.yaml \
  --log-level DEBUG \
  --debug \
  --interactive \
  --hot-reload \
  --no-headless \
  --video \
  --audio \
  --subtitles \
  --slow-mo 50
```

### Teste Rápido (sem vídeo)

```bash
playwright-simple run examples/racco/test_XXX.yaml \
  --log-level DEBUG \
  --debug \
  --interactive \
  --no-headless \
  --no-video
```

### Teste para Produção (headless)

```bash
playwright-simple run examples/racco/test_XXX.yaml \
  --log-level INFO \
  --headless \
  --video \
  --audio \
  --subtitles
```

## Credenciais

- **URL**: https://odoo.racco.com.br
- **Login Colaborador**: maria.santos@racco.com.br
- **Senha**: demo123
- **Database**: devel

## Lista de Testes

### Testes Básicos
- `test_simple_login.yaml` - Login simples para debug rápido
- `test_colaborador_portal.yaml` - Portal do colaborador completo
- `test_consumer_portal.yaml` - Portal do consumidor
- `test_reseller_portal.yaml` - Portal do revendedor
- `test_intro.yaml` - Introdução ao sistema
- `test_architecture.yaml` - Arquitetura do sistema

### Fluxos de Negócio
- `test_sale_flow.yaml` - Fluxo completo de venda
- `test_product_catalog.yaml` - Catálogo de produtos
- `test_partner_management.yaml` - Gestão de parceiros
- `test_commissions_system.yaml` - Sistema de comissões
- `test_ingress_criteria.yaml` - Critérios de ingresso
- `test_level_escalation.yaml` - Escalonamento de nível
- `test_complete_mlm_flow.yaml` - Fluxo MLM completo
- `test_network.yaml` - Gestão de rede

### Gamificação e Treinamento
- `test_training.yaml` - Jornada de treinamento
- `test_training_certification.yaml` - Certificação em cursos
- `test_gamification.yaml` - Gamificação completa
- `test_badges_achievements.yaml` - Conquista de badges
- `test_challenges_completion.yaml` - Completar desafios
- `test_all_badges.yaml` - Todos os badges
- `test_all_challenges.yaml` - Todos os desafios
- `test_all_courses.yaml` - Todos os cursos

### Revendedores e Níveis
- `test_reseller_prata.yaml` - Revendedor Prata
- `test_reseller_ouro.yaml` - Revendedor Ouro
- `test_reseller_platinum.yaml` - Revendedor Platinum
- `test_diretor_rede.yaml` - Diretor de Rede
- `test_level_comparison.yaml` - Comparação de níveis

### Testes Especiais
- `test_demo_orders.yaml` - Pedidos demo
- `test_cursor_debug.yaml` - Debug de cursor
- `common_login.yaml` - Login comum reutilizável

## Debugging

### Hot Reload

Quando `hot_reload_enabled: true`, o sistema monitora mudanças no YAML e recarrega automaticamente, permitindo iterar rapidamente sem reiniciar o teste.

### Interactive Mode

Quando ocorre um erro com `interactive_mode: true`, o sistema:
1. Pausa a execução
2. Salva o estado atual (HTML, URL, contexto)
3. Abre shell Python interativo com:
   - `page`: Objeto Playwright Page
   - `test`: Instância SimpleTestBase
   - `current_web_state`: WebState capturado
   - `debug_ext`: Instância da extensão de debug

### HTML Snapshots

O sistema salva automaticamente HTML snapshots em `debug_html/` para inspeção.

### Estado JSON

Estados são salvos em `debug_states/` quando ocorrem erros.

## Mapeamento de Ações

### Sintaxe Simplificada (Suportada)
```yaml
- login: email@example.com
  password: senha123
  database: devel
```

### Sintaxe Explícita (Recomendada)
```yaml
- action: login
  login: email@example.com
  password: senha123
  database: devel
```

### Ações Odoo
- `action: login` - Login no Odoo (usa `examples/odoo/login.yaml`)
- `action: navigate_menu` - Navegar por menus (usa `examples/odoo/navigate_menu.yaml`)
- `action: click_button` - Clicar em botão (usa `examples/odoo/click_button.yaml`)
- `action: fill_field` - Preencher campo (usa `examples/odoo/fill_field.yaml`)
- `action: open_record` - Abrir registro (usa `examples/odoo/open_record.yaml`)
- `action: filter_by` - Filtrar (usa `examples/odoo/filter_by.yaml`)

## Problemas Conhecidos

Nenhum problema conhecido no momento. Todos os testes foram migrados e validados.

## Status da Migração

✅ Todos os 30 testes migrados
✅ Todos com vídeo, áudio e legendas
✅ Todos validados e funcionando

