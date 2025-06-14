import os
from pathlib import Path

# Diretório base do projeto
BASE_DIR = Path(__file__).resolve().parent.parent

# Configurações da API Binance
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY', '')
BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET', '')
BINANCE_TESTNET = True

# Configurações de Trading
TRADING_SYMBOL = 'BTCUSDT'
TRADING_QUANTITY = 0.001  # Quantidade em BTC

# Configurações de Estratégia RSI
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

# Configurações de Estratégia Momentum Breakout (AGRESSIVA)
MOMENTUM_LOOKBACK_PERIOD = 5
MOMENTUM_BREAKOUT_THRESHOLD = 0.005  # 0.5%
MOMENTUM_VOLUME_MULTIPLIER = 1.5
MOMENTUM_MIN_VOLUME_PERIODS = 10

# Configurações de Log
LOG_FILE = BASE_DIR / 'logs' / 'trading_bot.log'
LOG_LEVEL = 'INFO' 