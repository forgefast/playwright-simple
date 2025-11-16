# Fluxo 03: Escalonamento de Níveis

## Descrição
Demonstra o sistema de escalonamento de níveis de revendedor, mostrando os critérios e revendedores em cada nível (Bronze, Prata, Ouro, Platinum).

## Pré-requisitos
- Usuário admin: `admin` (senha: `admin`)
- Dados demo: 15 revendedores distribuídos em 4 níveis
- Módulo `racco_demo` instalado

## Menu de Acesso
- Categorias: **Contatos > Categorias**
- Clientes: **Contatos > Clientes**

## Passos Detalhados

### 1. Login como Administrador
**Descrição**: Fazer login como admin

**Comandos playwright-simple**:
```bash
pw-click "Entrar"
subtitle "Acessando a tela de login"
audio-step "Acessando a tela de login"
wait 1.0

pw-type "admin" into "E-mail"
pw-type "admin" into "Senha"
pw-submit "Entrar"
subtitle "Login realizado com sucesso"
audio-step "Login realizado com sucesso"
wait 2.0
```

### 2. Acessar Categorias de Níveis
**Descrição**: Ver as categorias que representam os níveis

**Comandos playwright-simple**:
```bash
pw-click "Contatos"
wait 1.0
pw-click "Categorias"
subtitle "Acessando categorias de níveis"
audio-step "Aqui estão as categorias que representam os níveis de revendedor no sistema"
wait 2.0
```

### 3. Visualizar Nível Bronze
**Descrição**: Mostrar categoria Bronze e seus critérios

**Comandos playwright-simple**:
```bash
pw-type "Bronze" into "Buscar"
subtitle "Nível Bronze - Nível inicial"
audio-step "O nível Bronze é o nível inicial para novos revendedores. Revendedores começam aqui e podem subir conforme atingem os critérios"
wait 3.0
```

**Wait necessário**: 3 segundos para destacar o nível Bronze

### 4. Visualizar Revendedores Bronze
**Descrição**: Ver revendedores no nível Bronze

**Comandos playwright-simple**:
```bash
pw-click "Clientes"
wait 1.0
pw-type "Bronze" into "Buscar"
subtitle "Revendedores no nível Bronze"
audio-step "Aqui estão os revendedores que estão no nível Bronze"
wait 2.0
```

### 5. Visualizar Nível Prata
**Descrição**: Mostrar categoria Prata

**Comandos playwright-simple**:
```bash
pw-click "Categorias"
wait 1.0
pw-type "Prata" into "Buscar"
subtitle "Nível Prata - Nível intermediário"
audio-step "O nível Prata é o segundo nível, alcançado quando o revendedor atinge critérios específicos de faturamento ou cadastros"
wait 3.0
```

### 6. Visualizar Revendedores Prata
**Descrição**: Ver revendedores no nível Prata

**Comandos playwright-simple**:
```bash
pw-click "Clientes"
wait 1.0
pw-type "Prata" into "Buscar"
subtitle "Revendedores no nível Prata"
audio-step "Estes são revendedores que subiram para o nível Prata"
wait 2.0
```

### 7. Visualizar Nível Ouro
**Descrição**: Mostrar categoria Ouro

**Comandos playwright-simple**:
```bash
pw-click "Categorias"
wait 1.0
pw-type "Ouro" into "Buscar"
subtitle "Nível Ouro - Nível avançado"
audio-step "O nível Ouro é para revendedores experientes que atingiram metas mais altas de faturamento ou cadastros"
wait 3.0
```

### 8. Visualizar Revendedores Ouro
**Descrição**: Ver revendedores no nível Ouro

**Comandos playwright-simple**:
```bash
pw-click "Clientes"
wait 1.0
pw-type "Ouro" into "Buscar"
subtitle "Revendedores no nível Ouro"
audio-step "Revendedores Ouro têm acesso a maiores benefícios e comissões"
wait 2.0
```

### 9. Visualizar Nível Platinum
**Descrição**: Mostrar categoria Platinum

**Comandos playwright-simple**:
```bash
pw-click "Categorias"
wait 1.0
pw-type "Platinum" into "Buscar"
subtitle "Nível Platinum - Nível elite"
audio-step "O nível Platinum é o mais alto, reservado para os top performers com maiores volumes de faturamento e rede"
wait 3.0
```

### 10. Visualizar Revendedores Platinum
**Descrição**: Ver revendedores no nível Platinum

**Comandos playwright-simple**:
```bash
pw-click "Clientes"
wait 1.0
pw-type "Platinum" into "Buscar"
subtitle "Revendedores no nível Platinum"
audio-step "Estes são os revendedores de elite, com os maiores benefícios, comissões e acesso a produtos exclusivos"
wait 3.0
```

