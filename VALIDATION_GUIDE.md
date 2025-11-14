# Guia de Validação - Playwright Simple

Este guia ajuda você a testar e validar todas as funcionalidades implementadas, enquanto continuamos desenvolvendo.

---

## 🎯 Objetivo

Validar o que já está funcionando e identificar:
- ✅ O que funciona bem
- ⚠️ O que precisa melhorar
- 🐛 Problemas encontrados
- 💡 Ideias para melhorias

---

## 📋 Checklist de Validação

### 1. Gravação de Interações (RECORDER)

#### Teste Básico
```bash
# Teste 1: Gravação simples
playwright-simple record teste_gravacao.yaml --url https://example.com

# Durante a gravação:
# - Clique em alguns elementos
# - Digite em campos
# - Navegue entre páginas
# - Digite "exit" no console

# Verificar:
# [ ] Arquivo teste_gravacao.yaml foi criado
# [ ] YAML contém os passos corretos
# [ ] Descrições estão claras
```

#### Teste com Comandos
```bash
# Teste 2: Comandos durante gravação
playwright-simple record teste_comandos.yaml --url https://example.com

# Durante a gravação, teste:
# - caption "Esta é uma legenda"
# - audio "Esta é uma narração"
# - screenshot
# - pause
# - resume
# - save
# - exit

# Verificar:
# [ ] Comandos funcionam sem erros
# [ ] Legendas aparecem no YAML
# [ ] Áudio aparece no YAML
# [ ] Screenshots foram salvos
```

#### Teste Odoo
```bash
# Teste 3: Gravar interações no Odoo
playwright-simple record teste_odoo_gravacao.yaml --url http://localhost:8069

# Durante a gravação:
# - Faça login
# - Navegue pelo menu
# - Preencha um formulário
# - Salve um registro

# Verificar:
# [ ] YAML gerado usa ações Odoo quando apropriado
# [ ] Navegação por menu está correta
# [ ] Preenchimento de campos está correto
```

---

### 2. Execução de Testes YAML

#### Teste Básico
```bash
# Teste 4: Executar teste simples
playwright-simple run examples/basic_yaml.yaml

# Verificar:
# [ ] Teste executa sem erros
# [ ] Browser abre (ou executa em headless)
# [ ] Ações são executadas corretamente
# [ ] Resultado é exibido no console
```

#### Teste com Vídeo
```bash
# Teste 5: Executar com vídeo
playwright-simple run examples/basic_yaml.yaml --video

# Verificar:
# [ ] Vídeo é gerado em videos/
# [ ] Vídeo tem qualidade adequada
# [ ] Vídeo mostra todas as ações
# [ ] Vídeo tem duração correta
```

#### Teste com Legendas
```bash
# Teste 6: Executar com legendas
playwright-simple run examples/basic_yaml.yaml --video --subtitles

# Verificar:
# [ ] Legendas aparecem no vídeo
# [ ] Legendas estão sincronizadas
# [ ] Legendas são legíveis
```

#### Teste com Áudio
```bash
# Teste 7: Executar com áudio
playwright-simple run examples/basic_yaml.yaml --video --subtitles --audio

# Verificar:
# [ ] Áudio é gerado
# [ ] Áudio está sincronizado com ações
# [ ] Narração é clara
```

---

### 3. Auto-Fix Inteligente

#### Teste de Correção Automática
```bash
# Teste 8: Criar teste com erro proposital
# Crie teste_erro.yaml:
cat > teste_erro.yaml << 'EOF'
name: Teste com Erro
steps:
  - action: go_to
    url: http://localhost:8069
  - action: click
    text: "Botão Que Não Existe"  # Este botão não existe
EOF

# Executar e verificar auto-fix
playwright-simple run teste_erro.yaml --debug

# Verificar:
# [ ] Auto-fix detecta o erro
# [ ] Auto-fix sugere correção
# [ ] Auto-fix aplica correção (se possível)
# [ ] Teste tenta novamente
```

