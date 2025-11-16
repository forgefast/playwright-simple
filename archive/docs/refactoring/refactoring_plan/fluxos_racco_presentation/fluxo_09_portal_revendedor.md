# Fluxo 09: Portal do Revendedor

## Descrição
Demonstra o portal completo do revendedor, mostrando acesso a produtos, pedidos, comissões e informações da rede.

## Pré-requisitos
- Usuário de teste: `lucia.santos@exemplo.com` (senha: `demo123`) - Revendedor Bronze
- Dados demo: Revendedor com acesso, produtos, pedidos
- Módulo `racco_demo` instalado

## Menu de Acesso
- Portal: `/my` (após login)
- E-commerce: `/shop` (após login)

## Passos Detalhados

### 1. Login como Revendedor
**Descrição**: Fazer login como revendedor

**Comandos playwright-simple**:
```bash
pw-click "Entrar"
subtitle "Acessando a tela de login"
audio-step "Acessando a tela de login"
wait 1.0

pw-type "lucia.santos@exemplo.com" into "E-mail"
subtitle "Digitando email do revendedor"
audio-step "Digitando email do revendedor Bronze"
wait 0.5

pw-type "demo123" into "Senha"
subtitle "Digitando senha"
audio-step "Digitando senha"
wait 0.5

pw-submit "Entrar"
subtitle "Fazendo login como revendedor"
audio-step "Fazendo login como revendedor Bronze"
wait 2.0
```

### 2. Acessar Portal do Revendedor
**Descrição**: Navegar para o portal

**Comandos playwright-simple**:
```bash
pw-click "Portal"
subtitle "Acessando portal do revendedor"
audio-step "Aqui está o portal do revendedor, com acesso a todas as funcionalidades específicas do seu nível"
wait 2.0
```

**Wait necessário**: 2 segundos para carregar portal

### 3. Visualizar Dashboard do Portal
**Descrição**: Mostrar informações do revendedor

**Comandos playwright-simple**:
```bash
subtitle "Dashboard do portal do revendedor"
audio-step "O portal exibe informações do revendedor, incluindo nível atual, pedidos, comissões e acesso a produtos"
wait 3.0
```

**Wait necessário**: 3 segundos para destacar o dashboard

### 4. Visualizar Nível do Revendedor
**Descrição**: Mostrar nível atual

**Comandos playwright-simple**:
```bash
subtitle "Nível atual: Bronze"
audio-step "O revendedor pode ver seu nível atual, que neste caso é Bronze, o nível inicial"
wait 2.0
```

### 5. Acessar Produtos Disponíveis
**Descrição**: Ver produtos com preços para revendedor

**Comandos playwright-simple**:
```bash
pw-click "Loja"
subtitle "Acessando catálogo de produtos"
audio-step "Aqui estão os produtos disponíveis para o revendedor, com preços específicos do seu nível"
wait 2.0
```

### 6. Visualizar Catálogo de Produtos
**Descrição**: Mostrar produtos e preços

**Comandos playwright-simple**:
```bash
subtitle "Catálogo de produtos com preços para revendedor"
audio-step "O revendedor vê todos os produtos disponíveis com preços especiais conforme seu nível"
wait 3.0
```

**Wait necessário**: 3 segundos para visualizar produtos

### 7. Visualizar Detalhes de um Produto
**Descrição**: Ver página de produto

**Comandos playwright-simple**:
```bash
pw-click "Batom Matte Rouge"
subtitle "Visualizando detalhes do produto"
audio-step "O revendedor pode ver informações detalhadas do produto e preço especial para seu nível"
wait 2.0
```

### 8. Acessar Pedidos
**Descrição**: Ver pedidos do revendedor

**Comandos playwright-simple**:
```bash
pw-click "Portal"
wait 1.0
pw-click "Pedidos"
subtitle "Acessando pedidos do revendedor"
audio-step "Aqui o revendedor pode ver todos os seus pedidos e criar novos"
wait 2.0
```

### 9. Visualizar Comissões
**Descrição**: Ver comissões do revendedor

**Comandos playwright-simple**:
```bash
pw-click "Comissões"
subtitle "Acessando comissões"
audio-step "O revendedor pode ver suas comissões calculadas e histórico de pagamentos"
wait 2.0
```

