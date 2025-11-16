#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IPC Server - Comunicação eficiente entre processos usando Unix Domain Sockets.

Usa Unix Domain Sockets para comunicação bidirecional eficiente.
Alternativa melhor que arquivos JSON para comunicação em tempo real.
"""

import asyncio
import json
import logging
import socket
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class IPCServer:
    """Servidor IPC usando Unix Domain Sockets."""
    
    def __init__(self, socket_path: Path, message_handler: Optional[Callable] = None):
        """
        Inicializa servidor IPC.
        
        Args:
            socket_path: Caminho do socket Unix
            message_handler: Função para processar mensagens recebidas
        """
        self.socket_path = Path(socket_path)
        self.message_handler = message_handler
        self.server: Optional[asyncio.Server] = None
        self.running = False
        
        # Limpar socket antigo se existir
        if self.socket_path.exists():
            self.socket_path.unlink()
    
    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Processa mensagens de clientes."""
        try:
            while True:
                # Ler mensagem (formato: tamanho + JSON)
                size_bytes = await reader.readexactly(4)
                size = int.from_bytes(size_bytes, 'big')
                
                data_bytes = await reader.readexactly(size)
                message = json.loads(data_bytes.decode('utf-8'))
                
                logger.debug(f"Received message: {message}")
                
                # Processar mensagem
                if self.message_handler:
                    response = await self.message_handler(message)
                else:
                    response = {"status": "ok", "message": "received"}
                
                # Enviar resposta
                response_json = json.dumps(response)
                response_bytes = response_json.encode('utf-8')
                writer.write(len(response_bytes).to_bytes(4, 'big'))
                writer.write(response_bytes)
                await writer.drain()
                
        except asyncio.IncompleteReadError:
            # Cliente desconectou
            pass
        except Exception as e:
            logger.error(f"Error handling client: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
    
    async def start(self):
        """Inicia servidor."""
        self.server = await asyncio.start_unix_server(
            self.handle_client,
            str(self.socket_path)
        )
        self.running = True
        logger.info(f"IPC Server started on {self.socket_path}")
    
    async def stop(self):
        """Para servidor."""
        self.running = False
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        if self.socket_path.exists():
            self.socket_path.unlink()
        logger.info("IPC Server stopped")


class IPCClient:
    """Cliente IPC para comunicação com servidor."""
    
    def __init__(self, socket_path: Path):
        """
        Inicializa cliente IPC.
        
        Args:
            socket_path: Caminho do socket Unix
        """
        self.socket_path = Path(socket_path)
    
    async def send_message(self, message: Dict[str, Any], timeout: float = 5.0) -> Dict[str, Any]:
        """
        Envia mensagem e aguarda resposta.
        
        Args:
            message: Mensagem a enviar
            timeout: Timeout em segundos
            
        Returns:
            Resposta do servidor
        """
        if not self.socket_path.exists():
            raise ConnectionError(f"Socket not found: {self.socket_path}")
        
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_unix_connection(str(self.socket_path)),
                timeout=timeout
            )
            
            try:
                # Enviar mensagem
                message_json = json.dumps(message)
                message_bytes = message_json.encode('utf-8')
                writer.write(len(message_bytes).to_bytes(4, 'big'))
                writer.write(message_bytes)
                await writer.drain()
                
                # Ler resposta
                size_bytes = await asyncio.wait_for(reader.readexactly(4), timeout=timeout)
                size = int.from_bytes(size_bytes, 'big')
                
                response_bytes = await asyncio.wait_for(reader.readexactly(size), timeout=timeout)
                response = json.loads(response_bytes.decode('utf-8'))
                
                return response
            finally:
                writer.close()
                await writer.wait_closed()
        except asyncio.TimeoutError:
            raise TimeoutError(f"IPC communication timeout after {timeout}s")
        except Exception as e:
            raise ConnectionError(f"IPC communication error: {e}")
    
    def send_message_sync(self, message: Dict[str, Any], timeout: float = 5.0) -> Dict[str, Any]:
        """Versão síncrona de send_message."""
        return asyncio.run(self.send_message(message, timeout))

