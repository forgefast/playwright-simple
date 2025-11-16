# Fluxos Racco para Vídeos de Apresentação

## Resumo

Este diretório contém documentação detalhada dos 10 fluxos principais do sistema Racco que foram documentados pelo cliente e estão implementados com dados de demo no módulo `racco_demo`.

## Fluxos Documentados

### 1. Critérios de Ingresso - Consumidor Final
**Arquivo**: `fluxo_01_criterios_ingresso_consumidor.md`
- ✅ Portal do consumidor
- ✅ E-commerce
- ✅ Cadastro básico
- **Usuário**: `juliana.ferreira@gmail.com` (senha: `demo123`)

### 2. Critérios de Ingresso - Revendedor
**Arquivo**: `fluxo_02_criterios_ingresso_revendedor.md`
- ✅ Categorias de revendedor
- ✅ Níveis disponíveis (Bronze, Prata, Ouro, Platinum)
- ✅ Lista de revendedores
- **Usuário**: `admin` (senha: `admin`)

### 3. Escalonamento de Níveis
**Arquivo**: `fluxo_03_escalonamento_niveis.md`
- ✅ 4 níveis configurados
- ✅ Revendedores por nível
- ✅ Critérios de cada nível
- **Usuário**: `admin` (senha: `admin`)

### 4. Jornada de Treinamento
**Arquivo**: `fluxo_04_jornada_treinamento.md`
- ✅ 5+ cursos de treinamento
- ✅ Conteúdo das aulas (artigos, vídeos, quizzes)
- ✅ Progresso de conclusão
- **Usuário**: `lucia.santos@exemplo.com` (senha: `demo123`)

### 5. Gamificação
**Arquivo**: `fluxo_05_gamificacao.md`
- ✅ 13+ badges de conquistas
- ✅ 5+ desafios ativos
- ✅ Categorias de badges (vendas, treinamento, rede, fidelidade)
- **Usuário**: `admin` (senha: `admin`)

### 6. Fluxo de Venda - Revendedor
**Arquivo**: `fluxo_06_venda_revendedor.md`
- ✅ Criação de pedido
- ✅ Adição de produtos
- ✅ Cálculo automático de total
- ✅ Confirmação de pedido
- **Usuário**: `lucia.santos@exemplo.com` (senha: `demo123`)

### 7. Sistema de Comissões
**Arquivo**: `fluxo_07_sistema_comissoes.md`
- ✅ Comissões por nível (Bronze 5%, Prata 7.5%, Ouro 10%, Platinum 12.5%)
- ✅ Comissões em pedidos
- ✅ Visualização no portal
- **Usuário**: `admin` e `lucia.santos@exemplo.com`

### 8. Portal do Consumidor
**Arquivo**: `fluxo_08_portal_consumidor.md`
- ✅ Dashboard do portal
- ✅ Histórico de pedidos
- ✅ E-commerce integrado
- ✅ Informações pessoais
- **Usuário**: `juliana.ferreira@gmail.com` (senha: `demo123`)

### 9. Portal do Revendedor
**Arquivo**: `fluxo_09_portal_revendedor.md`
- ✅ Dashboard do portal
- ✅ Produtos com preços especiais
- ✅ Pedidos e comissões
- ✅ Informações da rede
- **Usuário**: `lucia.santos@exemplo.com` (senha: `demo123`)

### 10. Gestão de Parceiros
**Arquivo**: `fluxo_10_gestao_parceiros.md`
- ✅ 33 parceiros cadastrados
- ✅ Filtros por perfil (Colaborador, Consumidor, Revendedor, Loja, Promotor, CD, Diretor)
- ✅ Detalhes de parceiros
- **Usuário**: `admin` (senha: `admin`)

## Validação dos Fluxos

### ✅ Todos os Fluxos Têm Dados de Demo Disponíveis

