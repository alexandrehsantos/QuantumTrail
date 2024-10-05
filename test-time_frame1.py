import MetaTrader5 as mt5
import pandas as pd
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def log_info(message):
    logging.info(message)

def diagnose_1min_data(symbol, start_date, end_date):
    # Initialize MetaTrader 5
    if not mt5.initialize():
        log_info("MetaTrader 5 failed to initialize")
        return

    # Convert start and end dates to datetime objects
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")

    # Check if the symbol is available
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        log_info(f"Symbol {symbol} not found")
        mt5.shutdown()
        return

    if not symbol_info.visible:
        if not mt5.symbol_select(symbol, True):
            log_info(f"Failed to select {symbol}")
            mt5.shutdown()
            return

    # Fetch 1-minute historical data
    log_info(f"Fetching 1-minute data for {symbol} from {start_date} to {end_date}")
    rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M1, start_date, end_date)

    if rates is None or len(rates) == 0:
        log_info(f"No data retrieved for symbol: {symbol}, timeframe: 1 minute, start_date: {start_date}, end_date: {end_date}")
        mt5.shutdown()
        return

    # Convert to DataFrame
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=True)

    # Print each value in the DataFrame
    for index, row in df.iterrows():
        print(f"Time: {index}, Open: {row['open']}, High: {row['high']}, Low: {row['low']}, Close: {row['close']}, Tick Volume: {row['tick_volume']}, Spread: {row['spread']}, Real Volume: {row['real_volume']}")

    # Shutdown MetaTrader 5
    mt5.shutdown()

if __name__ == "__main__":
    symbol = "BTCUSD"
    start_date = "2024-01-01"
    end_date = "2024-01-02"
    diagnose_1min_data(symbol, start_date, end_date)