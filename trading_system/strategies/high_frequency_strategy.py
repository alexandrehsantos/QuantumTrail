import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from .strategy import Strategy
from .order_type import OrderType

class HighFrequencyStrategy(Strategy):
    def __init__(self, data_source, risk_manager, symbol, timeframe, initial_balance,
                 start_date, end_date, **kwargs):
        super().__init__(data_source, risk_manager, symbol, timeframe, initial_balance,
                         start_date, end_date)
        self.trade_open = False
        self.window_size = kwargs.get('window_size', 50)
        self.threshold = kwargs.get('threshold', 0.0001)
        self.min_volume = kwargs.get('min_volume', 0.01)
        logging.info(f"Initialized HighFrequencyStrategy for {symbol} with timeframe {timeframe}")

    def apply(self):
        logging.info(f"Starting High Frequency Strategy for {self.symbol}")
        while True:
            try:
                data = self.data_source.get_tick_data(self.symbol)
                if data is None or data.empty:
                    logging.warning("No tick data available.")
                    continue

                mid_prices = (data['ask'] + data['bid']) / 2
                if len(mid_prices) < self.window_size:
                    logging.info(f"Accumulating tick data. Current length: {len(mid_prices)}")
                    continue

                returns = mid_prices.pct_change().dropna()
                mean = returns[-self.window_size:].mean()
                std = returns[-self.window_size:].std()

                z_score = (returns.iloc[-1] - mean) / std if std != 0 else 0

                current_price = mid_prices.iloc[-1]

                if z_score > self.threshold and not self.trade_open:
                    logging.info(f"Sell signal detected. Z-Score: {z_score}")
                    self.execute_trade(OrderType.SELL, current_price)
                elif z_score < -self.threshold and not self.trade_open:
                    logging.info(f"Buy signal detected. Z-Score: {z_score}")
                    self.execute_trade(OrderType.BUY, current_price)

                self.manage_positions(current_price)
            except Exception as e:
                logging.error(f"An error occurred: {str(e)}")

    def execute_trade(self, order_type: OrderType, price: float):
        volume = self.min_volume
        min_stop_distance = self.data_source.get_min_stop_distance(self.symbol)  # Fetch minimum stop distance
        spread = self.data_source.get_current_spread(self.symbol)  # Fetch current spread

        # Calculate stop loss and take profit distances
        stop_loss_distance = max(price * 0.01, min_stop_distance + spread)
        take_profit_distance = max(price * 0.01, min_stop_distance + spread)

        # Adjust SL and TP based on order type
        if order_type == OrderType.BUY:
            sl = price - stop_loss_distance
            tp = price + take_profit_distance
        else:
            sl = price + stop_loss_distance
            tp = price - take_profit_distance

        # Normalize prices
        sl = self.data_source.normalize_price(sl, self.symbol)
        tp = self.data_source.normalize_price(tp, self.symbol)

        # Place order
        if order_type == OrderType.BUY:
            result = self.data_source.buy_order(self.symbol, volume, price, sl, tp)
        else:
            result = self.data_source.sell_order(self.symbol, volume, price, sl, tp)

        # Check result
        if result and result.retcode == self.data_source.mt5.TRADE_RETCODE_DONE:
            self.trade_open = True
            logging.info(f"{order_type.value.capitalize()} order placed successfully.")
        else:
            logging.error(f"Failed to place {order_type.value} order: {result}")

    def manage_positions(self, current_price: float):
        positions = self.data_source.get_positions(self.symbol)
        for position in positions:
            if self.should_close_position(position, current_price):
                self.close_position(position)

    def should_close_position(self, position, current_price: float) -> bool:
        profit_threshold = 0.0002  # 0.02% profit
        entry_price = position.price_open
        profit = (current_price - entry_price) / entry_price if position.type == 0 else (entry_price - current_price) / entry_price
        return abs(profit) >= profit_threshold

    def close_position(self, position):
        result = self.data_source.close_position(position.ticket)
        if result and hasattr(result, 'retcode') and result.retcode == self.data_source.mt5.TRADE_RETCODE_DONE:
            self.trade_open = False
            logging.info(f"Position {position.ticket} closed successfully.")
        else:
            logging.error(f"Failed to close position {position.ticket}: {result}")

    def update_balance(self, balance, current_price):
        # Balance updates handled by risk manager
        pass
