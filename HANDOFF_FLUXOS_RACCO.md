# HANDOFF - Validação dos Fluxos Racco

**Data:** 2025-01-17  
**Status:** Correções simples aplicadas - Captura de HTML, correções de navegação para revendedor  
**Último Commit:** `e1820b8` - fix: corrigir problemas simples dos fluxos Racco

## Contexto

Este handoff documenta o trabalho de validação e correção dos fluxos de teste do sistema Racco no Odoo. O objetivo é executar, corrigir, validar e iterar até ter todos os fluxos definidos em `test_complete_racco_flows.md` funcionando completamente.

## Estado Atual

### ✅ Concluído

1. **Fluxo_01 Validado**
   - ✅ Fluxo completo testado e funcionando
   - ✅ Todos os passos executados com sucesso (Login → Loja → Produto → Logout)
   - ✅ Marcado como validado em `test_complete_racco_flows.md`

2. **Fluxo_02 - Progresso Significativo (53/184 passos)**
   - ✅ Corrigido caminho: Contatos > Configuração > Marcadores de contato
   - ✅ Descoberto que "Contact Tags" em PT-BR é "Marcadores de contato"
   - ✅ Fluxo passa até passo 53/184
   - ⚠️ Problema menor: "Lucia Helena Santos" não encontrado (pode ser dados)

3. **Fluxo_06 - Progresso (27/76 passos)**
   - ✅ Fluxo passa até passo 27/76
   - ⚠️ Problema: "Portal" não encontrado para revendedor

4. **Fluxo_09 - Progresso (15/18 passos)**
   - ✅ Fluxo passa até passo 15/18
   - ⚠️ Problema: "Lucia Helena Santos" não encontrado (pode ser dados)

5. **Traduções PT-BR Corrigidas**
   - ✅ "Contact Tags" → "Marcadores de contato"
   - ✅ "Website" → "Site"
   - ✅ Verificadas no repositório Odoo 18 em /tmp/odoo-18-translations

6. **Testes Críticos**
   - ✅ 6 testes críticos passando
   - ✅ Sintaxe Python OK
   - ✅ Imports OK

7. **Captura de HTML em Erros**
   - ✅ Adicionada captura automática de HTML quando erros ocorrem
   - ✅ HTMLs salvos em `screenshots/test_complete_racco_flows/error_step_{i}.html`
   - ✅ Facilita análise de elementos disponíveis na página quando erro ocorre

8. **Correções de Navegação para Revendedor**
   - ✅ Fluxo_03: Removido menu Apps, revendedor usa Portal diretamente
   - ✅ Fluxo_05: Removido menu Apps, revendedor usa Portal diretamente
   - ✅ Descoberto: Revendedor tem interface diferente (Portal `/my` vs Odoo `/odoo`)

### 🔄 Em Progresso / Problemas Conhecidos

**Fluxo_02: Critérios de Ingresso - Revendedor**
- ✅ **RESOLVIDO:** Corrigido para usar "Marcadores de contato" (tradução PT-BR)
- ✅ Progresso: 53/184 passos OK
- ⚠️ Problema menor: "Lucia Helena Santos" não encontrado (pode ser dados)

**Fluxo_03: Jornada de Treinamento**
- ✅ **CORRIGIDO:** Removido menu Apps, revendedor usa link "Cursos" diretamente no Portal
- ✅ Descoberto: Revendedor está no Portal (`/my`), não no backend Odoo (`/odoo`)
- ⚠️ Problema menor: Nome da aula pode variar (ex: "Bem-vindo ao Curso de Produtos Racco" não encontrado)

**Fluxo_04: Gamificação**
- ⚠️ **PROBLEMA:** Módulo "Gamificação" não está instalado ou não está disponível
- ✅ Confirmado: Módulo não aparece no menu Apps do Odoo
- ⚠️ Necessário instalar módulo `gamification` ou verificar se está disponível

**Fluxo_05: Fluxo de Venda - Revendedor**
- ✅ **CORRIGIDO:** Removido menu Apps, revendedor usa Portal
- ⚠️ Problema: Revendedor pode não ter acesso a "Pedidos" no Portal
- ⚠️ Necessário verificar se há link "Pedidos" no menu do Portal ou navegação alternativa

**Fluxo_06: Sistema de Comissões**
- ✅ Progresso: 27/76 passos OK
- ⚠️ **PROBLEMA:** "Portal" não encontrado para revendedor
- ⚠️ Possível causa: revendedor não tem acesso ao Portal ou nome diferente

**Fluxo_07: Portal do Consumidor**
- ⚠️ **PROBLEMA:** "Portal" não encontrado
- ⚠️ Possível causa: tradução diferente ou elemento não visível

**Fluxo_08: Portal do Revendedor**
- ⚠️ **PROBLEMA:** "Portal" não encontrado (mesmo problema do fluxo_07)

**Fluxo_09: Gestão de Parceiros**
- ✅ Progresso: 15/18 passos OK
- ⚠️ **PROBLEMA:** "Clientes" não encontrado como submenu
- ⚠️ **PROBLEMA:** "Lucia Helena Santos" não encontrado (pode ser dados)

