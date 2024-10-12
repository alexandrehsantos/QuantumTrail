from trading_system.strategies.strategy import Strategy
import logging
import pandas as pd

class MLStrategy(Strategy):
    def __init__(self, data_source, risk_manager, symbol, timeframe, model, features):
        super().__init__(data_source, risk_manager, symbol, timeframe)
        self.model = model
        self.features = features

    def apply(self):
        logging.info("Applying ML Strategy")
        data = self.data_source.get_data(self.symbol, self.timeframe)
        if data.empty:
            logging.warning("No data available to apply strategy.")
            return

        # Prepare data for prediction
        data = self.prepare_data(data)
        X = data[self.features]

        # Predict signals
        data['signal'] = self.model.predict(X)
        data['position'] = data['signal'].diff()

        # Execute trades based on signals
        for index, row in data.iterrows():
            if row['position'] == 1:
                self.execute_buy(row['close'])
            elif row['position'] == -1:
                self.execute_sell(row['close'])

    def prepare_data(self, data):
        # Add feature engineering logic here
        data['ema_12'] = data['close'].ewm(span=12, adjust=False).mean()
        data['ema_26'] = data['close'].ewm(span=26, adjust=False).mean()
        data['macd'] = data['ema_12'] - data['ema_26']
        data['signal_line'] = data['macd'].ewm(span=9, adjust=False).mean()
        data['rsi'] = self.compute_rsi(data['close'], period=14)
        data.dropna(inplace=True)
        return data

    def compute_rsi(self, series, period=14):
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def execute_buy(self, price):
        # Implement buy logic
        logging.info(f"Executing buy at {price}")

    def execute_sell(self, price):
        # Implement sell logic
        logging.info(f"Executing sell at {price}")