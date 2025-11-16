# Fluxo 06: Fluxo de Venda - Revendedor

## Descrição
Demonstra o processo completo de criação de um pedido de venda por um revendedor, incluindo seleção de cliente, adição de produtos e confirmação.

## Pré-requisitos
- Usuário de teste: `lucia.santos@exemplo.com` (senha: `demo123`) - Revendedor Bronze
- Dados demo: 7+ produtos, clientes cadastrados
- Módulo `racco_demo` instalado

## Menu de Acesso
- Pedidos: **Vendas > Pedidos**

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
audio-step "Digitando email do revendedor"
wait 0.5

pw-type "demo123" into "Senha"
subtitle "Digitando senha"
audio-step "Digitando senha"
wait 0.5

pw-submit "Entrar"
subtitle "Fazendo login como revendedor"
audio-step "Fazendo login como revendedor"
wait 2.0
```

### 2. Acessar Menu de Pedidos
**Descrição**: Navegar para pedidos de venda

**Comandos playwright-simple**:
```bash
pw-click "Vendas"
subtitle "Acessando menu de vendas"
audio-step "Acessando o menu de vendas"
wait 1.0

pw-click "Pedidos"
subtitle "Acessando pedidos de venda"
audio-step "Aqui estão os pedidos de venda do revendedor"
wait 2.0
```

**Wait necessário**: 2 segundos para carregar lista de pedidos

### 3. Visualizar Pedidos Existentes
**Descrição**: Mostrar pedidos já cadastrados

**Comandos playwright-simple**:
```bash
subtitle "Lista de pedidos de venda"
audio-step "O revendedor pode ver todos os seus pedidos, incluindo rascunhos, confirmados e entregues"
wait 2.0
```

### 4. Criar Novo Pedido
**Descrição**: Iniciar criação de novo pedido

**Comandos playwright-simple**:
```bash
pw-click "Criar"
subtitle "Criando novo pedido de venda"
audio-step "Vamos criar um novo pedido de venda"
wait 2.0
```

**Wait necessário**: 2 segundos para carregar formulário

### 5. Selecionar Cliente
**Descrição**: Escolher cliente para o pedido

**Comandos playwright-simple**:
```bash
pw-type "Juliana" into "Cliente"
subtitle "Selecionando cliente"
audio-step "Selecionando o cliente para o pedido"
wait 1.0

pw-click "Juliana Ferreira"
subtitle "Cliente selecionado"
audio-step "Cliente selecionado com sucesso"
wait 1.0
```

### 6. Adicionar Primeiro Produto
**Descrição**: Adicionar produto ao pedido

**Comandos playwright-simple**:
```bash
pw-click "Adicionar linha"
subtitle "Adicionando produto ao pedido"
audio-step "Vamos adicionar produtos ao pedido"
wait 1.0

pw-type "Batom" into "Produto"
subtitle "Selecionando produto Batom Matte Rouge"
audio-step "Selecionando o produto Batom Matte Rouge"
wait 1.0

pw-click "Batom Matte Rouge"
subtitle "Produto selecionado"
audio-step "Produto selecionado"
wait 0.5

pw-type "10" into "Quantidade"
subtitle "Definindo quantidade"
audio-step "Definindo a quantidade de 10 unidades"
wait 1.0
```

**Wait necessário**: 1 segundo após cada produto para visualizar

### 7. Adicionar Segundo Produto
**Descrição**: Adicionar mais um produto

**Comandos playwright-simple**:
```bash
pw-click "Adicionar linha"
wait 1.0

pw-type "Base" into "Produto"
subtitle "Selecionando produto Base Líquida"
audio-step "Adicionando Base Líquida Perfect Skin"
wait 1.0

pw-click "Base Líquida Perfect Skin"
wait 0.5

pw-type "5" into "Quantidade"
subtitle "Definindo quantidade do segundo produto"
audio-step "Definindo quantidade de 5 unidades"
wait 1.0
```

### 8. Adicionar Terceiro Produto
**Descrição**: Adicionar mais um produto

**Comandos playwright-simple**:
```bash
pw-click "Adicionar linha"
wait 1.0

pw-type "Perfume" into "Produto"
subtitle "Selecionando produto Perfume"
audio-step "Adicionando Perfume Essence Woman"
wait 1.0

pw-click "Perfume Essence Woman"
wait 0.5

pw-type "2" into "Quantidade"
subtitle "Definindo quantidade do terceiro produto"
audio-step "Definindo quantidade de 2 unidades"
wait 1.0
```

### 9. Visualizar Total do Pedido
**Descrição**: Mostrar total calculado

**Comandos playwright-simple**:
```bash
subtitle "Total do pedido calculado automaticamente"
audio-step "O sistema calcula automaticamente o total do pedido com base nos produtos e quantidades"
wait 2.0
```

**Wait necessário**: 2 segundos para destacar o total

### 10. Salvar Pedido
**Descrição**: Salvar o pedido

**Comandos playwright-simple**:
```bash
pw-click "Salvar"
subtitle "Salvando pedido"
audio-step "Salvando o pedido de venda"
wait 2.0
```

### 11. Confirmar Pedido
**Descrição**: Confirmar o pedido

**Comandos playwright-simple**:
```bash
pw-click "Confirmar"
subtitle "Confirmando pedido"
audio-step "Confirmando o pedido para processamento"
wait 2.0
```

## Comandos de Terminal Completos

```bash
# 1. Iniciar recorder
cd /home/gabriel/softhill/playwright-simple
playwright-simple record fluxo_06_venda.yaml --url http://localhost:18069

