import logging
from datetime import datetime
from .data_sources.data_source import DataSource
from .strategies.strategy import Strategy
import MetaTrader5 as mt5
import sqlite3
import matplotlib.pyplot as plt

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def log_info(message):
    logging.info(message)

def map_timeframe(timeframe):
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
    def __init__(self, data_source: DataSource, strategy_class: Strategy):
        self.data_source = data_source
        self.strategy_class = strategy_class
        self.conn = sqlite3.connect('trading_history.db')
        self.create_tables()

    def create_tables(self):
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS execution_data (
                    time TEXT,
                    balance REAL
                )
            ''')

    def start_automation(self, symbol: str, timeframe: int):
        mapped_timeframe = map_timeframe(timeframe)
        logging.info(f"Starting automation for {symbol} with mapped timeframe {mapped_timeframe}")
        strategy = self.strategy_class(
            data_source=self.data_source,
            symbol=symbol,
            timeframe=mapped_timeframe
        )
        
        while True:
            # Implement live trading logic here
            pass  # Placeholder for actual implementation

    def run_backtest(self, symbol: str, timeframe: int, start_date, end_date):
        mapped_timeframe = map_timeframe(timeframe)
        logging.info(f"Running backtest for {symbol} with mapped timeframe {mapped_timeframe} from {start_date} to {end_date}")
        
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
        
        try:
            df = self.data_source.get_data(symbol, mapped_timeframe, start_date, end_date)
        except ValueError as e:
            logging.error(f"Error retrieving data: {e}")
            return

        strategy = self.strategy_class(
            data_source=self.data_source,
            symbol=symbol,
            timeframe=mapped_timeframe
        )
        final_balance = strategy.apply(initial_balance=10000, start_date=start_date, end_date=end_date)
        logging.info(f"Final Balance after backtest: {final_balance}")

def main():
    import argparse
    from trading_system.strategies.macd_strategy import MACDStrategy
    from trading_system.strategies.mean_reversion_strategy import MeanReversionStrategy
    from trading_system.data_sources.historical_data_source import HistoricalDataSource
    from trading_system.data_sources.live_data_source import LiveDataSource

    parser = argparse.ArgumentParser(description="Trading System")
    parser.add_argument('--mode', choices=['live', 'backtest'], required=True, help="Mode to run the trading system")
    parser.add_argument('--strategy', choices=['macd', 'mean_reversion'], required=True, help="Trading strategy to use")
    parser.add_argument('--symbol', required=True, help="Trading symbol")
    parser.add_argument('--timeframe', type=int, required=True, help="Timeframe for trading")
    parser.add_argument('--start_date', help="Start date for backtesting (YYYY-MM-DD)")
    parser.add_argument('--end_date', help="End date for backtesting (YYYY-MM-DD)")
    args = parser.parse_args()

    if args.strategy == 'macd':
        strategy_class = MACDStrategy
    elif args.strategy == 'mean_reversion':
        strategy_class = MeanReversionStrategy

    if args.mode == 'backtest':
        data_source = HistoricalDataSource()
        if not data_source.initialize():
            logging.error("Failed to initialize HistoricalDataSource")
            return
        trading_system = TradingSystem(data_source, strategy_class)
        trading_system.run_backtest(args.symbol, args.timeframe, args.start_date, args.end_date)
    elif args.mode == 'live':
        data_source = LiveDataSource()
        if not data_source.initialize():
            logging.error("Failed to initialize LiveDataSource")
            return
        trading_system = TradingSystem(data_source, strategy_class)
        trading_system.start_automation(args.symbol, args.timeframe)

if __name__ == "__main__":
    main()