from abc import ABC, abstractmethod
from typing import Dict, Any
from trading_system.data_sources.data_source import DataSource
import logging
from trading_system.risk_management.risk_manager import RiskManager
import MetaTrader5 as mt5

class Strategy(ABC):
    def __init__(self, data_source: DataSource, risk_manager: RiskManager, symbol: str, timeframe: int):
        self.data_source = data_source
        self.risk_manager = risk_manager
        self.symbol = symbol
        self.timeframe = timeframe
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
            # Assuming position is a named tuple or object with attributes
            if position.type == mt5.ORDER_TYPE_BUY:
                if current_price >= position.tp or current_price <= position.sl:
                    result = self.data_source.close_position(position.ticket)
                    if result:
                        self.trade_open = False
                        logging.info(f"Closed buy position at {current_price}")
                    else:
                        logging.error(f"Failed to close buy position at {current_price}")
            elif position.type == mt5.ORDER_TYPE_SELL:
                if current_price <= position.tp or current_price >= position.sl:
                    result = self.data_source.close_position(position.ticket)
                    if result:
                        self.trade_open = False
                        logging.info(f"Closed sell position at {current_price}")
                    else:
                        logging.error(f"Failed to close sell position at {current_price}")
            else:
                logging.warning(f"Unexpected position data structure: {position}")

    def calculate_lot_size(self, risk_amount: float, stop_loss_points: float) -> float:
        """
        Calculate the lot size based on risk amount and stop loss points.
        """
        return self.data_source.calculate_lot_size(self.symbol, risk_amount, stop_loss_points)
