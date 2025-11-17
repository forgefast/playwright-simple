# Teste Completo dos Fluxos Racco

Este arquivo contém os comandos a serem executados no teste completo dos fluxos Racco, cobrindo todas as telas de cada interface.

## Fluxos Validados

Fluxos que já foram validados e podem ser pulados durante os testes. Remova da lista quando quiser revalidar.

```yaml
validated_flows:
   - fluxo_01  # Critérios de Ingresso - Consumidor Final
   - fluxo_02  # Critérios de Ingresso - Revendedor (inclui escalonamento de níveis)
   # - fluxo_03  # Jornada de Treinamento - CORRIGIDO: Revendedor acessa Cursos no Portal
   # - fluxo_04  # Gamificação - CORRIGIDO: Módulo gamification está disponível como dependência
   # - fluxo_05  # Fluxo de Venda - Revendedor - CORRIGIDO: Revendedor acessa Pedidos no Portal
   # - fluxo_06  # Sistema de Comissões - CORRIGIDO: Removido clique em "Portal" (usuário já está no Portal)
   # - fluxo_07  # Portal do Consumidor - CORRIGIDO: Removido clique em "Portal" (usuário já está no Portal)
   # - fluxo_08  # Portal do Revendedor - CORRIGIDO: Removido clique em "Portal" (usuário já está no Portal)
   # - fluxo_09  # Gestão de Parceiros - CORRIGIDO: Nota sobre "Contatos" vs "Clientes"
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
pw-click selector "div.o_navbar_apps_menu button"
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

# Visualizar Categorias de Níveis (Escalonamento)
pw-click "Contatos"
pw-click "Configuração"
pw-click "Marcadores de contato"

# Visualizar Nível Bronze
pw-type "Bronze" into "Buscar"
pw-press "Enter"

# Visualizar Revendedores Bronze
pw-click "Contatos"
pw-type "Bronze" into "Buscar"
pw-press "Enter"

# Visualizar Nível Prata
pw-click "Contatos"
pw-click "Configuração"
pw-click "Marcadores de contato"
pw-type "Prata" into "Buscar"
pw-press "Enter"

# Visualizar Revendedores Prata
pw-click "Contatos"
pw-type "Prata" into "Buscar"
pw-press "Enter"

# Visualizar Nível Ouro
pw-click "Contatos"
pw-click "Configuração"
pw-click "Marcadores de contato"
pw-type "Ouro" into "Buscar"
pw-press "Enter"

# Visualizar Revendedores Ouro
pw-click "Contatos"
pw-type "Ouro" into "Buscar"
pw-press "Enter"

# Visualizar Nível Platinum
pw-click "Contatos"
pw-click "Configuração"
pw-click "Marcadores de contato"
pw-type "Platinum" into "Buscar"
pw-press "Enter"

# Visualizar Revendedores Platinum
pw-click "Contatos"
pw-type "Platinum" into "Buscar"
pw-press "Enter"

# Abrir Detalhes de um Revendedor
pw-click "Lucia Helena Santos"

# Logout
pw-click "Administrator"
pw-click "Sair"

# ========================================================================
# FLUXO 03: JORNADA DE TREINAMENTO
# ========================================================================
# Login como Revendedor
pw-click "Entrar"
pw-type "lucia.santos@exemplo.com" into "E-mail"
pw-type "demo123" into "Senha"
pw-submit "Entrar"

# Acessar Menu de Cursos (revendedor está no Portal, não tem menu Apps)
pw-click "Cursos"

# Abrir Curso "Introdução aos Produtos Racco"
pw-click "Introdução aos Produtos Racco"

# Abrir uma Aula (verificar qual aula está disponível no curso)
# Nota: O nome da aula pode variar, usar o primeiro link de aula disponível

# Voltar e Abrir Outro Curso
pw-click "Cursos"
pw-click "Técnicas de Vendas Racco"

# Logout
pw-click "Lucia Helena Santos"
pw-click "Sair"

# ========================================================================
# FLUXO 04: GAMIFICAÇÃO
# ========================================================================
# Login como Administrador
pw-click "Entrar"
pw-type "admin" into "E-mail"
pw-type "admin" into "Senha"
pw-submit "Entrar"

# Acessar Menu Apps
pw-click selector "div.o_navbar_apps_menu button"
# Aguardar dropdown do menu Apps abrir
# Acessar Definições (Settings) - pode estar no dropdown do menu Apps
# Alternativa: usar URL direta se menu não abrir: pw-goto "/odoo?action=base.action_res_config_settings"
pw-click "Definições"
# Acessar Gamification Tools (dentro de Definições)
# Nota: Módulo gamification está declarado como dependência em racco_demo
# Alternativa: Se menu não estiver visível, usar URL direta: pw-goto "/odoo/gamification"
pw-click "Gamification Tools"

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
# FLUXO 05: FLUXO DE VENDA - REVENDEDOR
# ========================================================================
# Login como Revendedor
pw-click "Entrar"
pw-type "lucia.santos@exemplo.com" into "E-mail"
pw-type "demo123" into "Senha"
pw-submit "Entrar"

# Acessar Menu de Pedidos (revendedor está no Portal, não tem menu Apps)
# Nota: Revendedor pode não ter acesso a Vendas/Pedidos no Portal
# Verificar se há link "Pedidos" no menu do Portal ou se precisa navegar diretamente
# Se não encontrar, pode usar URL direta: pw-goto "/my/orders"
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
# FLUXO 06: SISTEMA DE COMISSÕES
# ========================================================================
# Login como Administrador
pw-click "Entrar"
pw-type "admin" into "E-mail"
pw-type "admin" into "Senha"
pw-submit "Entrar"

# Acessar Menu Apps
pw-click selector "div.o_navbar_apps_menu button"
# Acessar Pedidos de Venda
pw-click "Vendas"
pw-click "Pedidos"

# Abrir um Pedido
pw-click "Pedido"

# Acessar Menu Apps
pw-click selector "div.o_navbar_apps_menu button"
# Voltar e Acessar Categorias
pw-click "Contatos"
pw-click "Configuração"
pw-click "Marcadores de contato"

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

# Nota: Revendedor já está no Portal após login, não precisa clicar em "Portal"
# Acessar Comissões (se disponível no Portal)
# Se não encontrar, pode usar URL direta: pw-goto "/my/commissions"
pw-click "Comissões"

# Logout
pw-click "Lucia Helena Santos"
pw-click "Sair"

# ========================================================================
# FLUXO 07: PORTAL DO CONSUMIDOR
# ========================================================================
# Login como Consumidor Final
pw-click "Entrar"
pw-type "juliana.ferreira@gmail.com" into "E-mail"
pw-type "demo123" into "Senha"
pw-submit "Entrar"

# Nota: Consumidor já está no Portal após login, não precisa clicar em "Portal"
# Visualizar Histórico de Pedidos
# Se não encontrar, pode usar URL direta: pw-goto "/my/orders"
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
# Navegar para o Portal usando "Minha conta" no dropdown do usuário
# Nota: Dropdown do usuário precisa ser aberto primeiro
pw-click "Juliana Ferreira"
# Aguardar dropdown abrir antes de clicar em "Minha conta"
pw-click "Minha conta"

# Logout
pw-click "Juliana Ferreira"
pw-click "Sair"

# ========================================================================
# FLUXO 08: PORTAL DO REVENDEDOR
# ========================================================================
# Login como Revendedor
pw-click "Entrar"
pw-type "lucia.santos@exemplo.com" into "E-mail"
pw-type "demo123" into "Senha"
pw-submit "Entrar"

# Nota: Revendedor já está no Portal após login, não precisa clicar em "Portal"
# Acessar Produtos Disponíveis
pw-click "Loja"

# Visualizar Detalhes de um Produto
pw-click "Batom Matte Rouge"

# Acessar Pedidos (voltar ao Portal se necessário)
# Se estiver na Loja, usar breadcrumb ou navegar diretamente
# Se não encontrar, pode usar URL direta: pw-goto "/my/orders"
pw-click "Pedidos"

# Acessar Comissões
# Se não encontrar, pode usar URL direta: pw-goto "/my/commissions"
pw-click "Comissões"

# Visualizar Informações da Rede (se disponível)
# Se não encontrar, pode usar URL direta: pw-goto "/my/network"
pw-click "Rede"

# Logout
pw-click "Lucia Helena Santos"
pw-click "Sair"

# ========================================================================
# FLUXO 09: GESTÃO DE PARCEIROS
# ========================================================================
# Login como Administrador
pw-click "Entrar"
pw-type "admin" into "E-mail"
pw-type "admin" into "Senha"
pw-submit "Entrar"

# Acessar Menu Apps
pw-click selector "div.o_navbar_apps_menu button"
# Acessar Lista de Contatos (que inclui clientes, revendedores, etc.)
pw-click "Contatos"
# Nota: "Contatos" já mostra todos os parceiros. Usar filtros de busca para filtrar por tipo

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
pw-click "Marcadores de contato"
```
