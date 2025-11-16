# Quick Start - Playwright Simple Framework v2.0

Guia rápido para começar a usar a GUI do Playwright Simple.

## Pré-requisitos

- Python 3.11+
- Node.js 18+ e npm
- Playwright (será instalado automaticamente)

## Setup Rápido

### 1. Instalar Dependências

```bash
./setup.sh
```

Este script irá:
- Instalar dependências Python
- Instalar dependências do frontend
- Criar diretório para banco de dados
- Verificar instalação do Playwright

### 2. Iniciar Serviços

**Opção A: Modo Background (recomendado para uso)**
```bash
./start.sh
```

**Opção B: Modo Desenvolvimento (ver logs)**
```bash
./start-dev.sh
```

### 3. Acessar a GUI

Abra seu navegador em:
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/api/docs

## Parar os Serviços

Se usou `./start.sh`:
- Pressione `Ctrl+C` no terminal

Se usou `./start-dev.sh`:
- Feche os terminais ou pressione `Ctrl+C` em cada um

## Primeiros Passos

### 1. Criar um Projeto

1. Acesse http://localhost:3000
2. Clique em "Novo Projeto" (ou use a API)
3. Preencha nome e descrição

### 2. Criar um Teste

**Opção A: Via GUI (Editor Visual)**
1. Vá para "Testes" → "Novo Teste"
2. Use a paleta de ações para adicionar steps
3. Arraste e solte para reordenar
4. Clique em "Salvar"

**Opção B: Via Gravação**
1. Vá para "Gravar"
2. Clique em "Iniciar Gravação"
3. Navegue pelo site (suas ações serão capturadas)
4. Clique em "Parar Gravação"
5. Revise os steps capturados
6. Salve como teste

### 3. Executar um Teste

1. Vá para a lista de testes
2. Clique no teste desejado
3. Clique em "Executar Teste"
4. Acompanhe a execução em tempo real

## Estrutura de Diretórios

```
playwright-simple/
├── data/                    # Banco de dados SQLite
├── logs/                    # Logs da API e frontend
├── framework/              # Código do framework
│   ├── domain/            # Camada de domínio
│   ├── application/       # Camada de aplicação
│   ├── infrastructure/    # Camada de infraestrutura
│   └── interfaces/        # Camada de interface (API, CLI)
├── gui/                    # Frontend React
│   └── frontend/
└── docs/                   # Documentação
```

## Troubleshooting

### Porta já em uso

```bash
# Liberar porta 8000 (API)
lsof -ti:8000 | xargs kill -9

# Liberar porta 3000 (Frontend)
lsof -ti:3000 | xargs kill -9
```

### Erro ao instalar dependências

```bash
# Python
pip install --upgrade pip
pip install -r requirements.txt

# Node.js
cd gui/frontend
npm install
```

### Banco de dados não criado

O banco é criado automaticamente na primeira execução em `data/playwright_simple.db`.

Se precisar recriar:
```bash
rm -rf data/
# Na próxima execução, será criado novamente
```

### Frontend não conecta na API

1. Verifique se a API está rodando: `curl http://localhost:8000/api/health`
2. Verifique os logs: `tail -f logs/api.log`
3. Verifique CORS (deve estar configurado para `*` em desenvolvimento)

### Erro de módulo não encontrado

Certifique-se de estar no diretório raiz do projeto:
```bash
cd /home/gabriel/softhill/playwright-simple
```

## Próximos Passos

- Leia a [Documentação Completa](ARCHITECTURE_INDEX.md)
- Veja o [Guia de Testes](TESTING_GUIDE.md)
- Explore a [Documentação da API](http://localhost:8000/api/docs)

## Suporte

Para problemas ou dúvidas:
1. Verifique os logs em `logs/`
2. Consulte a documentação em `docs/`
3. Verifique o status da API: `curl http://localhost:8000/api/health`

---

**Última Atualização**: Janeiro 2025


