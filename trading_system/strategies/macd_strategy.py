import pandas as pd
import logging
from trading_system.data_sources.data_source import DataSource

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def log_info(message):
    logging.info(message)

class MACDStrategy:
    def __init__(
        self,
        data_source: DataSource,
        symbol: str,
        timeframe: int,
        rsi_overbought: int = 70,
        rsi_oversold: int = 30,
        stop_loss_percent: float = 1.0,
        take_profit_percent: float = 2.0,
    ):
        self.data_source = data_source
        self.symbol = symbol
        self.timeframe = timeframe
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold
        self.stop_loss_percent = stop_loss_percent
        self.take_profit_percent = take_profit_percent
        self.trade_open = False

    def apply(self, initial_balance, start_date, end_date):
        df = self.data_source.get_data(self.symbol, self.timeframe, start_date, end_date)
        df = self.calculate_indicators(df)
        df.dropna(inplace=True)
        balance = initial_balance

        for index, row in df.iterrows():
            current_price = row['close']
            macd_hist = row['macd_hist']
            rsi = row['rsi']

            if macd_hist > 0 and rsi < self.rsi_overbought and not self.trade_open:
                self.execute_buy(current_price)
            elif macd_hist < 0 and rsi > self.rsi_oversold and not self.trade_open:
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
        sl = price - (price * self.stop_loss_percent / 100)
        tp = price + (price * self.take_profit_percent / 100)
        result = self.data_source.buy_order(self.symbol, 0.01, price, sl, tp)
        if result.get('status') == 'executed':
            logging.info(f"Buy order placed at {price}")
            self.trade_open = True
        else:
            logging.error(f"Buy order failed: {result.get('error_code')}")

    def execute_sell(self, price):
        sl = price + (price * self.stop_loss_percent / 100)
        tp = price - (price * self.take_profit_percent / 100)
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
                if current_price >= position['price'] + (position['price'] * self.take_profit_percent / 100):
                    logging.info(f"Take Profit reached for buy position. Closing at {current_price}")
                    self.data_source.close_position(position['ticket'])
                    self.trade_open = False
                elif current_price <= position['price'] - (position['price'] * self.stop_loss_percent / 100):
                    logging.info(f"Stop Loss reached for buy position. Closing at {current_price}")
                    self.data_source.close_position(position['ticket'])
                    self.trade_open = False
            elif position['type'] == 'sell':
                if current_price <= position['price'] - (position['price'] * self.take_profit_percent / 100):
                    logging.info(f"Take Profit reached for sell position. Closing at {current_price}")
                    self.data_source.close_position(position['ticket'])
                    self.trade_open = False
                elif current_price >= position['price'] + (position['price'] * self.stop_loss_percent / 100):
                    logging.info(f"Stop Loss reached for sell position. Closing at {current_price}")
                    self.data_source.close_position(position['ticket'])
                    self.trade_open = False

    def update_balance(self, balance, current_price):
        # Implement balance update logic based on executed trades
        return balance

    def calculate_lot_size(self, risk_amount: float) -> float:
        # Implement your lot size calculation logic here
        return 0.1  # Example fixed lot size