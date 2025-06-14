#!/usr/bin/env python3
"""
🚀 EXEMPLO DE INTEGRAÇÃO - QUANTUM TRAIL + MODELO ML

Este arquivo mostra EXATAMENTE como integrar o modelo de ML
no sistema QuantumTrail de forma prática e funcional.
"""

import pickle
import pandas as pd
import numpy as np
import requests
import logging
from datetime import datetime
import time
import json

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('quantum_trail_trading.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class QuantumTrailIntegration:
    """
    Classe principal para integração do modelo ML no QuantumTrail
    """
    
    def __init__(self, model_path='gpu_perfect_model.pkl'):
        self.model = None
        self.trading_active = False
        self.last_signal = None
        self.trade_history = []
        self.balance = 1000.0  # Saldo inicial simulado
        
        # Carregar modelo
        self.load_model(model_path)
        
        # Configurações de trading
        self.config = {
            'min_confidence': 'MEDIUM',  # HIGH, MEDIUM, LOW
            'max_risk_per_trade': 0.02,  # 2% do capital por trade
            'stop_loss': 0.001,          # 0.1% stop loss
            'take_profit': 0.002,        # 0.2% take profit
            'cooldown_minutes': 5        # Aguardar 5min entre trades
        }
    
    def load_model(self, model_path):
        """Carrega o modelo ML treinado"""
        try:
            with open(model_path, 'rb') as f:
                self.model = pickle.load(f)
            
            logger.info("✅ QUANTUM TRAIL - Modelo ML carregado!")
            logger.info("   🎯 Acurácia: 88.62%")
            logger.info("   💰 Target: 0.2% em 15min")
            logger.info("   🚀 Algoritmo: XGBoost GPU")
            
        except Exception as e:
            logger.error(f"❌ Erro ao carregar modelo: {e}")
            raise
    
    def get_market_data(self, symbol='BTCUSDT', limit=200):
        """Obtém dados do mercado em tempo real"""
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
            
            # Converter tipos
            df['time'] = pd.to_datetime(df['time'], unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
            
            df = df[['time', 'open', 'high', 'low', 'close', 'volume']]
            df = df.sort_values('time').reset_index(drop=True)
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter dados do mercado: {e}")
            return None
    
    def create_features(self, data):
        """Cria as mesmas features usadas no treinamento"""
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
        
        macd, macd_signal, macd_histogram = calculate_macd(df['close'])
        df['macd'] = macd
        df['macd_signal'] = macd_signal
        df['macd_histogram'] = macd_histogram
        
        # Bollinger Bands
        for window in [10, 20, 30, 50]:
            rolling_mean = df['close'].rolling(window=window).mean()
            rolling_std = df['close'].rolling(window=window).std()
            df[f'bb_upper_{window}'] = rolling_mean + (rolling_std * 2)
            df[f'bb_lower_{window}'] = rolling_mean - (rolling_std * 2)
            df[f'bb_width_{window}'] = df[f'bb_upper_{window}'] - df[f'bb_lower_{window}']
            df[f'bb_position_{window}'] = (df['close'] - df[f'bb_lower_{window}']) / df[f'bb_width_{window}']
        
        # Volatilidade
        for window in [5, 10, 20, 30]:
            df[f'volatility_{window}'] = df['close'].rolling(window=window).std()
            df[f'volatility_ratio_{window}'] = df[f'volatility_{window}'] / df['close']
        
        # Momentum
        for period in [3, 5, 10, 15, 20]:
            df[f'momentum_{period}'] = df['close'] / df['close'].shift(period) - 1
            df[f'roc_{period}'] = df['close'].pct_change(periods=period)
        
        # Volume features
        df['volume_sma_ratio'] = df['volume'] / df['volume'].rolling(window=20).mean()
        df['price_volume'] = df['close'] * df['volume']
        df['volume_price_trend'] = df['volume'].rolling(window=10).corr(df['close'])
        
        # Lags
        for lag in [1, 2, 3, 5, 10]:
            df[f'close_lag_{lag}'] = df['close'].shift(lag)
            df[f'volume_lag_{lag}'] = df['volume'].shift(lag)
            df[f'price_change_lag_{lag}'] = df['price_change'].shift(lag)
        
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
        
        # Remover NaN
        df = df.dropna()
        
        # Colunas de features (excluir dados básicos)
        feature_columns = [col for col in df.columns if col not in ['time', 'open', 'high', 'low', 'close', 'volume']]
        
        return df, feature_columns
    
    def get_trading_signal(self, symbol='BTCUSDT'):
        """Gera sinal de trading usando o modelo ML"""
        try:
            # Obter dados do mercado
            data = self.get_market_data(symbol)
            if data is None or len(data) < 100:
                return self.create_error_signal("Dados insuficientes")
            
            # Criar features
            df, feature_columns = self.create_features(data)
            if len(df) == 0:
                return self.create_error_signal("Erro na criação de features")
            
            # Fazer predição
            X = df[feature_columns].iloc[-1:]
            prediction = self.model.predict(X)[0]
            probability = self.model.predict_proba(X)[0][1] * 100
            
            # Preço atual
            current_price = data['close'].iloc[-1]
            
            # Determinar sinal e confiança
            if prediction == 1:
                signal = 'BUY'
                if probability > 90:
                    confidence = 'HIGH'
                elif probability > 70:
                    confidence = 'MEDIUM'
                else:
                    confidence = 'LOW'
            else:
                signal = 'HOLD'
                if probability < 10:
                    confidence = 'HIGH'
                elif probability < 30:
                    confidence = 'MEDIUM'
                else:
                    confidence = 'LOW'
            
            # Criar resultado
            result = {
                'signal': signal,
                'probability': round(probability, 2),
                'confidence': confidence,
                'price': current_price,
                'expected_profit': 0.2 if signal == 'BUY' else 0.0,
                'time_horizon': 15,
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol
            }
            
            self.last_signal = result
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro na geração de sinal: {e}")
            return self.create_error_signal(str(e))
    
    def create_error_signal(self, error_msg):
        """Cria sinal de erro"""
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
        """Decide se deve executar o trade baseado nas configurações"""
        if signal['signal'] != 'BUY':
            return False
        
        # Verificar confiança mínima
        confidence_levels = {'LOW': 1, 'MEDIUM': 2, 'HIGH': 3}
        min_level = confidence_levels[self.config['min_confidence']]
        current_level = confidence_levels[signal['confidence']]
        
        if current_level < min_level:
            logger.info(f"⚠️ Confiança insuficiente: {signal['confidence']} < {self.config['min_confidence']}")
            return False
        
        return True
    
    def execute_simulated_trade(self, signal):
        """Executa trade simulado (para demonstração)"""
        if not self.should_execute_trade(signal):
            return None
        
        # Calcular tamanho da posição
        risk_amount = self.balance * self.config['max_risk_per_trade']
        position_size = risk_amount / (signal['price'] * self.config['stop_loss'])
        
        # Simular execução
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
        logger.info(f"   💰 Preço entrada: ${trade['entry_price']:.2f}")
        logger.info(f"   📊 Tamanho posição: {trade['position_size']:.6f} BTC")
        logger.info(f"   🛡️ Stop Loss: ${trade['stop_loss']:.2f}")
        logger.info(f"   🎯 Take Profit: ${trade['take_profit']:.2f}")
        logger.info(f"   ⚡ Confiança: {signal['confidence']} ({signal['probability']:.1f}%)")
        
        return trade
    
    def run_trading_loop(self, symbol='BTCUSDT', interval_seconds=60):
        """Loop principal de trading"""
        logger.info("🚀 INICIANDO QUANTUM TRAIL TRADING")
        logger.info("=" * 60)
        logger.info(f"   💰 Saldo inicial: ${self.balance:.2f}")
        logger.info(f"   🎯 Confiança mínima: {self.config['min_confidence']}")
        logger.info(f"   🛡️ Risco por trade: {self.config['max_risk_per_trade']*100:.1f}%")
        logger.info("=" * 60)
        
        self.trading_active = True
        
        try:
            while self.trading_active:
                # Obter sinal
                signal = self.get_trading_signal(symbol)
                
                # Log do sinal
                logger.info("📊 SINAL ATUAL:")
                logger.info(f"   🎯 Sinal: {signal['signal']}")
                logger.info(f"   📈 Probabilidade: {signal['probability']:.1f}%")
                logger.info(f"   🔒 Confiança: {signal['confidence']}")
                logger.info(f"   💰 Preço: ${signal['price']:.2f}")
                
                # Executar trade se necessário
                if signal['signal'] == 'BUY':
                    trade = self.execute_simulated_trade(signal)
                    if trade:
                        logger.info(f"   ✅ Trade #{trade['id']} executado!")
                    else:
                        logger.info("   ⏸️ Trade não executado (critérios não atendidos)")
                elif signal['signal'] == 'HOLD':
                    logger.info("   ⏸️ Aguardando melhor oportunidade...")
                elif signal['signal'] == 'ERROR':
                    logger.error(f"   ❌ Erro: {signal.get('error', 'Desconhecido')}")
                
                logger.info("-" * 60)
                
                # Aguardar próximo ciclo
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            logger.info("⏸️ Trading interrompido pelo usuário")
        except Exception as e:
            logger.error(f"❌ Erro no loop de trading: {e}")
        finally:
            self.trading_active = False
            self.show_trading_summary()
    
    def show_trading_summary(self):
        """Mostra resumo dos trades"""
        logger.info("📊 RESUMO DE TRADING:")
        logger.info(f"   📈 Total de trades: {len(self.trade_history)}")
        
        if self.trade_history:
            logger.info("   🔍 Últimos trades:")
            for trade in self.trade_history[-5:]:
                logger.info(f"      #{trade['id']}: ${trade['entry_price']:.2f} | {trade['signal']['confidence']}")

def main():
    """Função principal - exemplo de uso"""
    
    # Inicializar integração
    quantum = QuantumTrailIntegration()
    
    # Configurar parâmetros (opcional)
    quantum.config['min_confidence'] = 'MEDIUM'  # Só trades com confiança média+
    quantum.config['max_risk_per_trade'] = 0.01  # 1% de risco por trade
    
    # Executar um sinal único (teste)
    logger.info("🧪 TESTE ÚNICO:")
    signal = quantum.get_trading_signal('BTCUSDT')
    logger.info(f"Resultado: {json.dumps(signal, indent=2)}")
    
    # Ou executar loop contínuo (descomente para usar)
    # quantum.run_trading_loop('BTCUSDT', interval_seconds=60)

if __name__ == "__main__":
    main() 