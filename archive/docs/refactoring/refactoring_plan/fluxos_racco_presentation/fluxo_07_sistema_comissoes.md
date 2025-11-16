# Fluxo 07: Sistema de Comissões

## Descrição
Demonstra o sistema de comissões do Racco, mostrando as comissões por nível de revendedor e como são calculadas nos pedidos.

## Pré-requisitos
- Usuário admin: `admin` (senha: `admin`)
- Dados demo: Comissões configuradas por nível (Bronze 5%, Prata 7.5%, Ouro 10%, Platinum 12.5%)
- Módulo `racco_demo` instalado

## Menu de Acesso
- Categorias: **Contatos > Categorias** (para ver níveis)
- Pedidos: **Vendas > Pedidos** (para ver comissões em pedidos)

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

### 2. Acessar Pedidos de Venda
**Descrição**: Ver pedidos para mostrar comissões

**Comandos playwright-simple**:
```bash
pw-click "Vendas"
subtitle "Acessando menu de vendas"
audio-step "Acessando o menu de vendas"
wait 1.0

pw-click "Pedidos"
subtitle "Acessando pedidos de venda"
audio-step "Aqui estão os pedidos de venda, onde podemos ver as comissões calculadas"
wait 2.0
```

### 3. Abrir um Pedido
**Descrição**: Abrir pedido para ver comissão

**Comandos playwright-simple**:
```bash
pw-click "Pedido"
subtitle "Abrindo pedido de venda"
audio-step "Vamos abrir um pedido para ver como a comissão é calculada"
wait 2.0
```

**Wait necessário**: 2 segundos para carregar detalhes

### 4. Visualizar Comissão no Pedido
**Descrição**: Mostrar comissão calculada

**Comandos playwright-simple**:
```bash
subtitle "Comissão calculada no pedido"
audio-step "O sistema calcula automaticamente a comissão do revendedor baseado no seu nível e no valor do pedido"
wait 3.0
```

**Wait necessário**: 3 segundos para destacar a comissão

### 5. Voltar e Acessar Categorias
**Descrição**: Ver níveis e suas comissões

**Comandos playwright-simple**:
```bash
pw-click "Contatos"
wait 1.0
pw-click "Categorias"
subtitle "Acessando categorias de níveis"
audio-step "Vamos ver as categorias de níveis e suas respectivas comissões"
wait 2.0
```

### 6. Visualizar Nível Bronze e Comissão
**Descrição**: Mostrar comissão do nível Bronze

**Comandos playwright-simple**:
```bash
pw-type "Bronze" into "Buscar"
subtitle "Nível Bronze - Comissão de 5%"
audio-step "O nível Bronze tem comissão de 5% sobre as vendas"
wait 2.0
```

### 7. Visualizar Nível Prata e Comissão
**Descrição**: Mostrar comissão do nível Prata

**Comandos playwright-simple**:
```bash
pw-type "Prata" into "Buscar"
subtitle "Nível Prata - Comissão de 7,5%"
audio-step "O nível Prata tem comissão de 7,5% sobre as vendas"
wait 2.0
```

### 8. Visualizar Nível Ouro e Comissão
**Descrição**: Mostrar comissão do nível Ouro

**Comandos playwright-simple**:
```bash
pw-type "Ouro" into "Buscar"
subtitle "Nível Ouro - Comissão de 10%"
audio-step "O nível Ouro tem comissão de 10% sobre as vendas"
wait 2.0
```

### 9. Visualizar Nível Platinum e Comissão
**Descrição**: Mostrar comissão do nível Platinum

**Comandos playwright-simple**:
```bash
pw-type "Platinum" into "Buscar"
subtitle "Nível Platinum - Comissão de 12,5%"
audio-step "O nível Platinum tem a maior comissão, 12,5% sobre as vendas"
wait 2.0
```

### 10. Login como Revendedor para Ver Comissões
**Descrição**: Ver comissões do ponto de vista do revendedor

