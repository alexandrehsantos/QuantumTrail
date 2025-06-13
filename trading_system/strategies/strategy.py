from abc import ABC, abstractmethod
from typing import Dict, Any
from trading_system.data_sources.data_source import DataSource
from trading_system.risk_management.risk_manager import RiskManager
import MetaTrader5 as mt5
from order_type import OrderType

class Strategy(ABC):
    def __init__(self, data_source, risk_manager: RiskManager, symbol, timeframe, initial_balance, start_date, end_date):
        self.data_source = data_source
        self.risk_manager = risk_manager
        self.symbol = symbol
        self.timeframe = timeframe
        self.initial_balance = initial_balance
        self.start_date = start_date
        self.end_date = end_date

    @abstractmethod
    def apply(self):
        pass

    @abstractmethod
    def manage_positions(self, current_price: float):
        pass

    @abstractmethod
    def update_balance(self, balance, current_price):
        pass
