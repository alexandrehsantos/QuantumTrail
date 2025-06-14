# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from typing import Dict, Any
from .base_strategy import BaseStrategy
import logging

class MomentumBreakoutStrategy(BaseStrategy):
    def __init__(self, lookback_period: int = 5, breakout_threshold: float = 0.005, 
                 volume_multiplier: float = 1.5, min_volume_periods: int = 10):
        super().__init__("MomentumBreakout")
        self.lookback_period = lookback_period
        self.breakout_threshold = breakout_threshold
        self.volume_multiplier = volume_multiplier
        self.min_volume_periods = min_volume_periods
        self.price_history = []
        self.volume_history = []
        self.high_history = []
        self.low_history = []
        
    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            df = pd.DataFrame(data)
            
            current_price = float(df['close'].iloc[-1])
            current_volume = float(df['volume'].iloc[-1]) if 'volume' in df else 0
            current_high = float(df['high'].iloc[-1]) if 'high' in df else current_price
            current_low = float(df['low'].iloc[-1]) if 'low' in df else current_price
            
            self.price_history.append(current_price)
            self.volume_history.append(current_volume)
            self.high_history.append(current_high)
            self.low_history.append(current_low)
            
            max_history = max(self.lookback_period, self.min_volume_periods) + 5
            if len(self.price_history) > max_history:
                self.price_history = self.price_history[-max_history:]
                self.volume_history = self.volume_history[-max_history:]
                self.high_history = self.high_history[-max_history:]
                self.low_history = self.low_history[-max_history:]
            
            if len(self.price_history) < self.lookback_period:
                return {"signal": "none", "reason": "insufficient_data", "confidence": 0}
            
            df_history = pd.DataFrame({
                'close': self.price_history,
                'volume': self.volume_history,
                'high': self.high_history,
                'low': self.low_history
            })
            
            df_with_indicators = self.calculate_indicators(df_history)
            signal = self.generate_signal(df_with_indicators)
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Error in momentum breakout analysis: {e}")
            return {"signal": "none", "reason": "error", "confidence": 0}
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        
        df['price_change'] = df['close'].pct_change()
        df['price_momentum'] = df['close'].pct_change(periods=self.lookback_period)
        
        if len(df) >= self.min_volume_periods:
            df['volume_ma'] = df['volume'].rolling(window=self.min_volume_periods).mean()
            df['volume_ratio'] = df['volume'] / df['volume_ma']
        else:
            df['volume_ma'] = df['volume'].mean()
            df['volume_ratio'] = 1.0
        
        df['resistance'] = df['high'].rolling(window=self.lookback_period).max()
        df['support'] = df['low'].rolling(window=self.lookback_period).min()
        
        df['resistance_breakout'] = df['close'] > df['resistance'].shift(1)
        df['support_breakout'] = df['close'] < df['support'].shift(1)
        
        df['price_velocity'] = df['close'].diff()
        df['velocity_ma'] = df['price_velocity'].rolling(window=3).mean()
        
        return df
    
    def generate_signal(self, data: pd.DataFrame) -> Dict[str, Any]:
        if len(data) < 2:
            return {"signal": "none", "reason": "insufficient_data", "confidence": 0}
        
        current = data.iloc[-1]
        
        current_price = current['close']
        price_momentum = current['price_momentum']
        volume_ratio = current['volume_ratio']
        resistance_breakout = current['resistance_breakout']
        support_breakout = current['support_breakout']
        price_velocity = current['velocity_ma']
        
        signal = "none"
        confidence = 0
        reason = ""
        
        if (resistance_breakout and 
            price_momentum > self.breakout_threshold and
            volume_ratio >= self.volume_multiplier and
            price_velocity > 0):
            
            signal = "buy"
            confidence = min(90, 50 + (price_momentum * 1000) + (volume_ratio * 10))
            reason = f"Bullish breakout: momentum={price_momentum:.3f}, volume_ratio={volume_ratio:.2f}"
            
        elif (support_breakout and 
              price_momentum < -self.breakout_threshold and
              volume_ratio >= self.volume_multiplier and
              price_velocity < 0):
            
            signal = "sell"
            confidence = min(90, 50 + (abs(price_momentum) * 1000) + (volume_ratio * 10))
            reason = f"Bearish breakout: momentum={price_momentum:.3f}, volume_ratio={volume_ratio:.2f}"
        
        elif (price_momentum > self.breakout_threshold * 1.5 and 
              volume_ratio >= self.volume_multiplier * 0.8):
            signal = "buy"
            confidence = min(70, 30 + (price_momentum * 800))
            reason = f"Strong bullish momentum: {price_momentum:.3f}"
            
        elif (price_momentum < -self.breakout_threshold * 1.5 and 
              volume_ratio >= self.volume_multiplier * 0.8):
            signal = "sell" 
            confidence = min(70, 30 + (abs(price_momentum) * 800))
            reason = f"Strong bearish momentum: {price_momentum:.3f}"
        
        if signal != "none":
            self.logger.info(f"🚀 MOMENTUM SIGNAL: {signal.upper()} | Confidence: {confidence}% | {reason}")
            self.logger.info(f"💰 Price: {current_price} | Momentum: {price_momentum:.4f} | Volume: {volume_ratio:.2f}x")
        
        return {
            "signal": signal,
            "confidence": confidence,
            "reason": reason,
            "price": current_price,
            "momentum": price_momentum,
            "volume_ratio": volume_ratio,
            "breakout_up": resistance_breakout,
            "breakout_down": support_breakout
        } 