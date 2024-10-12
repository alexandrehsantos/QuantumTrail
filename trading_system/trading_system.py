import logging
from datetime import datetime
from typing import Dict, Any
from .data_sources.data_source import DataSource
from .strategies.strategy import Strategy
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
    def __init__(self, data_source: DataSource, strategy_class: type):
        self.data_source = data_source
        self.strategy_class = strategy_class
        self.conn = sqlite3.connect('trading_history.db')
        self.create_tables()
        
        logging.info(f"Initialized TradingSystem with data source: {type(self.data_source).__name__}")

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

    def run_strategy(self, symbol: str, timeframe: int, initial_balance: float, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        mapped_timeframe = map_timeframe(timeframe)
        logging.info(f"Running strategy for {symbol} with mapped timeframe {mapped_timeframe}")
        
        strategy = self.strategy_class(
            data_source=self.data_source,
            symbol=symbol,
            timeframe=mapped_timeframe,
            start_date=start_date,
            end_date=end_date,
            initial_balance=initial_balance
        )
        
        result = strategy.apply()
        if start_date is not None and end_date is not None:
            self._process_backtest_results(result)
        return result

    def _process_backtest_results(self, results: Dict[str, Any]) -> None:
        with self.conn:
            for trade in results['trades']:
                self.conn.execute('''
                    INSERT INTO execution_data (time, balance, trade_type, price, lot_size)
                    VALUES (?, ?, ?, ?, ?)
                ''', (datetime.now().isoformat(), results['final_balance'], trade['type'], trade['price'], trade['lot_size']))
        logging.info(f"Backtest results processed. Final balance: {results['final_balance']}")

    def start_automation(self, symbol: str, timeframe: int, initial_balance: float) -> None:
        self.run_strategy(symbol, timeframe, initial_balance)

    def run(self):
        symbol = self.data_source.symbol
        timeframe = self.data_source.timeframe
        initial_balance = 10000  # You may want to make this configurable

        result = self.run_strategy(symbol, timeframe, initial_balance)
        logging.info(f"Strategy execution completed. Result: {result}")

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