#### Teste com Contexto
```bash
# Teste 9: Auto-fix com contexto HTML
# Crie teste_contexto.yaml com elemento similar:
cat > teste_contexto.yaml << 'EOF'
name: Teste Contexto
steps:
  - action: go_to
    url: http://localhost:8069
  - action: click
    text: "Entrar"  # Se não existir, mas existir "Login"
EOF

# Executar
playwright-simple run teste_contexto.yaml --debug

# Verificar:
# [ ] Auto-fix analisa HTML disponível
# [ ] Auto-fix encontra elemento similar
# [ ] Auto-fix sugere correção baseada em contexto
```

---

### 4. Comparação Visual

#### Teste de Comparação
```python
# Teste 10: Comparação de screenshots
# Crie test_visual.py:
cat > test_visual.py << 'EOF'
from playwright_simple.core.visual_comparison import VisualComparison
from pathlib import Path

comparison = VisualComparison(
    baseline_dir=Path("screenshots/baseline"),
    current_dir=Path("screenshots/current"),
    diff_dir=Path("screenshots/diffs")
)

# Criar diretórios
comparison.baseline_dir.mkdir(parents=True, exist_ok=True)
comparison.current_dir.mkdir(parents=True, exist_ok=True)
comparison.diff_dir.mkdir(parents=True, exist_ok=True)

# Testar comparação
result = comparison.compare_screenshot("test.png", threshold=0.01)
print(f"Match: {result['match']}")
EOF

python3 test_visual.py

# Verificar:
# [ ] Comparação funciona
# [ ] Diferenças são detectadas
# [ ] Diff images são geradas
```

---

### 5. Extensão Odoo

#### Teste de Login Odoo
```bash
# Teste 11: Login no Odoo
cat > teste_odoo_login.yaml << 'EOF'
name: Login Odoo
steps:
  - action: login
    login: admin
    password: admin
    database: devel
EOF

playwright-simple run teste_odoo_login.yaml --video

# Verificar:
# [ ] Login funciona
# [ ] Usuário é autenticado
# [ ] Dashboard aparece
```

#### Teste de Navegação Odoo
```bash
# Teste 12: Navegação por menu
cat > teste_odoo_nav.yaml << 'EOF'
name: Navegação Odoo
steps:
  - action: login
    login: admin
    password: admin
  - action: go_to
    go_to: "Vendas > Pedidos"
EOF

playwright-simple run teste_odoo_nav.yaml --video

# Verificar:
# [ ] Navegação funciona
# [ ] Menu é encontrado
# [ ] Página correta é aberta
```

#### Teste de Preenchimento Odoo
```bash
# Teste 13: Preencher campos Odoo
cat > teste_odoo_fill.yaml << 'EOF'
name: Preencher Odoo
steps:
  - action: login
    login: admin
    password: admin
  - action: go_to
    go_to: "Vendas > Pedidos"
  - action: click
    click: "Criar"
  - action: fill
    fill: "Cliente = João Silva"
EOF

playwright-simple run teste_odoo_fill.yaml --video

# Verificar:
# [ ] Campo é encontrado pelo label
# [ ] Valor é preenchido corretamente
# [ ] Campo aceita o valor
```

---

### 6. YAML Avançado

#### Teste de Variáveis
```bash
# Teste 14: Variáveis no YAML
cat > teste_variaveis.yaml << 'EOF'
name: Teste Variáveis
variables:
  email: admin@example.com
  password: senha123
steps:
  - action: go_to
    url: http://localhost:8069
  - action: type
    text: "{{ email }}"
    selector: input[name="login"]
  - action: type
    text: "{{ password }}"
    selector: input[name="password"]
EOF

playwright-simple run teste_variaveis.yaml

# Verificar:
# [ ] Variáveis são substituídas
# [ ] Valores corretos são usados
```

