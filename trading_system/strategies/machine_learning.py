import logging
import pandas as pd
import MetaTrader5 as mt5
from enum import Enum
from order_type import OrderType
import time
from datetime import datetime
from trading_system.strategies.strategy import Strategy
import traceback
import numpy as np
from typing import List, Optional
from trading_system.data_sources.data_source import DataSource
from trading_system.risk_management.risk_manager import RiskManager

class MLStrategy(Strategy):
    def __init__(self, data_source: DataSource, risk_manager: RiskManager, symbol: str, timeframe: str, 
                 model, features: List[str], initial_balance: float, start_date: str, end_date: str):
        super().__init__(data_source, risk_manager, symbol, timeframe, initial_balance, start_date, end_date)
        self.model = model
        self.features = features if isinstance(features, list) else ['macd', 'signal_line', 'rsi', 'log_tick_volume', 'log_spread', 'high_low_range', 'close_open_range']
        self.trade_open = False

    def apply(self):
        logging.info("Starting ML Strategy")
        while True:
            try:
                data = self.data_source.get_data(self.symbol, self.timeframe)
                if data is None or data.empty:
                    logging.warning("No data available to apply strategy.")
                    time.sleep(5)
                    continue

                logging.info(f"Received data shape: {data.shape}")
                logging.info(f"Received data columns: {data.columns.tolist()}")

                data = self.prepare_data(data)
                if data is None:
                    logging.error("Failed to prepare data.")
                    time.sleep(5)
                    continue

                X = data[self.features]
                predictions = self.model.predict(X)
                self.execute_trades(data, predictions)
                self.manage_positions(data['close'].iloc[-1])
                time.sleep(60)  # Wait for 1 minute before next iteration

            except Exception as e:
                logging.error(f"An error occurred: {e}")
                logging.error(f"Error traceback: {traceback.format_exc()}")
                time.sleep(5)

    def prepare_data(self, data: pd.DataFrame) -> Optional[pd.DataFrame]:
        try:
            # Calculate technical indicators
            data = self.calculate_indicators(data)

            # Ensure all required features are present
            missing_features = [f for f in self.features if f not in data.columns]
            if missing_features:
                logging.error(f"Missing required features: {missing_features}")
                return None

            data.dropna(inplace=True)

            # Ensure the order of features matches the model's expectations
            return data[self.features]
        except Exception as e:
            logging.error(f"Error in prepare_data: {e}")
            return None

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        # Existing calculations
        data['ema_12'] = data['close'].ewm(span=12, adjust=False).mean()
        data['ema_26'] = data['close'].ewm(span=26, adjust=False).mean()
        data['macd'] = data['ema_12'] - data['ema_26']
        data['signal_line'] = data['macd'].ewm(span=9, adjust=False).mean()
        data['rsi'] = self.compute_rsi(data['close'], period=14)
        
        # New features from tick data
        if 'tick_volume' in data.columns and 'log_tick_volume' not in data.columns:
            data['log_tick_volume'] = np.log1p(data['tick_volume'])
        if 'spread' in data.columns and 'log_spread' not in data.columns:
            data['log_spread'] = np.log1p(data['spread'])
        if 'high_low_range' not in data.columns:
            data['high_low_range'] = data['high'] - data['low']
        if 'close_open_range' not in data.columns:
            data['close_open_range'] = data['close'] - data['open']
        
        return data

    def compute_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def execute_trades(self, data: pd.DataFrame, predictions: np.ndarray):
        # Implement your trading logic here
        # For example:
        current_price = data['close'].iloc[-1]
        if predictions[-1] == 1 and not self.trade_open:
            # Place a buy order
            self.place_buy_order(current_price)
        elif predictions[-1] == 0 and self.trade_open:
            # Place a sell order
            self.place_sell_order(current_price)

    def manage_positions(self, current_price: float):
        # Implement your position management logic here
        # For example, check for stop loss or take profit
        pass

    def place_buy_order(self, price: float):
        # Implement buy order logic
        logging.info(f"Placing buy order at price: {price}")
        # Use self.data_source.buy_order() to place the actual order
        self.trade_open = True

    def place_sell_order(self, price: float):
        # Implement sell order logic
        logging.info(f"Placing sell order at price: {price}")
        # Use self.data_source.sell_order() to place the actual order
        self.trade_open = False

    def update_balance(self, balance: float, current_price: float):
        # Implement balance update logic here
        pass

    @staticmethod
    def _map_timeframe(timeframe: str) -> int:
        timeframe_map = {'1m': 1, '5m': 5, '15m': 15, '30m': 30, '1h': 60, '4h': 240, '1d': 1440}
        return timeframe_map.get(timeframe, 1)
