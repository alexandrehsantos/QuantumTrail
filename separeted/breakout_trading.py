import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def log_info(message):
    logging.info(message)

# Initialize MetaTrader 5
if not mt5.initialize():
    log_info("MetaTrader 5 failed to initialize")
    quit()

# Define trading parameters
symbol = "BTCUSD"
lookback_period = 20
risk_percent = 0.02

def get_data(symbol, timeframe, num_candles=1000):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, num_candles)
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=True)
    return df

def calculate_indicators(df):
    df['high'] = df['high'].rolling(window=lookback_period).max()
    df['low'] = df['low'].rolling(window=lookback_period).min()
    return df

def calculate_lot_size(stop_loss_points):
    account_balance = mt5.account_info().balance
    risk_amount = account_balance * risk_percent
    pip_value = mt5.symbol_info(symbol).trade_tick_value
    lot_size = risk_amount / (stop_loss_points * pip_value)
    return round(lot_size, 2)

def place_order(order_type, price, sl, tp, lot):
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": order_type,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": 10,
        "magic": 234000,
        "comment": "Breakout Trading",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_FOK,
    }
    result = mt5.order_send(request)
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        log_info(f"Order placed successfully. Order ticket: {result.order}")
    else:
        log_info(f"Order failed. Error code: {result.retcode}")
    return result

def breakout_trading():
    while True:
        df = get_data(symbol, mt5.TIMEFRAME_M5)
        df = calculate_indicators(df)
        current_price = df['close'].iloc[-1]
        high = df['high'].iloc[-1]
        low = df['low'].iloc[-1]

        if current_price > high:
            sl = low
            tp = current_price + (current_price - low)
            lot = calculate_lot_size(abs(current_price - sl))
            place_order(mt5.ORDER_TYPE_BUY, current_price, sl, tp, lot)
        elif current_price < low:
            sl = high
            tp = current_price - (high - current_price)
            lot = calculate_lot_size(abs(current_price - sl))
            place_order(mt5.ORDER_TYPE_SELL, current_price, sl, tp, lot)

        log_info("Waiting for 1 minute before next check")
        time.sleep(60)

# Start trading
if __name__ == "__main__":
    breakout_trading()
    mt5.shutdown()