### 11. Abrir Detalhes de um Revendedor
**Descrição**: Ver detalhes de um revendedor para mostrar nível

**Comandos playwright-simple**:
```bash
pw-click "Lucia Helena Santos"
subtitle "Detalhes do revendedor"
audio-step "Ao abrir um revendedor, podemos ver suas informações, nível atual e histórico"
wait 2.0
```

## Comandos de Terminal Completos

```bash
# 1. Iniciar recorder
cd /home/gabriel/softhill/playwright-simple
playwright-simple record fluxo_03_escalonamento.yaml --url http://localhost:18069

# 2. Executar comandos no terminal do recorder:
start
pw-click "Entrar"
subtitle "Acessando a tela de login"
audio-step "Acessando a tela de login"
wait 1.0
pw-type "admin" into "E-mail"
pw-type "admin" into "Senha"
pw-submit "Entrar"
subtitle "Login realizado com sucesso"
audio-step "Login realizado com sucesso"
wait 2.0
pw-click "Contatos"
wait 1.0
pw-click "Categorias"
subtitle "Acessando categorias de níveis"
audio-step "Aqui estão as categorias que representam os níveis de revendedor no sistema"
wait 2.0
pw-type "Bronze" into "Buscar"
subtitle "Nível Bronze - Nível inicial"
audio-step "O nível Bronze é o nível inicial para novos revendedores. Revendedores começam aqui e podem subir conforme atingem os critérios"
wait 3.0
pw-click "Clientes"
wait 1.0
pw-type "Bronze" into "Buscar"
subtitle "Revendedores no nível Bronze"
audio-step "Aqui estão os revendedores que estão no nível Bronze"
wait 2.0
pw-click "Categorias"
wait 1.0
pw-type "Prata" into "Buscar"
subtitle "Nível Prata - Nível intermediário"
audio-step "O nível Prata é o segundo nível, alcançado quando o revendedor atinge critérios específicos de faturamento ou cadastros"
wait 3.0
pw-click "Clientes"
wait 1.0
pw-type "Prata" into "Buscar"
subtitle "Revendedores no nível Prata"
audio-step "Estes são revendedores que subiram para o nível Prata"
wait 2.0
pw-click "Categorias"
wait 1.0
pw-type "Ouro" into "Buscar"
subtitle "Nível Ouro - Nível avançado"
audio-step "O nível Ouro é para revendedores experientes que atingiram metas mais altas de faturamento ou cadastros"
wait 3.0
pw-click "Clientes"
wait 1.0
pw-type "Ouro" into "Buscar"
subtitle "Revendedores no nível Ouro"
audio-step "Revendedores Ouro têm acesso a maiores benefícios e comissões"
wait 2.0
pw-click "Categorias"
wait 1.0
pw-type "Platinum" into "Buscar"
subtitle "Nível Platinum - Nível elite"
audio-step "O nível Platinum é o mais alto, reservado para os top performers com maiores volumes de faturamento e rede"
wait 3.0
pw-click "Clientes"
wait 1.0
pw-type "Platinum" into "Buscar"
subtitle "Revendedores no nível Platinum"
audio-step "Estes são os revendedores de elite, com os maiores benefícios, comissões e acesso a produtos exclusivos"
wait 3.0
pw-click "Lucia Helena Santos"
subtitle "Detalhes do revendedor"
audio-step "Ao abrir um revendedor, podemos ver suas informações, nível atual e histórico"
wait 2.0
save
exit
```

## Pontos de Atenção

1. **Cada Nível** (3 segundos de wait): Destacar os critérios e características de cada nível
2. **Comparação entre Níveis** (2 segundos entre cada): Mostrar a progressão Bronze → Prata → Ouro → Platinum
3. **Revendedores Platinum** (3 segundos de wait): Destacar que são os top performers

## Dados de Demo Disponíveis

- ✅ 4 níveis configurados: Bronze, Prata, Ouro, Platinum
- ✅ 15 revendedores distribuídos:
  - 4+ revendedores Bronze
  - 4+ revendedores Prata
  - 4+ revendedores Ouro
  - 3+ revendedores Platinum

## Notas Importantes

- Escalonamento é automático baseado em critérios (faturamento próprio/rede, cadastros)
- Novo revendedor inicia no Bronze
- Sistema calcula mensalmente e atualiza níveis automaticamente
- Cada nível tem comissão diferente (Bronze 5%, Prata 7.5%, Ouro 10%, Platinum 12.5%)

