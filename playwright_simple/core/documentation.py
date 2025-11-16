#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Documentation generator for playwright-simple.

Generates Markdown documentation from test execution results,
including screenshots, videos, and step descriptions.
"""

import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


class DocumentationGenerator:
    """
    Generates Markdown documentation from test results.
    
    Supports directives like:
    - {screenshot: nome} - Insert screenshot
    - {video: nome} - Insert video link
    - {step: descrição} - Insert step description
    """
    
    def __init__(self, output_dir: Path, screenshots_dir: Path, videos_dir: Path):
        """
        Initialize documentation generator.
        
        Args:
            output_dir: Directory for generated documentation
            screenshots_dir: Directory containing screenshots
            videos_dir: Directory containing videos
        """
        self.output_dir = Path(output_dir)
        self.screenshots_dir = Path(screenshots_dir)
        self.videos_dir = Path(videos_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_doc(
        self,
        test_name: str,
        test_description: str,
        screenshots: List[Dict[str, Any]],
        video_path: Optional[str] = None,
        template: Optional[str] = None
    ) -> Path:
        """
        Generate Markdown documentation for a test.
        
        Args:
            test_name: Name of the test
            test_description: Description of the test
            screenshots: List of screenshot metadata dicts with 'name', 'path', 'description'
            video_path: Optional path to video file
            template: Optional custom template (uses default if None)
            
        Returns:
            Path to generated documentation file
        """
        if template is None:
            template = self._default_template()
        
        # Process template
        content = template
        
        # Replace placeholders
        content = content.replace("{test_name}", test_name)
        content = content.replace("{test_description}", test_description)
        content = content.replace("{date}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        # Process screenshot directives
        content = self._process_screenshot_directives(content, screenshots, test_name)
        
        # Process video directive
        if video_path:
            content = self._process_video_directive(content, video_path, test_name)
        else:
            # Remove video directive if no video
            content = re.sub(r'\{video:.*?\}', '', content)
        
        # Process step directives (from screenshots with descriptions)
        content = self._process_step_directives(content, screenshots)
        
        # Save documentation
        doc_path = self.output_dir / f"{test_name}.md"
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return doc_path
    
    def _default_template(self) -> str:
        """Get default documentation template."""
        return """# {test_name}

{test_description}

*Documentação gerada em {date}*

## Vídeo do Teste

{video: test_name}

## Passos do Teste

{screenshots}

## Screenshots

{screenshots_list}
"""
    
    def _process_screenshot_directives(
        self,
        content: str,
        screenshots: List[Dict[str, Any]],
        test_name: str
    ) -> str:
        """
        Process {screenshot: nome} directives.
        
        Args:
            content: Template content
            screenshots: List of screenshot metadata
            test_name: Name of test
            
        Returns:
            Processed content
        """
        # Find all screenshot directives
        pattern = r'\{screenshot:\s*([^}]+)\}'
        
        def replace_screenshot(match):
            screenshot_name = match.group(1).strip()
            
            # Find screenshot in list
            screenshot = next(
                (s for s in screenshots if s.get('name') == screenshot_name or screenshot_name in s.get('name', '')),
                None
            )
            
            if screenshot:
                # Get relative path from output_dir
                screenshot_path = Path(screenshot['path'])
                relative_path = self._get_relative_path(screenshot_path, self.output_dir)
                
                description = screenshot.get('description', screenshot_name)
                
                return f"""![{description}]({relative_path})
*{description}*"""
            else:
                # Screenshot not found, try to find by filename
                screenshot_file = self.screenshots_dir / test_name / f"{screenshot_name}.png"
                if not screenshot_file.exists():
                    screenshot_file = self.screenshots_dir / test_name / f"{screenshot_name}.jpg"
                
                if screenshot_file.exists():
                    relative_path = self._get_relative_path(screenshot_file, self.output_dir)
                    return f"""![{screenshot_name}]({relative_path})
