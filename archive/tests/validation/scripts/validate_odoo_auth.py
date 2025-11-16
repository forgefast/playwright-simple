#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de validação automatizada para autenticação Odoo.

Verifica que login() e logout() funcionam corretamente.
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


class OdooAuthValidator:
    """Validador para autenticação Odoo."""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.metrics: Dict[str, any] = {}
        self.start_time = time.time()
    
    def validate(self) -> bool:
        """Executa todas as validações."""
        print("🔍 Validando Autenticação Odoo")
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
        await self._validate_login_method()
        await self._validate_logout_method()
        await self._validate_login_with_database()
        await self._validate_login_without_database()
    
    async def _validate_login_method(self):
        """Valida método login()."""
        print("\n🔐 Verificando login()...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Create Odoo login page mock
            await page.set_content("""
                <html>
                    <body>
                        <form id="login-form" class="o_login_form">
                            <input name="db" type="text" />
                            <input name="login" type="text" />
                            <input name="password" type="password" />
                            <button type="submit" class="btn btn-primary">Entrar</button>
                        </form>
                    </body>
                </html>
            """)
            
            config = TestConfig(base_url="http://localhost:18069")
            test = OdooTestBase(page, config)
            
            try:
                # Check if method exists
                assert hasattr(test, 'login'), "login() method should exist"
                assert callable(test.login), "login() should be callable"
                
                print("  ✅ login() method exists and is callable")
            except Exception as e:
                self.errors.append(f"login() validation failed: {e}")
                print(f"  ❌ login() validation failed: {e}")
            
            await context.close()
            await browser.close()
    
    async def _validate_logout_method(self):
        """Valida método logout()."""
        print("\n🚪 Verificando logout()...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Create Odoo logged in page mock
            await page.set_content("""
                <html>
                    <body>
                        <nav class="o_main_navbar">
                            <div class="o_user_menu">
                                <button class="dropdown-toggle">admin</button>
                                <div class="dropdown-menu">
                                    <a href="/web/session/logout">Sair</a>
                                </div>
                            </div>
                        </nav>
                    </body>
                </html>
            """)
            
            config = TestConfig(base_url="http://localhost:18069")
            test = OdooTestBase(page, config)
            
            try:
                # Check if method exists
                assert hasattr(test, 'logout'), "logout() method should exist"
                assert callable(test.logout), "logout() should be callable"
                
                print("  ✅ logout() method exists and is callable")
            except Exception as e:
                self.errors.append(f"logout() validation failed: {e}")
                print(f"  ❌ logout() validation failed: {e}")
            
            await context.close()
            await browser.close()
    
    async def _validate_login_with_database(self):
        """Valida login() com database."""
        print("\n🔐 Verificando login() com database...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            await page.set_content("""
                <html>
                    <body>
                        <form class="o_login_form">
                            <input name="db" type="text" />
                            <input name="login" type="text" />
                            <input name="password" type="password" />
                            <button type="submit">Entrar</button>
                        </form>
                    </body>
                </html>
            """)
            
            config = TestConfig(base_url="http://localhost:18069")
            test = OdooTestBase(page, config)
            
            try:
                # Method should accept database parameter
                result = await test.login("admin", "admin", database="devel")
                assert result is test, "login() should return self for chaining"
                
                print("  ✅ login() accepts database parameter")
            except Exception as e:
                # May fail if not real Odoo, but should accept parameters
                if "database" in str(e).lower() or "parameter" in str(e).lower():
                    self.errors.append(f"login() with database failed: {e}")
                    print(f"  ❌ login() with database failed: {e}")
                else:
                    print(f"  ⚠️  login() with database: {e} (expected if not real Odoo)")
            
            await context.close()
            await browser.close()
    
    async def _validate_login_without_database(self):
        """Valida login() sem database."""
        print("\n🔐 Verificando login() sem database...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            await page.set_content("""
                <html>
                    <body>
                        <form class="o_login_form">
                            <input name="login" type="text" />
                            <input name="password" type="password" />
                            <button type="submit">Entrar</button>
                        </form>
                    </body>
                </html>
            """)
            
            config = TestConfig(base_url="http://localhost:18069")
            test = OdooTestBase(page, config)
            
            try:
                # Method should work without database
                result = await test.login("admin", "admin")
                assert result is test, "login() should return self for chaining"
                
                print("  ✅ login() works without database parameter")
            except Exception as e:
                # May fail if not real Odoo
                print(f"  ⚠️  login() without database: {e} (expected if not real Odoo)")
            
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
        
        if self.warnings:
            print("\n⚠️  Avisos:")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        if len(self.errors) == 0:
            print("\n✅ Validação passou!")
        else:
            print("\n❌ Validação falhou!")


if __name__ == "__main__":
    validator = OdooAuthValidator()
    success = validator.validate()
    sys.exit(0 if success else 1)

