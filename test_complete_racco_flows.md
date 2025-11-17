# Teste Completo dos Fluxos Racco

Este arquivo contém os comandos a serem executados no teste completo dos fluxos Racco, cobrindo todas as telas de cada interface.

## Fluxos Validados

Fluxos que já foram validados e podem ser pulados durante os testes. Remova da lista quando quiser revalidar.

```yaml
validated_flows:
   - fluxo_01  # Critérios de Ingresso - Consumidor Final
   - fluxo_02  # Critérios de Ingresso - Revendedor
  # - fluxo_03  # Escalonamento de Níveis
  # - fluxo_04  # Jornada de Treinamento
  # - fluxo_05  # Gamificação
  # - fluxo_06  # Fluxo de Venda - Revendedor
  # - fluxo_07  # Sistema de Comissões
  # - fluxo_08  # Portal do Consumidor
  # - fluxo_09  # Portal do Revendedor
  # - fluxo_10  # Gestão de Parceiros
```

## Comandos de Terminal Completos

```bash
# ========================================================================
# FLUXO 01: CRITÉRIOS DE INGRESSO - CONSUMIDOR FINAL
# ========================================================================
# Login como Consumidor Final
pw-click "Entrar"
pw-type "juliana.ferreira@gmail.com" into "E-mail"
pw-type "demo123" into "Senha"
pw-submit "Entrar"

# Acessar E-commerce
pw-click "Loja"

# Visualizar Detalhes de um Produto
pw-click "Batom Matte Rouge"

# Logout
pw-click "Juliana Ferreira"
pw-click "Sair"

# ========================================================================
# FLUXO 02: CRITÉRIOS DE INGRESSO - REVENDEDOR
# ========================================================================
# Login como Administrador
pw-click "Entrar"
pw-type "admin" into "E-mail"
pw-type "admin" into "Senha"
pw-submit "Entrar"

# Acessar Menu Apps
pw-click selector "button.o_grid_apps_menu__button"
# Acessar Contatos (já mostra a lista de clientes/parceiros)
pw-click "Contatos"

# Filtrar por Revendedor Bronze usando o filtro criado
pw-click selector ".o_searchview_dropdown_toggler"
pw-click "Revendedor Bronze"

# Filtrar por Revendedor Prata usando o filtro criado
# Desselecionar filtro anterior e selecionar novo
pw-click selector ".o_searchview_dropdown_toggler"
pw-click selector ".o_searchview_dropdown_toggler"
pw-click "Revendedor Bronze"
pw-click "Revendedor Prata"

# Filtrar por Revendedor Ouro usando o filtro criado
# Desselecionar filtro anterior e selecionar novo
pw-click selector ".o_searchview_dropdown_toggler"
pw-click selector ".o_searchview_dropdown_toggler"
pw-click "Revendedor Prata"
pw-click "Revendedor Ouro"

# Filtrar por Revendedor Platinum usando o filtro criado
# Desselecionar filtro anterior e selecionar novo
pw-click selector ".o_searchview_dropdown_toggler"
pw-click selector ".o_searchview_dropdown_toggler"
pw-click "Revendedor Ouro"
pw-click "Revendedor Platinum"

# Logout
pw-click "Administrator"
pw-click "Sair"

# ========================================================================
# FLUXO 03: ESCALONAMENTO DE NÍVEIS
# ========================================================================
# Login como Administrador
pw-click "Entrar"
pw-type "admin" into "E-mail"
pw-type "admin" into "Senha"
pw-submit "Entrar"

# Acessar Menu Apps
pw-click selector "button.o_grid_apps_menu__button"
# Acessar Categorias de Níveis
pw-click "Contatos"
pw-click "Configuração"
pw-click "Marcadores de contato"

# Visualizar Nível Bronze
pw-click selector ".o_searchview_dropdown_toggler"
pw-type "Bronze" into "Buscar"

# Visualizar Revendedores Bronze
pw-click "Clientes"
pw-click selector ".o_searchview_dropdown_toggler"
pw-type "Bronze" into "Buscar"

# Visualizar Nível Prata
pw-click "Contatos"
pw-click "Configuração"
pw-click "Contact Tags"
pw-click selector ".o_searchview_dropdown_toggler"
pw-type "Prata" into "Buscar"

# Visualizar Revendedores Prata
pw-click "Clientes"
pw-click selector ".o_searchview_dropdown_toggler"
pw-type "Prata" into "Buscar"

# Visualizar Nível Ouro
pw-click "Contatos"
pw-click "Configuração"
pw-click "Contact Tags"
pw-click selector ".o_searchview_dropdown_toggler"
pw-type "Ouro" into "Buscar"

# Visualizar Revendedores Ouro
pw-click "Clientes"
pw-click selector ".o_searchview_dropdown_toggler"
pw-type "Ouro" into "Buscar"

# Visualizar Nível Platinum
pw-click "Contatos"
pw-click "Configuração"
pw-click "Contact Tags"
pw-click selector ".o_searchview_dropdown_toggler"
pw-type "Platinum" into "Buscar"

# Visualizar Revendedores Platinum
pw-click "Clientes"
pw-click selector ".o_searchview_dropdown_toggler"
pw-type "Platinum" into "Buscar"

# Abrir Detalhes de um Revendedor
pw-click "Lucia Helena Santos"

# Logout
pw-click "Administrator"
pw-click "Sair"

# ========================================================================
# FLUXO 04: JORNADA DE TREINAMENTO
# ========================================================================
# Login como Revendedor
pw-click "Entrar"
pw-type "lucia.santos@exemplo.com" into "E-mail"
pw-type "demo123" into "Senha"
pw-submit "Entrar"

# Acessar Menu Apps
pw-click selector "button.o_grid_apps_menu__button"
# Acessar Menu de Cursos
pw-click "Website"
pw-click "Cursos"

# Abrir Curso "Introdução aos Produtos Racco"
pw-click "Introdução aos Produtos Racco"

# Abrir uma Aula
pw-click "Bem-vindo ao Curso de Produtos Racco"

# Voltar e Abrir Outro Curso
pw-click "Cursos"
pw-click "Técnicas de Vendas Racco"

# Logout
pw-click "Lucia Helena Santos"
pw-click "Sair"

# ========================================================================
# FLUXO 05: GAMIFICAÇÃO
# ========================================================================
# Login como Administrador
pw-click "Entrar"
pw-type "admin" into "E-mail"
pw-type "admin" into "Senha"
pw-submit "Entrar"

# Acessar Menu Apps
pw-click selector "button.o_grid_apps_menu__button"
# Acessar Menu de Gamificação
pw-click "Gamificação"

# Visualizar Badges Disponíveis
pw-click "Badges"

# Filtrar Badges de Vendas
pw-type "Venda" into "Buscar"

# Filtrar Badges de Treinamento
pw-type "Treinamento" into "Buscar"

# Filtrar Badges de Rede
pw-type "Rede" into "Buscar"

# Acessar Desafios
pw-click "Desafios"

# Abrir Detalhes de um Desafio
pw-click "Desafio Mensal de Vendas"

# Logout
pw-click "Administrator"
pw-click "Sair"

# ========================================================================
# FLUXO 06: FLUXO DE VENDA - REVENDEDOR
# ========================================================================
# Login como Revendedor
pw-click "Entrar"
pw-type "lucia.santos@exemplo.com" into "E-mail"
pw-type "demo123" into "Senha"
pw-submit "Entrar"

# Acessar Menu Apps
pw-click selector "button.o_grid_apps_menu__button"
# Acessar Menu de Pedidos
pw-click "Vendas"
pw-click "Pedidos"

# Criar Novo Pedido
pw-click "Criar"

# Selecionar Cliente
pw-type "Juliana" into "Cliente"
pw-click "Juliana Ferreira"

# Adicionar Primeiro Produto
pw-click "Adicionar linha"
pw-type "Batom" into "Produto"
pw-click "Batom Matte Rouge"
pw-type "10" into "Quantidade"

# Adicionar Segundo Produto
pw-click "Adicionar linha"
pw-type "Base" into "Produto"
pw-click "Base Líquida Perfect Skin"
pw-type "5" into "Quantidade"

# Adicionar Terceiro Produto
pw-click "Adicionar linha"
pw-type "Perfume" into "Produto"
pw-click "Perfume Essence Woman"
pw-type "2" into "Quantidade"

# Salvar Pedido
pw-click "Salvar"

# Confirmar Pedido
pw-click "Confirmar"

# Logout
pw-click "Lucia Helena Santos"
pw-click "Sair"

# ========================================================================
# FLUXO 07: SISTEMA DE COMISSÕES
# ========================================================================
# Login como Administrador
pw-click "Entrar"
pw-type "admin" into "E-mail"
pw-type "admin" into "Senha"
pw-submit "Entrar"

# Acessar Menu Apps
pw-click selector "button.o_grid_apps_menu__button"
# Acessar Pedidos de Venda
pw-click "Vendas"
pw-click "Pedidos"

# Abrir um Pedido
pw-click "Pedido"

# Acessar Menu Apps
pw-click selector "button.o_grid_apps_menu__button"
# Voltar e Acessar Categorias
pw-click "Contatos"
pw-click "Configuração"
pw-click "Contact Tags"

# Visualizar Nível Bronze e Comissão
pw-click selector ".o_searchview_dropdown_toggler"
pw-type "Bronze" into "Buscar"

# Visualizar Nível Prata e Comissão
pw-click selector ".o_searchview_dropdown_toggler"
pw-type "Prata" into "Buscar"

# Visualizar Nível Ouro e Comissão
pw-click selector ".o_searchview_dropdown_toggler"
pw-type "Ouro" into "Buscar"

# Visualizar Nível Platinum e Comissão
pw-click selector ".o_searchview_dropdown_toggler"
pw-type "Platinum" into "Buscar"

# Login como Revendedor para Ver Comissões
pw-click "Administrator"
pw-click "Sair"
pw-click "Entrar"
pw-type "lucia.santos@exemplo.com" into "E-mail"
pw-type "demo123" into "Senha"
pw-submit "Entrar"

# Acessar Portal do Revendedor
pw-click "Portal"

# Acessar Comissões
pw-click "Comissões"

# Logout
pw-click "Lucia Helena Santos"
pw-click "Sair"

# ========================================================================
# FLUXO 08: PORTAL DO CONSUMIDOR
# ========================================================================
# Login como Consumidor Final
pw-click "Entrar"
pw-type "juliana.ferreira@gmail.com" into "E-mail"
pw-type "demo123" into "Senha"
pw-submit "Entrar"

# Acessar Portal do Consumidor
pw-click "Portal"

# Visualizar Histórico de Pedidos
pw-click "Pedidos"

# Abrir um Pedido
pw-click "Pedido"

# Acessar E-commerce
pw-click "Loja"

# Filtrar Produtos por Categoria
pw-click "Maquiagem"

# Visualizar Detalhes de um Produto
pw-click "Batom Matte Rouge"

# Voltar ao Portal e acessar Informações Pessoais
pw-click "Portal"
pw-click "Minha Conta"

# Logout
pw-click "Juliana Ferreira"
pw-click "Sair"

# ========================================================================
# FLUXO 09: PORTAL DO REVENDEDOR
# ========================================================================
# Login como Revendedor
pw-click "Entrar"
pw-type "lucia.santos@exemplo.com" into "E-mail"
pw-type "demo123" into "Senha"
pw-submit "Entrar"

# Acessar Portal do Revendedor
pw-click "Portal"

# Acessar Produtos Disponíveis
pw-click "Loja"

# Visualizar Detalhes de um Produto
pw-click "Batom Matte Rouge"

# Acessar Pedidos
pw-click "Portal"
pw-click "Pedidos"

# Acessar Comissões
pw-click "Comissões"

# Visualizar Informações da Rede (se disponível)
pw-click "Rede"

# Logout
pw-click "Lucia Helena Santos"
pw-click "Sair"

# ========================================================================
# FLUXO 10: GESTÃO DE PARCEIROS
# ========================================================================
# Login como Administrador
pw-click "Entrar"
pw-type "admin" into "E-mail"
pw-type "admin" into "Senha"
pw-submit "Entrar"

# Acessar Menu Apps
pw-click selector "button.o_grid_apps_menu__button"
# Acessar Lista de Clientes
pw-click "Contatos"
pw-click "Clientes"

# Filtrar por Colaboradores
pw-type "Colaborador" into "Buscar"

# Filtrar por Consumidores Finais
pw-type "Consumidor" into "Buscar"

# Filtrar por Revendedores
pw-type "Revendedor" into "Buscar"

# Filtrar por Lojas Multimarca
pw-type "Multimarca" into "Buscar"

# Filtrar por Promotores
pw-type "Promotor" into "Buscar"

# Filtrar por Centros de Distribuição
pw-type "Distribuição" into "Buscar"

# Filtrar por Diretor de Rede
pw-type "Diretor" into "Buscar"

# Abrir Detalhes de um Parceiro
pw-type "Lucia" into "Buscar"
pw-click "Lucia Helena Santos"

# Visualizar Categorias de Parceiros
pw-click "Contatos"
pw-click "Configuração"
pw-click "Contact Tags"
```
