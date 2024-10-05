from abc import ABC, abstractmethod
import pandas as pd

class DataSource(ABC):
    @abstractmethod
    def initialize(self):
        pass

    @abstractmethod
    def get_data(self, symbol: str, timeframe: str, start_date=None, end_date=None) -> pd.DataFrame:
        pass

    @abstractmethod
    def buy_order(self, symbol, volume, price, sl, tp, deviation=10, magic=234000, comment="Buy Order"):
        pass

    @abstractmethod
    def sell_order(self, symbol, volume, price, sl, tp, deviation=10, magic=234000, comment="Sell Order"):
        pass

    @abstractmethod
    def get_positions(self, symbol: str):
        """Retrieve open positions for the given symbol."""
        pass

    @abstractmethod
    def close_position(self, ticket: int):
        """Close the position with the given ticket."""
        pass