# 2. Executar comandos no terminal do recorder:
start
pw-click "Entrar"
subtitle "Acessando a tela de login"
audio-step "Acessando a tela de login"
wait 1.0
pw-type "lucia.santos@exemplo.com" into "E-mail"
subtitle "Digitando email do revendedor"
audio-step "Digitando email do revendedor"
wait 0.5
pw-type "demo123" into "Senha"
subtitle "Digitando senha"
audio-step "Digitando senha"
wait 0.5
pw-submit "Entrar"
subtitle "Fazendo login como revendedor"
audio-step "Fazendo login como revendedor"
wait 2.0
pw-click "Vendas"
subtitle "Acessando menu de vendas"
audio-step "Acessando o menu de vendas"
wait 1.0
pw-click "Pedidos"
subtitle "Acessando pedidos de venda"
audio-step "Aqui estão os pedidos de venda do revendedor"
wait 2.0
subtitle "Lista de pedidos de venda"
audio-step "O revendedor pode ver todos os seus pedidos, incluindo rascunhos, confirmados e entregues"
wait 2.0
pw-click "Criar"
subtitle "Criando novo pedido de venda"
audio-step "Vamos criar um novo pedido de venda"
wait 2.0
pw-type "Juliana" into "Cliente"
subtitle "Selecionando cliente"
audio-step "Selecionando o cliente para o pedido"
wait 1.0
pw-click "Juliana Ferreira"
subtitle "Cliente selecionado"
audio-step "Cliente selecionado com sucesso"
wait 1.0
pw-click "Adicionar linha"
subtitle "Adicionando produto ao pedido"
audio-step "Vamos adicionar produtos ao pedido"
wait 1.0
pw-type "Batom" into "Produto"
subtitle "Selecionando produto Batom Matte Rouge"
audio-step "Selecionando o produto Batom Matte Rouge"
wait 1.0
pw-click "Batom Matte Rouge"
subtitle "Produto selecionado"
audio-step "Produto selecionado"
wait 0.5
pw-type "10" into "Quantidade"
subtitle "Definindo quantidade"
audio-step "Definindo a quantidade de 10 unidades"
wait 1.0
pw-click "Adicionar linha"
wait 1.0
pw-type "Base" into "Produto"
subtitle "Selecionando produto Base Líquida"
audio-step "Adicionando Base Líquida Perfect Skin"
wait 1.0
pw-click "Base Líquida Perfect Skin"
wait 0.5
pw-type "5" into "Quantidade"
subtitle "Definindo quantidade do segundo produto"
audio-step "Definindo quantidade de 5 unidades"
wait 1.0
pw-click "Adicionar linha"
wait 1.0
pw-type "Perfume" into "Produto"
subtitle "Selecionando produto Perfume"
audio-step "Adicionando Perfume Essence Woman"
wait 1.0
pw-click "Perfume Essence Woman"
wait 0.5
pw-type "2" into "Quantidade"
subtitle "Definindo quantidade do terceiro produto"
audio-step "Definindo quantidade de 2 unidades"
wait 1.0
subtitle "Total do pedido calculado automaticamente"
audio-step "O sistema calcula automaticamente o total do pedido com base nos produtos e quantidades"
wait 2.0
pw-click "Salvar"
subtitle "Salvando pedido"
audio-step "Salvando o pedido de venda"
wait 2.0
pw-click "Confirmar"
subtitle "Confirmando pedido"
audio-step "Confirmando o pedido para processamento"
wait 2.0
save
exit
```

## Pontos de Atenção

1. **Formulário de Pedido** (2 segundos de wait): Destacar campos disponíveis
2. **Adição de Produtos** (1 segundo após cada): Mostrar processo de adicionar múltiplos produtos
3. **Total Calculado** (2 segundos de wait): Destacar cálculo automático do total
4. **Confirmação** (2 segundos de wait): Mostrar pedido confirmado

## Dados de Demo Disponíveis

- ✅ 7+ produtos cadastrados:
  - Batom Matte Rouge (R$ 45,00)
  - Base Líquida Perfect Skin (R$ 89,00)
  - Perfume Essence Woman (R$ 149,00)
  - Perfume Essence Men (R$ 139,00)
  - Creme Facial Hidratante (R$ 79,00)
  - Sérum Vitamina C (R$ 129,00)
  - Loção Corporal Hidratante (R$ 59,00)
- ✅ 10+ consumidores finais para usar como clientes
- ✅ 6+ pedidos de exemplo em diferentes estados

## Notas Importantes

- Revendedor pode criar pedidos para seus clientes
- Sistema calcula total automaticamente
- Pedidos podem estar em diferentes estados: rascunho, confirmado, entregue
- Preços podem variar conforme nível do revendedor (pricelist)

