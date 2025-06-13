import logging
from typing import Type
from datetime import datetime, timedelta
import joblib
from .strategies.strategy import Strategy
from .data_sources.data_source import DataSource
from .data_sources.live_data_source import LiveDataSource
from .risk_management.risk_manager import RiskManager
import traceback

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class TradingSystem:
    def __init__(self, strategy: Strategy):
        self.strategy = strategy
        self.data_source = strategy.data_source
        self.symbol = strategy.symbol
        self.timeframe = strategy.timeframe
        
        if isinstance(self.data_source, LiveDataSource):
            self.data_source.initialize()
        
        logging.info(f"Initialized TradingSystem with strategy: {type(self.strategy).__name__}, "
                     f"data source: {type(self.data_source).__name__}, symbol: {self.symbol}, timeframe: {self.timeframe}")

    def run(self):
        try:
            self.strategy.apply()
        except Exception as e:
            logging.error(f"An error occurred while running the trading system: {e}")
            logging.error(f"Error traceback: {traceback.format_exc()}")
            raise

if __name__ == "__main__":
    # Example usage
    data_source = LiveDataSource()
    trading_system = TradingSystem(MACDStrategy, data_source, "EURUSD", "15")  # 15-minute timeframe
    trading_system.run()
