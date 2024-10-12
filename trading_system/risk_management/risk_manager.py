import logging
import MetaTrader5 as mt5

class RiskManager:
    def __init__(self, initial_balance, risk_per_trade, min_lot_size=0.01, max_lot_size=1.0):
        self.account_balance = initial_balance
        self.risk_per_trade = risk_per_trade
        self.min_lot_size = min_lot_size
        self.max_lot_size = max_lot_size

    def calculate_position_size(self, symbol, stop_loss_distance):
        # Calculate risk amount
        risk_amount = self.account_balance * self.risk_per_trade
        
        # Calculate position size
        position_size = risk_amount / stop_loss_distance
        
        # Ensure position size is within limits
        position_size = max(self.min_lot_size, min(position_size, self.max_lot_size))
        
        return position_size

    def calculate_stop_loss_take_profit(self, symbol: str, entry_price: float, order_type: str, stop_loss_pct: float, take_profit_pct: float) -> tuple:
        if order_type == mt5.ORDER_TYPE_BUY:
            sl = entry_price * (1 - stop_loss_pct)  # SL below entry
            tp = entry_price * (1 + take_profit_pct)  # TP above entry
        elif order_type == mt5.ORDER_TYPE_SELL:
            sl = entry_price * (1 + stop_loss_pct)  # SL above entry
            tp = entry_price * (1 - take_profit_pct)  # TP below entry
        else:
            raise ValueError(f"Invalid order type: {order_type}")
        
        return sl, tp

    def update_balance(self, new_balance: float):
        self.daily_loss += max(0, self.current_balance - new_balance)
        self.current_balance = new_balance

    def can_open_trade(self) -> bool:
        return self.daily_loss < self.max_daily_loss

    def reset_daily_loss(self):
        self.daily_loss = 0
