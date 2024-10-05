import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import time
import logging
from datetime import datetime, timedelta

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
StopLossPercent = 1
TakeProfitPercent = 2
RSIOverbought = 70
RSIOversold = 30
risk_percent = 0.02

def get_data(symbol, timeframe, start_date=None):
    # Request the rates
    if start_date:
        rates = mt5.copy_rates_from(symbol, timeframe, start_date, 1000)
    else:
        num_candles = 1000
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, num_candles)
    
    df = pd.DataFrame(rates)
    
    if df.empty:
        raise ValueError("No data retrieved. Please check the symbol, timeframe, and connection.")
    
    if 'time' in df.columns:
        df['time'] = pd.to_datetime(df['time'], unit='s')
    elif 'datetime' in df.columns:
        df['time'] = pd.to_datetime(df['datetime'], unit='s')
    else:
        raise ValueError("No 'time' or 'datetime' column found in the DataFrame")
    
    df.set_index('time', inplace=True)
    return df

def calculate_indicators(df):
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

def calculate_lot_size(stop_loss_points):
    account_balance = mt5.account_info().balance
    risk_amount = account_balance * risk_percent
    pip_value = mt5.symbol_info(symbol).trade_tick_value  # Get tick value from symbol info
    lot_size = risk_amount / (stop_loss_points * pip_value)
    return round(lot_size, 2)

def refresh_price(symbol):
    tick = mt5.symbol_info_tick(symbol)
    return tick.bid, tick.ask

def log_trade_request(request):
    log_info("Trade Request:")
    for key, value in request.items():
        log_info(f"{key}: {value}")

def buy_order():
    price = mt5.symbol_info_tick(symbol).ask
    sl = price - (price * StopLossPercent / 100)
    tp = price + (price * TakeProfitPercent / 100)
    stop_loss_points = abs(price - sl)
    lot = calculate_lot_size(stop_loss_points)

    log_info(f"Placing buy order: Price={price}, SL={sl}, TP={tp}, Lot={lot}")
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": mt5.ORDER_TYPE_BUY,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": 10,
        "magic": 234000,
        "comment": "Buy signal",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_FOK,
    }
    result = mt5.order_send(request)
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        log_info(f"Buy order placed successfully. Order ticket: {result.order}")
    else:
        log_info(f"Buy order failed. Error code: {result.retcode}")
    return result

def sell_order():
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        log_info(f"{symbol} not found")
        return
    if not symbol_info.visible:
        if not mt5.symbol_select(symbol, True):
            log_info(f"Failed to select {symbol}")
            return
    if symbol_info.trade_mode == mt5.SYMBOL_TRADE_MODE_DISABLED:
        log_info(f"Trading is disabled for {symbol}")
        return

    bid, ask = refresh_price(symbol)
    price = bid

    sl = price + (price * StopLossPercent / 100)
    tp = price - (price * TakeProfitPercent / 100)

    sl_points = abs(price - sl) / symbol_info.point
    lot = calculate_lot_size(sl_points)

    log_info(f"Placing sell order: Price={price}, SL={sl}, TP={tp}, Lot={lot}")
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": mt5.ORDER_TYPE_SELL,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": 20,
        "magic": 234000,
        "comment": "Sell signal",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_FOK,  # Changed to FOK
    }
    log_trade_request(request)

    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        log_info(f"Order failed, retcode={result.retcode}")
        result_dict = result._asdict()
        for field in result_dict.keys():
            log_info(f"{field}={result_dict[field]}")
    else:
        log_info(f"Order placed successfully. Order ticket: {result.order}")
    return result

def live_trading():
    trade_open = False
    log_info("Starting trading loop")
    while True:
        df = get_data(symbol, mt5.TIMEFRAME_M5)
        df = calculate_indicators(df)
        df.dropna(inplace=True)  # Ensure no NaN values
        current_price = df['close'].iloc[-1]
        macd_hist = df['macd_hist'].iloc[-1]
        rsi = df['rsi'].iloc[-1]
        log_info(f"Current price: {current_price}")
        log_info(f"MACD Histogram: {macd_hist}, RSI: {rsi}")

        if macd_hist > 0 and rsi < RSIOverbought and not trade_open:
            log_info("Buy signal detected")
            result = buy_order()
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                log_info(f"Buy order placed at {current_price}")
                trade_open = True

        elif macd_hist < 0 and rsi > RSIOversold and not trade_open:
            log_info("Sell signal detected")
            result = sell_order()
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                log_info(f"Sell order placed at {current_price}")
                trade_open = True

        positions = mt5.positions_get(symbol=symbol)
        if positions:
            for position in positions:
                if position.type == mt5.ORDER_TYPE_BUY:
                    if current_price >= position.price_open + (position.price_open * TakeProfitPercent / 100):
                        log_info(f"Take Profit reached for buy position. Closing at {current_price}")
                        mt5.order_close(position.ticket)
                        trade_open = False
                    elif current_price <= position.price_open - (position.price_open * StopLossPercent / 100):
                        log_info(f"Stop Loss reached for buy position. Closing at {current_price}")
                        mt5.order_close(position.ticket)
                        trade_open = False
                elif position.type == mt5.ORDER_TYPE_SELL:
                    if current_price <= position.price_open - (position.price_open * TakeProfitPercent / 100):
                        log_info(f"Take Profit reached for sell position. Closing at {current_price}")
                        mt5.order_close(position.ticket)
                        trade_open = False
                    elif current_price >= position.price_open + (position.price_open * StopLossPercent / 100):
                        log_info(f"Stop Loss reached for sell position. Closing at {current_price}")
                        mt5.order_close(position.ticket)
                        trade_open = False
        log_info("Waiting for 1 minute before next check")
        time.sleep(60)

# Start trading
if __name__ == "__main__":
    live_trading()

    # Shutdown MetaTrader 5 connection when done
    mt5.shutdown()
