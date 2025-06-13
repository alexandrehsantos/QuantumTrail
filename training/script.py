import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
import logging
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import TimeSeriesSplit, GridSearchCV
from sklearn.metrics import classification_report, accuracy_score
import numpy as np
import joblib  # Import joblib for saving the model

class HistoricalDataRetriever:
    def __init__(self, symbol, start_date, end_date):
        self.symbol = symbol
        self.timeframe = mt5.TIMEFRAME_M5  # 5-minute timeframe
        self.start_date = start_date
        self.end_date = end_date

    def initialize_mt5(self):
        if not mt5.initialize():
            logging.error("MetaTrader5 initialization failed.")
            return False
        logging.info("MetaTrader5 initialized successfully.")
        return True

    def shutdown_mt5(self):
        mt5.shutdown()
        logging.info("MetaTrader5 shutdown successfully.")

    def get_historical_data(self):
        if not self.initialize_mt5():
            return None

        try:
            rates = mt5.copy_rates_range(self.symbol, self.timeframe, self.start_date, self.end_date)
        except Exception as e:
            logging.error(f"Error retrieving data: {e}")
            rates = None
        finally:
            self.shutdown_mt5()

        if rates is None or len(rates) == 0:
            logging.warning(f"No data available for {self.symbol} in the specified range.")
            return None

        logging.info(f"Retrieved {len(rates)} rows of historical data for {self.symbol}.")
        return rates

    def convert_to_dataframe(self, rates):
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df

def prepare_data(data):
    # Existing indicators
    data['ema_12'] = data['close'].ewm(span=12, adjust=False).mean()
    data['ema_26'] = data['close'].ewm(span=26, adjust=False).mean()
    data['macd'] = data['ema_12'] - data['ema_26']
    data['signal_line'] = data['macd'].ewm(span=9, adjust=False).mean()
    data['rsi'] = compute_rsi(data['close'], period=14)
    
    # New features from tick data
    data['log_tick_volume'] = np.log1p(data['tick_volume'])
    data['log_spread'] = np.log1p(data['spread'])
    data['high_low_range'] = data['high'] - data['low']
    data['close_open_range'] = data['close'] - data['open']
    
    data['price_change'] = data['close'].shift(-1) - data['close']
    data['target'] = data['price_change'].apply(lambda x: 1 if x > 0 else 0)
    data.dropna(inplace=True)
    return data

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def main():
    logging.basicConfig(level=logging.INFO)

    symbol = "BTCUSD"
    start_date = datetime(2020, 1, 1)
    end_date = datetime(2020, 2, 28)

    all_data = []

    while True:
        data_retriever = HistoricalDataRetriever(symbol, start_date, end_date)
        rates = data_retriever.get_historical_data()

        if rates is not None:
            df = data_retriever.convert_to_dataframe(rates)
            all_data.append(df)
            print(f"Retrieved data for {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
            print(f"DataFrame size: {df.shape}")
            
            # Move to the next month
            start_date = end_date + pd.Timedelta(days=1)
            end_date = (start_date + pd.DateOffset(months=1)) - pd.Timedelta(days=1)
        else:
            print(f"No more data found after {start_date.strftime('%Y-%m-%d')}")
            break

    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        print("\nCombined DataFrame:")
        print(f"Total size: {combined_df.shape}")
        print("First row of the combined DataFrame:")
        print(combined_df.iloc[0])
        print("\nLast row of the combined DataFrame:")
        print(combined_df.iloc[-1])
    else:
        print(f"No data found for {symbol} in any of the date ranges.")
        return

    # Prepare the data
    df = prepare_data(combined_df)

    features = ['macd', 'signal_line', 'rsi', 'log_tick_volume', 'log_spread', 'high_low_range', 'close_open_range']
    X = df[features]
    y = df['target']

    tscv = TimeSeriesSplit(n_splits=5)
    model = RandomForestClassifier(random_state=42)

    param_grid = {
        'n_estimators': [50, 100, 200],
        'max_depth': [4, 6, 8],
        'min_samples_split': [2, 5, 10]
    }

    grid_search = GridSearchCV(model, param_grid, cv=tscv, scoring='accuracy')
    grid_search.fit(X, y)
    best_model = grid_search.best_estimator_

    y_pred = best_model.predict(X)
    print(classification_report(y, y_pred))
    print(f"Accuracy: {accuracy_score(y, y_pred)}")

    # Save the trained model
    joblib.dump(best_model, 'ml_model.pkl')
    print("Model saved as 'ml_model.pkl'")

if __name__ == "__main__":
    main()
