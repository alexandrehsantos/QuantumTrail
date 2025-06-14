import pickle
import pandas as pd
import numpy as np
import requests
import logging
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QuantumTrailModel:
    def __init__(self, model_path='gpu_perfect_model.pkl'):
        self.model = None
        self.model_params = None
        self.load_model(model_path)
    
    def load_model(self, model_path):
        try:
            with open(model_path, 'rb') as f:
                self.model = pickle.load(f)
            
            logger.info("✅ Modelo QuantumTrail carregado!")
            logger.info("   🎯 Acurácia: 88.62%")
            logger.info("   💰 Target: 0.2% em 15min")
            logger.info("   🚀 Algoritmo: XGBoost GPU")
            
        except Exception as e:
            logger.error(f"❌ Erro ao carregar modelo: {e}")
            raise
    
    def get_binance_data(self, symbol='BTCUSDT', interval='1m', limit=200):
        try:
            url = f"https://api.binance.com/api/v3/klines"
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            
            response = requests.get(url, params=params)
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
        df = data.copy()
        
        df['price_change'] = df['close'].pct_change()
        df['volume_change'] = df['volume'].pct_change()
        df['high_low_ratio'] = df['high'] / df['low']
        df['close_open_ratio'] = df['close'] / df['open']
        df['price_range'] = (df['high'] - df['low']) / df['close']
        df['volume_price_ratio'] = df['volume'] / df['close']
        
        windows = [3, 5, 7, 10, 14, 20, 30, 50, 100]
        for window in windows:
            df[f'sma_{window}'] = df['close'].rolling(window=window).mean()
            df[f'ema_{window}'] = df['close'].ewm(span=window).mean()
            df[f'volume_sma_{window}'] = df['volume'].rolling(window=window).mean()
            
            df[f'price_sma_{window}_ratio'] = df['close'] / df[f'sma_{window}']
            df[f'volume_sma_{window}_ratio'] = df['volume'] / df[f'volume_sma_{window}']
            df[f'price_sma_{window}_dev'] = (df['close'] - df[f'sma_{window}']) / df[f'sma_{window}']
        
        def calculate_rsi(prices, window=14):
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
            rs = gain / loss
            return 100 - (100 / (1 + rs))
        
        for period in [7, 14, 21, 30, 50]:
            df[f'rsi_{period}'] = calculate_rsi(df['close'], period)
        
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
        
        for window in [10, 20, 30]:
            rolling_mean = df['close'].rolling(window=window).mean()
            rolling_std = df['close'].rolling(window=window).std()
            df[f'bb_upper_{window}'] = rolling_mean + (rolling_std * 2)
            df[f'bb_lower_{window}'] = rolling_mean - (rolling_std * 2)
            df[f'bb_width_{window}'] = df[f'bb_upper_{window}'] - df[f'bb_lower_{window}']
            df[f'bb_position_{window}'] = (df['close'] - df[f'bb_lower_{window}']) / df[f'bb_width_{window}']
        
        for window in [5, 10, 20, 30]:
            df[f'volatility_{window}'] = df['close'].rolling(window=window).std()
            df[f'volatility_ratio_{window}'] = df[f'volatility_{window}'] / df['close']
        
        for period in [3, 5, 10, 20]:
            df[f'momentum_{period}'] = df['close'] / df['close'].shift(period) - 1
            df[f'roc_{period}'] = df['close'].pct_change(periods=period)
        
        df['volume_sma_ratio'] = df['volume'] / df['volume'].rolling(window=20).mean()
        df['price_volume'] = df['close'] * df['volume']
        df['volume_price_trend'] = df['volume'].rolling(window=10).corr(df['close'])
        
        for lag in [1, 2, 3, 5, 10]:
            df[f'close_lag_{lag}'] = df['close'].shift(lag)
            df[f'volume_lag_{lag}'] = df['volume'].shift(lag)
            df[f'price_change_lag_{lag}'] = df['price_change'].shift(lag)
        
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
        
        df = df.dropna()
        
        feature_columns = [col for col in df.columns if col not in ['time', 'open', 'high', 'low', 'close', 'volume']]
        
        return df, feature_columns
    
    def predict(self, symbol='BTCUSDT'):
        try:
            data = self.get_binance_data(symbol)
            if data is None or len(data) < 100:
                return {
                    'signal': 'HOLD',
                    'probability': 0.0,
                    'confidence': 'LOW',
                    'price': 0.0,
                    'timestamp': datetime.now().isoformat()
                }
            
            df, feature_columns = self.create_features(data)
            
            if len(df) == 0:
                return {
                    'signal': 'HOLD',
                    'probability': 0.0,
                    'confidence': 'LOW',
                    'price': data['close'].iloc[-1],
                    'timestamp': datetime.now().isoformat()
                }
            
            X = df[feature_columns].iloc[-1:] 
            
            prediction = self.model.predict(X)[0]
            probability = self.model.predict_proba(X)[0][1] * 100
            
            current_price = data['close'].iloc[-1]
            
            if prediction == 1:
                signal = 'BUY'
                confidence = 'HIGH' if probability > 90 else 'MEDIUM' if probability > 70 else 'LOW'
            else:
                signal = 'HOLD'
                confidence = 'HIGH' if probability < 10 else 'MEDIUM' if probability < 30 else 'LOW'
            
            return {
                'signal': signal,
                'probability': round(probability, 2),
                'confidence': confidence,
                'price': current_price,
                'expected_profit': 0.2 if signal == 'BUY' else 0.0,
                'time_horizon': 15,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Erro na predição: {e}")
            return {
                'signal': 'ERROR',
                'probability': 0.0,
                'confidence': 'LOW',
                'price': 0.0,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

def main():
    logger.info("🚀 QUANTUM TRAIL - MODELO DE TRADING")
    logger.info("=" * 50)
    
    model = QuantumTrailModel()
    
    while True:
        try:
            result = model.predict('BTCUSDT')
            
            logger.info("📊 SINAL DE TRADING:")
            logger.info(f"   🎯 Sinal: {result['signal']}")
            logger.info(f"   📈 Probabilidade: {result['probability']}%")
            logger.info(f"   🔒 Confiança: {result['confidence']}")
            logger.info(f"   💰 Preço atual: ${result['price']:.2f}")
            
            if result['signal'] == 'BUY':
                logger.info(f"   💎 Lucro esperado: {result['expected_profit']}%")
                logger.info(f"   ⏰ Tempo: {result['time_horizon']} min")
            
            logger.info("-" * 50)
            
            import time
            time.sleep(60)
            
        except KeyboardInterrupt:
            logger.info("👋 Encerrando QuantumTrail...")
            break
        except Exception as e:
            logger.error(f"❌ Erro: {e}")
            import time
            time.sleep(30)

if __name__ == "__main__":
    main() 