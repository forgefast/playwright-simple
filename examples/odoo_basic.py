#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exemplo básico de teste Odoo usando playwright-simple[odoo] - User-friendly API.

Este exemplo demonstra como escrever testes de forma simples e intuitiva,
usando apenas labels visíveis e textos de botões.
"""

import asyncio
from playwright.async_api import async_playwright
from playwright_simple.odoo import OdooTestBase
from playwright_simple import TestConfig, TestRunner


async def test_create_sale_order(page, test: OdooTestBase):
    """
    Exemplo de teste user-friendly: criar pedido de venda.
    
    Note como usamos apenas:
    - Labels visíveis: "Cliente", "Produto", "Quantidade"
    - Textos de botões: "Criar", "Salvar", "Confirmar"
    - Navegação simples: "Vendas > Pedidos"
    """
    # Login
    await test.login("admin", "admin", database="devel")
    
    # Navegar para Pedidos (formato user-friendly)
    await test.go_to("Vendas > Pedidos")
    
    # Clicar em Criar (apenas texto do botão)
    await test.click("Criar")
    
    # Preencher campos usando labels visíveis
    # Formato 1: "Label = Valor"
    await test.fill("Cliente = João Silva")
    
    # Adicionar linha de produto
    await test.add_line("Adicionar linha")
    
    # Preencher produto e quantidade
    # Formato 2: label e value separados
    await test.fill("Produto", "Batom")
    await test.fill("Quantidade", "10")
    
    # Adicionar outro produto
    await test.add_line()
    await test.fill("Produto", "Base")
    await test.fill("Quantidade", "5")
    
    # Salvar pedido
    await test.click("Salvar")
    
    # Screenshot
    await test.screenshot("pedido_criado", "Pedido criado")
    
    # Confirmar pedido (wizard detectado automaticamente)
    await test.click("Confirmar")
    
    # Screenshot final
    await test.screenshot("pedido_confirmado", "Pedido confirmado")


async def test_search_and_open_record(page, test: OdooTestBase):
    """
    Exemplo: buscar e abrir registro.
    """
    await test.login("admin", "admin", database="devel")
    
    # Navegar para Clientes
    await test.go_to("Contatos > Clientes")
    
    # Buscar e abrir registro (usa primeiro resultado automaticamente)
    await test.open_record("João Silva")
    
    # Se houver múltiplos, pode especificar posição
    # await test.open_record("João", position="segundo")
    
    # Screenshot
    await test.screenshot("cliente_aberto", "Cliente aberto")


async def test_fill_with_context(page, test: OdooTestBase):
    """
    Exemplo: preencher campos com contexto (quando há campos duplicados).
    """
    await test.login("admin", "admin", database="devel")
    
    await test.go_to("Vendas > Pedidos")
    await test.click("Criar")
    
    # Se houver múltiplos campos "Nome", use context
    await test.fill("Nome", "João", context="Seção Cliente")
    await test.fill("Nome", "Maria", context="Seção Contato")


async def test_wizard_handling(page, test: OdooTestBase):
    """
    Exemplo: lidar com wizards (detecção automática).
    """
    await test.login("admin", "admin", database="devel")
    
    await test.go_to("Vendas > Pedidos")
    await test.open_record("Pedido Teste")
    
    # Clicar em botão que abre wizard
    await test.click("Processar")
    
    # Próximas operações são automaticamente no wizard
    await test.fill("Data", "01/01/2024")
    await test.fill("Observação", "Processamento automático")
    
    # Confirmar wizard (detectado automaticamente)
    await test.click("Confirmar")
    
    # Wizard fechado, operações voltam ao formulário


if __name__ == "__main__":
    # Configuração
    config = TestConfig(
        base_url="http://localhost:8069",
    )
    
    # Criar runner
    runner = TestRunner(config=config)
    
    # Executar teste
    asyncio.run(runner.run_test(test_create_sale_order))
