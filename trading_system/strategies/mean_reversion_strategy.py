import pandas as pd
import logging
from trading_system.data_sources.data_source import DataSource

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MeanReversionStrategy:
    def __init__(
        self,
        data_source: DataSource,
        symbol: str,
        timeframe: int,
        mean_window: int = 20,
        std_dev_factor: float = 2.0,
        risk_percent: float = 0.02
    ):
        self.data_source = data_source
        self.symbol = symbol
        self.timeframe = timeframe
        self.mean_window = mean_window
        self.std_dev_factor = std_dev_factor
        self.risk_percent = risk_percent
        self.trade_open = False

    def apply(self, initial_balance, start_date, end_date):
        df = self.data_source.get_data(self.symbol, self.timeframe, start_date, end_date)
        df = self.calculate_indicators(df)
        df.dropna(inplace=True)
        balance = initial_balance

        for index, row in df.iterrows():
            current_price = row['close']
            upper_band = row['upper_band']
            lower_band = row['lower_band']

            if current_price > upper_band and not self.trade_open:
                self.execute_sell(current_price)
            elif current_price < lower_band and not self.trade_open:
                self.execute_buy(current_price)

            self.manage_positions(current_price)
            balance = self.update_balance(balance, current_price)

        return balance

    def calculate_indicators(self, df):
        df['mean'] = df['close'].rolling(window=self.mean_window).mean()
        df['std_dev'] = df['close'].rolling(window=self.mean_window).std()
        df['upper_band'] = df['mean'] + (df['std_dev'] * self.std_dev_factor)
        df['lower_band'] = df['mean'] - (df['std_dev'] * self.std_dev_factor)
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