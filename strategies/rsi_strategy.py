import pandas as pd
import numpy as np
from typing import Dict, Any
from .base_strategy import BaseStrategy
import talib

class RSIStrategy(BaseStrategy):
    def __init__(self, rsi_period: int = 14, overbought: int = 70, oversold: int = 30):
        super().__init__("RSI Strategy")
        self.rsi_period = rsi_period
        self.overbought = overbought
        self.oversold = oversold
        
    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        df = pd.DataFrame(data)
        df = self.calculate_indicators(df)
        signal = self.generate_signal(df)
        return signal
        
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        if 'close' not in data.columns:
            raise ValueError("Data must contain 'close' column")
            
        data['rsi'] = talib.RSI(data['close'].values, timeperiod=self.rsi_period)
        return data
        
    def generate_signal(self, data: pd.DataFrame) -> Dict[str, Any]:
        if data.empty or 'rsi' not in data.columns:
            return {"signal": "none", "strength": 0}
            
        current_rsi = data['rsi'].iloc[-1]
        
        if current_rsi <= self.oversold:
            return {
                "signal": "buy",
                "strength": (self.oversold - current_rsi) / self.oversold,
                "rsi": current_rsi
            }
        elif current_rsi >= self.overbought:
            return {
                "signal": "sell",
                "strength": (current_rsi - self.overbought) / (100 - self.overbought),
                "rsi": current_rsi
            }
        else:
            return {
                "signal": "none",
                "strength": 0,
                "rsi": current_rsi
            } 