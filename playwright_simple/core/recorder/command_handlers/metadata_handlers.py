#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Metadata Handlers.

Handles metadata commands (caption, audio, screenshot).
"""


class MetadataHandlers:
    """Handles metadata commands."""
    
    def __init__(self, yaml_writer):
        """Initialize metadata handlers."""
        self.yaml_writer = yaml_writer
    
    async def handle_caption(self, args: str) -> None:
        """Handle caption command."""
        if not args:
            print("❌ Usage: caption \"text\"")
            return
        
        self.yaml_writer.add_caption(args)
        print(f"📝 Caption added: {args}")
    
    async def handle_subtitle(self, args: str) -> None:
        """Handle subtitle command - adds subtitle to last step."""
        # Empty string is valid (clears subtitle)
        text = args if args is not None else ""
        
        self.yaml_writer.add_subtitle_to_last_step(text)
        if text:
            print(f"📝 Subtitle added to last step: {text}")
        else:
            print(f"📝 Subtitle cleared from last step")
    
    async def handle_audio(self, args: str) -> None:
        """Handle audio command."""
        if not args:
            print("❌ Usage: audio \"text\"")
            return
        
        self.yaml_writer.add_audio(args)
        print(f"🔊 Audio added: {args}")
    
    async def handle_screenshot(self, args: str) -> None:
        """Handle screenshot command."""
        name = args if args else None
        self.yaml_writer.add_screenshot(name)
        print(f"📸 Screenshot step added: {name or 'auto'}")

