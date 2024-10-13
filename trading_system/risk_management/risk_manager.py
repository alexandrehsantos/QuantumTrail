import logging
import MetaTrader5 as mt5
import math
from order_type import OrderType

class RiskManager:
    def __init__(self, initial_balance: float, risk_per_trade: float, max_risk_per_trade: float, min_lot_size: float, max_lot_size: float):
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.risk_per_trade = risk_per_trade
        self.max_risk_per_trade = max_risk_per_trade
        self.min_lot_size = min_lot_size
        self.max_lot_size = max_lot_size
        self.daily_loss = 0.0

    def calculate_position_size(self, symbol: str, stop_loss_distance: float) -> float:
        # Calculate risk amount
        risk_amount = self.current_balance * self.max_risk_per_trade
        
        # Calculate position size
        position_size = risk_amount / stop_loss_distance
        
        # Round down to the nearest multiple of min_lot_size
        position_size = max(self.min_lot_size, min(position_size, self.max_lot_size))
        
        return position_size

    def calculate_stop_loss_take_profit(self, symbol: str, entry_price: float, order_type: OrderType, risk_percent: float, reward_ratio: float):
        if order_type not in [OrderType.BUY, OrderType.SELL]:
            raise ValueError(f"Invalid order type: {order_type}")

        if order_type == OrderType.BUY:
            sl = entry_price * (1 - risk_percent)
            tp = entry_price * (1 + reward_ratio)
        elif order_type == OrderType.SELL:
            sl = entry_price * (1 + risk_percent)
            tp = entry_price * (1 - reward_ratio)

        return sl, tp

    def update_balance(self, trade_profit: float):
        self.current_balance += trade_profit
        self.daily_loss += trade_profit
        return self.current_balance

    def can_open_trade(self) -> bool:
        return self.daily_loss < self.max_daily_loss

    def reset_daily_loss(self):
        self.daily_loss = 0.0
