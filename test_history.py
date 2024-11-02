import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime

# Initialize connection to MT5
if not mt5.initialize():
    print("Failed to initialize MetaTrader5:", mt5.last_error())
    quit()

# Set symbol and timeframe
symbol = "BTCUSD"
timeframe = mt5.TIMEFRAME_H1  # 1-hour timeframe

# Define the time range for historical data
start_time = datetime(2023, 1, 1)
end_time = datetime.now()

# Fetch historical data
rates = mt5.copy_rates_range(symbol, timeframe, start_time, end_time)

# Shutdown the connection to MT5
mt5.shutdown()

# Convert data to a pandas DataFrame for analysis
df = pd.DataFrame(rates)
df['time'] = pd.to_datetime(df['time'], unit='s')

# Display the historical data
print(df)
