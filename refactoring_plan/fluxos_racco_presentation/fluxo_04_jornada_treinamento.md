# Fluxo 04: Jornada de Treinamento

## Descrição
Demonstra a jornada de treinamento do sistema Racco, mostrando os cursos disponíveis, conteúdo das aulas e progresso de conclusão.

## Pré-requisitos
- Usuário de teste: `lucia.santos@exemplo.com` (senha: `demo123`) - Revendedor Bronze
- Dados demo: 5+ cursos de treinamento com slides/aulas
- Módulo `racco_demo` instalado

## Menu de Acesso
- Cursos: **Website > Cursos**

## Passos Detalhados

### 1. Login como Revendedor
**Descrição**: Fazer login como revendedor para acessar cursos

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

### 2. Acessar Menu de Cursos
**Descrição**: Navegar para a seção de cursos

**Comandos playwright-simple**:
```bash
pw-click "Website"
subtitle "Acessando menu Website"
audio-step "Acessando o menu Website"
wait 1.0

pw-click "Cursos"
subtitle "Acessando cursos de treinamento"
audio-step "Aqui estão os cursos de treinamento disponíveis para revendedores"
wait 2.0
```

**Wait necessário**: 2 segundos para carregar lista de cursos

### 3. Visualizar Lista de Cursos
**Descrição**: Mostrar todos os cursos disponíveis

**Comandos playwright-simple**:
```bash
subtitle "Lista completa de cursos de treinamento"
audio-step "O sistema oferece diversos cursos para capacitação dos revendedores, incluindo introdução aos produtos, técnicas de vendas, gestão de clientes e sistema de comissões"
wait 3.0
```

**Wait necessário**: 3 segundos para destacar os cursos

### 4. Abrir Curso "Introdução aos Produtos Racco"
**Descrição**: Acessar o primeiro curso

**Comandos playwright-simple**:
```bash
pw-click "Introdução aos Produtos Racco"
subtitle "Abrindo curso Introdução aos Produtos Racco"
audio-step "Vamos ver o conteúdo do curso de introdução aos produtos"
wait 2.0
```

### 5. Visualizar Conteúdo do Curso
**Descrição**: Mostrar as aulas/slides do curso

**Comandos playwright-simple**:
```bash
subtitle "Conteúdo do curso com aulas, vídeos e quizzes"
audio-step "O curso contém várias aulas com diferentes formatos: artigos, vídeos e quizzes para testar o conhecimento"
wait 3.0
```

**Wait necessário**: 3 segundos para visualizar o conteúdo

### 6. Abrir uma Aula
**Descrição**: Clicar em uma aula para ver detalhes

**Comandos playwright-simple**:
```bash
pw-click "Bem-vindo ao Curso de Produtos Racco"
subtitle "Visualizando conteúdo da aula"
audio-step "Cada aula tem conteúdo detalhado, tempo estimado de conclusão e pode gerar certificado"
wait 2.0
```

### 7. Voltar e Abrir Outro Curso
**Descrição**: Ver outro curso disponível

**Comandos playwright-simple**:
```bash
pw-click "Cursos"
wait 1.0
pw-click "Técnicas de Vendas Racco"
subtitle "Abrindo curso Técnicas de Vendas"
audio-step "Este curso ensina técnicas eficazes para aumentar as vendas"
wait 2.0
```

### 8. Visualizar Progresso de Treinamento
**Descrição**: Mostrar progresso do revendedor nos cursos

**Comandos playwright-simple**:
```bash
subtitle "Progresso de conclusão dos cursos"
audio-step "O sistema acompanha o progresso do revendedor em cada curso, mostrando quais aulas foram concluídas"
wait 2.0
```

## Comandos de Terminal Completos

```bash
# 1. Iniciar recorder
cd /home/gabriel/softhill/playwright-simple
playwright-simple record fluxo_04_treinamento.yaml --url http://localhost:18069

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
pw-click "Website"
subtitle "Acessando menu Website"
audio-step "Acessando o menu Website"
wait 1.0
pw-click "Cursos"
subtitle "Acessando cursos de treinamento"
audio-step "Aqui estão os cursos de treinamento disponíveis para revendedores"
wait 2.0
subtitle "Lista completa de cursos de treinamento"
audio-step "O sistema oferece diversos cursos para capacitação dos revendedores, incluindo introdução aos produtos, técnicas de vendas, gestão de clientes e sistema de comissões"
wait 3.0
pw-click "Introdução aos Produtos Racco"
subtitle "Abrindo curso Introdução aos Produtos Racco"
audio-step "Vamos ver o conteúdo do curso de introdução aos produtos"
wait 2.0
subtitle "Conteúdo do curso com aulas, vídeos e quizzes"
audio-step "O curso contém várias aulas com diferentes formatos: artigos, vídeos e quizzes para testar o conhecimento"
wait 3.0
pw-click "Bem-vindo ao Curso de Produtos Racco"
subtitle "Visualizando conteúdo da aula"
audio-step "Cada aula tem conteúdo detalhado, tempo estimado de conclusão e pode gerar certificado"
wait 2.0
pw-click "Cursos"
wait 1.0
pw-click "Técnicas de Vendas Racco"
subtitle "Abrindo curso Técnicas de Vendas"
audio-step "Este curso ensina técnicas eficazes para aumentar as vendas"
wait 2.0
subtitle "Progresso de conclusão dos cursos"
audio-step "O sistema acompanha o progresso do revendedor em cada curso, mostrando quais aulas foram concluídas"
wait 2.0
save
exit
```

## Pontos de Atenção

1. **Lista de Cursos** (3 segundos de wait): Destacar todos os cursos disponíveis
2. **Conteúdo do Curso** (3 segundos de wait): Mostrar diferentes tipos de aulas (artigo, vídeo, quiz)
3. **Progresso** (2 segundos de wait): Destacar o acompanhamento de progresso

## Dados de Demo Disponíveis

- ✅ 5+ cursos de treinamento:
  - Introdução aos Produtos Racco
  - Técnicas de Vendas Racco
  - Gestão de Clientes e Relacionamento
  - Sistema de Comissões e Níveis
  - Como Usar o Portal do Revendedor
- ✅ Múltiplos slides/aulas por curso (artigos, vídeos, quizzes)
- ✅ Cursos publicados e acessíveis

## Notas Importantes

- Cursos podem ter diferentes formatos: artigos, vídeos, quizzes
- Sistema acompanha progresso de conclusão
- Algumas aulas podem gerar certificado
- Cursos são parte da gamificação (pontos e badges)

