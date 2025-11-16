# Fluxo 02: Critérios de Ingresso - Revendedor

## Descrição
Demonstra os critérios de ingresso para revendedores, mostrando as categorias de revendedor disponíveis e os níveis (Bronze, Prata, Ouro, Platinum).

## Pré-requisitos
- Usuário admin: `admin` (senha: `admin`)
- Dados demo: 15 revendedores em 4 níveis
- Módulo `racco_demo` instalado

## Menu de Acesso
- Categorias: **Contatos > Categorias**
- Clientes: **Contatos > Clientes**

## Passos Detalhados

### 1. Login como Administrador
**Descrição**: Fazer login como admin para visualizar categorias

**Comandos playwright-simple**:
```bash
pw-click "Entrar"
subtitle "Acessando a tela de login"
audio-step "Acessando a tela de login"
wait 1.0

pw-type "admin" into "E-mail"
subtitle "Digitando email do administrador"
audio-step "Digitando email do administrador"
wait 0.5

pw-type "admin" into "Senha"
subtitle "Digitando senha"
audio-step "Digitando senha"
wait 0.5

pw-submit "Entrar"
subtitle "Fazendo login como administrador"
audio-step "Fazendo login como administrador"
wait 2.0
```

### 2. Acessar Categorias de Parceiros
**Descrição**: Navegar para ver as categorias de revendedor

**Comandos playwright-simple**:
```bash
pw-click "Contatos"
subtitle "Acessando o menu de contatos"
audio-step "Acessando o menu de contatos"
wait 1.0

pw-click "Categorias"
subtitle "Acessando categorias de parceiros"
audio-step "Aqui estão as categorias de parceiros do sistema, incluindo os níveis de revendedor"
wait 2.0
```

**Wait necessário**: 2 segundos para visualizar todas as categorias

### 3. Visualizar Categorias de Revendedor
**Descrição**: Mostrar as categorias de revendedor disponíveis

**Comandos playwright-simple**:
```bash
subtitle "Categorias de revendedor: Bronze, Prata, Ouro e Platinum"
audio-step "O sistema possui quatro níveis de revendedor: Bronze, Prata, Ouro e Platinum"
wait 3.0
```

**Wait necessário**: 3 segundos para destacar os níveis

### 4. Filtrar por Revendedor Bronze
**Descrição**: Buscar e mostrar revendedores Bronze

**Comandos playwright-simple**:
```bash
pw-type "Bronze" into "Buscar"
subtitle "Filtrando revendedores Bronze"
audio-step "Vamos ver os revendedores do nível Bronze, que é o nível inicial"
wait 2.0
```

**Wait necessário**: 2 segundos para carregar resultados

### 5. Visualizar Revendedores Bronze
**Descrição**: Mostrar lista de revendedores Bronze

**Comandos playwright-simple**:
```bash
subtitle "Revendedores do nível Bronze cadastrados no sistema"
audio-step "Aqui estão os revendedores Bronze, que são iniciantes no sistema"
wait 2.0
```

### 6. Filtrar por Revendedor Prata
**Descrição**: Mostrar revendedores Prata

**Comandos playwright-simple**:
```bash
pw-type "Prata" into "Buscar"
subtitle "Filtrando revendedores Prata"
audio-step "Agora vamos ver os revendedores Prata, nível intermediário"
wait 2.0
```

### 7. Filtrar por Revendedor Ouro
**Descrição**: Mostrar revendedores Ouro

**Comandos playwright-simple**:
```bash
pw-type "Ouro" into "Buscar"
subtitle "Filtrando revendedores Ouro"
audio-step "Revendedores Ouro são experientes e têm maiores benefícios"
wait 2.0
```

### 8. Filtrar por Revendedor Platinum
**Descrição**: Mostrar revendedores Platinum

**Comandos playwright-simple**:
```bash
pw-type "Platinum" into "Buscar"
subtitle "Filtrando revendedores Platinum"
audio-step "Revendedores Platinum são o nível elite, com os maiores benefícios e comissões"
wait 2.0
```

### 9. Acessar Lista de Clientes
**Descrição**: Ver todos os revendedores cadastrados

