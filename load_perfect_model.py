import pandas as pd
import numpy as np
import pickle
import json
import logging
from datetime import datetime
import os
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PerfectModelLoader:
    def __init__(self, model_path=None, params_path=None):
        self.model = None
        self.model_params = None
        self.feature_columns = None
        
        # Caminhos padrão
        if model_path is None:
            model_path = 'gpu_perfect_model.pkl'
        if params_path is None:
            params_path = 'gpu_perfect_model_params.json'
            
        self.model_path = model_path
        self.params_path = params_path
        
    def load_model(self):
        try:
            # Carregar modelo
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
            
            # Carregar parâmetros
            with open(self.params_path, 'r') as f:
                self.model_params = json.load(f)
            
            logger.info("✅ Modelo perfeito carregado com sucesso!")
            logger.info(f"   🤖 Algoritmo: {self.model_params['model_name']}")
            logger.info(f"   🎯 Acurácia: {self.model_params['cv_mean_accuracy']:.4f}")
            logger.info(f"   💰 Threshold: {self.model_params['profit_threshold']}%")
            logger.info(f"   ⏰ Horizonte: {self.model_params['time_horizon']} min")
            logger.info(f"   🚀 GPU usado: {'Sim' if self.model_params.get('gpu_used', False) else 'Não'}")
            
            return True
            
        except FileNotFoundError as e:
            logger.error(f"❌ Arquivo não encontrado: {e}")
            logger.error("💡 Certifique-se de que os arquivos estão no diretório correto:")
            logger.error(f"   - {self.model_path}")
            logger.error(f"   - {self.params_path}")
            return False
        except Exception as e:
            logger.error(f"❌ Erro ao carregar modelo: {e}")
            return False
    
    def create_features(self, data):
        """
        Cria as mesmas features usadas no treinamento
        """
        df = data.copy()
        
        # Features básicas
        df['price_change'] = df['close'].pct_change()
        df['volume_change'] = df['volume'].pct_change()
        df['high_low_ratio'] = df['high'] / df['low']
        df['close_open_ratio'] = df['close'] / df['open']
        df['price_range'] = (df['high'] - df['low']) / df['close']
        df['volume_price_ratio'] = df['volume'] / df['close']
        
        # Médias móveis múltiplas
        windows = [3, 5, 7, 10, 14, 20, 30, 50, 100]
        for window in windows:
            df[f'sma_{window}'] = df['close'].rolling(window=window).mean()
            df[f'ema_{window}'] = df['close'].ewm(span=window).mean()
            df[f'volume_sma_{window}'] = df['volume'].rolling(window=window).mean()
            
            df[f'price_sma_{window}_ratio'] = df['close'] / df[f'sma_{window}']
            df[f'volume_sma_{window}_ratio'] = df['volume'] / df[f'volume_sma_{window}']
            df[f'price_sma_{window}_dev'] = (df['close'] - df[f'sma_{window}']) / df[f'sma_{window}']
        
        # RSI múltiplos
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
        
        # Bollinger Bands
        for window in [20, 30, 50]:
            sma = df['close'].rolling(window=window).mean()
            std = df['close'].rolling(window=window).std()
            df[f'bb_upper_{window}'] = sma + (std * 2)
            df[f'bb_lower_{window}'] = sma - (std * 2)
            df[f'bb_position_{window}'] = (df['close'] - df[f'bb_lower_{window}']) / (df[f'bb_upper_{window}'] - df[f'bb_lower_{window}'])
            df[f'bb_width_{window}'] = (df[f'bb_upper_{window}'] - df[f'bb_lower_{window}']) / sma
        
        # Volatilidade
        for window in [5, 10, 20, 30, 50]:
            df[f'volatility_{window}'] = df['close'].rolling(window=window).std()
            df[f'volatility_{window}_norm'] = df[f'volatility_{window}'] / df['close']
        
        # Features de momentum
        for period in [3, 5, 10, 15, 20, 30]:
            df[f'momentum_{period}'] = df['close'] / df['close'].shift(period) - 1
            df[f'roc_{period}'] = df['close'].pct_change(periods=period)
        
        # Features de volume
        df['volume_price_trend'] = df['volume'] * df['price_change']
        df['volume_weighted_price'] = (df['volume'] * df['close']).rolling(window=20).sum() / df['volume'].rolling(window=20).sum()
        
        # Features de tempo
        if 'time' in df.columns:
            df['hour'] = pd.to_datetime(df['time']).dt.hour
            df['day_of_week'] = pd.to_datetime(df['time']).dt.dayofweek
            df['month'] = pd.to_datetime(df['time']).dt.month
            df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
            df['is_night'] = ((df['hour'] >= 22) | (df['hour'] <= 6)).astype(int)
            
            # Features cíclicas
            df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
            df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
            df['day_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
            df['day_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        else:
            # Se não tiver coluna time, usar timestamp atual
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
        df = df.dropna().reset_index(drop=True)
        
        # Selecionar features (excluir colunas originais)
        feature_columns = [col for col in df.columns if col not in ['time', 'open', 'high', 'low', 'close', 'volume']]
        
        return df, feature_columns
    
    def predict_profit(self, data, return_probabilities=False):
        """
        Prediz se haverá lucro nos dados fornecidos
        
        Args:
            data: DataFrame com colunas ['open', 'high', 'low', 'close', 'volume']
            return_probabilities: Se True, retorna probabilidades ao invés de classes
            
        Returns:
            predictions: Array com predições (0/1) ou probabilidades
        """
        if self.model is None:
            logger.error("❌ Modelo não carregado. Execute load_model() primeiro.")
            return None
        
        try:
            # Criar features
            df_with_features, feature_columns = self.create_features(data)
            
            if len(df_with_features) == 0:
                logger.warning("⚠️ Nenhum dado válido após criação de features")
                return None
            
            # Selecionar features para predição
            X = df_with_features[feature_columns]
            
            # Fazer predição
            if return_probabilities:
                if hasattr(self.model, 'predict_proba'):
                    predictions = self.model.predict_proba(X)[:, 1]  # Probabilidade da classe positiva
                else:
                    logger.warning("⚠️ Modelo não suporta probabilidades, retornando predições binárias")
                    predictions = self.model.predict(X)
            else:
                predictions = self.model.predict(X)
            
            return predictions
            
        except Exception as e:
            logger.error(f"❌ Erro na predição: {e}")
            return None
    
    def get_trading_signal(self, data, probability_threshold=0.7):
        """
        Gera sinal de trading baseado no modelo
        
        Args:
            data: DataFrame com dados OHLCV
            probability_threshold: Threshold mínimo de probabilidade para sinal de compra
            
        Returns:
            dict com sinal e informações
        """
        probabilities = self.predict_profit(data, return_probabilities=True)
        
        if probabilities is None or len(probabilities) == 0:
            return {
                'signal': 'HOLD',
                'probability': 0.0,
                'confidence': 'LOW',
                'reason': 'Dados insuficientes'
            }
        
        # Usar a última predição (mais recente)
        latest_prob = probabilities[-1]
        
        # Determinar sinal
        if latest_prob >= probability_threshold:
            signal = 'BUY'
            confidence = 'HIGH' if latest_prob >= 0.8 else 'MEDIUM'
        elif latest_prob <= (1 - probability_threshold):
            signal = 'SELL'
            confidence = 'HIGH' if latest_prob <= 0.2 else 'MEDIUM'
        else:
            signal = 'HOLD'
            confidence = 'LOW'
        
        return {
            'signal': signal,
            'probability': latest_prob,
            'confidence': confidence,
            'expected_profit': self.model_params['profit_threshold'],
            'time_horizon': self.model_params['time_horizon'],
            'reason': f"Probabilidade de {self.model_params['profit_threshold']}% lucro em {self.model_params['time_horizon']}min: {latest_prob:.1%}"
        }
    
    def get_model_info(self):
        """Retorna informações do modelo"""
        if self.model_params is None:
            return None
        
        return {
            'algorithm': self.model_params['model_name'],
            'accuracy': self.model_params['cv_mean_accuracy'],
            'profit_threshold': self.model_params['profit_threshold'],
            'time_horizon': self.model_params['time_horizon'],
            'gpu_trained': self.model_params.get('gpu_used', False),
            'generation': self.model_params['generation'],
            'training_samples': self.model_params['n_samples'],
            'features_count': self.model_params['n_features']
        }

def copy_model_to_quantum_trail():
    """
    Copia o modelo para o projeto QuantumTrail
    """
    quantum_trail_path = "/media/fns/d2d27ca5-f4ff-47d5-904c-16d415de1501/git/personal/quantum-trail/QuantumTrail"
    
    if not os.path.exists(quantum_trail_path):
        logger.error(f"❌ Diretório QuantumTrail não encontrado: {quantum_trail_path}")
        return False
    
    try:
        import shutil
        
        # Arquivos para copiar
        files_to_copy = [
            'gpu_perfect_model.pkl',
            'gpu_perfect_model_params.json',
            'load_perfect_model.py'
        ]
        
        copied_files = []
        for file in files_to_copy:
            if os.path.exists(file):
                dest_path = os.path.join(quantum_trail_path, file)
                shutil.copy2(file, dest_path)
                copied_files.append(file)
                logger.info(f"✅ Copiado: {file} → QuantumTrail/")
        
        if copied_files:
            logger.info(f"🎉 {len(copied_files)} arquivos copiados para QuantumTrail!")
            logger.info("💡 Para usar no QuantumTrail:")
            logger.info("   from load_perfect_model import PerfectModelLoader")
            logger.info("   loader = PerfectModelLoader()")
            logger.info("   loader.load_model()")
            logger.info("   signal = loader.get_trading_signal(your_data)")
            return True
        else:
            logger.warning("⚠️ Nenhum arquivo encontrado para copiar")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erro ao copiar arquivos: {e}")
        return False

# Exemplo de uso
def example_usage():
    """Exemplo de como usar o modelo"""
    
    # Carregar modelo
    loader = PerfectModelLoader()
    if not loader.load_model():
        return
    
    # Dados de exemplo (substitua pelos seus dados reais)
    sample_data = pd.DataFrame({
        'open': [50000, 50100, 50200, 50150, 50300],
        'high': [50200, 50300, 50400, 50350, 50500],
        'low': [49900, 50000, 50100, 50050, 50200],
        'close': [50100, 50200, 50150, 50300, 50400],
        'volume': [1000, 1200, 800, 1500, 1100]
    })
    
    # Obter sinal de trading
    signal = loader.get_trading_signal(sample_data)
    
    logger.info("📊 SINAL DE TRADING:")
    logger.info(f"   🎯 Sinal: {signal['signal']}")
    logger.info(f"   📈 Probabilidade: {signal['probability']:.1%}")
    logger.info(f"   🔒 Confiança: {signal['confidence']}")
    logger.info(f"   💰 Lucro esperado: {signal['expected_profit']}%")
    logger.info(f"   ⏰ Horizonte: {signal['time_horizon']} min")
    logger.info(f"   💡 Razão: {signal['reason']}")

if __name__ == "__main__":
    # Executar exemplo
    example_usage()
    
    # Copiar para QuantumTrail se solicitado
    if len(sys.argv) > 1 and sys.argv[1] == "--copy-to-quantum":
        copy_model_to_quantum_trail() 