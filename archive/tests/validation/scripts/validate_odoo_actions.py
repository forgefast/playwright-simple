#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de validação automatizada para ações Odoo.

Valida todas as ações críticas: click, fill, search, etc.
"""

import sys
import time
from pathlib import Path
from typing import Dict, List
import asyncio
from playwright.async_api import async_playwright

# Adicionar diretório raiz ao path
root_dir = Path(__file__).parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from playwright_simple.odoo import OdooTestBase
from playwright_simple import TestConfig


class OdooActionsValidator:
    """Validador para ações Odoo."""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.metrics: Dict[str, any] = {}
        self.start_time = time.time()
    
    def validate(self) -> bool:
        """Executa todas as validações."""
        print("🔍 Validando Ações Odoo")
        print("=" * 60)
        
        # Executar validações assíncronas
        asyncio.run(self._validate_all())
        
        # Calcular métricas
        self._calculate_metrics()
        
        # Exibir resultados
        self._print_results()
        
        # Retornar sucesso/falha
        return len(self.errors) == 0
    
    async def _validate_all(self):
        """Executa todas as validações assíncronas."""
        await self._validate_click()
        await self._validate_fill()
        await self._validate_search()
        await self._validate_crud()
    
    async def _validate_click(self):
        """Valida ação click()."""
        print("\n🖱️  Verificando click()...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            await page.set_content("""
                <html>
                    <body>
                        <button>Criar</button>
                        <button class="btn-primary">Salvar</button>
                    </body>
                </html>
            """)
            
            config = TestConfig(base_url="http://localhost:18069")
            test = OdooTestBase(page, config)
            
            try:
                assert hasattr(test, 'click'), "click() method should exist"
                assert callable(test.click), "click() should be callable"
                
                # Test click by text
                result = await test.click("Criar")
                assert result is test, "click() should return self for chaining"
                
                print("  ✅ click() method exists and works")
            except Exception as e:
                self.errors.append(f"click() validation failed: {e}")
                print(f"  ❌ click() validation failed: {e}")
            
            await context.close()
            await browser.close()
    
    async def _validate_fill(self):
        """Valida ação fill()."""
        print("\n📝 Verificando fill()...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            await page.set_content("""
                <html>
                    <body>
                        <form>
                            <label for="name">Nome</label>
                            <input id="name" name="name" type="text" />
                        </form>
                    </body>
                </html>
            """)
            
            config = TestConfig(base_url="http://localhost:18069")
            test = OdooTestBase(page, config)
            
            try:
                assert hasattr(test, 'fill'), "fill() method should exist"
                assert callable(test.fill), "fill() should be callable"
                
                # Test fill with separate args
                result = await test.fill("Nome", "Test")
                assert result is test, "fill() should return self for chaining"
                
                print("  ✅ fill() method exists and works")
            except Exception as e:
                self.errors.append(f"fill() validation failed: {e}")
                print(f"  ❌ fill() validation failed: {e}")
            
            await context.close()
            await browser.close()
    
    async def _validate_search(self):
        """Valida ação search()."""
        print("\n🔍 Verificando search()...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            await page.set_content("""
                <html>
                    <body>
                        <div class="o_cp_searchview">
                            <input type="search" class="o_searchview_input" />
                        </div>
                    </body>
                </html>
            """)
            
            config = TestConfig(base_url="http://localhost:18069")
            test = OdooTestBase(page, config)
            
            try:
                # Check if search method exists (may be search_records)
                has_search = hasattr(test, 'search') or hasattr(test, 'search_records')
                assert has_search, "search() or search_records() method should exist"
                
                print("  ✅ search() method exists")
            except Exception as e:
                self.errors.append(f"search() validation failed: {e}")
                print(f"  ❌ search() validation failed: {e}")
            
            await context.close()
            await browser.close()
    
    async def _validate_crud(self):
        """Valida ações CRUD."""
        print("\n📦 Verificando CRUD operations...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            config = TestConfig(base_url="http://localhost:18069")
            test = OdooTestBase(page, config)
            
            try:
                # Check CRUD methods
                assert hasattr(test, 'create_record'), "create_record() should exist"
                assert hasattr(test, 'search_and_open'), "search_and_open() should exist"
                assert hasattr(test, 'open_record'), "open_record() should exist"
                assert hasattr(test, 'add_line'), "add_line() should exist"
                
                print("  ✅ CRUD methods exist")
            except Exception as e:
                self.errors.append(f"CRUD validation failed: {e}")
                print(f"  ❌ CRUD validation failed: {e}")
            
            await context.close()
            await browser.close()
    
    def _calculate_metrics(self):
        """Calcula métricas de validação."""
        elapsed = time.time() - self.start_time
        self.metrics = {
            'total_time': elapsed,
            'errors': len(self.errors),
            'warnings': len(self.warnings),
        }
    
    def _print_results(self):
        """Exibe resultados da validação."""
        print("\n" + "=" * 60)
        print("📊 Resultados da Validação")
        print("=" * 60)
        print(f"⏱️  Tempo total: {self.metrics['total_time']:.2f}s")
        print(f"❌ Erros: {self.metrics['errors']}")
        print(f"⚠️  Avisos: {self.metrics['warnings']}")
        
        if self.errors:
            print("\n❌ Erros encontrados:")
            for error in self.errors:
                print(f"  - {error}")
        
        if len(self.errors) == 0:
            print("\n✅ Validação passou!")
        else:
            print("\n❌ Validação falhou!")


if __name__ == "__main__":
    validator = OdooActionsValidator()
    success = validator.validate()
    sys.exit(0 if success else 1)

