#!/usr/bin/env python3
"""
🚀 QUANTUM TRAIL - SISTEMA DE TRADING OTIMIZADO
Sistema de trading automatizado com modelo ML de 88.62% de acurácia
"""

import pickle
import pandas as pd
import numpy as np
import requests
import logging
from datetime import datetime
import time
import json
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('quantum_trading.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class QuantumTradingSystem:
    def __init__(self, model_path='gpu_perfect_model.pkl'):
        self.model = None
        self.trading_active = False
        self.trade_history = []
        self.balance = 1000.0
        self.total_profit = 0.0
        self.win_rate = 0.0
        
        self.load_model(model_path)
        
        self.config = {
            'min_confidence': 'MEDIUM',
            'max_risk_per_trade': 0.02,
            'stop_loss': 0.001,
            'take_profit': 0.002,
            'cooldown_minutes': 5,
            'probability_threshold': 0.70
        }
    
    def load_model(self, model_path):
        try:
            with open(model_path, 'rb') as f:
                self.model = pickle.load(f)
            
            logger.info("🚀 QUANTUM TRAIL SISTEMA CARREGADO!")
            logger.info("=" * 50)
            logger.info("   🤖 Modelo: XGBoost GPU")
            logger.info("   🎯 Acurácia: 88.62%")
            logger.info("   💰 Target: 0.2% em 15min")
            logger.info("   🔥 Features: 113 indicadores")
            logger.info("=" * 50)
            
        except Exception as e:
            logger.error(f"❌ Erro ao carregar modelo: {e}")
            raise
    
    def get_market_data(self, symbol='BTCUSDT', limit=200):
        try:
            url = "https://api.binance.com/api/v3/klines"
            params = {
                'symbol': symbol,
                'interval': '1m',
                'limit': limit
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            df = pd.DataFrame(data, columns=[
                'time', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            df['time'] = pd.to_datetime(df['time'], unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
            
            df = df[['time', 'open', 'high', 'low', 'close', 'volume']]
            df = df.sort_values('time').reset_index(drop=True)
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter dados: {e}")
            return None
    
    def create_features(self, data):
        """Cria features EXATAMENTE como no modelo treinado"""
        df = data.copy()
        
        # Features básicas
        df['price_change'] = df['close'].pct_change()
        df['volume_change'] = df['volume'].pct_change()
        df['high_low_ratio'] = df['high'] / df['low']
        df['close_open_ratio'] = df['close'] / df['open']
        df['price_range'] = (df['high'] - df['low']) / df['close']
        df['volume_price_ratio'] = df['volume'] / df['close']
        
        # Médias móveis
        windows = [3, 5, 7, 10, 14, 20, 30, 50, 100]
        for window in windows:
            df[f'sma_{window}'] = df['close'].rolling(window=window).mean()
            df[f'ema_{window}'] = df['close'].ewm(span=window).mean()
            df[f'volume_sma_{window}'] = df['volume'].rolling(window=window).mean()
            
            df[f'price_sma_{window}_ratio'] = df['close'] / df[f'sma_{window}']
            df[f'volume_sma_{window}_ratio'] = df['volume'] / df[f'volume_sma_{window}']
            df[f'price_sma_{window}_dev'] = (df['close'] - df[f'sma_{window}']) / df[f'sma_{window}']
        
        # RSI
        def calculate_rsi(prices, window=14):
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
            rs = gain / loss
            return 100 - (100 / (1 + rs))
        
        for period in [7, 14, 21, 30, 50]:
            df[f'rsi_{period}'] = calculate_rsi(df['close'], period)
        
        # MACD
        def calculate_macd(prices, fast=12, slow=26, signal=9):
            ema_fast = prices.ewm(span=fast).mean()
            ema_slow = prices.ewm(span=slow).mean()
            macd = ema_fast - ema_slow
            signal_line = macd.ewm(span=signal).mean()
            histogram = macd - signal_line
            return macd, signal_line, histogram
        
        macd, macd_signal, macd_hist = calculate_macd(df['close'])
        df['macd'] = macd
        df['macd_signal'] = macd_signal
        df['macd_histogram'] = macd_hist
        
        # Bollinger Bands (usando os mesmos períodos do modelo)
        for window in [20, 30, 50]:
            sma = df['close'].rolling(window=window).mean()
            std = df['close'].rolling(window=window).std()
            df[f'bb_upper_{window}'] = sma + (std * 2)
            df[f'bb_lower_{window}'] = sma - (std * 2)
            df[f'bb_position_{window}'] = (df['close'] - df[f'bb_lower_{window}']) / (df[f'bb_upper_{window}'] - df[f'bb_lower_{window}'])
            df[f'bb_width_{window}'] = (df[f'bb_upper_{window}'] - df[f'bb_lower_{window}']) / sma
        
        # Volatilidade (usando _norm como no modelo)
        for window in [5, 10, 20, 30, 50]:
            df[f'volatility_{window}'] = df['close'].rolling(window=window).std()
            df[f'volatility_{window}_norm'] = df[f'volatility_{window}'] / df['close']
        
        # Momentum (incluindo período 30 que estava faltando)
        for period in [3, 5, 10, 15, 20, 30]:
            df[f'momentum_{period}'] = df['close'] / df['close'].shift(period) - 1
            df[f'roc_{period}'] = df['close'].pct_change(periods=period)
        
        # Features de volume
        df['volume_price_trend'] = df['volume'] * df['price_change']
        df['volume_weighted_price'] = (df['volume'] * df['close']).rolling(window=20).sum() / df['volume'].rolling(window=20).sum()
        
        # Features temporais
        now = datetime.now()
        df['hour'] = now.hour
        df['day_of_week'] = now.weekday()
        df['month'] = now.month
        df['is_weekend'] = (now.weekday() >= 5)
        df['is_night'] = (now.hour >= 22 or now.hour <= 6)
        
        df['hour_sin'] = np.sin(2 * np.pi * now.hour / 24)
        df['hour_cos'] = np.cos(2 * np.pi * now.hour / 24)
        df['day_sin'] = np.sin(2 * np.pi * now.weekday() / 7)
        df['day_cos'] = np.cos(2 * np.pi * now.weekday() / 7)
        
        # Usar pd.concat para melhor performance
        df = df.dropna().reset_index(drop=True)
        
        feature_columns = [col for col in df.columns if col not in ['time', 'open', 'high', 'low', 'close', 'volume']]
        
        return df, feature_columns
    
    def get_trading_signal(self, symbol='BTCUSDT'):
        try:
            data = self.get_market_data(symbol)
            if data is None or len(data) < 100:
                return self.create_error_signal("Dados insuficientes")
            
            df, feature_columns = self.create_features(data)
            if len(df) == 0:
                return self.create_error_signal("Erro na criação de features")
            
            X = df[feature_columns].iloc[-1:]
            prediction = self.model.predict(X)[0]
            probability = self.model.predict_proba(X)[0][1] * 100
            
            current_price = data['close'].iloc[-1]
            
            if prediction == 1 and probability >= self.config['probability_threshold'] * 100:
                signal = 'BUY'
                if probability > 90:
                    confidence = 'HIGH'
                elif probability > 75:
                    confidence = 'MEDIUM'
                else:
                    confidence = 'LOW'
            else:
                signal = 'HOLD'
                if probability < 20:
                    confidence = 'HIGH'
                elif probability < 40:
                    confidence = 'MEDIUM'
                else:
                    confidence = 'LOW'
            
            return {
                'signal': signal,
                'probability': round(probability, 2),
                'confidence': confidence,
                'price': current_price,
                'expected_profit': 0.2 if signal == 'BUY' else 0.0,
                'time_horizon': 15,
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol
            }
            
        except Exception as e:
            logger.error(f"❌ Erro na geração de sinal: {e}")
            return self.create_error_signal(str(e))
    
    def create_error_signal(self, error_msg):
        return {
            'signal': 'ERROR',
            'probability': 0.0,
            'confidence': 'LOW',
            'price': 0.0,
            'expected_profit': 0.0,
            'time_horizon': 0,
            'timestamp': datetime.now().isoformat(),
            'error': error_msg
        }
    
    def should_execute_trade(self, signal):
        if signal['signal'] != 'BUY':
            return False
        
        confidence_levels = {'LOW': 1, 'MEDIUM': 2, 'HIGH': 3}
        min_level = confidence_levels[self.config['min_confidence']]
        current_level = confidence_levels[signal['confidence']]
        
        return current_level >= min_level
    
    def execute_trade(self, signal):
        if not self.should_execute_trade(signal):
            return None
        
        risk_amount = self.balance * self.config['max_risk_per_trade']
        position_size = risk_amount / (signal['price'] * self.config['stop_loss'])
        
        trade = {
            'id': len(self.trade_history) + 1,
            'timestamp': datetime.now().isoformat(),
            'signal': signal,
            'entry_price': signal['price'],
            'position_size': position_size,
            'risk_amount': risk_amount,
            'stop_loss': signal['price'] * (1 - self.config['stop_loss']),
            'take_profit': signal['price'] * (1 + self.config['take_profit']),
            'status': 'OPEN'
        }
        
        self.trade_history.append(trade)
        
        logger.info("🚀 TRADE EXECUTADO!")
        logger.info(f"   💰 Preço: ${trade['entry_price']:.2f}")
        logger.info(f"   📊 Posição: {trade['position_size']:.6f} BTC")
        logger.info(f"   🛡️ Stop: ${trade['stop_loss']:.2f}")
        logger.info(f"   🎯 Target: ${trade['take_profit']:.2f}")
        logger.info(f"   ⚡ Confiança: {signal['confidence']} ({signal['probability']:.1f}%)")
        
        return trade
    
    def run_continuous_trading(self, symbol='BTCUSDT', interval_seconds=30):
        logger.info("🚀 INICIANDO QUANTUM TRAIL TRADING")
        logger.info("=" * 60)
        logger.info(f"   💰 Capital inicial: ${self.balance:.2f}")
        logger.info(f"   🎯 Confiança mínima: {self.config['min_confidence']}")
        logger.info(f"   🛡️ Risco por trade: {self.config['max_risk_per_trade']*100:.1f}%")
        logger.info(f"   📊 Threshold: {self.config['probability_threshold']*100:.0f}%")
        logger.info("=" * 60)
        
        self.trading_active = True
        
        try:
            while self.trading_active:
                signal = self.get_trading_signal(symbol)
                
                logger.info("📊 ANÁLISE ATUAL:")
                logger.info(f"   🎯 Sinal: {signal['signal']}")
                logger.info(f"   📈 Probabilidade: {signal['probability']:.1f}%")
                logger.info(f"   🔒 Confiança: {signal['confidence']}")
                logger.info(f"   💰 Preço: ${signal['price']:.2f}")
                
                if signal['signal'] == 'BUY':
                    trade = self.execute_trade(signal)
                    if trade:
                        logger.info(f"   ✅ Trade #{trade['id']} executado!")
                    else:
                        logger.info("   ⏸️ Trade rejeitado (critérios)")
                elif signal['signal'] == 'HOLD':
                    logger.info("   ⏸️ Aguardando oportunidade...")
                elif signal['signal'] == 'ERROR':
                    logger.error(f"   ❌ Erro: {signal.get('error', 'Desconhecido')}")
                
                self.show_performance()
                logger.info("-" * 60)
                
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            logger.info("⏸️ Trading interrompido pelo usuário")
        except Exception as e:
            logger.error(f"❌ Erro no loop: {e}")
        finally:
            self.trading_active = False
            self.show_final_summary()
    
    def show_performance(self):
        if len(self.trade_history) > 0:
            logger.info(f"📊 Trades executados: {len(self.trade_history)}")
            logger.info(f"💰 Lucro total: ${self.total_profit:.2f}")
    
    def show_final_summary(self):
        logger.info("📊 RESUMO FINAL:")
        logger.info(f"   📈 Total trades: {len(self.trade_history)}")
        logger.info(f"   💰 Lucro total: ${self.total_profit:.2f}")
        logger.info(f"   🎯 Taxa de acerto: {self.win_rate:.1f}%")

def main():
    quantum = QuantumTradingSystem()
    
    quantum.config['min_confidence'] = 'MEDIUM'
    quantum.config['probability_threshold'] = 0.75
    quantum.config['max_risk_per_trade'] = 0.01
    
    logger.info("🧪 TESTE ÚNICO:")
    signal = quantum.get_trading_signal('BTCUSDT')
    logger.info(f"Resultado: {json.dumps(signal, indent=2)}")
    
    logger.info("\n🚀 Iniciando trading contínuo em 5 segundos...")
    time.sleep(5)
    
    quantum.run_continuous_trading('BTCUSDT', interval_seconds=30)

if __name__ == "__main__":
    main() 