# -*- coding: utf-8 -*-
import asyncio
import logging
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Carrega variáveis de ambiente ANTES de importar config
load_dotenv()

from collectors.binance_collector import BinanceCollector
from strategies.momentum_breakout_strategy import MomentumBreakoutStrategy
from order_management.order_manager import OrderManager
from config.config import (
    BINANCE_API_KEY,
    BINANCE_API_SECRET,
    TRADING_SYMBOL,
    MOMENTUM_LOOKBACK_PERIOD,
    MOMENTUM_BREAKOUT_THRESHOLD,
    MOMENTUM_VOLUME_MULTIPLIER,
    MOMENTUM_MIN_VOLUME_PERIODS,
    LOG_FILE,
    LOG_LEVEL
)

# Cria diretório de logs se não existir
Path(LOG_FILE).parent.mkdir(parents=True, exist_ok=True)

# Configura logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TradingBot:
    def __init__(self):
        if not BINANCE_API_KEY or not BINANCE_API_SECRET:
            raise ValueError("API keys not configured. Please configure the .env file")
            
        self.symbol = TRADING_SYMBOL
        self.collector = BinanceCollector(BINANCE_API_KEY, BINANCE_API_SECRET)
        
        # NOVA ESTRATÉGIA MOMENTUM BREAKOUT AGRESSIVA
        self.strategy = MomentumBreakoutStrategy(
            lookback_period=MOMENTUM_LOOKBACK_PERIOD,
            breakout_threshold=MOMENTUM_BREAKOUT_THRESHOLD,
            volume_multiplier=MOMENTUM_VOLUME_MULTIPLIER,
            min_volume_periods=MOMENTUM_MIN_VOLUME_PERIODS
        )
        
        self.order_manager = OrderManager(self.collector, self.strategy)
        self.running = False
        
    async def initialize(self):
        try:
            await self.collector.initialize()
            logger.info(f"🚀 MOMENTUM BOT initialized for {self.symbol}")
            logger.info(f"⚡ Strategy: Momentum Breakout (AGGRESSIVE)")
            logger.info(f"📊 Lookback: {MOMENTUM_LOOKBACK_PERIOD} | Threshold: {MOMENTUM_BREAKOUT_THRESHOLD*100}% | Volume: {MOMENTUM_VOLUME_MULTIPLIER}x")
        except Exception as e:
            logger.error(f"Failed to initialize bot: {e}")
            raise
            
    async def on_ticker_update(self, data):
        try:
            # Convert ticker data to DataFrame format
            df_data = {
                'close': [float(data['c'])],
                'high': [float(data['h'])],
                'low': [float(data['l'])],
                'volume': [float(data['v'])]
            }
            
            # Log market data
            logger.info(f"📈 Market data for {self.symbol}: Price=${data['c']}, Volume={data['v']}")
            
            # Analyze data and get trading signal
            signal = await self.strategy.analyze(df_data)
            
            # Log strategy signal
            if signal['signal'] != 'none':
                logger.info(f"🎯 Strategy signal: {signal}")
                
                # Execute trading signal if any
                order = await self.order_manager.execute_strategy_signal(self.symbol, signal)
                if order:
                    logger.info(f"💰 Order executed: {json.dumps(order, indent=2)}")
                    
        except Exception as e:
            logger.error(f"Error processing ticker update: {e}")
            
    async def start(self):
        try:
            self.running = True
            await self.initialize()
            
            # Subscribe to ticker updates
            await self.collector.subscribe_to_ticker(self.symbol, self.on_ticker_update)
            
            logger.info(f"🚀 MOMENTUM BOT started for {self.symbol}")
            
            # Keep the bot running
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Bot error: {e}")
            self.running = False
        finally:
            await self.stop()
            
    async def stop(self):
        self.running = False
        await self.collector.close()
        logger.info("🛑 Momentum Bot stopped")

async def main():
    bot = None
    try:
        bot = TradingBot()
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Shutdown signal received")
        if bot:
            await bot.stop()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if bot:
            await bot.stop()

if __name__ == "__main__":
    asyncio.run(main()) 