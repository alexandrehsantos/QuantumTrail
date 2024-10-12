import MetaTrader5 as mt5
import pandas as pd
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class BreakoutTrading:
    def __init__(self, symbol, lookback_period, risk_percent):
        self.symbol = symbol
        self.lookback_period = lookback_period
        self.risk_percent = risk_percent

    def get_data(self, timeframe, num_candles=1000):
        rates = mt5.copy_rates_from_pos(self.symbol, timeframe, 0, num_candles)
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)
        return df

    def calculate_indicators(self, df):
        df['high'] = df['high'].rolling(window=self.lookback_period).max()
        df['low'] = df['low'].rolling(window=self.lookback_period).min()
        return df

    def calculate_lot_size(self, stop_loss_points):
        account_balance = mt5.account_info().balance
        risk_amount = account_balance * self.risk_percent
        pip_value = mt5.symbol_info(self.symbol).trade_tick_value
        lot_size = risk_amount / (stop_loss_points * pip_value)
        return round(lot_size, 2)

    def place_order(self, order_type, price, sl, tp, lot):
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
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
            logging.info(f"Order placed successfully. Order ticket: {result.order}")
        else:
            logging.info(f"Order failed. Error code: {result.retcode}")
        return result

    def trade(self):
        while True:
            df = self.get_data(mt5.TIMEFRAME_M5)
            df = self.calculate_indicators(df)
            current_price = df['close'].iloc[-1]
            high = df['high'].iloc[-1]
            low = df['low'].iloc[-1]

            if current_price > high:
                sl = low
                tp = current_price + (current_price - low)
                lot = self.calculate_lot_size(abs(current_price - sl))
                self.place_order(mt5.ORDER_TYPE_BUY, current_price, sl, tp, lot)
            elif current_price < low:
                sl = high
                tp = current_price - (high - current_price)
                lot = self.calculate_lot_size(abs(current_price - sl))
                self.place_order(mt5.ORDER_TYPE_SELL, current_price, sl, tp, lot)

            logging.info("Waiting for 1 minute before next check")
            time.sleep(60)

if __name__ == "__main__":
    if not mt5.initialize():
        logging.info("MetaTrader 5 failed to initialize")
        quit()

    # Example usage: Assume `symbol` is received from the UI
    symbol_from_ui = "BTCUSD"  # This should be dynamically set based on UI input
    breakout_trading = BreakoutTrading(symbol=symbol_from_ui, lookback_period=20, risk_percent=0.02)
    breakout_trading.trade()
    mt5.shutdown()