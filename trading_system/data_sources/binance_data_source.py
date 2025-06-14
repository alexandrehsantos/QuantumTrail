import os
from typing import Optional
import pandas as pd
from datetime import datetime
from .data_source import DataSource
from binance.client import Client
import logging

class BinanceDataSource(DataSource):
    """Data source using Binance API."""
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        self.api_key = api_key or os.getenv("BINANCE_API_KEY")
        self.api_secret = api_secret or os.getenv("BINANCE_API_SECRET")
        self.client: Optional[Client] = None

    def initialize(self):
        self.client = Client(self.api_key, self.api_secret)
        logging.info("Binance client initialized")

    def get_data(self, symbol: str, timeframe: str, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> pd.DataFrame:
        if self.client is None:
            raise RuntimeError("BinanceDataSource not initialized")

        start_str = start_date.strftime("%Y-%m-%d %H:%M:%S") if start_date else None
        end_str = end_date.strftime("%Y-%m-%d %H:%M:%S") if end_date else None

        klines = self.client.get_historical_klines(symbol, timeframe, start_str, end_str)
        if not klines:
            return pd.DataFrame()

        columns = [
            'open_time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'num_trades',
            'taker_buy_base_volume', 'taker_buy_quote_volume', 'ignore'
        ]
        df = pd.DataFrame(klines, columns=columns)
        df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
        df.set_index('open_time', inplace=True)
        df = df.astype(float)
        logging.info(f"Retrieved {len(df)} rows from Binance for {symbol}")
        return df[['open','high','low','close','volume']]

    def buy_order(self, symbol, volume, price, sl, tp, deviation=10, magic=234000, comment="Buy Order"):
        if self.client is None:
            raise RuntimeError("BinanceDataSource not initialized")
        return self.client.create_order(symbol=symbol, side='BUY', type='MARKET', quantity=volume)

    def sell_order(self, symbol, volume, price, sl, tp, deviation=10, magic=234000, comment="Sell Order"):
        if self.client is None:
            raise RuntimeError("BinanceDataSource not initialized")
        return self.client.create_order(symbol=symbol, side='SELL', type='MARKET', quantity=volume)

    def get_positions(self, symbol: str):
        if self.client is None:
            raise RuntimeError("BinanceDataSource not initialized")
        return self.client.get_open_orders(symbol=symbol)

    def close_position(self, ticket: int):
        # Binance API does not use ticket numbers in the same way; placeholder implementation
        logging.warning("close_position is not fully implemented for BinanceDataSource")
        return None
