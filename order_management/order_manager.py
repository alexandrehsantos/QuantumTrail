from typing import Dict, Any, Optional
import logging
import asyncio
from datetime import datetime

class OrderManager:
    def __init__(self, collector, strategy):
        self.collector = collector
        self.strategy = strategy
        self.logger = logging.getLogger(self.__class__.__name__)
        self.active_orders = {}
        self.order_history = []
        
    async def place_order(self, symbol: str, side: str, quantity: float, price: Optional[float] = None) -> Dict[str, Any]:
        try:
            order = await self.collector.create_order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price
            )
            
            self.active_orders[order['id']] = order
            self.order_history.append({
                'order': order,
                'timestamp': datetime.now().isoformat(),
                'strategy': self.strategy.name
            })
            
            return order
        except Exception as e:
            self.logger.error(f"Error placing order: {e}")
            raise
            
    async def cancel_order(self, order_id: str) -> bool:
        try:
            result = await self.collector.cancel_order(order_id)
            if result:
                self.active_orders.pop(order_id, None)
            return result
        except Exception as e:
            self.logger.error(f"Error canceling order: {e}")
            raise
            
    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        try:
            status = await self.collector.get_order(order_id)
            if status['status'] in ['FILLED', 'CANCELED', 'REJECTED']:
                self.active_orders.pop(order_id, None)
            return status
        except Exception as e:
            self.logger.error(f"Error getting order status: {e}")
            raise
            
    def get_active_orders(self) -> Dict[str, Any]:
        return self.active_orders
        
    def get_order_history(self) -> list:
        return self.order_history
        
    async def execute_strategy_signal(self, symbol: str, signal: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if signal['signal'] == 'none':
            return None
            
        current_position = self.strategy.position
        quantity = abs(signal['strength'])  # Scale position size by signal strength
        
        if signal['signal'] == 'buy' and current_position <= 0:
            return await self.place_order(symbol, 'buy', quantity)
        elif signal['signal'] == 'sell' and current_position >= 0:
            return await self.place_order(symbol, 'sell', quantity)
            
        return None 