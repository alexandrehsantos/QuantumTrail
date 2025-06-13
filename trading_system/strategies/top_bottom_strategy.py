import logging
import pandas as pd
import time
from .strategy import Strategy
from order_type import OrderType
from datetime import datetime, timedelta

class TopBottomStrategy(Strategy):
    def __init__(self, data_source, risk_manager, symbol, timeframe, initial_balance, start_date, end_date):
        super().__init__(data_source, risk_manager, symbol, timeframe, initial_balance, start_date, end_date)
        self.trade_open = False
        self.min_volume = 0.01
        self.cooldown_period = timedelta(minutes=15)
        self.last_trade_time = None

    def apply(self):
        logging.info(f"Iniciando a estratégia de Topos e Fundos para {self.symbol}")
        while True:
            try:
                data = self.data_source.get_data(self.symbol, self.timeframe)
                if data is None or data.empty:
                    logging.warning("Sem dados disponíveis para aplicar a estratégia.")
                    time.sleep(60)
                    continue

                rsi = self.calculate_rsi(data['close'])

                current_time = datetime.now()
                if self.last_trade_time and (current_time - self.last_trade_time) < self.cooldown_period:
                    logging.info("Em período de espera, pulando análise de trade.")
                    time.sleep(60)
                    continue

                if not self.trade_open:
                    if rsi.iloc[-1] < 30:
                        self.execute_trade(data, OrderType.BUY)
                    elif rsi.iloc[-1] > 70:
                        self.execute_trade(data, OrderType.SELL)
                else:
                    self.manage_positions(data['close'].iloc[-1])

                time.sleep(60)

            except Exception as e:
                logging.error(f"Ocorreu um erro: {e}")
                time.sleep(60)

    def execute_trade(self, data, order_type: OrderType):
        price = data['close'].iloc[-1]
        volume = self.min_volume

        sl, tp = self.calculate_sl_tp(price, order_type)

        if order_type == OrderType.BUY:
            result = self.data_source.buy_order(self.symbol, volume, price, sl, tp)
        elif order_type == OrderType.SELL:
            result = self.data_source.sell_order(self.symbol, volume, price, sl, tp)

        if result and result.retcode == self.data_source.mt5.TRADE_RETCODE_DONE:
            self.trade_open = True
            self.last_trade_time = datetime.now()
            logging.info(f"Ordem de {order_type.value} executada com sucesso.")
        else:
            logging.error(f"Falha ao executar a ordem de {order_type.value}: {result}")

    def manage_positions(self, current_price: float):
        logging.info(f"Managing positions at current price: {current_price}")
        positions = self.data_source.get_positions(self.symbol)
        for position in positions:
            logging.info(f"Checking position: {position}")
            if position.type == mt5.POSITION_TYPE_BUY:
                if current_price >= position.tp or current_price <= position.sl:
                    logging.info(f"Closing BUY position. Current price: {current_price}, TP: {position.tp}, SL: {position.sl}")
                    result = self.data_source.close_position(position.ticket)
                    if result:
                        self.trade_open = False
                        logging.info(f"Successfully closed BUY position at {current_price}")
                    else:
                        logging.error(f"Failed to close BUY position at {current_price}")
            elif position.type == mt5.POSITION_TYPE_SELL:
                if current_price <= position.tp or current_price >= position.sl:
                    logging.info(f"Closing SELL position. Current price: {current_price}, TP: {position.tp}, SL: {position.sl}")
                    result = self.data_source.close_position(position.ticket)
                    if result:
                        self.trade_open = False
                        logging.info(f"Successfully closed SELL position at {current_price}")
                    else:
                        logging.error(f"Failed to close SELL position at {current_price}")

    def update_balance(self, balance, current_price):
        self.initial_balance = balance
        logging.info(f"Updated balance: {self.initial_balance}")

    def calculate_sl_tp(self, price, order_type: OrderType):
        if order_type == OrderType.BUY:
            sl = price * 0.98
            tp = price * 1.02
        else:
            sl = price * 1.02
            tp = price * 0.98
        return sl, tp

    def calculate_rsi(self, prices, period=14):
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