**Comandos playwright-simple**:
```bash
pw-click "Clientes"
subtitle "Acessando lista de clientes"
audio-step "Aqui estão todos os parceiros cadastrados, incluindo revendedores"
wait 2.0
```

### 10. Filtrar Revendedores na Lista
**Descrição**: Filtrar para mostrar apenas revendedores

**Comandos playwright-simple**:
```bash
pw-type "Revendedor" into "Buscar"
subtitle "Filtrando apenas revendedores"
audio-step "Filtrando a lista para mostrar apenas revendedores de todos os níveis"
wait 2.0
```

## Comandos de Terminal Completos

```bash
# 1. Iniciar recorder
cd /home/gabriel/softhill/playwright-simple
playwright-simple record fluxo_02_revendedor.yaml --url http://localhost:18069

# 2. Executar comandos no terminal do recorder:
start
pw-click "Entrar"
subtitle "Acessando a tela de login"
audio-step "Acessando a tela de login"
wait 1.0
pw-type "admin" into "E-mail"
subtitle "Digitando email do administrador"
audio-step "Digitando email do administrador"
wait 0.5
pw-type "admin" into "Senha"
subtitle "Digitando senha"
audio-step "Digitando senha"
wait 0.5
pw-submit "Entrar"
subtitle "Fazendo login como administrador"
audio-step "Fazendo login como administrador"
wait 2.0
pw-click "Contatos"
subtitle "Acessando o menu de contatos"
audio-step "Acessando o menu de contatos"
wait 1.0
pw-click "Categorias"
subtitle "Acessando categorias de parceiros"
audio-step "Aqui estão as categorias de parceiros do sistema, incluindo os níveis de revendedor"
wait 2.0
subtitle "Categorias de revendedor: Bronze, Prata, Ouro e Platinum"
audio-step "O sistema possui quatro níveis de revendedor: Bronze, Prata, Ouro e Platinum"
wait 3.0
pw-type "Bronze" into "Buscar"
subtitle "Filtrando revendedores Bronze"
audio-step "Vamos ver os revendedores do nível Bronze, que é o nível inicial"
wait 2.0
subtitle "Revendedores do nível Bronze cadastrados no sistema"
audio-step "Aqui estão os revendedores Bronze, que são iniciantes no sistema"
wait 2.0
pw-type "Prata" into "Buscar"
subtitle "Filtrando revendedores Prata"
audio-step "Agora vamos ver os revendedores Prata, nível intermediário"
wait 2.0
pw-type "Ouro" into "Buscar"
subtitle "Filtrando revendedores Ouro"
audio-step "Revendedores Ouro são experientes e têm maiores benefícios"
wait 2.0
pw-type "Platinum" into "Buscar"
subtitle "Filtrando revendedores Platinum"
audio-step "Revendedores Platinum são o nível elite, com os maiores benefícios e comissões"
wait 2.0
pw-click "Clientes"
subtitle "Acessando lista de clientes"
audio-step "Aqui estão todos os parceiros cadastrados, incluindo revendedores"
wait 2.0
pw-type "Revendedor" into "Buscar"
subtitle "Filtrando apenas revendedores"
audio-step "Filtrando a lista para mostrar apenas revendedores de todos os níveis"
wait 2.0
save
exit
```

## Pontos de Atenção

1. **Categorias de Revendedor** (3 segundos de wait): Destacar os 4 níveis disponíveis
2. **Filtros por Nível** (2 segundos cada): Mostrar revendedores de cada nível
3. **Lista Completa** (2 segundos de wait): Mostrar todos os revendedores cadastrados

## Dados de Demo Disponíveis

- ✅ 4 categorias de revendedor: Bronze, Prata, Ouro, Platinum
- ✅ 15 revendedores distribuídos pelos níveis:
  - 4+ revendedores Bronze
  - 4+ revendedores Prata
  - 4+ revendedores Ouro
  - 3+ revendedores Platinum

## Notas Importantes

- Novo revendedor inicia no nível Bronze (conforme documentação)
- Cada nível tem critérios específicos de escalonamento
- Revendedores podem subir de nível automaticamente conforme critérios

