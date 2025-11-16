# Fluxo 08: Portal do Consumidor

## Descrição
Demonstra o portal completo do consumidor final, incluindo acesso ao e-commerce, histórico de pedidos e informações pessoais.

## Pré-requisitos
- Usuário de teste: `juliana.ferreira@gmail.com` (senha: `demo123`)
- Dados demo: Consumidor com pedidos, produtos no e-commerce
- Módulo `racco_demo` instalado

## Menu de Acesso
- Portal: `/my` (após login)
- E-commerce: `/shop` (após login)

## Passos Detalhados

### 1. Login como Consumidor Final
**Descrição**: Fazer login no sistema

**Comandos playwright-simple**:
```bash
pw-click "Entrar"
subtitle "Acessando a tela de login"
audio-step "Acessando a tela de login"
wait 1.0

pw-type "juliana.ferreira@gmail.com" into "E-mail"
subtitle "Digitando email do consumidor"
audio-step "Digitando email do consumidor final"
wait 0.5

pw-type "demo123" into "Senha"
subtitle "Digitando senha"
audio-step "Digitando senha"
wait 0.5

pw-submit "Entrar"
subtitle "Fazendo login no sistema"
audio-step "Fazendo login no sistema"
wait 2.0
```

### 2. Acessar Portal do Consumidor
**Descrição**: Navegar para o portal

**Comandos playwright-simple**:
```bash
pw-click "Portal"
subtitle "Acessando portal do consumidor"
audio-step "Aqui está o portal do consumidor final, com acesso a todas as funcionalidades"
wait 2.0
```

**Wait necessário**: 2 segundos para carregar portal

### 3. Visualizar Dashboard do Portal
**Descrição**: Mostrar informações disponíveis

**Comandos playwright-simple**:
```bash
subtitle "Dashboard do portal com informações pessoais e pedidos"
audio-step "O portal exibe informações pessoais do consumidor, histórico de pedidos e acesso rápido ao e-commerce"
wait 3.0
```

**Wait necessário**: 3 segundos para destacar o dashboard

### 4. Visualizar Histórico de Pedidos
**Descrição**: Ver pedidos do consumidor

**Comandos playwright-simple**:
```bash
pw-click "Pedidos"
subtitle "Acessando histórico de pedidos"
audio-step "Aqui o consumidor pode ver todos os seus pedidos, status e detalhes"
wait 2.0
```

### 5. Abrir um Pedido
**Descrição**: Ver detalhes de um pedido

**Comandos playwright-simple**:
```bash
pw-click "Pedido"
subtitle "Visualizando detalhes do pedido"
audio-step "O consumidor pode ver todos os detalhes do pedido, produtos comprados e status"
wait 2.0
```

### 6. Acessar E-commerce
**Descrição**: Navegar para o e-commerce

**Comandos playwright-simple**:
```bash
pw-click "Loja"
subtitle "Acessando e-commerce Racco"
audio-step "Aqui está o e-commerce onde o consumidor pode comprar produtos"
wait 2.0
```

### 7. Visualizar Catálogo de Produtos
**Descrição**: Mostrar produtos disponíveis

**Comandos playwright-simple**:
```bash
subtitle "Catálogo completo de produtos"
audio-step "O e-commerce exibe todos os produtos disponíveis com preços, descrições e imagens"
wait 3.0
```

**Wait necessário**: 3 segundos para visualizar catálogo

### 8. Filtrar Produtos por Categoria
**Descrição**: Mostrar filtros de categoria

**Comandos playwright-simple**:
```bash
pw-click "Maquiagem"
subtitle "Filtrando produtos por categoria"
audio-step "O consumidor pode filtrar produtos por categoria, como maquiagem, perfumaria e cuidados"
wait 2.0
```

### 9. Visualizar Detalhes de um Produto
**Descrição**: Ver página de produto