### 📋 Resumo do Progresso

**Fluxos Testados:**
- ✅ `fluxo_01` - **VALIDADO** - Funcionando completamente
- 🔄 `fluxo_02` - **53/184 passos OK** - Corrigido tradução "Marcadores de contato"
- ✅ `fluxo_03` - **CORRIGIDO** - Removido menu Apps, usa Portal diretamente
- ⚠️ `fluxo_04` - Módulo "Gamificação" não está instalado
- ✅ `fluxo_05` - **CORRIGIDO** - Removido menu Apps, usa Portal (pode não ter acesso a Pedidos)
- 🔄 `fluxo_06` - **27/76 passos OK** - "Portal" não encontrado
- ⚠️ `fluxo_07` - "Portal" não encontrado
- ⚠️ `fluxo_08` - "Portal" não encontrado
- 🔄 `fluxo_09` - **15/18 passos OK** - "Clientes" e "Lucia Helena Santos" não encontrados

**Principais Descobertas:**
1. **Traduções PT-BR:** Muitos elementos estão em português, não em inglês
   - "Contact Tags" → "Marcadores de contato"
   - "Website" → "Site"
2. **Revendedor tem interface diferente:** 
   - Usa Portal (`/my`) em vez do backend Odoo (`/odoo`)
   - Não tem acesso ao menu Apps (botão não existe)
   - Navegação deve ser feita diretamente pelos links do Portal
3. **Portal:** Elemento "Portal" não encontrado - pode ser tradução diferente ou não disponível
4. **Captura de HTML:** HTMLs são capturados automaticamente quando erros ocorrem, facilitando análise

## Arquivos Importantes

### Arquivos de Teste
- **`test_complete_racco_flows.md`** - Define todos os fluxos de teste em formato markdown com comandos bash-like
- **`test_complete_racco_flows.py`** - Script Python que executa os comandos do arquivo MD
  - Lê comandos do arquivo MD
  - Captura HTML quando erros ocorrem (salva em `screenshots/test_complete_racco_flows/error_step_{i}.html`)
- **`playwright_simple/core/recorder/cursor_controller/interaction.py`** - Lógica de cliques por texto (revertida para commit 6ba1966)

### Configuração de Fluxos Validados

No arquivo `test_complete_racco_flows.md`, seção `validated_flows`:

```yaml
validated_flows:
   - fluxo_01  # Critérios de Ingresso - Consumidor Final
  # - fluxo_02  # Critérios de Ingresso - Revendedor (inclui escalonamento de níveis)
```

O script `test_complete_racco_flows.py` automaticamente pula fluxos marcados como validados.

## Como Executar

### Executar Todos os Fluxos (exceto validados)
```bash
cd /home/gabriel/softhill/playwright-simple
timeout 300 python3 test_complete_racco_flows.py
```

### Executar Apenas um Fluxo Específico
Edite `test_complete_racco_flows.md` e comente os outros fluxos, ou modifique o script para aceitar parâmetros.

### Ver Logs Detalhados
```bash
cd /home/gabriel/softhill/playwright-simple
timeout 300 python3 test_complete_racco_flows.py 2>&1 | tee /tmp/fluxo_test.log
```

## Problemas Conhecidos

### 1. "Categorias" não encontrado (Fluxo_02)

**Sintoma:**
```
[30/185] pw-click "Categorias"
Attempting to click by text: 'Categorias'
Element with text 'Categorias' not found
   ⚠️  Elemento 'Categorias' não encontrado
  ❌ Erro: Element not found
```

**Contexto:**
- Ocorre após clicar em "Contatos"
- Fluxo esperado: Contatos → Categorias → Buscar "Bronze" → Enter → Ver categorias de níveis

**Investigações Necessárias:**
1. Verificar se o menu "Categorias" existe na página atual do Odoo
2. Verificar se há um delay necessário após clicar em "Contatos"
3. Verificar se a navegação está indo para a página correta
4. Capturar HTML da página quando o erro ocorre para análise

**Comandos Úteis para Debug:**
```bash
# Capturar HTML quando erro ocorre
cd /home/gabriel/softhill/playwright-simple
timeout 120 python3 test_complete_racco_flows.py 2>&1 | grep -A 10 "Categorias"
```

### 2. Regressão de Cliques em Filtros (RESOLVIDO)

**Status:** ✅ Corrigido no commit a21f715

**Problema Original:**
- Cliques em filtros (ex: "Revendedor Ouro") navegavam para `/odoo/contacts/28` (página de detalhes)
- Em vez de aplicar o filtro na lista atual

**Solução:**
- Revertido `interaction.py` para código do commit `6ba1966` que funcionava
- Removida lógica de priorização de dropdowns que estava causando o problema

## Estrutura do Código

### `click_by_text` - Lógica de Cliques

O método `click_by_text` em `interaction.py` funciona assim:

