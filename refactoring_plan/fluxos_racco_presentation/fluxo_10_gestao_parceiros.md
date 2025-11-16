# Fluxo 10: Gestão de Parceiros

## Descrição
Demonstra a gestão completa de parceiros no sistema Racco, mostrando diferentes perfis (Colaboradores, Consumidores, Revendedores, Lojas, Promotores, CDs, Diretor) e filtros.

## Pré-requisitos
- Usuário admin: `admin` (senha: `admin`)
- Dados demo: 33 parceiros de diferentes perfis
- Módulo `racco_demo` instalado

## Menu de Acesso
- Clientes: **Contatos > Clientes**
- Categorias: **Contatos > Categorias**

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

### 2. Acessar Lista de Clientes
**Descrição**: Ver todos os parceiros cadastrados

**Comandos playwright-simple**:
```bash
pw-click "Contatos"
subtitle "Acessando menu de contatos"
audio-step "Acessando o menu de contatos"
wait 1.0

pw-click "Clientes"
subtitle "Acessando lista de clientes"
audio-step "Aqui estão todos os parceiros cadastrados no sistema, incluindo colaboradores, consumidores, revendedores e outros perfis"
wait 2.0
```

**Wait necessário**: 2 segundos para carregar lista

### 3. Visualizar Todos os Parceiros
**Descrição**: Mostrar lista completa

**Comandos playwright-simple**:
```bash
subtitle "Lista completa de parceiros do sistema"
audio-step "O sistema possui 33 parceiros cadastrados, incluindo colaboradores, consumidores finais, revendedores em diferentes níveis, lojas multimarca, promotores, centros de distribuição e diretor de rede"
wait 3.0
```

**Wait necessário**: 3 segundos para destacar a lista

### 4. Filtrar por Colaboradores
**Descrição**: Mostrar apenas colaboradores

**Comandos playwright-simple**:
```bash
pw-type "Colaborador" into "Buscar"
subtitle "Filtrando colaboradores Racco"
audio-step "Colaboradores são funcionários CLT da empresa Racco"
wait 2.0
```

### 5. Filtrar por Consumidores Finais
**Descrição**: Mostrar consumidores finais

**Comandos playwright-simple**:
```bash
pw-type "Consumidor" into "Buscar"
subtitle "Filtrando consumidores finais"
audio-step "Consumidores finais são clientes que compram produtos para uso próprio"
wait 2.0
```

### 6. Filtrar por Revendedores
**Descrição**: Mostrar todos os revendedores

**Comandos playwright-simple**:
```bash
pw-type "Revendedor" into "Buscar"
subtitle "Filtrando revendedores"
audio-step "Revendedores são parceiros que vendem produtos e podem ter diferentes níveis: Bronze, Prata, Ouro e Platinum"
wait 2.0
```

### 7. Filtrar por Lojas Multimarca
**Descrição**: Mostrar lojas multimarca

**Comandos playwright-simple**:
```bash
pw-type "Multimarca" into "Buscar"
subtitle "Filtrando lojas multimarca"
audio-step "Lojas multimarca são estabelecimentos que revendem produtos Racco junto com outras marcas"
wait 2.0
```

### 8. Filtrar por Promotores
**Descrição**: Mostrar promotores de vendas

**Comandos playwright-simple**:
```bash
pw-type "Promotor" into "Buscar"
subtitle "Filtrando promotores de vendas"
audio-step "Promotores de vendas são profissionais que trabalham em pontos de venda"
wait 2.0
```

### 9. Filtrar por Centros de Distribuição
**Descrição**: Mostrar CDs

**Comandos playwright-simple**:
```bash
pw-type "Distribuição" into "Buscar"
subtitle "Filtrando centros de distribuição"
audio-step "Centros de distribuição são responsáveis pelo estoque e distribuição de produtos"
wait 2.0
```

### 10. Filtrar por Diretor de Rede
**Descrição**: Mostrar diretor de rede

**Comandos playwright-simple**:
```bash
pw-type "Diretor" into "Buscar"
subtitle "Filtrando diretor de rede"
audio-step "Diretor de rede gerencia grandes redes de revendedores"
wait 2.0
```

### 11. Abrir Detalhes de um Parceiro
**Descrição**: Ver informações detalhadas

