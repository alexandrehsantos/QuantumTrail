import pandas as pd
import logging
from trading_system.data_sources.data_source import DataSource
from trading_system.strategies.strategy import Strategy
from trading_system.risk_management.risk_manager import RiskManager
from trading_system.strategies.order_type import OrderType
import time
from datetime import datetime
import MetaTrader5 as mt5

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MeanReversionStrategy(Strategy):
    def __init__(self, data_source, risk_manager, symbol, timeframe, initial_balance, start_date, end_date, **kwargs):
        super().__init__(data_source, risk_manager, symbol, timeframe, initial_balance, start_date, end_date)
        logging.info(f"Initialized MeanReversionStrategy for {symbol} with timeframe {timeframe}")
        self.trade_open = False
        # Initialize other attributes specific to MeanReversionStrategy

    def apply(self):
        logging.info(f"Starting Mean Reversion Strategy application for {self.symbol}")
        balance = self.initial_balance
        trades = []

        try:
            while True:  # Run the strategy continuously
                logging.info(f"Fetching data for {self.symbol} with timeframe {self.timeframe}")
                data = self.data_source.get_data(self.symbol, self.timeframe)
                if data.empty:
                    logging.warning(f"No data available for {self.symbol}. Waiting before retry.")
                    time.sleep(60)
                    continue

                logging.info(f"Data fetched: {data.tail()}")

                current_price = data['close'].iloc[-1]
                sma = data['close'].rolling(window=20).mean().iloc[-1]
                logging.info(f"Current price: {current_price}, 20-period SMA: {sma}")

                if not self.trade_open:
                    if current_price < sma * 0.95:
                        logging.info(f"Buy signal detected. Price {current_price} is below 95% of SMA {sma}")
                        position_size = self.risk_manager.calculate_position_size(self.symbol, current_price * 0.02)
                        sl, tp = self.risk_manager.calculate_stop_loss_take_profit(self.symbol, current_price, OrderType.BUY, 0.02, 0.03)
                        
                        logging.info(f"Attempting to place buy order: size={position_size}, price={current_price}, stop_loss={sl}, take_profit={tp}")
                        order_result = self.data_source.buy_order(self.symbol, position_size, current_price, sl, tp)
                        if order_result:
                            self.trade_open = True
                            trades.append(('BUY', current_price, position_size))
                            logging.info(f"Successfully opened BUY position at {current_price}")
                        else:
                            logging.warning("Failed to place buy order")
                    else:
                        logging.info("No buy signal. Current price is not below 95% of SMA")
                else:
                    logging.info("Trade already open. Skipping buy signal check")
                logging.info("Managing open positions")
                self.manage_positions(current_price)

                # Calculate profit or loss for the trade
                if trades:
                    last_trade = trades[-1]
                    trade_profit = self.calculate_trade_profit(current_price, last_trade[1], last_trade[2])
                else:
                    trade_profit = 0
                
                # Update balance using trade profit
                balance = self.risk_manager.update_balance(trade_profit)
                logging.info(f"Updated balance: {balance}")

                time.sleep(60)
                logging.info("Waiting for next iteration")

        except Exception as e:
            logging.error(f"An error occurred in MeanReversionStrategy: {str(e)}", exc_info=True)

        logging.info(f"MeanReversionStrategy application completed. Final balance: {balance}, Total trades: {len(trades)}")
        return {'balance': balance, 'trades': trades}

    def calculate_indicators(self, df):
        df['mean'] = df['close'].rolling(window=self.mean_window).mean()
        df['std_dev'] = df['close'].rolling(window=self.mean_window).std()
        df['upper_band'] = df['mean'] + (df['std_dev'] * self.std_dev_factor)
        df['lower_band'] = df['mean'] - (df['std_dev'] * self.std_dev_factor)
        return df

    def execute_buy(self, price):
        position_size = self.risk_manager.calculate_position_size(self.symbol, price * self.risk_percent)
        sl, tp = self.risk_manager.calculate_stop_loss_take_profit(
            self.symbol, price, OrderType.BUY, self.risk_percent, self.risk_percent * 2
        )
        result = self.data_source.buy_order(self.symbol, position_size, price, sl, tp)
        if result and result['status'] == "executed":
            logging.info(f"Buy order placed at {price}")
            self.trade_open = True
        else:
            logging.error("Failed to place buy order.")

    def execute_sell(self, price):
        position_size = self.risk_manager.calculate_position_size(self.symbol, price * self.risk_percent)
        sl, tp = self.risk_manager.calculate_stop_loss_take_profit(
            self.symbol, price, OrderType.SELL, self.risk_percent, self.risk_percent * 2
        )
        result = self.data_source.sell_order(self.symbol, position_size, price, sl, tp)
        if result and result['status'] == "executed":
            logging.info(f"Sell order placed at {price}")
            self.trade_open = True
        else:
            logging.error("Failed to place sell order.")

    def manage_positions(self, current_price: float):
        logging.info(f"Managing positions at current price: {current_price}")
        positions = self.data_source.get_positions(self.symbol)
        for position in positions:
            logging.info(f"Checking position: {position}")
            if position.type == mt5.POSITION_TYPE_BUY or position.type == 0:
                if current_price >= position.tp or current_price <= position.sl:
                    logging.info(f"Closing BUY position. Current price: {current_price}, TP: {position.tp}, SL: {position.sl}")
                    result = self.data_source.close_position(position.ticket)
                    if result:
                        self.trade_open = False
                        logging.info(f"Successfully closed BUY position at {current_price}")
                    else:
                        logging.error(f"Failed to close BUY position at {current_price}")
            elif position.type == mt5.POSITION_TYPE_SELL or position.type == 1:
                if current_price <= position.tp or current_price >= position.sl:
                    logging.info(f"Closing SELL position. Current price: {current_price}, TP: {position.tp}, SL: {position.sl}")
                    result = self.data_source.close_position(position.ticket)
                    if result:
                        self.trade_open = False
                        logging.info(f"Successfully closed SELL position at {current_price}")
                    else:
                        logging.error(f"Failed to close SELL position at {current_price}")
            else:
                logging.warning(f"Unexpected position type: {position.type}")

    def update_balance(self, balance, current_price):
        logging.info(f"Updating balance. Current balance: {balance}, Current price: {current_price}")
        positions = self.data_source.get_positions(self.symbol)
        for position in positions:
            if position.type == mt5.POSITION_TYPE_BUY or position.type == 0:
                profit = (current_price - position.price_open) * position.volume
                logging.info(f"BUY position profit: {profit}")
            elif position.type == mt5.POSITION_TYPE_SELL or position.type == 1:
                profit = (position.price_open - current_price) * position.volume
                logging.info(f"SELL position profit: {profit}")
            else:
                logging.warning(f"Unexpected position type: {position.type}")
                continue
            
            try:
                self.risk_manager.update_balance(balance + profit)
                balance = self.risk_manager.current_balance
                logging.info(f"Updated balance after position: {balance}")
            except AttributeError as e:
                logging.error(f"Error updating balance: {str(e)}")
                logging.error(f"RiskManager attributes: {vars(self.risk_manager)}")
                # You might want to handle this error more gracefully, depending on your requirements

        return balance

    def calculate_trade_profit(self, current_price, entry_price, trade_volume):
        # Implement logic to calculate trade profit
        return (current_price - entry_price) * trade_volume