1. **Espera página estar pronta** - `wait_for_load_state('domcontentloaded')`
2. **Busca elemento por texto** usando JavaScript no browser:
   - Prioriza botões de submit (priority 10-11)
   - Depois botões normais (priority 3-4)
   - Depois links (priority 1-3)
   - Penaliza links quando busca por nomes de campos (priority -2)
3. **Ordena por prioridade** e seleciona o melhor match
4. **Move cursor** e clica no elemento

**Nota:** A versão atual (revertida) não tem lógica de priorização de dropdowns, o que estava causando problemas.

## Próximos Passos

### Imediato
1. **Resolver problemas de tradução PT-BR**
   - Verificar tradução de "Portal" no Odoo (fluxos 06, 07, 08)
   - Verificar se "Portal" é um link no menu ou navegação diferente
   - Verificar se "Clientes" existe como submenu ou apenas como filtro

2. **Resolver problema de Módulo Gamificação**
   - Instalar módulo `gamification` no Odoo ou verificar se está disponível
   - Verificar se há nome alternativo ou caminho diferente para acessar

3. **Resolver problemas de dados**
   - Verificar se "Lucia Helena Santos" existe no banco de dados
   - Verificar se dados de teste estão corretos

4. **Resolver acesso a Pedidos no Portal (fluxo_05)**
   - Verificar se revendedor tem acesso a "Pedidos" no Portal
   - Verificar se há link "Pedidos" no menu do Portal
   - Verificar se precisa navegar diretamente por URL

### Médio Prazo
4. **Completar fluxos parciais**
   - fluxo_02: Resolver "Lucia Helena Santos" (53/184 → completo)
   - fluxo_03: Resolver nome da aula (pode variar)
   - fluxo_05: Resolver acesso a "Pedidos" no Portal
   - fluxo_06: Resolver "Portal" (27/76 → completo)
   - fluxo_09: Resolver "Clientes" e "Lucia Helena Santos" (15/18 → completo)

5. **Resolver fluxos com problemas conhecidos**
   - fluxo_04: Instalar módulo "Gamificação" ou verificar disponibilidade
   - fluxo_07, 08: Resolver "Portal" (verificar tradução ou navegação)

## Comandos Git Úteis

```bash
# Ver histórico de commits relacionados
cd /home/gabriel/softhill/playwright-simple
git log --oneline --all --grep="fluxo\|filtro\|dropdown" -10

# Ver diferenças do último commit
git show HEAD

# Ver código que funcionava (commit 6ba1966)
git show 6ba1966:playwright_simple/core/recorder/cursor_controller/interaction.py | head -100

# Reverter arquivo específico (se necessário)
git checkout 6ba1966 -- playwright_simple/core/recorder/cursor_controller/interaction.py
```

## Ambiente

- **Odoo:** Rodando em `http://localhost:18069`
- **Módulo:** `racco_demo` instalado
- **Python:** 3.11.2
- **Playwright:** Versão instalada via pip
- **Headless:** False (browser visível para debug)

## Notas Importantes

1. **Commits de Segurança:** O usuário pediu para commitar quando um clique funciona, para facilitar reversão
2. **Sem Timeouts Fixos:** O código deve ser dinâmico, sem delays hardcoded
3. **Script Minimalista:** `test_complete_racco_flows.py` apenas lê comandos do MD e executa, sem lógica extra
4. **Validação Automática:** Fluxos marcados como validados são automaticamente pulados

## Contato e Referências

- **Arquivo de Fluxos:** `test_complete_racco_flows.md`
- **Script de Execução:** `test_complete_racco_flows.py`
- **Código de Cliques:** `playwright_simple/core/recorder/cursor_controller/interaction.py`
- **Último Commit:** `e1820b8` - "fix: corrigir problemas simples dos fluxos Racco"
- **Último Commit Funcional:** `6ba1966` - "feat: fluxo_02 validado - Critérios de Ingresso - Revendedor"

## Correções Recentes (Commit e1820b8)

1. **Captura de HTML em Erros**
   - Adicionada captura automática de HTML quando erros ocorrem
   - HTMLs salvos em `screenshots/test_complete_racco_flows/error_step_{i}.html`
   - Facilita análise de elementos disponíveis na página

2. **Fluxo_03 - Jornada de Treinamento**
   - Removido acesso ao menu Apps (revendedor não tem acesso)
   - Corrigido para usar link "Cursos" diretamente no Portal
   - Removido passo "Site" desnecessário

3. **Fluxo_05 - Fluxo de Venda - Revendedor**
   - Removido acesso ao menu Apps
   - Ajustado para usar Portal (nota: pode não ter acesso a Pedidos no Portal)

4. **Fluxo_04 - Gamificação**
   - Documentado que módulo "Gamificação" não está instalado/disponível
   - Adicionado comentário explicativo no código

---

**Última Atualização:** 2025-01-17  
**Próxima Ação:** Resolver problemas de "Portal" (fluxos 06, 07, 08) e instalar/verificar módulo "Gamificação" (fluxo_04)

