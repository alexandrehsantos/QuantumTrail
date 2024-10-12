from datetime import datetime, timedelta
import logging
import time
from trading_system.strategies.strategy import Strategy
import pandas as pd
import numpy as np

class MACDStrategy(Strategy):
    def __init__(self, data_source, symbol: str, timeframe: int, start_date: str = None, end_date: str = None, initial_balance: float = None, rsi_overbought: int = 70, rsi_oversold: int = 30):
        super().__init__(data_source, symbol, timeframe, start_date, end_date, initial_balance)
        self.required_candles = 78  # Adjust as needed for MACD calculation
        self.fast_period = 12
        self.slow_period = 26
        self.signal_period = 9
        self.rsi_period = 14
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold

    def apply(self) -> dict:
        logging.info(f"Starting MACD trading for {self.symbol} with timeframe {self.timeframe}")
        balance = self.initial_balance
        trades = []
        last_processed_time = None

        while True:
            try:
                # Fetch data
                if last_processed_time:
                    new_data = self.data_source.get_data(self.symbol, self.timeframe, start_date=last_processed_time)
                    logging.info(f"Fetched new data: {len(new_data)} rows")
                    if not new_data.empty:
                        data = pd.concat([data, new_data])
                        data = data.iloc[-self.required_candles:]
                else:
                    end_time = datetime.now()
                    start_time = end_time - timedelta(minutes=self.required_candles * self.timeframe)
                    data = self.data_source.get_data(self.symbol, self.timeframe, start_date=start_time, end_date=end_time)
                    logging.info(f"Fetched initial data: {len(data)} rows")

                if data.empty or len(data) < self.required_candles:
                    logging.info(f"Not enough data for {self.symbol}. Waiting...")
                    time.sleep(5)
                    continue

                logging.info(f"Data columns: {data.columns}")
                logging.info(f"First few rows of data:\n{data.head()}")

                # Calculate indicators
                data = self.calculate_indicators(data)
                
                # Get the latest values
                current_price = data['close'].iloc[-1]
                macd = data['macd'].iloc[-1]
                signal = data['signal'].iloc[-1]
                histogram = data['histogram'].iloc[-1]
                rsi = data['rsi'].iloc[-1]

                logging.info(f"Current price: {current_price}, MACD: {macd:.4f}, Signal: {signal:.4f}, Histogram: {histogram:.4f}, RSI: {rsi:.2f}")

                # Check for buy signal
                if histogram > 0 and rsi < self.rsi_overbought and not self.trade_open:
                    logging.info("Buy signal detected")
                    # Place buy order
                    order_result = self.data_source.buy_order(self.symbol, 0.01, current_price, current_price * 0.99, current_price * 1.02)
                    logging.info(f"Buy order result: {order_result}")
                    if order_result:
                        logging.info(f"Buy order placed at {current_price}")
                        self.trade_open = True
                        trades.append(('buy', current_price, datetime.now()))
                    else:
                        logging.error("Failed to place buy order")

                # Check for sell signal
                elif histogram < 0 and rsi > self.rsi_oversold and not self.trade_open:
                    logging.info("Sell signal detected")
                    # Place sell order
                    order_result = self.data_source.sell_order(self.symbol, 0.01, current_price, current_price * 1.01, current_price * 0.98)
                    logging.info(f"Sell order result: {order_result}")
                    if order_result:
                        logging.info(f"Sell order placed at {current_price}")
                        self.trade_open = True
                        trades.append(('sell', current_price, datetime.now()))
                    else:
                        logging.error("Failed to place sell order")

                # Manage open positions
                if self.trade_open:
                    self.manage_positions(current_price)

                last_processed_time = data.index[-1]
                logging.info(f"Last processed time: {last_processed_time}")

                # Add a small delay to avoid excessive API calls
                time.sleep(1)

            except Exception as e:
                logging.error(f"Error in trading: {str(e)}")
                break

        return {'final_balance': balance, 'trades': trades}

    def calculate_indicators(self, data):
        # Calculate MACD
        exp1 = data['close'].ewm(span=self.fast_period, adjust=False).mean()
        exp2 = data['close'].ewm(span=self.slow_period, adjust=False).mean()
        data['macd'] = exp1 - exp2
        data['signal'] = data['macd'].ewm(span=self.signal_period, adjust=False).mean()
        data['histogram'] = data['macd'] - data['signal']

        # Calculate RSI
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        data['rsi'] = 100 - (100 / (1 + rs))

        return data