**Comandos playwright-simple**:
```bash
pw-click "Batom Matte Rouge"
subtitle "Visualizando detalhes do produto"
audio-step "Ao clicar em um produto, o consumidor vê informações detalhadas, preço e pode adicionar ao carrinho"
wait 2.0
```

### 10. Visualizar Informações Pessoais
**Descrição**: Ver perfil do consumidor

**Comandos playwright-simple**:
```bash
pw-click "Portal"
wait 1.0
pw-click "Minha Conta"
subtitle "Acessando informações pessoais"
audio-step "O consumidor pode visualizar e editar suas informações pessoais, endereço e preferências"
wait 2.0
```

## Comandos de Terminal Completos

```bash
# 1. Iniciar recorder
cd /home/gabriel/softhill/playwright-simple
playwright-simple record fluxo_08_portal_consumidor.yaml --url http://localhost:18069

# 2. Executar comandos no terminal do recorder:
start
pw-click "Entrar"
subtitle "Acessando a tela de login"
audio-step "Acessando a tela de login"
wait 1.0
pw-type "juliana.ferreira@gmail.com" into "E-mail"
subtitle "Digitando email do consumidor"
audio-step "Digitando email do consumidor final"
wait 0.5
pw-type "demo123" into "Senha"
subtitle "Digitando senha"
audio-step "Digitando senha"
wait 0.5
pw-submit "Entrar"
subtitle "Fazendo login no sistema"
audio-step "Fazendo login no sistema"
wait 2.0
pw-click "Portal"
subtitle "Acessando portal do consumidor"
audio-step "Aqui está o portal do consumidor final, com acesso a todas as funcionalidades"
wait 2.0
subtitle "Dashboard do portal com informações pessoais e pedidos"
audio-step "O portal exibe informações pessoais do consumidor, histórico de pedidos e acesso rápido ao e-commerce"
wait 3.0
pw-click "Pedidos"
subtitle "Acessando histórico de pedidos"
audio-step "Aqui o consumidor pode ver todos os seus pedidos, status e detalhes"
wait 2.0
pw-click "Pedido"
subtitle "Visualizando detalhes do pedido"
audio-step "O consumidor pode ver todos os detalhes do pedido, produtos comprados e status"
wait 2.0
pw-click "Loja"
subtitle "Acessando e-commerce Racco"
audio-step "Aqui está o e-commerce onde o consumidor pode comprar produtos"
wait 2.0
subtitle "Catálogo completo de produtos"
audio-step "O e-commerce exibe todos os produtos disponíveis com preços, descrições e imagens"
wait 3.0
pw-click "Maquiagem"
subtitle "Filtrando produtos por categoria"
audio-step "O consumidor pode filtrar produtos por categoria, como maquiagem, perfumaria e cuidados"
wait 2.0
pw-click "Batom Matte Rouge"
subtitle "Visualizando detalhes do produto"
audio-step "Ao clicar em um produto, o consumidor vê informações detalhadas, preço e pode adicionar ao carrinho"
wait 2.0
pw-click "Portal"
wait 1.0
pw-click "Minha Conta"
subtitle "Acessando informações pessoais"
audio-step "O consumidor pode visualizar e editar suas informações pessoais, endereço e preferências"
wait 2.0
save
exit
```

## Pontos de Atenção

1. **Dashboard do Portal** (3 segundos de wait): Destacar todas as seções disponíveis
2. **E-commerce** (3 segundos de wait): Mostrar catálogo completo
3. **Histórico de Pedidos** (2 segundos de wait): Destacar acompanhamento de pedidos

## Dados de Demo Disponíveis

- ✅ Consumidor final cadastrado: `juliana.ferreira@gmail.com`
- ✅ 7+ produtos publicados no e-commerce
- ✅ Pedidos de exemplo para o consumidor
- ✅ Portal do consumidor funcional

## Notas Importantes

- Consumidor final não precisa de aprovação para cadastro
- Portal integrado com e-commerce
- Consumidor pode acompanhar status de pedidos
- Preços exibidos são para consumidor final (podem diferir de revendedores)

