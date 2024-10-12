import logging
from typing import Type
from .data_sources.data_source import DataSource
from .strategies.strategy import Strategy
from .risk_management.risk_manager import RiskManager
from .strategies.macd_strategy import MACDStrategy
from .data_sources.live_data_source import LiveDataSource
import sqlite3
import MetaTrader5 as mt5

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def map_timeframe(timeframe: int) -> mt5.TIMEFRAME_M1:
    mapping = {
        1: mt5.TIMEFRAME_M1,
        5: mt5.TIMEFRAME_M5,
        15: mt5.TIMEFRAME_M15,
        30: mt5.TIMEFRAME_M30,
        60: mt5.TIMEFRAME_H1,
        240: mt5.TIMEFRAME_H4,
        1440: mt5.TIMEFRAME_D1,
        10080: mt5.TIMEFRAME_W1,
        43200: mt5.TIMEFRAME_MN1
    }
    return mapping.get(timeframe, mt5.TIMEFRAME_M1)

class TradingSystem:
    def __init__(self, data_source: DataSource, strategy: Strategy, symbol: str, timeframe: int):
        self.data_source = data_source
        self.strategy = strategy
        self.symbol = symbol
        self.timeframe = timeframe
        
        logging.info(f"Initialized TradingSystem with data source: {type(self.data_source).__name__}, "
                     f"strategy: {type(self.strategy).__name__}, symbol: {symbol}, timeframe: {timeframe}")

    def create_tables(self) -> None:
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS execution_data (
                    time TEXT,
                    balance REAL,
                    trade_type TEXT,
                    price REAL,
                    lot_size REAL
                )
            ''')

    def run(self):
        logging.info("Starting trading system...")
        result = self.strategy.apply()
        logging.info(f"Trading completed. Result: {result}")

if __name__ == "__main__":
    # Example usage
    data_source = LiveDataSource()
    trading_system = TradingSystem(data_source, MACDStrategy, "EURUSD", 15)  # 15-minute timeframe
    trading_system.run()
