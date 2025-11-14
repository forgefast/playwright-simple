#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para mapear todas as ações deprecated (que não usam cursor).

Gera um relatório completo de todas as ações que não utilizam cursor_manager.
"""

import re
import ast
from pathlib import Path
from typing import List, Dict, Tuple
from collections import defaultdict

# Padrões de código que indicam uso sem cursor
DEPRECATED_PATTERNS = [
    (r'page\.mouse\.click\(', 'page.mouse.click() - uso direto sem cursor_manager'),
    (r'page\.keyboard\.press\(', 'page.keyboard.press() - uso direto sem cursor'),
    (r'element\.click\(\)', 'element.click() - uso direto sem cursor_manager'),
    (r'\.fill\(', 'element.fill() - uso direto sem cursor'),
    (r'\.type\(', 'element.type() - uso direto sem cursor'),
    (r'\.select\(', 'element.select() - uso direto sem cursor'),
    (r'\.hover\(\)', 'element.hover() - uso direto sem cursor'),
]

# Padrões que indicam uso COM cursor (não são deprecated)
CURSOR_PATTERNS = [
    r'cursor_manager\.move_to',
    r'cursor_manager\.show_click_effect',
    r'cursor_manager\.show_hover_effect',
    r'_helpers\.move_cursor_to_element',
    r'test\.click\(',
    r'test\.type\(',
    r'test\.select\(',
    r'test\.hover\(',
    r'super\(\)\.click\(',
    r'super\(\)\.type\(',
]


def check_uses_cursor(lines: List[str], line_num: int, context_lines: int = 10) -> bool:
    """Verifica se o código ao redor usa cursor."""
    start = max(0, line_num - context_lines)
    end = min(len(lines), line_num + context_lines)
    context = '\n'.join(lines[start:end])
    
    for pattern in CURSOR_PATTERNS:
        if re.search(pattern, context):
            return True
    return False


def scan_file(file_path: Path) -> List[Dict]:
    """Escaneia um arquivo Python procurando por ações deprecated."""
    try:
        content = file_path.read_text(encoding='utf-8')
        lines = content.split('\n')
        issues = []
        
        for line_num, line in enumerate(lines, 1):
            for pattern, description in DEPRECATED_PATTERNS:
                if re.search(pattern, line):
                    # Verifica se usa cursor no contexto
                    if not check_uses_cursor(lines, line_num - 1):
                        issues.append({
                            'file': str(file_path.relative_to(Path(__file__).parent.parent)),
                            'line': line_num,
                            'code': line.strip(),
                            'issue': description,
                        })
        
        return issues
    except Exception as e:
        print(f"Erro ao processar {file_path}: {e}")
        return []


def main():
    """Gera relatório completo de ações deprecated."""
    base_dir = Path(__file__).parent.parent / 'playwright_simple'
    
    all_issues = []
    files_scanned = 0
    
    # Escaneia todos os arquivos Python
    for py_file in base_dir.rglob('*.py'):
        # Ignora arquivos de teste e backups
        if 'test' in py_file.name.lower() or 'backup' in py_file.name.lower():
            continue
        
        issues = scan_file(py_file)
        if issues:
            all_issues.extend(issues)
        files_scanned += 1
    
    # Agrupa por tipo de issue
    by_issue = defaultdict(list)
    for issue in all_issues:
        by_issue[issue['issue']].append(issue)
    
    # Gera relatório
    report = []
    report.append("# Relatório de Ações Deprecated (Sem Cursor)\n")
    report.append(f"**Total de arquivos escaneados:** {files_scanned}\n")
    report.append(f"**Total de issues encontradas:** {len(all_issues)}\n\n")
    report.append("---\n\n")
    
    for issue_type, issues in sorted(by_issue.items()):
        report.append(f"## {issue_type}\n")
        report.append(f"**Ocorrências:** {len(issues)}\n\n")
        
        for issue in issues[:10]:  # Limita a 10 por tipo
            report.append(f"- `{issue['file']}:{issue['line']}`")
            report.append(f"  ```python")
            report.append(f"  {issue['code']}")
            report.append(f"  ```\n")
        
        if len(issues) > 10:
            report.append(f"\n*... e mais {len(issues) - 10} ocorrências*\n")
        
        report.append("\n")
    
    # Salva relatório
    report_path = base_dir.parent / 'docs' / 'DEPRECATED_ACTIONS_REPORT.md'
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(''.join(report), encoding='utf-8')
    
    print(f"✅ Relatório gerado: {report_path}")
    print(f"📊 Total de issues: {len(all_issues)}")
    print(f"📁 Arquivos escaneados: {files_scanned}")


if __name__ == '__main__':
    main()

