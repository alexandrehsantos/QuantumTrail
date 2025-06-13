import logging
import time
import pandas as pd
import numpy as np
from .strategy import Strategy
from order_type import OrderType
from collections import deque
from datetime import datetime, timedelta

class ChartPatternStrategy(Strategy):
    def __init__(self, data_source, risk_manager, symbol, timeframe, initial_balance, start_date, end_date, start_with_min_volume=False, auto_trade=False):
        super().__init__(data_source, risk_manager, symbol, timeframe, initial_balance, start_date, end_date)
        self.start_with_min_volume = start_with_min_volume
        self.min_volume = 0.01  # Set a default minimum volume
        logging.info(f"Initialized ChartPatternStrategy for {symbol} with timeframe {timeframe}")
        self.trade_open = False
        self.last_trade_time = None
        self.cooldown_period = timedelta(minutes=30)
        self.warning_cooldown = timedelta(minutes=5)
        self.last_warning_time = None
        self.consecutive_warnings = 0
        self.max_consecutive_warnings = 2  # Reduced from 3 to 2
        self.open_position = None
        self.auto_trade = auto_trade
        
        self.max_lookback = self.calculate_max_lookback()
        self.stored_data = deque(maxlen=self.max_lookback + 50)
        logging.debug(f"min_volume initialized: {self.min_volume}")
        self.risk_per_trade = 0.01  # 1% risk per trade

    def calculate_max_lookback(self):
        # Return the maximum lookback period used in any indicator or pattern detection
        return max(
            20,  # For rolling windows in pattern detection
            14,  # For RSI calculation (if used)
            26   # For MACD calculation (if used)
        )

    def apply(self):
        logging.info(f"Starting Chart Pattern Strategy for {self.symbol}")
        while True:
            try:
                data = self.data_source.get_data(self.symbol, self.timeframe)
                if data is None or data.empty:
                    logging.warning("No data available to apply strategy.")
                    time.sleep(5)
                    continue

                self.store_data(data)

                if len(self.stored_data) < self.max_lookback:
                    logging.info(f"Accumulating data. Current length: {len(self.stored_data)}")
                    time.sleep(60)
                    continue

                analysis_data = pd.DataFrame(list(self.stored_data))
                
                patterns = self.detect_patterns(analysis_data)

                current_time = datetime.now()
                if self.last_trade_time and (current_time - self.last_trade_time) < self.cooldown_period:
                    logging.info("In cooldown period, skipping trade analysis.")
                    time.sleep(60)
                    continue

                if not self.open_position:
                    trade_decision = self.analyze_pre_trade(analysis_data, patterns)
                    if trade_decision['should_trade']:
                        self.warn_and_confirm(trade_decision, analysis_data)
                else:
                    self.manage_positions(analysis_data['close'].iloc[-1])

                time.sleep(60)

            except Exception as e:
                logging.error(f"An error occurred: {e}")
                time.sleep(5)

    def warn_and_confirm(self, trade_decision, data):
        current_time = datetime.now()
        if self.last_warning_time and (current_time - self.last_warning_time) < self.warning_cooldown:
            logging.info("Warning cooldown in effect, skipping warning.")
            return

        self.consecutive_warnings += 1
        logging.warning(f"Warning {self.consecutive_warnings}: {trade_decision['direction']} signal detected")
        logging.info(f"Signal strength: {trade_decision['strength']}")
        logging.info(f"Current price: {data['close'].iloc[-1]}")
        logging.info(f"RSI: {self.calculate_rsi(data['close']).iloc[-1]:.2f}")
        macd, signal, _ = self.calculate_macd(data['close'])
        logging.info(f"MACD: {macd.iloc[-1]:.2f}, Signal: {signal.iloc[-1]:.2f}")
        
        logging.info("Signal details:")
        for reason in trade_decision['reasons']:
            logging.info(f"  {reason}")
        
        self.last_warning_time = current_time

        if self.consecutive_warnings >= self.max_consecutive_warnings:
            logging.warning(f"Preparing to execute trade after {self.consecutive_warnings} consecutive warnings")
            if self.auto_trade:
                self.execute_trade(data, trade_decision['direction'])
            else:
                confirmation = input(f"Do you want to execute this {trade_decision['direction'].value} trade? (yes/no): ").lower()
                if confirmation == 'yes':
                    self.execute_trade(data, trade_decision['direction'])
                else:
                    logging.info("Trade execution cancelled by user.")
            self.reset_warnings()

    def execute_trade(self, data, order_type: OrderType):
        price = data['close'].iloc[-1]
        
        # Calculate position size based on risk percentage
        account_balance = self.data_source.get_account_balance()
        risk_amount = account_balance * self.risk_per_trade
        stop_loss_distance = price * 0.01  # 1% stop loss
        position_size = risk_amount / stop_loss_distance
        
        # Ensure position size is within allowed limits
        min_volume = self.data_source.get_min_lot_size(self.symbol)
        max_volume = self.data_source.get_max_lot_size(self.symbol)
        volume = max(min(position_size, max_volume), min_volume)
        
        # Round volume to the nearest valid step size
        volume_step = self.data_source.get_volume_step(self.symbol)
        volume = round(volume / volume_step) * volume_step

        min_stop_distance = self.data_source.get_min_stop_distance(self.symbol)
        spread = self.data_source.get_current_spread(self.symbol)

        # Calculate stop loss and take profit distances
        stop_loss_distance = max(price * 0.01, min_stop_distance + spread)
        take_profit_distance = max(price * 0.02, min_stop_distance + spread)  # 2% take profit

        # Adjust SL and TP based on order type
        if order_type == OrderType.BUY:
            sl = price - stop_loss_distance
            tp = price + take_profit_distance
        elif order_type == OrderType.SELL:
            sl = price + stop_loss_distance
            tp = price - take_profit_distance
        else:
            raise ValueError("Invalid order type")

        # Normalize prices
        sl = self.data_source.normalize_price(sl, self.symbol)
        tp = self.data_source.normalize_price(tp, self.symbol)

        # Place order
        result = None
        if order_type == OrderType.BUY:
            result = self.data_source.buy_order(self.symbol, volume, price, sl, tp)
        elif order_type == OrderType.SELL:
            result = self.data_source.sell_order(self.symbol, volume, price, sl, tp)

        # Check result
        if result and hasattr(result, 'retcode') and result.retcode == self.data_source.mt5.TRADE_RETCODE_DONE:
            self.trade_open = True
            self.open_position = {
                'type': order_type,
                'entry_price': price,
                'volume': volume,
                'sl': sl,
                'tp': tp,
                'ticket': getattr(result, 'order', None)
            }
            logging.info(f"{order_type.value.capitalize()} order placed successfully. Entry: {price}, SL: {sl}, TP: {tp}, Volume: {volume}")
        else:
            logging.error(f"Failed to place {order_type.value} order: {result}")

        self.last_trade_time = datetime.now()
        self.reset_warnings()

    def manage_positions(self, current_price):
        if not self.open_position:
            return

        entry_price = self.open_position['entry_price']
        if self.open_position['type'] == OrderType.BUY:
            profit = (current_price - entry_price) / entry_price
        else:
            profit = (entry_price - current_price) / entry_price

        if profit >= 0.02 or profit <= -0.01:  # 2% take profit or 1% stop loss
            self.close_position(current_price)

    def close_position(self, current_price):
        if not self.open_position:
            return

        logging.warning(f"Closing position at price: {current_price}")

        ticket = self.open_position.get('ticket')
        if ticket is not None:
            result = self.data_source.close_position(ticket)
        else:
            logging.error("No ticket found for open position; cannot close.")
            return

        logging.info(f"Close result type: {type(result)}")
        logging.info(f"Close result content: {result}")

        if hasattr(result, 'retcode') and result.retcode == self.data_source.mt5.TRADE_RETCODE_DONE:
            logging.info(f"Position closed at price: {current_price}")
            self.open_position = None
        else:
            logging.error(f"Failed to close position. Result: {result}")

    def reset_warnings(self):
        if self.consecutive_warnings > 0:
            logging.info(f"Resetting warnings. Previous count: {self.consecutive_warnings}")
        self.consecutive_warnings = 0
        self.last_warning_time = None

    def analyze_pre_trade(self, data, patterns):
        analysis = {
            'should_trade': False,
            'direction': None,
            'strength': 0,
            'reasons': []
        }

        # Check for persistent pattern
        if patterns['bullish'].iloc[-3:].all():
            analysis['direction'] = OrderType.BUY
            analysis['strength'] += 1
            analysis['reasons'].append("Persistent bullish pattern")
        elif patterns['bearish'].iloc[-3:].all():
            analysis['direction'] = OrderType.SELL
            analysis['strength'] += 1
            analysis['reasons'].append("Persistent bearish pattern")
        else:
            return analysis  # No persistent pattern, don't trade

        # Volume confirmation
        if data['volume'].iloc[-1] > data['volume'].rolling(window=20).mean().iloc[-1]:
            analysis['strength'] += 1
            analysis['reasons'].append("Volume confirmation")

        # Trend confirmation (using simple moving averages)
        short_ma = data['close'].rolling(window=10).mean()
        long_ma = data['close'].rolling(window=30).mean()
        if analysis['direction'] == OrderType.BUY and short_ma.iloc[-1] > long_ma.iloc[-1]:
            analysis['strength'] += 1
            analysis['reasons'].append("Upward trend confirmation")
        elif analysis['direction'] == OrderType.SELL and short_ma.iloc[-1] < long_ma.iloc[-1]:
            analysis['strength'] += 1
            analysis['reasons'].append("Downward trend confirmation")

        # RSI confirmation
        rsi = self.calculate_rsi(data['close'])
        if analysis['direction'] == OrderType.BUY and 30 < rsi.iloc[-1] < 70:
            analysis['strength'] += 1
            analysis['reasons'].append(f"RSI confirmation: {rsi.iloc[-1]:.2f}")
        elif analysis['direction'] == OrderType.SELL and 30 < rsi.iloc[-1] < 70:
            analysis['strength'] += 1
            analysis['reasons'].append(f"RSI confirmation: {rsi.iloc[-1]:.2f}")

        # MACD confirmation
        macd, signal, _ = self.calculate_macd(data['close'])
        if analysis['direction'] == OrderType.BUY and macd.iloc[-1] > signal.iloc[-1]:
            analysis['strength'] += 1
            analysis['reasons'].append(f"MACD confirmation: MACD {macd.iloc[-1]:.2f} > Signal {signal.iloc[-1]:.2f}")
        elif analysis['direction'] == OrderType.SELL and macd.iloc[-1] < signal.iloc[-1]:
            analysis['strength'] += 1
            analysis['reasons'].append(f"MACD confirmation: MACD {macd.iloc[-1]:.2f} < Signal {signal.iloc[-1]:.2f}")

        # Decide if we should trade based on the strength of signals
        analysis['should_trade'] = analysis['strength'] >= 4  # Adjust this threshold as needed

        return analysis

    def calculate_rsi(self, prices, period=14):
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def calculate_macd(self, prices, fast_period=12, slow_period=26, signal_period=9):
        fast_ema = prices.ewm(span=fast_period, adjust=False).mean()
        slow_ema = prices.ewm(span=slow_period, adjust=False).mean()
        macd = fast_ema - slow_ema
        signal = macd.ewm(span=signal_period, adjust=False).mean()
        histogram = macd - signal
        return macd, signal, histogram

    def store_data(self, data):
        """Store the latest data."""
        for _, row in data.iterrows():
            self.stored_data.append({
                'time': row.name,
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close'],
                'volume': row['tick_volume']
            })
        logging.debug(f"Stored data. Current length: {len(self.stored_data)}")

    def detect_patterns(self, data: pd.DataFrame) -> pd.DataFrame:
        patterns = pd.DataFrame(index=data.index)
        patterns['ascending_triangle'] = self.detect_ascending_triangle(data)
        patterns['descending_triangle'] = self.detect_descending_triangle(data)
        patterns['head_and_shoulders'] = self.detect_head_and_shoulders(data)
        patterns['double_top'] = self.detect_double_top(data)
        patterns['double_bottom'] = self.detect_double_bottom(data)
        patterns['flag'] = self.detect_flags(data)
        patterns['wedge'] = self.detect_wedges(data)
        patterns['rectangle'] = self.detect_rectangles(data)
        patterns['cup_and_handle'] = self.detect_cup_and_handle(data)

        # Combine patterns into a single bullish/bearish signal
        patterns['bullish'] = patterns[['ascending_triangle', 'double_bottom', 'flag', 'cup_and_handle']].any(axis=1)
        patterns['bearish'] = patterns[['descending_triangle', 'head_and_shoulders', 'double_top', 'wedge']].any(axis=1)

        return patterns

    def detect_ascending_triangle(self, data: pd.DataFrame) -> pd.Series:
        result = (data['high'].rolling(window=5).max() == data['high'].rolling(window=20).max()) & \
                 (data['low'].rolling(window=5).min() > data['low'].rolling(window=20).min())
        logging.debug(f"Ascending Triangle detected: {result.any()}")
        return result

    def detect_descending_triangle(self, data: pd.DataFrame) -> pd.Series:
        result = (data['low'].rolling(window=5).min() == data['low'].rolling(window=20).min()) & \
                 (data['high'].rolling(window=5).max() < data['high'].rolling(window=20).max())
        logging.debug(f"Descending Triangle detected: {result.any()}")
        return result

    def detect_head_and_shoulders(self, data: pd.DataFrame) -> pd.Series:
        result = (data['high'].shift(1) < data['high']) & \
                 (data['high'].shift(-1) < data['high']) & \
                 (data['low'].shift(1) > data['low']) & \
                 (data['low'].shift(-1) > data['low'])
        logging.debug(f"Head and Shoulders detected: {result.any()}")
        return result

    def detect_double_top(self, data: pd.DataFrame) -> pd.Series:
        result = (data['high'].shift(1) == data['high']) & \
                 (data['high'].shift(-1) == data['high'])
        logging.debug(f"Double Top detected: {result.any()}")
        return result

    def detect_double_bottom(self, data: pd.DataFrame) -> pd.Series:
        result = (data['low'].shift(1) == data['low']) & \
                 (data['low'].shift(-1) == data['low'])
        logging.debug(f"Double Bottom detected: {result.any()}")
        return result

    def detect_flags(self, data: pd.DataFrame) -> pd.Series:
        result = (data['close'].rolling(window=5).mean() > data['close'].rolling(window=20).mean())
        logging.debug(f"Flag detected: {result.any()}")
        return result

    def detect_wedges(self, data: pd.DataFrame) -> pd.Series:
        result = (data['high'].rolling(window=5).max() < data['high'].rolling(window=20).max()) & \
                 (data['low'].rolling(window=5).min() > data['low'].rolling(window=20).min())
        logging.debug(f"Wedge detected: {result.any()}")
        return result

    def detect_rectangles(self, data: pd.DataFrame) -> pd.Series:
        result = (data['high'].rolling(window=5).max() == data['high'].rolling(window=20).max()) & \
                 (data['low'].rolling(window=5).min() == data['low'].rolling(window=20).min())
        logging.debug(f"Rectangle detected: {result.any()}")
        return result

    def detect_cup_and_handle(self, data: pd.DataFrame) -> pd.Series:
        result = (data['close'].rolling(window=10).mean() < data['close'].rolling(window=20).mean()) & \
                 (data['close'].rolling(window=5).mean() > data['close'].rolling(window=10).mean())
        logging.debug(f"Cup and Handle detected: {result.any()}")
        return result

    def update_balance(self, balance, current_price):
        # Implement balance update logic here
        pass

    def get_stored_data(self):
        """Return the stored data."""
        return list(self.stored_data)










