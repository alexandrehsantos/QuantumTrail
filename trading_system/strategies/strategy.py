from abc import ABC, abstractmethod
from typing import Dict, Any
from trading_system.data_sources.data_source import DataSource
import logging

class Strategy(ABC):
    def __init__(self, data_source: DataSource, symbol: str, timeframe: int, start_date: str = None, end_date: str = None, initial_balance: float = None):
        self.data_source = data_source
        self.symbol = symbol
        self.timeframe = timeframe
        self.start_date = start_date
        self.end_date = end_date
        self.initial_balance = initial_balance
        self.trade_open = False

    @abstractmethod
    def apply(self) -> Dict[str, Any]:
        """
        Apply the strategy in either live or backtest mode.
        Returns a dictionary containing the results of the strategy application.
        """
        pass

    def manage_positions(self, current_price: float) -> None:
        """
        Manage open positions based on current price and predefined stop loss and take profit levels.
        """
        positions = self.data_source.get_positions(self.symbol)
        for position in positions:
            if position['type'] == 'buy':
                sl, tp = position['sl'], position['tp']
                if current_price >= tp or current_price <= sl:
                    self.data_source.close_position(position['ticket'])
                    self.trade_open = False
                    logging.info(f"Closed buy position at {current_price}")
            elif position['type'] == 'sell':
                sl, tp = position['sl'], position['tp']
                if current_price <= tp or current_price >= sl:
                    self.data_source.close_position(position['ticket'])
                    self.trade_open = False
                    logging.info(f"Closed sell position at {current_price}")

    def calculate_lot_size(self, risk_amount: float, stop_loss_points: float) -> float:
        """
        Calculate the lot size based on risk amount and stop loss points.
        """
        return self.data_source.calculate_lot_size(self.symbol, risk_amount, stop_loss_points)