*{screenshot_name}*"""
                else:
                    return f"*Screenshot '{screenshot_name}' não encontrado*"
        
        content = re.sub(pattern, replace_screenshot, content)
        
        # Replace {screenshots} placeholder with all screenshots
        if '{screenshots}' in content or '{screenshots_list}' in content:
            screenshots_section = self._generate_screenshots_section(screenshots, test_name)
            content = content.replace('{screenshots}', screenshots_section)
            content = content.replace('{screenshots_list}', screenshots_section)
        
        return content
    
    def _process_video_directive(
        self,
        content: str,
        video_path: str,
        test_name: str
    ) -> str:
        """
        Process {video: nome} directive.
        
        Args:
            content: Template content
            video_path: Path to video file
            test_name: Name of test
            
        Returns:
            Processed content
        """
        video_file = Path(video_path)
        if video_file.exists():
            relative_path = self._get_relative_path(video_file, self.output_dir)
            video_name = video_file.stem
            
            # Generate video link
            video_markdown = f"""### Vídeo: {video_name}

[Assistir vídeo]({relative_path})

*Formato: {video_file.suffix[1:].upper()}*"""
            
            # Replace {video: test_name} or {video: *}
            pattern = r'\{video:[^}]*\}'
            content = re.sub(pattern, video_markdown, content)
        else:
            # Remove video directive if file not found
            content = re.sub(r'\{video:.*?\}', '*Vídeo não encontrado*', content)
        
        return content
    
    def _process_step_directives(
        self,
        content: str,
        screenshots: List[Dict[str, Any]]
    ) -> str:
        """
        Process {step: descrição} directives.
        
        Args:
            content: Template content
            screenshots: List of screenshot metadata
            
        Returns:
            Processed content
        """
        # Find all step directives
        pattern = r'\{step:\s*([^}]+)\}'
        
        def replace_step(match):
            step_description = match.group(1).strip()
            return f"### {step_description}"
        
        return re.sub(pattern, replace_step, content)
    
    def _generate_screenshots_section(
        self,
        screenshots: List[Dict[str, Any]],
        test_name: str
    ) -> str:
        """
        Generate screenshots section from list.
        
        Args:
            screenshots: List of screenshot metadata
            test_name: Name of test
            
        Returns:
            Markdown section with all screenshots
        """
        if not screenshots:
            return "*Nenhum screenshot disponível*"
        
        sections = []
        for i, screenshot in enumerate(screenshots, 1):
            screenshot_path = Path(screenshot.get('path', ''))
            if not screenshot_path.exists():
                # Try to find in screenshots directory
                screenshot_name = screenshot.get('name', f'screenshot_{i}')
                screenshot_path = self.screenshots_dir / test_name / f"{screenshot_name}.png"
                if not screenshot_path.exists():
                    screenshot_path = self.screenshots_dir / test_name / f"{screenshot_name}.jpg"
            
            if screenshot_path.exists():
                relative_path = self._get_relative_path(screenshot_path, self.output_dir)
                description = screenshot.get('description', screenshot.get('name', f'Screenshot {i}'))
                
                sections.append(f"""### {i}. {description}

![{description}]({relative_path})

""")
        
        return '\n'.join(sections)
    
    def _get_relative_path(self, file_path: Path, base_dir: Path) -> str:
        """
        Get relative path from base directory.
        
        Args:
            file_path: Path to file
            base_dir: Base directory
            
        Returns:
            Relative path string
        """
        try:
            return str(file_path.relative_to(base_dir))
        except ValueError:
            # If not relative, return absolute path
            return str(file_path)
    
    def generate_index(self, test_docs: List[Dict[str, Any]]) -> Path:
        """
        Generate index page listing all test documentation.
        
        Args:
            test_docs: List of test documentation dicts with 'name', 'path', 'description'
            
        Returns:
            Path to index file
        """
        index_path = self.output_dir / "README.md"
        
        content = """# Documentação de Testes

Documentação gerada automaticamente dos testes executados.

## Testes Disponíveis

"""
        
        for test in test_docs:
            test_name = test.get('name', 'Unknown')
            test_description = test.get('description', '')
            test_path = test.get('path', '')
            
            if test_path:
                relative_path = self._get_relative_path(Path(test_path), self.output_dir)
                content += f"""### [{test_name}]({relative_path})

{test_description}

"""
            else:
                content += f"""### {test_name}

{test_description}

"""
        
        content += f"""
*Última atualização: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""
        
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return index_path

