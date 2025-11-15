#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YAML writer module.

Writes YAML incrementally as events are captured.
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class YAMLWriter:
    """Writes YAML incrementally."""
    
    def __init__(self, output_path: Path):
        """
        Initialize YAML writer.
        
        Args:
            output_path: Path to output YAML file
        """
        self.output_path = Path(output_path)
        self.steps: List[Dict[str, Any]] = []
        self.metadata = {
            'name': 'Gravação Automática',
            'description': f'Gravação interativa do usuário - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        }
        self.config: Dict[str, Any] = {}  # Configuração do YAML (video, browser, etc.)
        self._ensure_directory()
    
    def _ensure_directory(self):
        """Ensure output directory exists."""
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
    
    def add_step(self, step: Dict[str, Any]):
        """
        Add a step to the YAML.
        
        Args:
            step: Step dictionary to add
        """
        if step:
            self.steps.append(step)
            action_type = step.get('action', step.get('caption', step.get('audio', 'unknown')))
            logger.debug(f"Added step #{len(self.steps)}: {action_type} - {step}")
        else:
            logger.warning("Attempted to add empty step")
    
    def add_caption(self, text: str):
        """
        Add caption/subtitle step.
        
        Args:
            text: Caption text
        """
        self.add_step({
            'caption': text
        })
    
    def add_subtitle_to_last_step(self, text: str):
        """
        Add subtitle to the last step (for video subtitles).
        
        This adds the 'subtitle' field to the most recently added step,
        which will be used for video subtitle generation.
        
        Args:
            text: Subtitle text (empty string to clear)
        """
        if not self.steps:
            logger.warning("No steps to add subtitle to")
            return
        
        # Add subtitle to last step
        self.steps[-1]['subtitle'] = text
        logger.info(f"Added subtitle to last step: {text}")
    
    def add_audio(self, text: str):
        """
        Add audio/narration step.
        
        Args:
            text: Audio narration text
        """
        self.add_step({
            'audio': text
        })
    
    def add_screenshot(self, name: Optional[str] = None):
        """
        Add screenshot step.
        
        Args:
            name: Screenshot name (optional)
        """
        step = {
            'action': 'screenshot'
        }
        if name:
            step['name'] = name
        else:
            step['name'] = f"screenshot_{len(self.steps) + 1}"
        
        step['description'] = f"Tirar screenshot: {step['name']}"
        self.add_step(step)
    
    def set_metadata(self, name: Optional[str] = None, description: Optional[str] = None):
        """
        Set metadata for the YAML.
        
        Args:
            name: Test name
            description: Test description
        """
        if name:
            self.metadata['name'] = name
        if description:
            self.metadata['description'] = description
    
    def set_config(self, section: str, key: Optional[str] = None, value: Any = None, config_dict: Optional[Dict[str, Any]] = None):
        """
        Set configuration in YAML.
        
        Args:
            section: Config section (e.g., 'video', 'browser', 'step')
            key: Config key (e.g., 'enabled', 'quality') - if None, config_dict is used
            value: Config value - if None, config_dict is used
            config_dict: Dictionary with config values (alternative to key/value)
        
        Examples:
            writer.set_config('video', 'enabled', True)
            writer.set_config('video', config_dict={'enabled': True, 'quality': 'high'})
        """
        if section not in self.config:
            self.config[section] = {}
        
        if config_dict:
            # Update entire section
            self.config[section].update(config_dict)
            logger.info(f"Config updated: {section} = {config_dict}")
        elif key is not None:
            # Update single key
            self.config[section][key] = value
            logger.info(f"Config updated: {section}.{key} = {value}")
        else:
            logger.warning(f"set_config called without key or config_dict for section: {section}")
    
    def get_config(self, section: str, key: Optional[str] = None) -> Any:
        """
        Get configuration value.
        
        Args:
            section: Config section (e.g., 'video', 'browser')
            key: Config key (if None, returns entire section)
        
        Returns:
            Config value or entire section dict
        """
        if section not in self.config:
            return None if key else {}
        
        if key:
            return self.config[section].get(key)
        else:
            return self.config[section]
    
    def save(self):
        """Save YAML to file."""
        try:
            yaml_data = {
                **self.metadata,
                'steps': self.steps
            }
            
            # Add config if it exists
            if self.config:
                yaml_data['config'] = self.config
            
            logger.debug(f"Preparing to save YAML with {len(self.steps)} steps")
            logger.debug(f"Metadata: {self.metadata}")
            
            # Ensure path is absolute
            output_path = self.output_path.resolve()
            logger.debug(f"Resolved output path: {output_path}")
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Directory created/verified: {output_path.parent}")
            
            logger.debug(f"Writing YAML to file...")
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(yaml_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
            
            # Verify file was created
            if output_path.exists():
                file_size = output_path.stat().st_size
                logger.info(f"✅ YAML saved successfully to {output_path} ({file_size} bytes)")
                return True
            else:
                logger.error(f"❌ File was not created: {output_path}")
                return False
        except Exception as e:
            logger.error(f"❌ Error saving YAML: {e}", exc_info=True)
            return False
    
    def get_steps_count(self) -> int:
        """Get number of steps."""
        return len(self.steps)
    
    def get_yaml_content(self) -> str:
        """Get current YAML content as string."""
        yaml_data = {
            **self.metadata,
            'steps': self.steps
        }
        
        # Add config if it exists
        if self.config:
            yaml_data['config'] = self.config
        
        return yaml.dump(yaml_data, allow_unicode=True, default_flow_style=False, sort_keys=False)

