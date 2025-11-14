#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main CLI Entry Point.

Coordinates command execution and delegates to appropriate handlers.
"""

import asyncio
import sys
import argparse

from .parser import create_parser
from .config_builder import create_config_from_args
from .run_handlers import run_test
from .record_handlers import record_interactions
from .command_handlers import handle_command_commands


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == 'run':
        # Create config
        config = create_config_from_args(args)
        
        # Run test
        asyncio.run(run_test(args.yaml_file, config, args))
    elif args.command == 'record':
        # Record interactions
        asyncio.run(record_interactions(
            output_path=args.output,
            initial_url=getattr(args, 'url', None),
            headless=args.headless,
            debug=args.debug
        ))
    elif args.command in ['find', 'click', 'type', 'submit', 'wait', 'info', 'html']:
        # Command commands - send to active recording session
        handle_command_commands(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()

