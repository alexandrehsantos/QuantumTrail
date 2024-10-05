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
mean_window = 20
std_dev_factor = 2
risk_percent = 0.02

def get_data(symbol, timeframe, num_candles=1000):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, num_candles)
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=True)
    return df

def calculate_indicators(df):
    df['mean'] = df['close'].rolling(window=mean_window).mean()
    df['std_dev'] = df['close'].rolling(window=mean_window).std()
    df['upper_band'] = df['mean'] + (df['std_dev'] * std_dev_factor)
    df['lower_band'] = df['mean'] - (df['std_dev'] * std_dev_factor)
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
        "comment": "Mean Reversion",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_FOK,
    }
    result = mt5.order_send(request)
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        log_info(f"Order placed successfully. Order ticket: {result.order}")
    else:
        log_info(f"Order failed. Error code: {result.retcode}")
    return result

def mean_reversion_trading():
    while True:
        df = get_data(symbol, mt5.TIMEFRAME_M5)
        df = calculate_indicators(df)
        current_price = df['close'].iloc[-1]
        upper_band = df['upper_band'].iloc[-1]
        lower_band = df['lower_band'].iloc[-1]
        mean = df['mean'].iloc[-1]

        if current_price > upper_band:
            sl = current_price + (current_price - mean)
            tp = mean
            lot = calculate_lot_size(abs(current_price - sl))
            place_order(mt5.ORDER_TYPE_SELL, current_price, sl, tp, lot)
        elif current_price < lower_band:
            sl = current_price - (mean - current_price)
            tp = mean
            lot = calculate_lot_size(abs(current_price - sl))
            place_order(mt5.ORDER_TYPE_BUY, current_price, sl, tp, lot)

        log_info("Waiting for 1 minute before next check")
        time.sleep(60)

# Start trading
if __name__ == "__main__":
    mean_reversion_trading()
    mt5.shutdown()