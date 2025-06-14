from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
import logging

class BaseStrategy(ABC):
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(self.__class__.__name__)
        self.position = 0
        self.entry_price = 0
        self.stop_loss = 0
        self.take_profit = 0
        
    @abstractmethod
    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        pass
        
    @abstractmethod
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        pass
        
    @abstractmethod
    def generate_signal(self, data: pd.DataFrame) -> Dict[str, Any]:
        pass
        
    def update_position(self, position: int, entry_price: float):
        self.position = position
        self.entry_price = entry_price
        
    def set_stop_loss(self, price: float):
        self.stop_loss = price
        
    def set_take_profit(self, price: float):
        self.take_profit = price
        
    def should_close_position(self, current_price: float) -> bool:
        if self.position == 0:
            return False
            
        if self.position > 0:
            return current_price <= self.stop_loss or current_price >= self.take_profit
        else:
            return current_price >= self.stop_loss or current_price <= self.take_profit
            
    def get_position_info(self) -> Dict[str, Any]:
        return {
            "position": self.position,
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit
        } 