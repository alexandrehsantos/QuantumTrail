import MetaTrader5 as mt5
import pandas as pd
import time
from datetime import datetime, timedelta
import numpy as np

# Initialize MetaTrader 5
if not mt5.initialize():
    print("MetaTrader 5 initialization failed")
    quit()

symbol = "BTCUSD"
timeframe = mt5.TIMEFRAME_M1  # 1-minute timeframe

def get_last_candle():
    current_time = datetime.now().replace(second=0, microsecond=0)
    past_time = current_time - timedelta(minutes=1)
    rates = mt5.copy_rates_range(symbol, timeframe, past_time, current_time)
    if rates is not None and len(rates) > 0:
        last_candle = rates[-1]
        return {
            'time': datetime.fromtimestamp(last_candle['time']),
            'open': last_candle['open'],
            'high': last_candle['high'],
            'low': last_candle['low'],
            'close': last_candle['close'],
            'volume': last_candle['tick_volume']
        }
    return None

def print_last_candle():
    candle = get_last_candle()
    if candle:
        print(f"Time: {candle['time']}")
        print(f"Open: {candle['open']}")
        print(f"High: {candle['high']}")
        print(f"Low: {candle['low']}")
        print(f"Close: {candle['close']}")
        print(f"Volume: {candle['volume']}")
        print("------------------------")
    else:
        print("No data available")

try:
    while True:
        print_last_candle()
        time.sleep(30)  # Wait for 30 seconds before the next print
except KeyboardInterrupt:
    print("Script terminated by user")
finally:
    mt5.shutdown()