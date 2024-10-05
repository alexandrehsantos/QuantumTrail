import MetaTrader5 as mt5
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def log_info(message):
    logging.info(message)

def log_account_info():
    account_info = mt5.account_info()
    if account_info is not None:
        log_info(f"Account Balance: {account_info.balance}, Equity: {account_info.equity}, Margin Free: {account_info.margin_free}")
    else:
        log_info("Failed to retrieve account information.")

def check_symbol_info(symbol):
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        log_info(f"Symbol {symbol} not found")
        return None
    if not symbol_info.visible:
        if not mt5.symbol_select(symbol, True):
            log_info(f"Failed to select {symbol}")
            return None
    log_info(f"Symbol {symbol} info: Min lot size: {symbol_info.volume_min}, Max lot size: {symbol_info.volume_max}, Step: {symbol_info.volume_step}")
    return symbol_info

def check_lot_size(symbol_info, lot):
    if lot < symbol_info.volume_min or lot > symbol_info.volume_max:
        log_info(f"Invalid lot size. Lot size must be between {symbol_info.volume_min} and {symbol_info.volume_max}.")
        return False
    if (lot - symbol_info.volume_min) % symbol_info.volume_step != 0:
        log_info(f"Lot size must increment by {symbol_info.volume_step}")
        return False
    return True

def place_order(request, order_type):
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        log_info(f"{order_type} order failed, retcode={result.retcode}")
        return None
    log_info(f"{order_type} order placed successfully. Ticket: {result.order}")
    return result

def main():
    # Inicializa a conexão com o MetaTrader 5
    if not mt5.initialize():
        log_info("MetaTrader 5 falhou ao inicializar")
        return

    log_account_info()

    # Define o símbolo e parâmetros
    symbol = "BTCUSD"
    lot = 0.01  # Tamanho do lote mínimo; ajuste conforme as especificações do seu broker
    deviation = 100  # Aumentar o desvio de preço para 100 pontos
    magic_number = 123456  # Identificador único para suas ordens

    # Verifica se o símbolo está disponível
    symbol_info = check_symbol_info(symbol)
    if symbol_info is None:
        mt5.shutdown()
        return

    # Valida o tamanho do lote
    if not check_lot_size(symbol_info, lot):
        mt5.shutdown()
        return

    # Verifica o preço atual do ativo
    symbol_tick = mt5.symbol_info_tick(symbol)
    if symbol_tick is None:
        log_info(f"Failed to get tick info for {symbol}")
        mt5.shutdown()
        return

    # Coloca ordem de compra no mercado
    price_buy = symbol_tick.ask
    log_info(f"Market Buy price for {symbol}: {price_buy}")
    request_buy = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": mt5.ORDER_TYPE_BUY,
        "price": price_buy,
        "deviation": deviation,
        "magic": magic_number,
        "comment": "Market Buy Order",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_FOK,  # Alterado para FOK
    }

    # Envia a ordem de compra
    result_buy = place_order(request_buy, "Buy")
    if result_buy is None:
        mt5.shutdown()
        return

    # Aguarda 1 segundo antes de vender
    time.sleep(1)

    # Fecha a posição (coloca ordem de venda)
    position_id = result_buy.order
    price_sell = mt5.symbol_info_tick(symbol).bid
    log_info(f"Market Sell price for {symbol}: {price_sell}")
    close_request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "position": position_id,
        "symbol": symbol,
        "volume": lot,
        "type": mt5.ORDER_TYPE_SELL,
        "price": price_sell,
        "deviation": deviation,
        "magic": magic_number,
        "comment": "Market Sell Order",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_FOK,  # Alterado para FOK
    }

    # Envia a ordem de venda
    result_sell = place_order(close_request, "Sell")
    if result_sell is None:
        log_info("Failed to close the buy position")

    # Finaliza a conexão com o MetaTrader 5
    mt5.shutdown()

if __name__ == "__main__":
    main()
