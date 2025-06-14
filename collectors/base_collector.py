from abc import ABC, abstractmethod
import asyncio
import logging
from typing import Dict, Any, Optional
import aiohttp
import websockets

class BaseCollector(ABC):
    def __init__(self, api_key: str, api_secret: str, base_url: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.logger = logging.getLogger(self.__class__.__name__)
        
    async def initialize(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
            
    async def close(self):
        if self.session:
            await self.session.close()
        if self.ws:
            await self.ws.close()
            
    @abstractmethod
    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        pass
        
    @abstractmethod
    async def get_orderbook(self, symbol: str, depth: int = 20) -> Dict[str, Any]:
        pass
        
    @abstractmethod
    async def get_recent_trades(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        pass
        
    @abstractmethod
    async def subscribe_to_ticker(self, symbol: str, callback):
        pass
        
    @abstractmethod
    async def subscribe_to_trades(self, symbol: str, callback):
        pass
        
    @abstractmethod
    async def subscribe_to_orderbook(self, symbol: str, callback):
        pass 