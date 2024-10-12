import pandas as pd
import logging
from trading_system.data_sources.data_source import DataSource

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def log_info(message):
    logging.info(message)

class EnchanceMACDStrategy(Strategy):
    def __init__(self, data_source, symbol: str, timeframe: int, start_date=None, end_date=None, initial_balance=None, RSIOverbought: int = 70, RSIOversold: int = 30, risk_percent: float = 0.02):
        super().__init__(data_source, symbol, timeframe, start_date, end_date)
        self.initial_balance = initial_balance
        self.RSIOverbought = RSIOverbought
        self.RSIOversold = RSIOversold
        self.risk_percent = risk_percent
        self.trade_open = False

    def apply(self):
        df = self.data_source.get_data(self.symbol, self.timeframe, self.start_date, self.end_date)
        df = self.calculate_indicators(df)
        df.dropna(inplace=True)
        balance = self.initial_balance

        for index, row in df.iterrows():
            current_price = row['close']
            macd_hist = row['macd_hist']
            rsi = row['rsi']

            if macd_hist > 0 and rsi < self.RSIOverbought and not self.trade_open:
                self.execute_buy(current_price)
            elif macd_hist < 0 and rsi > self.RSIOversold and not self.trade_open:
                self.execute_sell(current_price)

            self.manage_positions(current_price)
            balance = self.update_balance(balance, current_price)

        return balance

    def calculate_indicators(self, df):
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = exp1 - exp2
        df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['signal']
        
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        return df

    def execute_buy(self, price):
        sl = price - (price * 0.01)  # Example stop loss
        tp = price + (price * 0.02)  # Example take profit
        result = self.data_source.buy_order(self.symbol, 0.01, price, sl, tp)
        if result.get('status') == 'executed':
            logging.info(f"Buy order placed at {price}")
            self.trade_open = True
        else:
            logging.error(f"Buy order failed: {result.get('error_code')}")

    def execute_sell(self, price):
        sl = price + (price * 0.01)  # Example stop loss
        tp = price - (price * 0.02)  # Example take profit
        result = self.data_source.sell_order(self.symbol, 0.01, price, sl, tp)
        if result.get('status') == 'executed':
            logging.info(f"Sell order placed at {price}")
            self.trade_open = True
        else:
            logging.error(f"Sell order failed: {result.get('error_code')}")

    def manage_positions(self, current_price):
        positions = self.data_source.get_positions(self.symbol)
        for position in positions:
            if position['type'] == 'buy':
                sl = position['sl']
                tp = position['tp']
                if current_price >= tp:
                    logging.info(f"Take Profit reached for buy position. Closing at {current_price}")
                    self.data_source.close_position(position['ticket'])
                    self.trade_open = False
                elif current_price <= sl:
                    logging.info(f"Stop Loss reached for buy position. Closing at {current_price}")
                    self.data_source.close_position(position['ticket'])
                    self.trade_open = False
            elif position['type'] == 'sell':
                sl = position['sl']
                tp = position['tp']
                if current_price <= tp:
                    logging.info(f"Take Profit reached for sell position. Closing at {current_price}")
                    self.data_source.close_position(position['ticket'])
                    self.trade_open = False
                elif current_price >= sl:
                    logging.info(f"Stop Loss reached for sell position. Closing at {current_price}")
                    self.data_source.close_position(position['ticket'])
                    self.trade_open = False

    def update_balance(self, balance, current_price):
        # Implement balance update logic based on executed trades
        return balance