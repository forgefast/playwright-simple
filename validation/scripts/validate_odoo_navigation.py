#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de validação automatizada para navegação Odoo.

Verifica que go_to, go_to_menu, go_to_dashboard funcionam corretamente.
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


class OdooNavigationValidator:
    """Validador para navegação Odoo."""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.metrics: Dict[str, any] = {}
        self.start_time = time.time()
    
    def validate(self) -> bool:
        """Executa todas as validações."""
        print("🔍 Validando Navegação Odoo")
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
        await self._validate_go_to()
        await self._validate_go_to_menu()
        await self._validate_go_to_dashboard()
        await self._validate_go_to_home()
        await self._validate_go_to_model()
    
    async def _validate_go_to(self):
        """Valida método go_to()."""
        print("\n🧭 Verificando go_to()...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            config = TestConfig(base_url="http://localhost:18069")
            test = OdooTestBase(page, config)
            
            try:
                assert hasattr(test, 'go_to'), "go_to() method should exist"
                assert callable(test.go_to), "go_to() should be callable"
                
                # Test with menu path
                result = await test.go_to("Vendas > Pedidos")
                assert result is test, "go_to() should return self for chaining"
                
                print("  ✅ go_to() method exists and works")
            except Exception as e:
                self.errors.append(f"go_to() validation failed: {e}")
                print(f"  ❌ go_to() validation failed: {e}")
            
            await context.close()
            await browser.close()
    
    async def _validate_go_to_menu(self):
        """Valida método go_to_menu()."""
        print("\n🧭 Verificando go_to_menu()...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            config = TestConfig(base_url="http://localhost:18069")
            test = OdooTestBase(page, config)
            
            try:
                assert hasattr(test, 'go_to_menu'), "go_to_menu() method should exist"
                assert callable(test.go_to_menu), "go_to_menu() should be callable"
                
                # Test with separate args
                result = await test.go_to_menu("Vendas", "Pedidos")
                assert result is test, "go_to_menu() should return self for chaining"
                
                print("  ✅ go_to_menu() method exists and works")
            except Exception as e:
                self.errors.append(f"go_to_menu() validation failed: {e}")
                print(f"  ❌ go_to_menu() validation failed: {e}")
            
            await context.close()
            await browser.close()
    
    async def _validate_go_to_dashboard(self):
        """Valida método go_to_dashboard()."""
        print("\n🧭 Verificando go_to_dashboard()...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            config = TestConfig(base_url="http://localhost:18069")
            test = OdooTestBase(page, config)
            
            try:
                assert hasattr(test, 'go_to_dashboard'), "go_to_dashboard() method should exist"
                assert callable(test.go_to_dashboard), "go_to_dashboard() should be callable"
                
                result = await test.go_to_dashboard()
                assert result is test, "go_to_dashboard() should return self for chaining"
                
                print("  ✅ go_to_dashboard() method exists and works")
            except Exception as e:
                self.errors.append(f"go_to_dashboard() validation failed: {e}")
                print(f"  ❌ go_to_dashboard() validation failed: {e}")
            
            await context.close()
            await browser.close()
    
    async def _validate_go_to_home(self):
        """Valida método go_to_home()."""
        print("\n🧭 Verificando go_to_home()...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            config = TestConfig(base_url="http://localhost:18069")
            test = OdooTestBase(page, config)
            
            try:
                assert hasattr(test, 'go_to_home'), "go_to_home() method should exist"
                assert callable(test.go_to_home), "go_to_home() should be callable"
                
                print("  ✅ go_to_home() method exists")
            except Exception as e:
                self.errors.append(f"go_to_home() validation failed: {e}")
                print(f"  ❌ go_to_home() validation failed: {e}")
            
            await context.close()
            await browser.close()
    
    async def _validate_go_to_model(self):
        """Valida método go_to_model()."""
        print("\n🧭 Verificando go_to_model()...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            config = TestConfig(base_url="http://localhost:18069")
            test = OdooTestBase(page, config)
            
            try:
                assert hasattr(test, 'go_to_model'), "go_to_model() method should exist"
                assert callable(test.go_to_model), "go_to_model() should be callable"
                
                print("  ✅ go_to_model() method exists")
            except Exception as e:
                self.errors.append(f"go_to_model() validation failed: {e}")
                print(f"  ❌ go_to_model() validation failed: {e}")
            
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
    validator = OdooNavigationValidator()
    success = validator.validate()
    sys.exit(0 if success else 1)

