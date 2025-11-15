#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YAML resolution: inheritance, includes, compose, and path resolution.

Handles:
- extends (inheritance)
- includes
- compose resolution
- YAML path resolution
- Action YAML lookup
- YAML file parsing (replaces YAMLParser.parse_file)
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

logger = logging.getLogger(__name__)


def parse_yaml_file(yaml_path: Path) -> Dict[str, Any]:
    """
    Parse YAML test file with support for inheritance and composition.
    
    This function replaces YAMLParser.parse_file() and can be used by extensions
    that need to parse YAML files without depending on the full YAMLParser class.
    
    Args:
        yaml_path: Path to YAML file
        
    Returns:
        Dictionary with test definition (with resolved inheritance/composition)
    """
    if not YAML_AVAILABLE:
        raise ImportError("PyYAML is required for YAML support. Install with: pip install pyyaml")
    
    yaml_path = Path(yaml_path)
    base_dir = yaml_path.parent
    
    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    # Resolve inheritance and composition
    data = YAMLResolver.resolve_inheritance(data, base_dir)
    data = YAMLResolver.resolve_includes(data, base_dir)
    data = YAMLResolver.resolve_compose(data, base_dir)
    
    return data


class YAMLResolver:
    """Resolves YAML inheritance, includes, and composition."""
    
    @staticmethod
    def resolve_inheritance(data: Dict[str, Any], base_dir: Path) -> Dict[str, Any]:
        """
        Resolve extends (inheritance) in YAML data.
        
        Args:
            data: YAML data dictionary
            base_dir: Base directory for resolving relative paths
            
        Returns:
            Resolved YAML data with parent steps merged
        """
        if 'extends' not in data:
            return data
        
        extends_path = data['extends']
        if not extends_path:
            return data
        
        # Resolve path
        if not Path(extends_path).is_absolute():
            extends_path = base_dir / extends_path
        else:
            extends_path = Path(extends_path)
        
        if not extends_path.exists():
            raise FileNotFoundError(f"Extended YAML file not found: {extends_path}")
        
        # Load parent data
        with open(extends_path, 'r', encoding='utf-8') as f:
            parent_data = yaml.safe_load(f)
        
        # Recursively resolve parent's inheritance
        parent_data = YAMLResolver.resolve_inheritance(parent_data, extends_path.parent)
        parent_data = YAMLResolver.resolve_includes(parent_data, extends_path.parent)
        
        # Merge: child overrides parent
        merged = parent_data.copy()
        
        # Merge config (child overrides parent)
        if 'config' in data:
            if 'config' in merged:
                # Deep merge config
                merged_config = merged['config'].copy()
                merged_config.update(data['config'])
                merged['config'] = merged_config
            else:
                merged['config'] = data['config']
        
        # Merge steps: parent steps first, then child steps
        if 'steps' in parent_data:
            merged['steps'] = parent_data['steps'].copy()
        else:
            merged['steps'] = []
        
        if 'steps' in data:
            merged['steps'].extend(data['steps'])
        
        # Child metadata overrides parent
        for key in ['name', 'description', 'setup', 'teardown']:
            if key in data:
                merged[key] = data[key]
        
        # Remove extends from merged data
        if 'extends' in merged:
            del merged['extends']
        
        return merged
    
    @staticmethod
    def resolve_includes(data: Dict[str, Any], base_dir: Path) -> Dict[str, Any]:
        """
        Resolve includes in YAML data.
        
        Args:
            data: YAML data dictionary
            base_dir: Base directory for resolving relative paths
            
        Returns:
            Resolved YAML data with included steps merged
        """
        if 'includes' not in data:
            return data
        
        includes = data['includes']
        if not includes:
            return data
        
        if not isinstance(includes, list):
            includes = [includes]
        
        # Collect included steps
        included_steps = []
        
        for include_path in includes:
            # Resolve path
            if not Path(include_path).is_absolute():
                include_path = base_dir / include_path
            else:
                include_path = Path(include_path)
            
            if not include_path.exists():
                logger.warning(f"Included YAML file not found: {include_path}")
                continue
            
            # Load included data
            with open(include_path, 'r', encoding='utf-8') as f:
                included_data = yaml.safe_load(f)
            
            # Recursively resolve includes
            included_data = YAMLResolver.resolve_includes(included_data, include_path.parent)
            
            # Add included steps
            if 'steps' in included_data:
                included_steps.extend(included_data['steps'])
        
        # Merge: included steps first, then current steps
        if 'steps' not in data:
            data['steps'] = []
        
        data['steps'] = included_steps + data['steps']
        
        # Remove includes from data
        if 'includes' in data:
            del data['includes']
        
        return data
    
    @staticmethod
    def resolve_compose(data: Dict[str, Any], base_dir: Path) -> Dict[str, Any]:
        """
        Resolve compose (inline composition) in YAML data.
        
        Args:
            data: YAML data dictionary
            base_dir: Base directory for resolving relative paths
            
        Returns:
            Resolved YAML data with compose steps expanded
        """
        if 'steps' not in data:
            return data
        
        resolved_steps = []
        
        for step in data['steps']:
            if 'compose' in step:
                compose_file = step.get('compose')
                params = step.get('params', {})
                
                if compose_file:
                    yaml_path = YAMLResolver.resolve_yaml_path(compose_file, base_dir)
                    if yaml_path:
                        with open(yaml_path, 'r', encoding='utf-8') as f:
                            composed_data = yaml.safe_load(f)
                        
                        # Resolve dependencies
                        composed_data = YAMLResolver.resolve_inheritance(composed_data, yaml_path.parent)
                        composed_data = YAMLResolver.resolve_includes(composed_data, yaml_path.parent)
                        composed_data = YAMLResolver.resolve_compose(composed_data, yaml_path.parent)
                        
                        # Add params as metadata to each step
                        composed_steps = composed_data.get('steps', [])
                        for composed_step in composed_steps:
                            composed_step['_compose_params'] = params
                        
                        resolved_steps.extend(composed_steps)
                    else:
                        logger.warning(f"Compose YAML not found: {compose_file}")
                        resolved_steps.append(step)
                else:
                    resolved_steps.append(step)
            else:
                resolved_steps.append(step)
        
        data['steps'] = resolved_steps
        return data
    
    @staticmethod
    def resolve_yaml_path(file_path: str, base_dir: Path) -> Optional[Path]:
        """
        Resolve YAML file path.
        
        Tries multiple locations:
        1. Relative to base_dir
        2. Relative to base_dir/examples/
        3. Relative to base_dir/odoo/ (if base_dir contains 'examples')
        4. Absolute path
        
        Args:
            file_path: File path (relative or absolute)
            base_dir: Base directory for resolution
            
        Returns:
            Resolved Path or None if not found
        """
        file_path = file_path.strip()
        
        # Try as absolute path first
        if Path(file_path).is_absolute():
            if Path(file_path).exists():
                return Path(file_path)
            return None
        
        # Try relative to base_dir
        candidate = base_dir / file_path
        if candidate.exists():
            return candidate
        
        # Try with .yaml extension
        if not file_path.endswith('.yaml') and not file_path.endswith('.yml'):
            candidate = base_dir / f"{file_path}.yaml"
            if candidate.exists():
                return candidate
        
        # Try in examples/ subdirectory
        examples_dir = base_dir / 'examples'
        if examples_dir.exists():
            candidate = examples_dir / file_path
            if candidate.exists():
                return candidate
            
            # Try with .yaml extension
            if not file_path.endswith('.yaml') and not file_path.endswith('.yml'):
                candidate = examples_dir / f"{file_path}.yaml"
                if candidate.exists():
                    return candidate
            
            # Try in examples/odoo/ subdirectory
            odoo_dir = examples_dir / 'odoo'
            if odoo_dir.exists():
                candidate = odoo_dir / file_path
                if candidate.exists():
                    return candidate
                
                # Try with .yaml extension
                if not file_path.endswith('.yaml') and not file_path.endswith('.yml'):
                    candidate = odoo_dir / f"{file_path}.yaml"
                    if candidate.exists():
                        return candidate
        
        return None
    
    @staticmethod
    def find_action_yaml(action_name: str, base_dir: Path) -> Optional[Path]:
        """
        Find YAML file for a generic action.
        
        Looks for: {action_name}.yaml in:
        1. base_dir/
        2. base_dir/examples/
        3. base_dir/examples/odoo/
        4. Project root examples/ (if base_dir is not project root)
        5. Project root examples/odoo/
        
        Args:
            action_name: Name of action (e.g., 'login')
            base_dir: Base directory to search
            
        Returns:
            Path to YAML file or None if not found
        """
        # Try different locations
        candidates = [
            base_dir / f"{action_name}.yaml",
            base_dir / f"{action_name}.yml",
        ]
        
        # Try in examples/ relative to base_dir
        examples_dir = base_dir / 'examples'
        if examples_dir.exists():
            candidates.extend([
                examples_dir / f"{action_name}.yaml",
                examples_dir / f"{action_name}.yml",
            ])
            
            # Try in examples/odoo/
            odoo_dir = examples_dir / 'odoo'
            if odoo_dir.exists():
                candidates.extend([
                    odoo_dir / f"{action_name}.yaml",
                    odoo_dir / f"{action_name}.yml",
                ])
        
        # Also try project root (if base_dir is not already project root)
        # Try to find project root by looking for playwright_simple directory
        current = base_dir
        project_root = None
        for _ in range(5):  # Look up to 5 levels
            if (current / "playwright_simple").exists() or (current / "examples").exists():
                project_root = current
                break
            if current == current.parent:  # Reached filesystem root
                break
            current = current.parent
        
        if project_root and project_root != base_dir:
            # Try project root examples/
            project_examples = project_root / 'examples'
            if project_examples.exists():
                candidates.extend([
                    project_examples / f"{action_name}.yaml",
                    project_examples / f"{action_name}.yml",
                ])
                
                # Try project root examples/odoo/
                project_odoo = project_examples / 'odoo'
                if project_odoo.exists():
                    candidates.extend([
                        project_odoo / f"{action_name}.yaml",
                        project_odoo / f"{action_name}.yml",
                    ])
        
        # Return first existing candidate
        for candidate in candidates:
            if candidate.exists():
                logger.debug(f"Found action YAML: {candidate}")
                return candidate
        
        return None

