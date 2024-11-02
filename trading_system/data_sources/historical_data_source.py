import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
import pytz
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class HistoricalDataSource:
    def __init__(self):
        self.initialized = False

    def initialize(self):
        if not mt5.initialize():
            logging.error(f"MetaTrader5 initialization failed. Error code: {mt5.last_error()}")
            return False
        self.initialized = True
        logging.info("MetaTrader5 initialized successfully.")
        return True

    def get_data(self, symbol, timeframe, start_date, end_date):
        if not self.initialized:
            if not self.initialize():
                return None

        # Convert timeframe string to MT5 timeframe
        mt5_timeframe = self.get_mt5_timeframe(timeframe)

        logging.info(f"Fetching historical data for {symbol} with timeframe {timeframe} from {start_date} to {end_date}")

        try:
            rates = mt5.copy_rates_range(symbol, mt5_timeframe, start_date, end_date)
            
            if rates is None or len(rates) == 0:
                logging.warning(f"No data available for {symbol} in the specified range.")
                return None

            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
            df.set_index('time', inplace=True)

            logging.info(f"Retrieved {len(df)} rows of historical data for {symbol}.")
            logging.info(f"Data range: from {df.index.min()} to {df.index.max()}")
            logging.info(f"Data columns: {df.columns.tolist()}")
            logging.info(f"First few rows of data:\n{df.head()}")
            logging.info(f"Last few rows of data:\n{df.tail()}")

            return df

        except Exception as e:
            logging.error(f"Error retrieving data: {e}")
            return None

    def get_mt5_timeframe(self, timeframe):
        timeframe_map = {
            '1m': mt5.TIMEFRAME_M1,
            '5m': mt5.TIMEFRAME_M5,
            '15m': mt5.TIMEFRAME_M15,
            '30m': mt5.TIMEFRAME_M30,
            '1h': mt5.TIMEFRAME_H1,
            '4h': mt5.TIMEFRAME_H4,
            '1d': mt5.TIMEFRAME_D1,
            '1w': mt5.TIMEFRAME_W1,
            '1mn': mt5.TIMEFRAME_MN1
        }
        return timeframe_map.get(timeframe.lower(), mt5.TIMEFRAME_M1)

    def __del__(self):
        if self.initialized:
            mt5.shutdown()
            logging.info("MetaTrader5 shut down.")

# Usage
if __name__ == "__main__":
    data_source = HistoricalDataSource()
    
    # Fetch data for the last hour
    end_date = datetime.now(pytz.utc)
    start_date = end_date - timedelta(hours=1)
    
    data = data_source.get_data("BTCUSD", "1m", start_date, end_date)
    
    if data is not None:
        print(data.head())
    else:
        print("Failed to fetch data.")