#### Teste de Loops
```bash
# Teste 15: Loops no YAML
cat > teste_loops.yaml << 'EOF'
name: Teste Loops
steps:
  - for:
      var: user
      in: ["admin", "user"]
    steps:
      - action: go_to
        url: /login
      - action: type
        text: "{{ user }}"
        selector: input[name="username"]
EOF

playwright-simple run teste_loops.yaml

# Verificar:
# [ ] Loop executa para cada item
# [ ] Variável é substituída corretamente
```

---

## 📊 Template de Relatório de Validação

Use este template para reportar seus testes:

```markdown
# Relatório de Validação - [Data]

## Funcionalidades Testadas

### 1. Gravação de Interações
- [ ] Teste básico: ✅/❌
- [ ] Comandos: ✅/❌
- [ ] Odoo: ✅/❌

**Observações:**
- O que funcionou bem:
- O que precisa melhorar:
- Problemas encontrados:

### 2. Execução de Testes
- [ ] Teste básico: ✅/❌
- [ ] Com vídeo: ✅/❌
- [ ] Com legendas: ✅/❌
- [ ] Com áudio: ✅/❌

**Observações:**
- O que funcionou bem:
- O que precisa melhorar:
- Problemas encontrados:

### 3. Auto-Fix
- [ ] Detecção de erro: ✅/❌
- [ ] Sugestão de correção: ✅/❌
- [ ] Aplicação automática: ✅/❌

**Observações:**
- O que funcionou bem:
- O que precisa melhorar:
- Problemas encontrados:

### 4. Extensão Odoo
- [ ] Login: ✅/❌
- [ ] Navegação: ✅/❌
- [ ] Preenchimento: ✅/❌

**Observações:**
- O que funcionou bem:
- O que precisa melhorar:
- Problemas encontrados:

## Ideias e Sugestões

### Melhorias Prioritárias
1. 
2. 
3. 

### Novas Funcionalidades
1. 
2. 
3. 

### Problemas Críticos
1. 
2. 
3. 
```

---

## 🎯 Prioridades de Teste

### Alta Prioridade (Testar Primeiro)
1. ✅ Gravação básica
2. ✅ Execução básica
3. ✅ Login Odoo
4. ✅ Navegação Odoo

### Média Prioridade
1. ⚠️ Vídeo e legendas
2. ⚠️ Auto-fix
3. ⚠️ Preenchimento Odoo

### Baixa Prioridade (Opcional)
1. 📝 Comparação visual
2. 📝 YAML avançado (loops, variáveis)
3. 📝 Hot reload

---

## 💡 Dicas para Validação

1. **Comece simples**: Teste funcionalidades básicas primeiro
2. **Documente problemas**: Anote exatamente o que aconteceu
3. **Capture evidências**: Screenshots, logs, vídeos
4. **Teste casos reais**: Use cenários do seu dia a dia
5. **Compare com expectativa**: O que você esperava vs o que aconteceu

---

## 🐛 Como Reportar Problemas

### Informações Essenciais
1. **O que você estava fazendo**: Passo a passo
2. **O que aconteceu**: Erro, comportamento inesperado
3. **O que você esperava**: Comportamento esperado
4. **Arquivos relevantes**: YAML, logs, screenshots

### Exemplo de Report
```markdown
**Problema**: Gravação não captura cliques em botões Odoo

**Passos para reproduzir**:
1. playwright-simple record teste.yaml --url http://localhost:8069
2. Clicar em botão "Criar" no Odoo
3. Digitar "exit"

**O que aconteceu**:
- YAML gerado não contém o clique no botão
- Apenas navegação foi capturada

**O que esperava**:
- YAML deveria conter: `- action: click, click: "Criar"`

**Arquivos**:
- teste.yaml (anexado)
- Logs: [se disponível]
```

---

## ✅ Checklist Final

Antes de considerar validação completa:

- [ ] Todas as funcionalidades básicas testadas
- [ ] Problemas documentados
- [ ] Sugestões anotadas
- [ ] Relatório de validação preenchido
- [ ] Feedback compartilhado

---

**Última Atualização**: Novembro 2024

