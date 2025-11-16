# Fluxo 05: Gamificação

## Descrição
Demonstra o sistema de gamificação do Racco, mostrando badges de conquistas, desafios ativos e rankings.

## Pré-requisitos
- Usuário admin: `admin` (senha: `admin`)
- Dados demo: 13+ badges, 5+ desafios
- Módulo `racco_demo` instalado

## Menu de Acesso
- Badges: **Gamificação > Badges**
- Desafios: **Gamificação > Desafios**

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

### 2. Acessar Menu de Gamificação
**Descrição**: Navegar para gamificação

**Comandos playwright-simple**:
```bash
pw-click "Gamificação"
subtitle "Acessando menu de gamificação"
audio-step "Acessando o sistema de gamificação"
wait 1.0
```

### 3. Visualizar Badges Disponíveis
**Descrição**: Ver todos os badges de conquistas

**Comandos playwright-simple**:
```bash
pw-click "Badges"
subtitle "Acessando badges de conquistas"
audio-step "Aqui estão todos os badges de conquistas disponíveis no sistema"
wait 2.0
```

### 4. Visualizar Lista de Badges
**Descrição**: Mostrar os badges cadastrados

**Comandos playwright-simple**:
```bash
subtitle "Badges de vendas, treinamento, rede e fidelidade"
audio-step "O sistema possui badges para diferentes conquistas: vendas, treinamento, construção de rede e fidelidade de clientes"
wait 3.0
```

**Wait necessário**: 3 segundos para destacar os badges

### 5. Filtrar Badges de Vendas
**Descrição**: Ver badges relacionados a vendas

**Comandos playwright-simple**:
```bash
pw-type "Venda" into "Buscar"
subtitle "Badges relacionados a vendas"
audio-step "Estes são badges conquistados por atingir metas de vendas, como primeira venda, vendedor de mil reais, cinco mil reais e dez mil reais"
wait 2.0
```

### 6. Filtrar Badges de Treinamento
**Descrição**: Ver badges relacionados a treinamento

**Comandos playwright-simple**:
```bash
pw-type "Treinamento" into "Buscar"
subtitle "Badges relacionados a treinamento"
audio-step "Badges de treinamento são conquistados ao completar cursos, como iniciante nos estudos, expert em treinamento e mestre em conhecimento"
wait 2.0
```

### 7. Filtrar Badges de Rede
**Descrição**: Ver badges relacionados a construção de rede

**Comandos playwright-simple**:
```bash
pw-type "Rede" into "Buscar"
subtitle "Badges relacionados a construção de rede"
audio-step "Estes badges são conquistados ao indicar novos revendedores, como primeiro indicado, construtor de rede e líder de rede"
wait 2.0
```

### 8. Acessar Desafios
**Descrição**: Ver desafios ativos

**Comandos playwright-simple**:
```bash
pw-click "Desafios"
subtitle "Acessando desafios ativos"
audio-step "Aqui estão os desafios ativos do sistema, que podem ser mensais, trimestrais ou anuais"
wait 2.0
```

### 9. Visualizar Lista de Desafios
**Descrição**: Mostrar desafios disponíveis

**Comandos playwright-simple**:
```bash
subtitle "Desafios mensais, trimestrais e anuais"
audio-step "O sistema possui desafios de diferentes períodos: mensais de vendas, novos clientes, trimestrais de vendas e crescimento de rede, e o desafio anual de campeão do ano"
wait 3.0
```

**Wait necessário**: 3 segundos para destacar os desafios

### 10. Abrir Detalhes de um Desafio
**Descrição**: Ver informações de um desafio específico

**Comandos playwright-simple**:
```bash
pw-click "Desafio Mensal de Vendas"
subtitle "Detalhes do desafio mensal de vendas"
audio-step "Cada desafio tem descrição, período de validade e objetivos a serem atingidos"
wait 2.0
```

## Comandos de Terminal Completos

```bash
# 1. Iniciar recorder
cd /home/gabriel/softhill/playwright-simple
playwright-simple record fluxo_05_gamificacao.yaml --url http://localhost:18069

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
pw-click "Gamificação"
subtitle "Acessando menu de gamificação"
audio-step "Acessando o sistema de gamificação"
wait 1.0
pw-click "Badges"
subtitle "Acessando badges de conquistas"
audio-step "Aqui estão todos os badges de conquistas disponíveis no sistema"
wait 2.0
subtitle "Badges de vendas, treinamento, rede e fidelidade"
audio-step "O sistema possui badges para diferentes conquistas: vendas, treinamento, construção de rede e fidelidade de clientes"
wait 3.0
pw-type "Venda" into "Buscar"
subtitle "Badges relacionados a vendas"
audio-step "Estes são badges conquistados por atingir metas de vendas, como primeira venda, vendedor de mil reais, cinco mil reais e dez mil reais"
wait 2.0
pw-type "Treinamento" into "Buscar"
subtitle "Badges relacionados a treinamento"
audio-step "Badges de treinamento são conquistados ao completar cursos, como iniciante nos estudos, expert em treinamento e mestre em conhecimento"
wait 2.0
pw-type "Rede" into "Buscar"
subtitle "Badges relacionados a construção de rede"
audio-step "Estes badges são conquistados ao indicar novos revendedores, como primeiro indicado, construtor de rede e líder de rede"
wait 2.0
pw-click "Desafios"
subtitle "Acessando desafios ativos"
audio-step "Aqui estão os desafios ativos do sistema, que podem ser mensais, trimestrais ou anuais"
wait 2.0
subtitle "Desafios mensais, trimestrais e anuais"
audio-step "O sistema possui desafios de diferentes períodos: mensais de vendas, novos clientes, trimestrais de vendas e crescimento de rede, e o desafio anual de campeão do ano"
wait 3.0
pw-click "Desafio Mensal de Vendas"
subtitle "Detalhes do desafio mensal de vendas"
audio-step "Cada desafio tem descrição, período de validade e objetivos a serem atingidos"
wait 2.0
save
exit
```

## Pontos de Atenção

1. **Lista de Badges** (3 segundos de wait): Destacar a variedade de badges disponíveis
2. **Categorias de Badges** (2 segundos cada): Mostrar badges por categoria (vendas, treinamento, rede)
3. **Desafios** (3 segundos de wait): Destacar os diferentes tipos de desafios

## Dados de Demo Disponíveis

- ✅ 13+ badges de conquistas:
  - **Vendas**: Primeira Venda, Vendedor R$ 1.000, R$ 5.000, R$ 10.000, Subiu de Nível
  - **Treinamento**: Iniciante nos Estudos, Expert em Treinamento, Mestre em Conhecimento
  - **Rede**: Primeiro Indicado, Construtor de Rede, Líder de Rede
  - **Fidelidade**: Cliente Fiel, Cliente VIP
- ✅ 5+ desafios ativos:
  - Desafio Mensal de Vendas
  - Novos Clientes
  - Desafio Trimestral de Vendas
  - Crescimento de Rede
  - Campeão do Ano

## Notas Importantes

- Badges são conquistados automaticamente quando critérios são atingidos
- Desafios podem ser mensais, trimestrais ou anuais
- Sistema de gamificação integra com vendas, treinamento e rede
- Badges e desafios motivam revendedores a atingir metas

