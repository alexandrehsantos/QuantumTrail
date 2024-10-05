import MetaTrader5 as mt5
import pandas as pd
import logging
from trading_system.data_sources.data_source import DataSource

class LiveDataSource(DataSource):
    def initialize(self):
        if not mt5.initialize():
            logging.error("MetaTrader 5 failed to initialize.")
            return False
        logging.info("Live data source initialized.")
        return True

    def get_data(self, symbol: str, timeframe: int, start_date=None, end_date=None) -> pd.DataFrame:
        logging.info(f"Fetching live data for {symbol} with timeframe {timeframe}")

        if not mt5.symbol_select(symbol, True):
            logging.error(f"Failed to select symbol: {symbol}")
            raise ValueError(f"Failed to select symbol: {symbol}")

        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            logging.error(f"Symbol info not found for: {symbol}")
            raise ValueError(f"Symbol info not found for: {symbol}")

        if not symbol_info.visible:
            logging.info(f"Symbol {symbol} is not visible, attempting to make it visible")
            if not mt5.symbol_select(symbol, True):
                logging.error(f"Failed to make symbol {symbol} visible")
                raise ValueError(f"Failed to make symbol {symbol} visible")

        try:
            logging.info(f"Calling mt5.copy_rates_from_pos with symbol={symbol}, timeframe={timeframe}, start_pos=0, count=1000")
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 1000)
        except Exception as e:
            logging.error(f"Error fetching data: {e}")
            raise

        if rates is None or len(rates) == 0:
            logging.error(f"No data retrieved for symbol: {symbol}, timeframe: {timeframe}")
            raise ValueError("No data retrieved. Please check the symbol and timeframe.")
        
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)
        return df

    def buy_order(self, symbol, volume, price, sl, tp, deviation=10, magic=234000, comment="Buy Order"):
        return self.place_order(mt5.ORDER_TYPE_BUY, symbol, volume, price, sl, tp, deviation, magic, comment)

    def sell_order(self, symbol, volume, price, sl, tp, deviation=10, magic=234000, comment="Sell Order"):
        return self.place_order(mt5.ORDER_TYPE_SELL, symbol, volume, price, sl, tp, deviation, magic, comment)

    def place_order(self, order_type, symbol, volume, price, sl, tp, deviation, magic, comment):
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": order_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": deviation,
            "magic": magic,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }
        result = mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            logging.info(f"Order placed successfully. Order ticket: {result.order}")
            return {"status": "executed", "order": result.order}
        else:
            logging.error(f"Order failed. Error code: {result.retcode}")
            return {"status": "failed", "error_code": result.retcode}

    def get_positions(self, symbol: str):
        positions = mt5.positions_get(symbol=symbol)
        if positions:
            return [pos._asdict() for pos in positions]
        return []

    def close_position(self, ticket: int):
        position = mt5.position_get(ticket=ticket)
        if not position:
            logging.error(f"No position found with ticket: {ticket}")
            return None
        position = position[0]
        symbol = position.symbol
        volume = position.volume
        position_type = position.type
        price = mt5.symbol_info_tick(symbol).bid if position_type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(symbol).ask

        close_request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "position": ticket,
            "symbol": symbol,
            "volume": volume,
            "type": mt5.ORDER_TYPE_SELL if position_type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY,
            "price": price,
            "deviation": 10,
            "magic": position.magic,
            "comment": "Position Close",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }

        result = mt5.order_send(close_request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            logging.info(f"Position {ticket} closed successfully.")
        else:
            logging.error(f"Failed to close position {ticket}. Error code: {result.retcode}")
        return result._asdict()

    def __del__(self):
        mt5.shutdown()