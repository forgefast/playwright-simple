# Handoff - Problema de Navegação no Odoo

**Data**: 2025-11-13  
**Status**: 🔴 PROBLEMA ATIVO - Navegação para Dashboard não funciona

---

## 🎯 CONTEXTO

Após login no Odoo, o sistema redireciona automaticamente para `/discuss` (Mensagens). Para acessar o Dashboard (menu de apps), é necessário:
1. Clicar no ícone do menu de apps (canto superior esquerdo) - `button.o_grid_apps_menu__button`
2. Fechar o menu (pressionar Escape ou clicar novamente) para voltar ao Dashboard

O problema é que `go_to: "Dashboard"` não consegue fazer essa navegação automaticamente.

---

## 🔍 PROBLEMA ATUAL

### Sintoma
- `go_to: "Dashboard"` falha quando está em `/discuss`
- `menu.go_to_dashboard()` clica no botão, mas apenas abre/fecha o menu, não navega para Dashboard
- Teste `test_colaborador_portal` falha no passo 2 (navegação para Dashboard)

### Código Problemático
**Arquivo**: `playwright-simple/playwright_simple/odoo/menus.py` - método `go_to_dashboard()`

O método tenta:
1. Clicar no botão do menu de apps
2. Verificar se menu abriu
3. Fechar menu
4. Verificar se está no Dashboard

Mas não funciona porque:
- Clicar no botão quando está em `/discuss` apenas abre o menu
- Fechar o menu não navega para Dashboard, apenas fecha o menu
- Ainda permanece em `/discuss`

---

## ✅ O QUE JÁ FUNCIONA

1. **Máquina de estados**: `go_to` verifica se já está no destino antes de tentar navegar
2. **Detecção de Dashboard**: `_is_on_dashboard()` detecta Dashboard mesmo quando URL ainda é `/discuss` (se menu fechado e sem conteúdo de discuss)
3. **Suporte a seletores CSS**: `click` no YAML aceita seletores CSS (mas usuário não quer isso)
4. **Suporte a `press`**: YAML aceita `press: "Escape"` para pressionar teclas

---

## 🔧 SOLUÇÃO NECESSÁRIA

### Opção 1: Corrigir `go_to_dashboard()` para funcionar de `/discuss`
- Quando em `/discuss`, clicar no botão do menu
- Pressionar Escape (ou clicar fora) para fechar menu
- Verificar se chegou ao Dashboard
- Se não chegou, tentar outra abordagem

### Opção 2: Usar navegação direta para `/web` (mas com cursor)
- Encontrar elemento clicável que leve a `/web`
- Clicar nele com cursor visual
- Verificar se chegou ao Dashboard

### Opção 3: Melhorar detecção de Dashboard
- Se menu está fechado e não há conteúdo de discuss visível, considerar como Dashboard
- Ajustar `_is_on_dashboard()` para ser mais permissivo

---

## 📝 ARQUIVOS PARA REVISAR

1. **`playwright-simple/playwright_simple/odoo/menus.py`**
   - Método `go_to_dashboard()` (linha ~600)
   - Precisa funcionar quando está em `/discuss`

2. **`playwright-simple/playwright_simple/odoo/specific/logo.py`**
   - Método `_is_on_dashboard()` (linha ~33)
   - Já tem lógica para detectar Dashboard quando menu fechado

3. **`playwright-simple/playwright_simple/odoo/base.py`**
   - Método `go_to()` (linha ~360)
   - Chama `menu.go_to_dashboard()` para Dashboard

4. **`presentation/playwright/tests/yaml/test_colaborador_portal.yaml`**
   - Linha 22: `go_to: "Dashboard"` - precisa funcionar
   - Linhas 32, 37: Ainda tem seletores CSS - precisa converter para abstrações

---

## 🧪 TESTE PARA VALIDAÇÃO

```bash
cd /home/gabriel/softhill/presentation/playwright
timeout 300 python3 run_test.py test_colaborador_portal
```

**Esperado**:
- ✅ Passo 1 (login) funciona
- ✅ Passo 2 (`go_to: "Dashboard"`) navega corretamente de `/discuss` para Dashboard
- ✅ Passo 3 (screenshot) captura Dashboard
- ✅ Passos seguintes funcionam

---

## 💡 DICAS

1. **HTML de erro salvo**: Quando há erro, HTML é salvo em `screenshots/{test_name}/debug_error_step_{N}.html`
2. **Verificar HTML**: Abrir HTML salvo para ver estrutura da página e entender o que clicar
3. **Cursor é protagonista**: Toda navegação deve ser via cursor visual, sem `page.goto()` direto
4. **Abstrações amigáveis**: Usuário não deve precisar usar seletores CSS - manter `go_to: "Dashboard"`, `go_to: "Contatos"`, etc.

---

## 🚫 O QUE NÃO FAZER

- ❌ Não exigir seletores CSS no YAML
- ❌ Não usar `page.goto()` direto (sem cursor)
- ❌ Não remover abstrações amigáveis
- ❌ Não simplificar demais (usuário rejeitou isso)

---

## 📚 REFERÊNCIAS

- Arquivo de handoff principal: `playwright-simple/HANDOFF_NOTE.md`
- Teste problemático: `presentation/playwright/tests/yaml/test_colaborador_portal.yaml`
- HTML de erro: `presentation/playwright/screenshots/test_colaborador_portal/debug_error_step_2.html`

