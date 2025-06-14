import json
import hmac
import hashlib
import time
from typing import Dict, Any, Optional
from .base_collector import BaseCollector
import aiohttp
import websockets
from binance.client import Client
from binance.exceptions import BinanceAPIException

class BinanceCollector(BaseCollector):
    def __init__(self, api_key: str, api_secret: str):
        super().__init__(api_key, api_secret, "https://testnet.binance.vision")
        self.client = Client(api_key, api_secret, testnet=True)
        self.ws_base_url = "wss://stream.testnet.binance.vision/ws"
        
    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        try:
            ticker = await self.client.get_symbol_ticker(symbol=symbol)
            return ticker
        except BinanceAPIException as e:
            self.logger.error(f"Error getting ticker: {e}")
            raise
            
    async def get_orderbook(self, symbol: str, depth: int = 20) -> Dict[str, Any]:
        try:
            orderbook = await self.client.get_order_book(symbol=symbol, limit=depth)
            return orderbook
        except BinanceAPIException as e:
            self.logger.error(f"Error getting orderbook: {e}")
            raise
            
    async def get_recent_trades(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        try:
            trades = await self.client.get_recent_trades(symbol=symbol, limit=limit)
            return trades
        except BinanceAPIException as e:
            self.logger.error(f"Error getting recent trades: {e}")
            raise
            
    async def subscribe_to_ticker(self, symbol: str, callback):
        stream_name = f"{symbol.lower()}@ticker"
        await self._subscribe_to_stream(stream_name, callback)
        
    async def subscribe_to_trades(self, symbol: str, callback):
        stream_name = f"{symbol.lower()}@trade"
        await self._subscribe_to_stream(stream_name, callback)
        
    async def subscribe_to_orderbook(self, symbol: str, callback):
        stream_name = f"{symbol.lower()}@depth"
        await self._subscribe_to_stream(stream_name, callback)
        
    async def _subscribe_to_stream(self, stream_name: str, callback):
        try:
            async with websockets.connect(f"{self.ws_base_url}/{stream_name}") as websocket:
                while True:
                    try:
                        message = await websocket.recv()
                        data = json.loads(message)
                        await callback(data)
                    except websockets.exceptions.ConnectionClosed:
                        self.logger.warning("WebSocket connection closed. Reconnecting...")
                        break
                    except Exception as e:
                        self.logger.error(f"Error processing message: {e}")
                        continue
        except Exception as e:
            self.logger.error(f"WebSocket connection error: {e}")
            raise 