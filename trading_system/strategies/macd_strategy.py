from datetime import datetime, timedelta
import logging
import time
import pandas as pd
from trading_system.strategies.strategy import Strategy
import MetaTrader5 as mt5

class MACDStrategy(Strategy):
    def __init__(self, data_source, risk_manager, symbol: str, timeframe: int):
        super().__init__(data_source, risk_manager, symbol, timeframe)
        self.fast_period = 12
        self.slow_period = 26
        self.signal_period = 9
        self.rsi_period = 14
        self.rsi_overbought = 70
        self.rsi_oversold = 30
        self.stop_loss_pct = 0.02
        self.take_profit_pct = 0.03
        self.required_candles = max(self.slow_period, self.rsi_period) + self.signal_period
        self.warm_up_candles = self.required_candles * 2

    def calculate_indicators(self, data):
        ema_fast = data['close'].ewm(span=self.fast_period, adjust=False).mean()
        ema_slow = data['close'].ewm(span=self.slow_period, adjust=False).mean()
        data['macd'] = ema_fast - ema_slow
        data['signal'] = data['macd'].ewm(span=self.signal_period, adjust=False).mean()
        data['histogram'] = data['macd'] - data['signal']
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        data['rsi'] = 100 - (100 / (1 + rs))
        return data

    def apply(self) -> dict:
        logging.info(f"Starting MACD trading for {self.symbol} with timeframe {self.timeframe}")
        trades = []
        warm_up_complete = False

        while True:
            try:
                current_time = datetime.now()
                start_time = current_time - timedelta(minutes=self.warm_up_candles * self.timeframe)
                data = self.data_source.get_data(self.symbol, self.timeframe, start_date=start_time, end_date=current_time)
                
                if len(data) < self.warm_up_candles:
                    logging.info(f"Not enough data for {self.symbol}. Waiting...")
                    time.sleep(5)
                    continue

                data = self.calculate_indicators(data)
                
                if not warm_up_complete:
                    logging.info("Warm-up period complete. Starting to analyze trading signals.")
                    warm_up_complete = True
                    continue

                current_price = data['close'].iloc[-1]
                histogram = data['histogram'].iloc[-1]
                prev_histogram = data['histogram'].iloc[-2]
                rsi = data['rsi'].iloc[-1]

                logging.info(f"Current price: {current_price}, Histogram: {histogram}, RSI: {rsi}")

                # Buy signal logic
                if histogram > 0 and prev_histogram <= 0 and rsi < self.rsi_overbought and not self.trade_open:
                    logging.info("Buy signal detected")
                    position_size = self.risk_manager.calculate_position_size(self.symbol, self.stop_loss_pct * current_price)
                    sl, tp = self.risk_manager.calculate_stop_loss_take_profit(
                        self.symbol, current_price, mt5.ORDER_TYPE_BUY, 
                        self.stop_loss_pct, self.take_profit_pct
                    )
                    logging.info(f"Attempting to place buy order with SL: {sl}, TP: {tp}, Position Size: {position_size}")
                    order_result = self.data_source.buy_order(self.symbol, position_size, current_price, sl, tp)
                    if order_result:
                        logging.info(f"Buy order placed at {current_price}")
                        self.trade_open = True
                        trades.append(('buy', current_price, datetime.now()))
                    else:
                        logging.error("Failed to place buy order")

                # Sell signal logic
                if histogram < 0 and prev_histogram >= 0 and rsi > self.rsi_oversold and not self.trade_open:
                    logging.info("Sell signal detected")
                    position_size = self.risk_manager.calculate_position_size(self.symbol, self.stop_loss_pct * current_price)
                    sl, tp = self.risk_manager.calculate_stop_loss_take_profit(
                        self.symbol, current_price, mt5.ORDER_TYPE_SELL, 
                        self.stop_loss_pct, self.take_profit_pct
                    )
                    logging.info(f"Attempting to place sell order with SL: {sl}, TP: {tp}, Position Size: {position_size}")
                    order_result = self.data_source.sell_order(self.symbol, position_size, current_price, sl, tp)
                    if order_result:
                        logging.info(f"Sell order placed at {current_price}")
                        self.trade_open = True
                        trades.append(('sell', current_price, datetime.now()))
                    else:
                        logging.error("Failed to place sell order")

                self.manage_positions(current_price)
                
                time.sleep(self.timeframe * 60)

            except Exception as e:
                logging.error(f"An error occurred: {e}")
                time.sleep(5)

        return {'trades': trades}
