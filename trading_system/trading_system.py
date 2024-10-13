import logging
from typing import Type
from datetime import datetime, timedelta
import joblib
from .strategies.strategy import Strategy
from .data_sources.data_source import DataSource
from .data_sources.live_data_source import LiveDataSource
from .risk_management.risk_manager import RiskManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class TradingSystem:
    def __init__(self, strategy_class: Type[Strategy], data_source: DataSource, symbol: str, timeframe: str, model_path=None, features=None):
        self.data_source = data_source
        self.symbol = symbol
        self.timeframe = timeframe
        self.initial_balance = 10000  # Example initial balance
        self.start_date = datetime.now().strftime("%Y-%m-%d")
        self.end_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        if isinstance(self.data_source, LiveDataSource):
            self.data_source.initialize()
        
        risk_manager = RiskManager(
            initial_balance=self.initial_balance,
            risk_per_trade=0.02,
            max_risk_per_trade=0.05,
            min_lot_size=0.01,
            max_lot_size=1.0
        )
        
        if strategy_class.__name__ == 'MLStrategy':
            if model_path is None:
                raise ValueError("Model path must be provided for MLStrategy")
            model = joblib.load(model_path)
            
            # Ensure features match those used in training
            if features is None:
                features = ['macd', 'signal_line', 'rsi']
            
            self.strategy = strategy_class(
                data_source=self.data_source,
                risk_manager=risk_manager,
                symbol=self.symbol,
                timeframe=self.timeframe,
                model=model,
                features=features,
                initial_balance=self.initial_balance,
                start_date=self.start_date,
                end_date=self.end_date
            )
        else:
            self.strategy = strategy_class(
                data_source=self.data_source,
                risk_manager=risk_manager,
                symbol=self.symbol,
                timeframe=self.timeframe,
                initial_balance=self.initial_balance,
                start_date=self.start_date,
                end_date=self.end_date
            )
        
        logging.info(f"Initialized TradingSystem with strategy: {type(self.strategy).__name__}, "
                     f"data source: {type(self.data_source).__name__}, symbol: {symbol}, timeframe: {timeframe}")

    def run(self):
        try:
            self.strategy.apply()
        except Exception as e:
            logging.error(f"An error occurred while running the trading system: {e}")
            raise

if __name__ == "__main__":
    # Example usage
    data_source = LiveDataSource()
    trading_system = TradingSystem(MACDStrategy, data_source, "EURUSD", "15")  # 15-minute timeframe
    trading_system.run()
