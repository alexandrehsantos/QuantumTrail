import os
from typing import Optional
import pandas as pd
from datetime import datetime
from .data_source import DataSource
from okx.api.market import Market
from okx.api.trade import Trade
import logging

class OKXDataSource(DataSource):
    """Data source using OKX API."""
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, passphrase: Optional[str] = None):
        self.api_key = api_key or os.getenv("OKX_API_KEY")
        self.api_secret = api_secret or os.getenv("OKX_API_SECRET")
        self.passphrase = passphrase or os.getenv("OKX_API_PASSPHRASE")
        self.market: Optional[Market] = None
        self.trade: Optional[Trade] = None

    def initialize(self):
        self.market = Market(self.api_key, self.api_secret, self.passphrase)
        self.trade = Trade(self.api_key, self.api_secret, self.passphrase)
        logging.info("OKX client initialized")

    def get_data(self, symbol: str, timeframe: str, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> pd.DataFrame:
        if self.market is None:
            raise RuntimeError("OKXDataSource not initialized")

        after = int(start_date.timestamp() * 1000) if start_date else ''
        before = int(end_date.timestamp() * 1000) if end_date else ''

        resp = self.market.get_candles(instId=symbol, bar=timeframe, after=str(after), before=str(before), limit='100')
        data = resp.get('data', [])
        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data, columns=['ts','open','high','low','close','volume','volCcy','volCcyQuote','confirm'])
        df['ts'] = pd.to_datetime(df['ts'].astype(float), unit='ms')
        df.set_index('ts', inplace=True)
        df = df.astype(float)
        logging.info(f"Retrieved {len(df)} rows from OKX for {symbol}")
        return df[['open','high','low','close','volume']]

    def buy_order(self, symbol, volume, price, sl, tp, deviation=10, magic=234000, comment="Buy Order"):
        if self.trade is None:
            raise RuntimeError("OKXDataSource not initialized")
        return self.trade.set_order(instId=symbol, tdMode='cash', side='buy', ordType='market', sz=str(volume))

    def sell_order(self, symbol, volume, price, sl, tp, deviation=10, magic=234000, comment="Sell Order"):
        if self.trade is None:
            raise RuntimeError("OKXDataSource not initialized")
        return self.trade.set_order(instId=symbol, tdMode='cash', side='sell', ordType='market', sz=str(volume))

    def get_positions(self, symbol: str):
        if self.trade is None:
            raise RuntimeError("OKXDataSource not initialized")
        return self.trade.get_orders_pending(instId=symbol)

    def close_position(self, ticket: int):
        logging.warning("close_position is not fully implemented for OKXDataSource")
        return None
