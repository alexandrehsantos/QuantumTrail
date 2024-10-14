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
    def __init__(self, strategy_class: Type[Strategy], data_source: DataSource, symbol: str, timeframe: str, model_path=None, features=None, risk_manager=None, initial_balance=10000, start_date=None, end_date=None):
        self.strategy = strategy_class(
            data_source=data_source,
            risk_manager=risk_manager,
            symbol=symbol,
            timeframe=timeframe,
            model_path=model_path,
            features=features,
            initial_balance=initial_balance,
            start_date=start_date,
            end_date=end_date
        )
        self.data_source = data_source
        self.symbol = symbol
        self.timeframe = timeframe
        
        if isinstance(self.data_source, LiveDataSource):
            self.data_source.initialize()
        
        logging.info(f"Initialized TradingSystem with strategy: {type(self.strategy).__name__}, "
                     f"data source: {type(self.data_source).__name__}, symbol: {symbol}, timeframe: {timeframe}")

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
