import MetaTrader5 as mt5
import pandas as pd
import logging
from datetime import datetime
from .data_source import DataSource

class HistoricalDataSource(DataSource):
    def __init__(self):
        self.simulated_positions = []

    def initialize(self):
        if not mt5.initialize():
            logging.error("MetaTrader 5 initialization failed.")
            return False
        logging.info("Historical data source initialized.")
        return True

    def get_data(self, symbol, timeframe, start_date, end_date) -> pd.DataFrame:
        logging.info(f"Fetching historical data for {symbol} with timeframe {timeframe} from {start_date} to {end_date}")
        
        # Ensure the symbol is selected and visible
        if not mt5.symbol_select(symbol, True):
            logging.error(f"Failed to select symbol: {symbol}")
            raise ValueError(f"Symbol {symbol} not found or not selected")

        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            logging.error(f"Symbol info not found for: {symbol}")
            raise ValueError(f"Symbol info not found for: {symbol}")

        if not symbol_info.visible:
            logging.info(f"Symbol {symbol} is not visible, attempting to make it visible")
            if not mt5.symbol_select(symbol, True):
                logging.error(f"Failed to make symbol {symbol} visible")
                raise ValueError(f"Failed to make symbol {symbol} visible")

        # Convert start_date and end_date to datetime objects if they are strings
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d")

        # Fetch historical rates
        try:
            logging.info(f"Calling mt5.copy_rates_range with symbol={symbol}, timeframe={timeframe}, from_={start_date}, to_={end_date}")
            rates = mt5.copy_rates_range(symbol, timeframe, start_date, end_date)
        except Exception as e:
            logging.error(f"Error fetching data: {e}")
            raise

        if rates is None or len(rates) == 0:
            logging.error(f"No data retrieved for symbol: {symbol}, timeframe: {timeframe}, start_date: {start_date}, end_date: {end_date}")
            # Check if the date range is in the future
            current_time = datetime.now()
            if start_date > current_time or end_date > current_time:
                raise ValueError("The specified date range is in the future. Please use a past date range.")
            # Check if the symbol is available for the specified timeframe
            available_data = mt5.copy_rates_from(symbol, timeframe, current_time, 1)
            if available_data is None or len(available_data) == 0:
                raise ValueError(f"No data available for symbol: {symbol} in the specified timeframe.")
            raise ValueError("No data retrieved. Please check the symbol and timeframe.")

        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)
        return df

    def buy_order(self, symbol, volume, price, sl, tp, deviation=10, magic=234000, comment="Buy Order"):
        logging.info(f"Simulated buy order: {symbol}, volume: {volume}, price: {price}, sl: {sl}, tp: {tp}")
        order = {
            "type": "buy",
            "symbol": symbol,
            "volume": volume,
            "price": price,
            "sl": sl,
            "tp": tp,
            "ticket": len(self.simulated_positions) + 1
        }
        self.simulated_positions.append(order)
        return {"status": "executed", "order_type": "buy", "tp": tp, "sl": sl}

    def sell_order(self, symbol, volume, price, sl, tp, deviation=10, magic=234000, comment="Sell Order"):
        logging.info(f"Simulated sell order: {symbol}, volume: {volume}, price: {price}, sl: {sl}, tp: {tp}")
        order = {
            "type": "sell",
            "symbol": symbol,
            "volume": volume,
            "price": price,
            "sl": sl,
            "tp": tp,
            "ticket": len(self.simulated_positions) + 1
        }
        self.simulated_positions.append(order)
        return {"status": "executed", "order_type": "sell", "tp": tp, "sl": sl}

    def get_positions(self, symbol: str):
        return self.simulated_positions

    def close_position(self, ticket: int):
        for pos in self.simulated_positions:
            if pos["ticket"] == ticket:
                logging.info(f"Simulated closing of position {ticket}")
                self.simulated_positions.remove(pos)
                return {"status": "executed"}
        logging.error(f"No simulated position found with ticket: {ticket}")
        return None

    def __del__(self):
        mt5.shutdown()