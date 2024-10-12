from typing import Dict, List, Optional
import pandas as pd
from datetime import datetime, timedelta
from .data_source import DataSource
from ..utils.time_utils import convert_timeframe
import MetaTrader5 as mt5

class LiveDataSource(DataSource):
    def __init__(self, symbol: str = "BTCUSD", timeframe: str = "1m"):
        super().__init__()  # Call the base class __init__ without arguments
        self.symbol = symbol
        self.timeframe = timeframe
        self.last_candle_time: Optional[datetime] = None
        self.mt5 = None
        self._initialized = False

    def __del__(self):
        if hasattr(self, '_initialized') and self._initialized:
            if self.mt5:
                self.mt5.shutdown()

    def initialize(self) -> None:
        if not self._initialized:
            if not mt5.initialize():
                print("initialize() failed")
                mt5.shutdown()
                raise RuntimeError("MetaTrader5 initialization failed")
            self.mt5 = mt5
            self._initialized = True

    def get_data(self, symbol: str, timeframe: int, start_date=None, end_date=None) -> pd.DataFrame:
        self._ensure_initialized()
        if start_date is None:
            start_date = datetime.now() - timedelta(days=1)
        if end_date is None:
            end_date = datetime.now()
        rates = self.mt5.copy_rates_range(symbol, self._map_timeframe(timeframe), start_date, end_date)
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)
        return df

    def _map_timeframe(self, timeframe: int) -> int:
        mapping = {1: self.mt5.TIMEFRAME_M1, 5: self.mt5.TIMEFRAME_M5, 15: self.mt5.TIMEFRAME_M15,
                   30: self.mt5.TIMEFRAME_M30, 60: self.mt5.TIMEFRAME_H1, 240: self.mt5.TIMEFRAME_H4,
                   1440: self.mt5.TIMEFRAME_D1}
        return mapping.get(timeframe, self.mt5.TIMEFRAME_M1)

    def fetch_data(self) -> pd.DataFrame:
        self._ensure_initialized()
        ticks = self._fetch_ticks()
        timeframe_minutes = convert_timeframe(self.timeframe)
        return self._process_ticks(ticks, timeframe_minutes)

    def _ensure_initialized(self):
        if not self._initialized:
            raise RuntimeError("LiveDataSource not initialized. Call initialize() first.")

    def _fetch_ticks(self) -> List[Dict]:
        current_time = datetime.now()
        from_date = current_time - timedelta(days=1)  # Fetch last 24 hours of data
        ticks = self.mt5.copy_ticks_range(self.symbol, from_date, current_time, self.mt5.COPY_TICKS_ALL)
        return [{'time': tick[0], 'price': tick[1], 'volume': tick[2]} for tick in ticks]

    def _process_ticks(self, ticks: List[Dict], timeframe_minutes: int) -> pd.DataFrame:
        candles = self._aggregate_ticks_to_candles(ticks, timeframe_minutes)
        return pd.DataFrame(candles)

    def _aggregate_ticks_to_candles(self, ticks: List[Dict], timeframe_minutes: int) -> List[Dict]:
        candles = []
        current_candle = None

        for tick in ticks:
            tick_time = datetime.fromtimestamp(tick['time'])
            
            if not current_candle or self._is_new_candle(tick_time, current_candle['time'], timeframe_minutes):
                if current_candle:
                    candles.append(current_candle)
                current_candle = self._initialize_candle(tick)
            
            self._update_candle(current_candle, tick)

        if current_candle:
            candles.append(current_candle)

        return candles

    def _is_new_candle(self, tick_time: datetime, candle_time: datetime, timeframe_minutes: int) -> bool:
        return tick_time >= candle_time + timedelta(minutes=timeframe_minutes)

    def _initialize_candle(self, tick: Dict) -> Dict:
        return {
            'time': datetime.fromtimestamp(tick['time']),
            'open': tick['price'],
            'high': tick['price'],
            'low': tick['price'],
            'close': tick['price'],
            'volume': tick['volume']
        }

    def _update_candle(self, candle: Dict, tick: Dict) -> None:
        candle['high'] = max(candle['high'], tick['price'])
        candle['low'] = min(candle['low'], tick['price'])
        candle['close'] = tick['price']
        candle['volume'] += tick['volume']

    def update(self) -> Optional[pd.DataFrame]:
        self._ensure_initialized()
        new_ticks = self._fetch_new_ticks()
        if not new_ticks:
            return None

        timeframe_minutes = convert_timeframe(self.timeframe)
        new_candles = self._process_ticks(new_ticks, timeframe_minutes)
        
        if not new_candles.empty:
            self.last_candle_time = new_candles['time'].max()
        return new_candles

    def _fetch_new_ticks(self) -> List[Dict]:
        current_time = datetime.now()
        from_time = self.last_candle_time if self.last_candle_time else (current_time - timedelta(minutes=convert_timeframe(self.timeframe)))
        ticks = self.mt5.copy_ticks_range(self.symbol, from_time, current_time, self.mt5.COPY_TICKS_ALL)
        return [{'time': tick[0], 'price': tick[1], 'volume': tick[2]} for tick in ticks]

    def buy_order(self, symbol, volume, price, sl, tp, deviation=10, magic=234000, comment="Buy Order"):
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": mt5.ORDER_TYPE_BUY,
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
        return result

    def sell_order(self, symbol, volume, price, sl, tp, deviation=10, magic=234000, comment="Sell Order"):
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": mt5.ORDER_TYPE_SELL,
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
        return result

    def get_positions(self, symbol: str):
        return mt5.positions_get(symbol=symbol)

    def close_position(self, ticket: int):
        position = mt5.positions_get(ticket=ticket)
        if position:
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "position": ticket,
                "symbol": position[0].symbol,
                "volume": position[0].volume,
                "type": mt5.ORDER_TYPE_SELL if position[0].type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY,
                "price": mt5.symbol_info_tick(position[0].symbol).bid if position[0].type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(position[0].symbol).ask,
                "deviation": 20,
                "magic": 234000,
                "comment": "Close position",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            result = mt5.order_send(request)
            return result
        return None

    def start_streaming(self, symbol: str, timeframe: int) -> None:
        logging.info(f"Starting streaming for {symbol} with timeframe {timeframe}")
        if symbol not in self._data_queues:
            self._data_queues[symbol] = queue.Queue()
            self._stop_flags[symbol] = threading.Event()
            self._accumulated_data[symbol] = pd.DataFrame()
        else:
            self._stop_flags[symbol].clear()
        
        threading.Thread(target=self._stream_data, args=(symbol, timeframe), daemon=True).start()

    def stop_streaming(self, symbol: str) -> None:
        if symbol in self._stop_flags:
            self._stop_flags[symbol].set()
            logging.info(f"Stopped streaming for {symbol}")

    def _stream_data(self, symbol: str, timeframe: int) -> None:
        logging.info(f"Streaming thread started for {symbol}")
        while not self._stop_flags[symbol].is_set():
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 1000)
            if rates is not None and len(rates) > 0:
                df = pd.DataFrame(rates)
                df['time'] = pd.to_datetime(df['time'], unit='s')
                df.set_index('time', inplace=True)
                
                # Keep only the latest data (e.g., last 1000 candles)
                self._accumulated_data[symbol] = df.iloc[-1000:]
                logging.info(f"Updated data for {symbol}: {len(df)} rows")
            else:
                logging.info(f"No data received for {symbol}. Waiting...")

            self._stop_flags[symbol].wait(timeframe * 60)  # Wait for one candle period