**Comandos playwright-simple**:
```bash
pw-click "Sair"
wait 1.0
pw-click "Entrar"
wait 1.0
pw-type "lucia.santos@exemplo.com" into "E-mail"
pw-type "demo123" into "Senha"
pw-submit "Entrar"
subtitle "Login como revendedor Bronze"
audio-step "Fazendo login como revendedor Bronze para ver suas comissões"
wait 2.0
```

### 11. Acessar Portal do Revendedor
**Descrição**: Ver comissões no portal

**Comandos playwright-simple**:
```bash
pw-click "Portal"
subtitle "Acessando portal do revendedor"
audio-step "No portal, o revendedor pode ver suas comissões e histórico"
wait 2.0
```

## Comandos de Terminal Completos

```bash
# 1. Iniciar recorder
cd /home/gabriel/softhill/playwright-simple
playwright-simple record fluxo_07_comissoes.yaml --url http://localhost:18069

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
pw-click "Vendas"
subtitle "Acessando menu de vendas"
audio-step "Acessando o menu de vendas"
wait 1.0
pw-click "Pedidos"
subtitle "Acessando pedidos de venda"
audio-step "Aqui estão os pedidos de venda, onde podemos ver as comissões calculadas"
wait 2.0
pw-click "Pedido"
subtitle "Abrindo pedido de venda"
audio-step "Vamos abrir um pedido para ver como a comissão é calculada"
wait 2.0
subtitle "Comissão calculada no pedido"
audio-step "O sistema calcula automaticamente a comissão do revendedor baseado no seu nível e no valor do pedido"
wait 3.0
pw-click "Contatos"
wait 1.0
pw-click "Categorias"
subtitle "Acessando categorias de níveis"
audio-step "Vamos ver as categorias de níveis e suas respectivas comissões"
wait 2.0
pw-type "Bronze" into "Buscar"
subtitle "Nível Bronze - Comissão de 5%"
audio-step "O nível Bronze tem comissão de 5% sobre as vendas"
wait 2.0
pw-type "Prata" into "Buscar"
subtitle "Nível Prata - Comissão de 7,5%"
audio-step "O nível Prata tem comissão de 7,5% sobre as vendas"
wait 2.0
pw-type "Ouro" into "Buscar"
subtitle "Nível Ouro - Comissão de 10%"
audio-step "O nível Ouro tem comissão de 10% sobre as vendas"
wait 2.0
pw-type "Platinum" into "Buscar"
subtitle "Nível Platinum - Comissão de 12,5%"
audio-step "O nível Platinum tem a maior comissão, 12,5% sobre as vendas"
wait 2.0
pw-click "Sair"
wait 1.0
pw-click "Entrar"
wait 1.0
pw-type "lucia.santos@exemplo.com" into "E-mail"
pw-type "demo123" into "Senha"
pw-submit "Entrar"
subtitle "Login como revendedor Bronze"
audio-step "Fazendo login como revendedor Bronze para ver suas comissões"
wait 2.0
pw-click "Portal"
subtitle "Acessando portal do revendedor"
audio-step "No portal, o revendedor pode ver suas comissões e histórico"
wait 2.0
save
exit
```

## Pontos de Atenção

1. **Comissão no Pedido** (3 segundos de wait): Destacar como a comissão é calculada e exibida
2. **Comissões por Nível** (2 segundos cada): Mostrar a progressão de comissões (5% → 7.5% → 10% → 12.5%)
3. **Portal do Revendedor** (2 segundos de wait): Destacar onde o revendedor vê suas comissões

## Dados de Demo Disponíveis

- ✅ Comissões configuradas por nível:
  - Bronze: 5%
  - Prata: 7.5%
  - Ouro: 10%
  - Platinum: 12.5%
- ✅ Pedidos de venda com comissões calculadas
- ✅ Revendedores em diferentes níveis para demonstrar

## Notas Importantes

- Comissões são calculadas automaticamente baseadas no nível do revendedor
- Cada nível tem uma taxa de comissão diferente
- Comissões aparecem nos pedidos de venda
- Revendedores podem ver suas comissões no portal
- Sistema pode calcular comissões sobre faturamento próprio e/ou da rede (conforme configuração)