**Comandos playwright-simple**:
```bash
pw-type "Lucia" into "Buscar"
wait 1.0
pw-click "Lucia Helena Santos"
subtitle "Visualizando detalhes do parceiro"
audio-step "Ao abrir um parceiro, podemos ver todas as informações: contato, endereço, categoria, nível e histórico"
wait 2.0
```

### 12. Visualizar Categorias de Parceiros
**Descrição**: Ver todas as categorias disponíveis

**Comandos playwright-simple**:
```bash
pw-click "Categorias"
subtitle "Acessando categorias de parceiros"
audio-step "Aqui estão todas as categorias de parceiros disponíveis no sistema"
wait 2.0
```

## Comandos de Terminal Completos

```bash
# 1. Iniciar recorder
cd /home/gabriel/softhill/playwright-simple
playwright-simple record fluxo_10_gestao_parceiros.yaml --url http://localhost:18069

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
subtitle "Acessando menu de contatos"
audio-step "Acessando o menu de contatos"
wait 1.0
pw-click "Clientes"
subtitle "Acessando lista de clientes"
audio-step "Aqui estão todos os parceiros cadastrados no sistema, incluindo colaboradores, consumidores, revendedores e outros perfis"
wait 2.0
subtitle "Lista completa de parceiros do sistema"
audio-step "O sistema possui 33 parceiros cadastrados, incluindo colaboradores, consumidores finais, revendedores em diferentes níveis, lojas multimarca, promotores, centros de distribuição e diretor de rede"
wait 3.0
pw-type "Colaborador" into "Buscar"
subtitle "Filtrando colaboradores Racco"
audio-step "Colaboradores são funcionários CLT da empresa Racco"
wait 2.0
pw-type "Consumidor" into "Buscar"
subtitle "Filtrando consumidores finais"
audio-step "Consumidores finais são clientes que compram produtos para uso próprio"
wait 2.0
pw-type "Revendedor" into "Buscar"
subtitle "Filtrando revendedores"
audio-step "Revendedores são parceiros que vendem produtos e podem ter diferentes níveis: Bronze, Prata, Ouro e Platinum"
wait 2.0
pw-type "Multimarca" into "Buscar"
subtitle "Filtrando lojas multimarca"
audio-step "Lojas multimarca são estabelecimentos que revendem produtos Racco junto com outras marcas"
wait 2.0
pw-type "Promotor" into "Buscar"
subtitle "Filtrando promotores de vendas"
audio-step "Promotores de vendas são profissionais que trabalham em pontos de venda"
wait 2.0
pw-type "Distribuição" into "Buscar"
subtitle "Filtrando centros de distribuição"
audio-step "Centros de distribuição são responsáveis pelo estoque e distribuição de produtos"
wait 2.0
pw-type "Diretor" into "Buscar"
subtitle "Filtrando diretor de rede"
audio-step "Diretor de rede gerencia grandes redes de revendedores"
wait 2.0
pw-type "Lucia" into "Buscar"
wait 1.0
pw-click "Lucia Helena Santos"
subtitle "Visualizando detalhes do parceiro"
audio-step "Ao abrir um parceiro, podemos ver todas as informações: contato, endereço, categoria, nível e histórico"
wait 2.0
pw-click "Categorias"
subtitle "Acessando categorias de parceiros"
audio-step "Aqui estão todas as categorias de parceiros disponíveis no sistema"
wait 2.0
save
exit
```

## Pontos de Atenção

1. **Lista Completa** (3 segundos de wait): Destacar todos os tipos de parceiros
2. **Filtros por Perfil** (2 segundos cada): Mostrar cada tipo de parceiro
3. **Detalhes do Parceiro** (2 segundos de wait): Destacar informações disponíveis

## Dados de Demo Disponíveis

- ✅ 33 parceiros cadastrados:
  - 3 Colaboradores Racco
  - 10 Consumidores Finais
  - 15 Revendedores (4 Bronze, 4 Prata, 4 Ouro, 3 Platinum)
  - 3 Lojas Multimarca
  - 2 Promotores de Vendas
  - 2 Centros de Distribuição
  - 1 Diretor de Rede
- ✅ Categorias configuradas para cada perfil

## Notas Importantes

- Cada parceiro tem uma categoria específica
- Revendedores têm níveis adicionais (Bronze, Prata, Ouro, Platinum)
- Sistema permite filtrar por categoria, nível, cidade, estado
- Parceiros podem ter diferentes permissões e acessos conforme perfil

