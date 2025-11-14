#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML Analyzer - Analisa HTML da página para sugerir correções precisas.

Lê HTML salvo pelo debug extension e sugere seletores e ações corretas.
"""

import re
from pathlib import Path
from typing import Optional, Dict, Any, List
from html.parser import HTMLParser
import json


class HTMLAnalyzer:
    """Analisa HTML para sugerir correções."""
    
    def __init__(self, html_file: Path = None):
        """
        Inicializa analyzer.
        
        Args:
            html_file: Arquivo HTML para analisar (default: /tmp/playwright_html.html)
        """
        self.html_file = html_file or Path("/tmp/playwright_html.html")
        self.simplified_file = Path("/tmp/playwright_html_simplified.json")
    
    def analyze(self) -> Dict[str, Any]:
        """
        Analisa HTML e retorna informações úteis.
        
        Returns:
            Dict com informações sobre botões, inputs, etc.
        """
        result = {
            "buttons": [],
            "inputs": [],
            "links": [],
            "suggestions": []
        }
        
        # Tentar ler versão simplificada primeiro
        if self.simplified_file.exists():
            try:
                data = json.loads(self.simplified_file.read_text(encoding='utf-8'))
                result.update(data)
                return result
            except:
                pass
        
        # Se não tiver simplificado, analisar HTML completo
        if self.html_file.exists():
            html = self.html_file.read_text(encoding='utf-8')
            result.update(self._parse_html(html))
        
        return result
    
    def _parse_html(self, html: str) -> Dict[str, Any]:
        """Parse HTML básico para extrair elementos."""
        buttons = []
        inputs = []
        links = []
        
        # Buscar botões
        button_pattern = r'<button[^>]*>(.*?)</button>'
        for match in re.finditer(button_pattern, html, re.DOTALL | re.IGNORECASE):
            text = re.sub(r'<[^>]+>', '', match.group(1)).strip()
            if text:
                buttons.append({"text": text, "type": "button"})
        
        # Buscar inputs do tipo button/submit
        input_pattern = r'<input[^>]*type=["\'](?:button|submit)["\'][^>]*>'
        for match in re.finditer(input_pattern, html, re.IGNORECASE):
            value_match = re.search(r'value=["\']([^"\']+)["\']', match.group(0))
            if value_match:
                buttons.append({"text": value_match.group(1), "type": "input"})
        
        # Buscar links que parecem botões
        link_pattern = r'<a[^>]*>(.*?)</a>'
        for match in re.finditer(link_pattern, html, re.DOTALL | re.IGNORECASE):
            text = re.sub(r'<[^>]+>', '', match.group(1)).strip()
            if text and len(text) < 50:  # Links muito longos provavelmente não são botões
                links.append({"text": text, "type": "link"})
        
        return {
            "buttons": buttons,
            "inputs": inputs,
            "links": links
        }
    
    def suggest_selector(self, target_text: str) -> Optional[str]:
        """
        Sugere seletor para elemento com texto específico.
        
        Args:
            target_text: Texto do elemento procurado
            
        Returns:
            Seletor sugerido ou None
        """
        data = self.analyze()
        
        # Procurar em botões
        for btn in data.get("buttons", []):
            if target_text.lower() in btn.get("text", "").lower():
                return f'button:has-text("{btn["text"]}")'
        
        # Procurar em links
        for link in data.get("links", []):
            if target_text.lower() in link.get("text", "").lower():
                return f'a:has-text("{link["text"]}")'
        
        return None
    
    def get_all_clickable_elements(self) -> List[Dict[str, str]]:
        """Retorna todos os elementos clicáveis encontrados."""
        data = self.analyze()
        elements = []
        
        for btn in data.get("buttons", []):
            elements.append({
                "text": btn.get("text", ""),
                "type": "button",
                "suggestion": f'button:has-text("{btn["text"]}")'
            })
        
        for link in data.get("links", []):
            elements.append({
                "text": link.get("text", ""),
                "type": "link",
                "suggestion": f'a:has-text("{link["text"]}")'
            })
        
        return elements

