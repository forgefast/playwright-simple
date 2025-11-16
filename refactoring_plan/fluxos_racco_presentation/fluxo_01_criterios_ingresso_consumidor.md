# Fluxo 01: Critérios de Ingresso - Consumidor Final

## Descrição
Demonstra os critérios e processo de cadastro de consumidor final no sistema Racco, mostrando o portal do consumidor e e-commerce.

## Pré-requisitos
- Usuário de teste: `juliana.ferreira@gmail.com` (senha: `demo123`)
- Dados demo: 10 consumidores finais cadastrados
- Módulo `racco_demo` instalado

## Menu de Acesso
- Portal do Consumidor: `/my` (após login)
- E-commerce: `/shop` (após login)

## Passos Detalhados

### 1. Login como Consumidor Final
**Descrição**: Fazer login no sistema como consumidor final

**Comandos playwright-simple**:
```bash
# Iniciar recorder
playwright-simple record fluxo_01_consumidor.yaml --url http://localhost:18069

# No terminal do recorder:
pw-click "Entrar"
subtitle "Acessando a tela de login"
audio-step "Acessando a tela de login"
wait 1.0

pw-type "juliana.ferreira@gmail.com" into "E-mail"
subtitle "Digitando email do consumidor final"
audio-step "Digitando email do consumidor final"
wait 0.5

pw-type "demo123" into "Senha"
subtitle "Digitando senha"
audio-step "Digitando senha"
wait 0.5

pw-submit "Entrar"
subtitle "Fazendo login no sistema"
audio-step "Fazendo login no sistema"
wait 3.0
subtitle "Acessando o portal do consumidor"
audio-step "Aqui está o portal do consumidor final, onde ele pode acompanhar seus pedidos e informações"
wait 2.0
subtitle "O portal mostra informações pessoais, pedidos e histórico"
audio-step "O portal do consumidor exibe informações pessoais, histórico de pedidos e acesso ao e-commerce"
wait 2.0
```

**Wait necessário**: 3 segundos após login para carregar dashboard, depois mais 2 segundos para mostrar o portal

### 2. Acessar E-commerce

**Wait necessário**: 2 segundos para carregar o catálogo

### 3. Visualizar Catálogo de Produtos
**Descrição**: Navegar para o e-commerce

**Comandos playwright-simple**:
```bash
pw-click "Loja"
subtitle "Acessando o e-commerce Racco"
audio-step "Aqui está o e-commerce onde o consumidor pode comprar produtos"
wait 2.0
```

**Wait necessário**: 2 segundos para carregar o catálogo

### 5. Visualizar Catálogo de Produtos
**Descrição**: Mostrar os produtos disponíveis para o consumidor

**Comandos playwright-simple**:
```bash
subtitle "Catálogo completo de produtos disponíveis para compra"
audio-step "O e-commerce exibe todos os produtos disponíveis com preços e descrições"
wait 3.0
```

**Wait necessário**: 3 segundos para visualizar os produtos

### 6. Visualizar Detalhes de um Produto
**Descrição**: Clicar em um produto para ver detalhes

**Comandos playwright-simple**:
```bash
pw-click "Batom Matte Rouge"
subtitle "Visualizando detalhes do produto"
audio-step "Ao clicar em um produto, o consumidor vê informações detalhadas, preço e pode adicionar ao carrinho"
wait 2.0
```

**Wait necessário**: 2 segundos para carregar página do produto

## Comandos de Terminal Completos

```bash
# 1. Iniciar recorder
cd /home/gabriel/softhill/playwright-simple
playwright-simple record fluxo_01_consumidor.yaml --url http://localhost:18069

# 2. Executar comandos no terminal do recorder (copiar e colar):
start
pw-click "Entrar"
subtitle "Acessando a tela de login"
audio-step "Acessando a tela de login"
wait 1.0
pw-type "juliana.ferreira@gmail.com" into "E-mail"
subtitle "Digitando email do consumidor final"
audio-step "Digitando email do consumidor final"
wait 0.5
pw-type "demo123" into "Senha"
subtitle "Digitando senha"
audio-step "Digitando senha"
wait 0.5
pw-submit "Entrar"
subtitle "Fazendo login no sistema"
audio-step "Fazendo login no sistema"
wait 3.0
subtitle "Acessando o portal do consumidor"
audio-step "Aqui está o portal do consumidor final, onde ele pode acompanhar seus pedidos e informações"
wait 2.0
subtitle "O portal mostra informações pessoais, pedidos e histórico"
audio-step "O portal do consumidor exibe informações pessoais, histórico de pedidos e acesso ao e-commerce"
wait 2.0
pw-click "Loja"
subtitle "Acessando o e-commerce Racco"
audio-step "Aqui está o e-commerce onde o consumidor pode comprar produtos"
wait 2.0
subtitle "Catálogo completo de produtos disponíveis para compra"
audio-step "O e-commerce exibe todos os produtos disponíveis com preços e descrições"
wait 3.0
pw-click "Batom Matte Rouge"
subtitle "Visualizando detalhes do produto"
audio-step "Ao clicar em um produto, o consumidor vê informações detalhadas, preço e pode adicionar ao carrinho"
wait 2.0
save
exit
```

## Pontos de Atenção

1. **Portal do Consumidor** (3 segundos de wait): Destacar as seções disponíveis (pedidos, informações pessoais)
2. **E-commerce** (3 segundos de wait): Mostrar o catálogo completo com produtos
3. **Detalhes do Produto** (2 segundos de wait): Destacar preço, descrição e botão de adicionar ao carrinho

## Dados de Demo Disponíveis

- ✅ 10 consumidores finais cadastrados
- ✅ Usuário de teste: `juliana.ferreira@gmail.com` (senha: `demo123`)
- ✅ 7+ produtos publicados no e-commerce
- ✅ Portal do consumidor funcional

## Notas Importantes

- O cadastro de consumidor final não requer aprovação (conforme documentação)
- Consumidor pode se cadastrar via e-mail/senha ou OAuth (Facebook/Gmail)
- Portal mostra histórico de pedidos e informações pessoais