### 10. Visualizar Informações da Rede (se disponível)
**Descrição**: Ver informações sobre rede de indicados

**Comandos playwright-simple**:
```bash
pw-click "Rede"
subtitle "Acessando informações da rede"
audio-step "O revendedor pode ver informações sobre sua rede de indicados e performance"
wait 2.0
```

## Comandos de Terminal Completos

```bash
# 1. Iniciar recorder
cd /home/gabriel/softhill/playwright-simple
playwright-simple record fluxo_09_portal_revendedor.yaml --url http://localhost:18069

# 2. Executar comandos no terminal do recorder:
start
pw-click "Entrar"
subtitle "Acessando a tela de login"
audio-step "Acessando a tela de login"
wait 1.0
pw-type "lucia.santos@exemplo.com" into "E-mail"
subtitle "Digitando email do revendedor"
audio-step "Digitando email do revendedor Bronze"
wait 0.5
pw-type "demo123" into "Senha"
subtitle "Digitando senha"
audio-step "Digitando senha"
wait 0.5
pw-submit "Entrar"
subtitle "Fazendo login como revendedor"
audio-step "Fazendo login como revendedor Bronze"
wait 2.0
pw-click "Portal"
subtitle "Acessando portal do revendedor"
audio-step "Aqui está o portal do revendedor, com acesso a todas as funcionalidades específicas do seu nível"
wait 2.0
subtitle "Dashboard do portal do revendedor"
audio-step "O portal exibe informações do revendedor, incluindo nível atual, pedidos, comissões e acesso a produtos"
wait 3.0
subtitle "Nível atual: Bronze"
audio-step "O revendedor pode ver seu nível atual, que neste caso é Bronze, o nível inicial"
wait 2.0
pw-click "Loja"
subtitle "Acessando catálogo de produtos"
audio-step "Aqui estão os produtos disponíveis para o revendedor, com preços específicos do seu nível"
wait 2.0
subtitle "Catálogo de produtos com preços para revendedor"
audio-step "O revendedor vê todos os produtos disponíveis com preços especiais conforme seu nível"
wait 3.0
pw-click "Batom Matte Rouge"
subtitle "Visualizando detalhes do produto"
audio-step "O revendedor pode ver informações detalhadas do produto e preço especial para seu nível"
wait 2.0
pw-click "Portal"
wait 1.0
pw-click "Pedidos"
subtitle "Acessando pedidos do revendedor"
audio-step "Aqui o revendedor pode ver todos os seus pedidos e criar novos"
wait 2.0
pw-click "Comissões"
subtitle "Acessando comissões"
audio-step "O revendedor pode ver suas comissões calculadas e histórico de pagamentos"
wait 2.0
pw-click "Rede"
subtitle "Acessando informações da rede"
audio-step "O revendedor pode ver informações sobre sua rede de indicados e performance"
wait 2.0
save
exit
```

## Pontos de Atenção

1. **Dashboard do Portal** (3 segundos de wait): Destacar todas as funcionalidades disponíveis
2. **Nível do Revendedor** (2 segundos de wait): Mostrar nível atual (Bronze)
3. **Catálogo de Produtos** (3 segundos de wait): Destacar preços especiais para revendedor
4. **Comissões** (2 segundos de wait): Destacar onde o revendedor vê suas comissões

## Dados de Demo Disponíveis

- ✅ Revendedor Bronze: `lucia.santos@exemplo.com`
- ✅ 7+ produtos com preços para revendedor
- ✅ Pedidos de exemplo do revendedor
- ✅ Portal do revendedor funcional
- ✅ Comissões configuradas (Bronze: 5%)

## Notas Importantes

- Portal do revendedor mostra informações específicas do nível
- Preços podem variar conforme nível do revendedor (pricelist)
- Revendedor pode criar pedidos para seus clientes
- Comissões são calculadas automaticamente
- Cada nível tem acesso a diferentes funcionalidades

## Variações por Nível

Para demonstrar diferentes níveis, pode-se usar:
- **Prata**: `mariana.lima@exemplo.com` (comissão 7.5%)
- **Ouro**: `adriana.santos@exemplo.com` (comissão 10%)
- **Platinum**: `helena.souza@exemplo.com` (comissão 12.5%)

