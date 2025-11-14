#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Expression evaluation and variable substitution for YAML parser.

Handles:
- Expression evaluation ({{ a + b }}, {{ x > 10 }}, etc.)
- Variable substitution with context
- Safe Python expression evaluation
"""

import logging
import re
from typing import Any, Dict

logger = logging.getLogger(__name__)


class ExpressionEvaluator:
    """Evaluates Python expressions safely within YAML context."""
    
    # Safe builtins for expression evaluation
    SAFE_BUILTINS = {
        'len': len,
        'str': str,
        'int': int,
        'float': float,
        'bool': bool,
        'list': list,
        'dict': dict,
        'tuple': tuple,
        'min': min,
        'max': max,
        'sum': sum,
        'abs': abs,
        'round': round,
    }
    
    @staticmethod
    def evaluate(expr: str, context: Dict[str, Any]) -> Any:
        """
        Evaluate a Python expression safely.
        
        Args:
            expr: Expression string (e.g., "{{ a + b }}", "{{ x > 10 }}")
            context: Context dictionary with vars and params
            
        Returns:
            Evaluated result
        """
        # Remove {{ }} if present
        expr = expr.strip()
        if expr.startswith('{{') and expr.endswith('}}'):
            expr = expr[2:-2].strip()
        
        # Get variables from context
        vars_dict = context.get('vars', {})
        params_dict = context.get('params', {})
        
        # Merge vars and params (vars take precedence)
        local_vars = {**params_dict, **vars_dict}
        
        # Add previous_state if available
        if 'previous_state' in context:
            local_vars['previous_state'] = context['previous_state']
        
        try:
            # Compile and evaluate expression
            code = compile(expr, '<string>', 'eval')
            result = eval(code, {'__builtins__': ExpressionEvaluator.SAFE_BUILTINS}, local_vars)
            return result
        except Exception as e:
            logger.warning(f"Error evaluating expression '{expr}': {e}")
            # Return the original expression if evaluation fails
            return expr
    
    @staticmethod
    def substitute_variables(obj: Any, context: Dict[str, Any]) -> Any:
        """
        Substitute variables in object recursively.
        
        Supports:
        - {{ var }} - Simple variable substitution
        - {{ expr }} - Expression evaluation
        
        Args:
            obj: Object to substitute (dict, list, str, etc.)
            context: Context dictionary with vars and params
            
        Returns:
            Object with variables substituted
        """
        if isinstance(obj, str):
            # Check if string contains {{ }}
            if '{{' in obj and '}}' in obj:
                # Find all {{ }} expressions
                pattern = r'\{\{([^}]+)\}\}'
                matches = re.findall(pattern, obj)
                
                if matches:
                    # If entire string is an expression, evaluate it
                    if obj.strip().startswith('{{') and obj.strip().endswith('}}'):
                        return ExpressionEvaluator.evaluate(obj, context)
                    
                    # Otherwise, substitute each expression
                    result = obj
                    for match in matches:
                        expr = match.strip()
                        value = ExpressionEvaluator.evaluate(f"{{{{ {expr} }}}}", context)
                        # Convert to string for substitution
                        value_str = str(value) if value is not None else ''
                        result = result.replace(f"{{{{ {expr} }}}}", value_str)
                    return result
            
            return obj
        
        elif isinstance(obj, dict):
            return {
                key: ExpressionEvaluator.substitute_variables(value, context)
                for key, value in obj.items()
            }
        
        elif isinstance(obj, list):
            return [
                ExpressionEvaluator.substitute_variables(item, context)
                for item in obj
            ]
        
        else:
            return obj