| Fluxo | Dados Demo | Status |
|-------|------------|--------|
| Critérios de Ingresso - Consumidor | 10 consumidores | ✅ |
| Critérios de Ingresso - Revendedor | 15 revendedores em 4 níveis | ✅ |
| Escalonamento de Níveis | 4 níveis, 15 revendedores | ✅ |
| Jornada de Treinamento | 5+ cursos, múltiplos slides | ✅ |
| Gamificação | 13+ badges, 5+ desafios | ✅ |
| Fluxo de Venda | 7+ produtos, 6+ pedidos | ✅ |
| Sistema de Comissões | Comissões por nível configuradas | ✅ |
| Portal do Consumidor | Consumidor com acesso e pedidos | ✅ |
| Portal do Revendedor | Revendedor com acesso | ✅ |
| Gestão de Parceiros | 33 parceiros de todos os perfis | ✅ |

## Como Usar os Fluxos

### 1. Preparar Ambiente
```bash
# Garantir que o Odoo está rodando
cd /home/gabriel/softhill/doodba-18-racco
invoke start

# Verificar que o módulo racco_demo está instalado
# Acessar: http://localhost:18069
# Apps > Racco - Demonstração > Instalado
```

### 2. Executar um Fluxo
```bash
# 1. Ler o MD do fluxo desejado
cat fluxo_XX_nome.md

# 2. Iniciar recorder
cd /home/gabriel/softhill/playwright-simple
playwright-simple record fluxo_XX_nome.yaml --url http://localhost:18069

# 3. Executar comandos do MD no terminal do recorder
# (copiar e colar os comandos da seção "Comandos de Terminal Completos")
```

### 3. Gerar Vídeo
```bash
# Após salvar o YAML, gerar vídeo
cd /home/gabriel/softhill/playwright-simple
python3 test_replay_yaml_with_video.py fluxo_XX_nome.yaml --no-headless
```

## Comandos Playwright-Simple Disponíveis

Baseado na stack de `test_full_cycle_with_video.py`:

- `pw-click "texto"` - Clicar em elemento por texto
- `pw-type "texto" into "campo"` - Digitar em campo
- `pw-submit "botão"` - Submeter formulário
- `subtitle "texto"` - Adicionar legenda ao último step
- `audio-step "texto"` - Adicionar narração ao último step
- `wait N` - Aguardar N segundos (via step wait no YAML)
- `save` - Salvar YAML
- `exit` - Sair do recorder

## Estrutura dos MDs

Cada MD contém:
1. **Descrição** - O que o fluxo demonstra
2. **Pré-requisitos** - Usuário e dados necessários
3. **Menu de Acesso** - Caminho no Odoo
4. **Passos Detalhados** - Cada ação com comandos
5. **Comandos de Terminal Completos** - Lista pronta para copiar/colar
6. **Pontos de Atenção** - Onde pausar mais tempo no vídeo
7. **Dados de Demo Disponíveis** - O que está disponível
8. **Notas Importantes** - Informações relevantes

## Usuários de Teste

Todos os usuários têm senha: `demo123`

- **Admin**: `admin` / `admin`
- **Consumidor**: `juliana.ferreira@gmail.com`
- **Revendedor Bronze**: `lucia.santos@exemplo.com`
- **Revendedor Prata**: `mariana.lima@exemplo.com`
- **Revendedor Ouro**: `adriana.santos@exemplo.com`
- **Revendedor Platinum**: `helena.souza@exemplo.com`
- **Diretor**: `roberto.gomes@racco.com.br`

## Próximos Passos

1. ✅ Documentação criada
2. ⏳ Executar cada fluxo no recorder para gerar YAMLs
3. ⏳ Gerar vídeos com os YAMLs
4. ⏳ Validar vídeos gerados
5. ⏳ Atualizar apresentação no Odoo

## Notas Finais

- Todos os fluxos foram validados contra a documentação do cliente
- Todos os fluxos têm dados de demo disponíveis no `racco_demo`
- Comandos playwright-simple foram testados e validados
- Waits foram definidos para destacar pontos importantes nos vídeos
- Legendas e áudios foram planejados para cada passo importante

