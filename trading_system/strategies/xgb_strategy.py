import logging
import pandas as pd
import numpy as np
import joblib
from datetime import datetime
from typing import Optional  # Import Optional from typing
from .strategy import Strategy
from trading_system.data_sources.data_source import DataSource
from trading_system.risk_management.risk_manager import RiskManager
import time
import traceback

class XGBStrategy(Strategy):
    def __init__(self, data_source: DataSource, risk_manager: RiskManager, symbol: str, timeframe: str, 
                 model_path: str, features: list, initial_balance: float, start_date: str, end_date: str, start_with_min_volume: bool = False):
        super().__init__(data_source, risk_manager, symbol, timeframe, initial_balance, start_date, end_date)
        self.model = joblib.load(model_path)
        self.features = features
        self.trade_open = False
        self.start_with_min_volume = start_with_min_volume

    def apply(self):
        logging.info("Starting XGB Strategy")
        while True:
            try:
                data = self.data_source.get_data(self.symbol, self.timeframe)
                if data is None or data.empty:
                    logging.warning("No data available to apply strategy.")
                    time.sleep(5)
                    continue

                logging.info(f"Received data shape: {data.shape}")
                logging.info(f"Received data columns: {data.columns.tolist()}")

                prepared_data = self.prepare_data(data)
                if prepared_data is None:
                    logging.error("Failed to prepare data.")
                    time.sleep(5)
                    continue

                X = prepared_data[self.features]
                predictions = self.model.predict(X)
                self.execute_trades(prepared_data, predictions)
                self.manage_positions(prepared_data['close'].iloc[-1])
                time.sleep(60)  # Wait for 1 minute before next iteration

            except Exception as e:
                logging.error(f"An error occurred: {e}")
                logging.error(f"Error traceback: {traceback.format_exc()}")
                time.sleep(5)

    def prepare_data(self, data: pd.DataFrame) -> Optional[pd.DataFrame]:
        try:
            prepared_data = data.copy()
            prepared_data['ema_12'] = prepared_data['close'].ewm(span=12, adjust=False).mean()
            prepared_data['ema_26'] = prepared_data['close'].ewm(span=26, adjust=False).mean()
            prepared_data['macd'] = prepared_data['ema_12'] - prepared_data['ema_26']
            prepared_data['signal_line'] = prepared_data['macd'].ewm(span=9, adjust=False).mean()
            prepared_data['rsi'] = self.compute_rsi(prepared_data['close'], period=14)
            prepared_data['log_tick_volume'] = np.log1p(prepared_data['tick_volume'])
            prepared_data['log_spread'] = np.log1p(prepared_data['spread'])
            prepared_data['high_low_range'] = prepared_data['high'] - prepared_data['low']
            prepared_data['close_open_range'] = prepared_data['close'] - prepared_data['open']

            missing_features = [f for f in self.features if f not in prepared_data.columns]
            if missing_features:
                logging.error(f"Missing required features: {missing_features}")
                return None

            prepared_data.dropna(inplace=True)
            return prepared_data
        except Exception as e:
            logging.error(f"Error in prepare_data: {e}")
            return None

    def execute_trades(self, data: pd.DataFrame, predictions: np.ndarray):
        current_price = data['close'].iloc[-1]
        volume = 0.01  # Minimum trade size

        min_stop_level = self.get_min_stop_distance(self.symbol)
        spread = self.data_source.get_current_spread(self.symbol)

        stop_loss_distance = max(current_price * 0.01, min_stop_level + spread)
        take_profit_distance = max(current_price * 0.01, min_stop_level + spread)

        if predictions[-1] == 1 and not self.trade_open:
            sl = current_price - stop_loss_distance
            tp = current_price + take_profit_distance
            sl = self.data_source.normalize_price(sl, self.symbol)
            tp = self.data_source.normalize_price(tp, self.symbol)
            logging.info("Buy signal detected")
            self.place_buy_order(current_price, volume, sl, tp)
        elif predictions[-1] == 0 and self.trade_open:
            sl = current_price + stop_loss_distance
            tp = current_price - take_profit_distance
            sl = self.data_source.normalize_price(sl, self.symbol)
            tp = self.data_source.normalize_price(tp, self.symbol)
            logging.info("Sell signal detected")
            self.place_sell_order(current_price, volume, sl, tp)

    def get_min_stop_distance(self, symbol: str) -> float:
        symbol_info = self.data_source.mt5.symbol_info(symbol)
        if symbol_info is None:
            raise RuntimeError(f"Failed to get symbol info for {symbol}")

        min_stop_level_points = symbol_info.trade_stops_level
        point_size = symbol_info.point

        min_stop_distance = min_stop_level_points * point_size
        return min_stop_distance

    def manage_positions(self, current_price: float):
        # Implement your position management logic here
        pass

    def update_balance(self, balance, current_price):
        # Implement balance update logic here
        logging.info(f"Updating balance. Current balance: {balance}, Current price: {current_price}")

    def place_buy_order(self, price: float, volume: float, sl: float, tp: float):
        logging.info(f"Placing buy order at price: {price}")
        try:
            result = self.data_source.buy_order(self.symbol, volume, price, sl, tp)
            if result and result.retcode == self.data_source.mt5.TRADE_RETCODE_DONE:
                self.trade_open = True
                logging.info(f"Buy order placed successfully. Ticket: {result.order}")
            else:
                logging.error(f"Failed to place buy order: {result}")
        except Exception as e:
            logging.error(f"Failed to place buy order: {e}")

    def place_sell_order(self, price: float, volume: float, sl: float, tp: float):
        logging.info(f"Placing sell order at price: {price}")
        try:
            result = self.data_source.sell_order(self.symbol, volume, price, sl, tp)
            if result and result.retcode == self.data_source.mt5.TRADE_RETCODE_DONE:
                self.trade_open = False
                logging.info(f"Sell order placed successfully. Ticket: {result.order}")
            else:
                logging.error(f"Failed to place sell order: {result}")
        except Exception as e:
            logging.error(f"Failed to place sell order: {e}")

    def compute_rsi(self, series, period=14):
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
