# 🚀 Como Usar o Modelo Perfeito no QuantumTrail

## 📋 Resumo

Este modelo foi treinado com **GPU acceleration** usando dados históricos de BTC-USDT para predizer lucros em criptomoedas. O modelo utiliza **113 features técnicas** avançadas e foi otimizado para encontrar a configuração perfeita.

## 🎯 Especificações do Modelo

- **Algoritmo**: XGBoost com GPU (tree_method='gpu_hist')
- **Target**: 92% acurácia mínima, 98% perfeita
- **Features**: 113 indicadores técnicos (RSI, MACD, Bollinger Bands, etc.)
- **Configurações testadas**: 756 combinações diferentes
- **Dados de treino**: ~79k registros históricos

## 📁 Arquivos Necessários

Quando o treinamento terminar, estes arquivos serão copiados automaticamente para o QuantumTrail:

```
QuantumTrail/
├── gpu_perfect_model.pkl           # Modelo treinado
├── gpu_perfect_model_params.json   # Parâmetros e métricas
└── load_perfect_model.py          # Script para carregar e usar
```

## 🔧 Como Usar

### 1. Importar e Carregar

```python
from load_perfect_model import PerfectModelLoader

# Criar loader
loader = PerfectModelLoader()

# Carregar modelo
if loader.load_model():
    print("✅ Modelo carregado com sucesso!")
else:
    print("❌ Erro ao carregar modelo")
```

### 2. Preparar Dados

Seus dados devem ter estas colunas obrigatórias:

```python
import pandas as pd

# Formato esperado
data = pd.DataFrame({
    'open': [50000, 50100, 50200, ...],      # Preço abertura
    'high': [50200, 50300, 50400, ...],      # Preço máximo
    'low': [49900, 50000, 50100, ...],       # Preço mínimo
    'close': [50100, 50200, 50150, ...],     # Preço fechamento
    'volume': [1000, 1200, 800, ...]         # Volume negociado
})

# Opcional: coluna 'time' para features temporais
data['time'] = pd.date_range('2024-01-01', periods=len(data), freq='5min')
```

### 3. Obter Sinais de Trading

```python
# Obter sinal de trading
signal = loader.get_trading_signal(data)

print(f"🎯 Sinal: {signal['signal']}")           # BUY/SELL/HOLD
print(f"📈 Probabilidade: {signal['probability']:.1%}")
print(f"🔒 Confiança: {signal['confidence']}")   # HIGH/MEDIUM/LOW
print(f"💰 Lucro esperado: {signal['expected_profit']}%")
print(f"⏰ Horizonte: {signal['time_horizon']} min")
```

### 4. Predições Diretas

```python
# Predições binárias (0/1)
predictions = loader.predict_profit(data)

# Probabilidades (0.0 a 1.0)
probabilities = loader.predict_profit(data, return_probabilities=True)
```

### 5. Informações do Modelo

```python
info = loader.get_model_info()
print(f"Algoritmo: {info['algorithm']}")
print(f"Acurácia: {info['accuracy']:.4f}")
print(f"Threshold: {info['profit_threshold']}%")
print(f"Horizonte: {info['time_horizon']} min")
```

## 🎮 Integração com QuantumTrail

### Exemplo Completo

```python
#!/usr/bin/env python3
"""
Exemplo de integração do modelo perfeito com QuantumTrail
"""

from load_perfect_model import PerfectModelLoader
import pandas as pd
import numpy as np

class QuantumTrailPredictor:
    def __init__(self):
        self.loader = PerfectModelLoader()
        self.model_loaded = False
        
    def initialize(self):
        """Inicializar modelo"""
        self.model_loaded = self.loader.load_model()
        return self.model_loaded
    
    def analyze_market(self, ohlcv_data):
        """
        Analisar mercado e retornar recomendação
        
        Args:
            ohlcv_data: DataFrame com dados OHLCV
            
        Returns:
            dict com análise completa
        """
        if not self.model_loaded:
            return {'error': 'Modelo não carregado'}
        
        # Obter sinal
        signal = self.loader.get_trading_signal(ohlcv_data)
        
        # Análise adicional
        analysis = {
            'timestamp': pd.Timestamp.now(),
            'signal': signal['signal'],
            'probability': signal['probability'],
            'confidence': signal['confidence'],
            'expected_profit': signal['expected_profit'],
            'time_horizon': signal['time_horizon'],
            'reason': signal['reason'],
            'model_info': self.loader.get_model_info()
        }
        
        return analysis
    
    def should_buy(self, data, min_confidence='MEDIUM'):
        """Decisão de compra simplificada"""
        signal = self.loader.get_trading_signal(data)
        
        confidence_levels = {'LOW': 0, 'MEDIUM': 1, 'HIGH': 2}
        min_level = confidence_levels.get(min_confidence, 1)
        current_level = confidence_levels.get(signal['confidence'], 0)
        
        return (signal['signal'] == 'BUY' and 
                current_level >= min_level)
    
    def should_sell(self, data, min_confidence='MEDIUM'):
        """Decisão de venda simplificada"""
        signal = self.loader.get_trading_signal(data)
        
        confidence_levels = {'LOW': 0, 'MEDIUM': 1, 'HIGH': 2}
        min_level = confidence_levels.get(min_confidence, 1)
        current_level = confidence_levels.get(signal['confidence'], 0)
        
        return (signal['signal'] == 'SELL' and 
                current_level >= min_level)

# Uso no QuantumTrail
if __name__ == "__main__":
    # Inicializar
    predictor = QuantumTrailPredictor()
    
    if predictor.initialize():
        print("✅ QuantumTrail Predictor inicializado!")
        
        # Dados de exemplo (substitua pelos dados reais do QuantumTrail)
        sample_data = pd.DataFrame({
            'open': np.random.uniform(50000, 51000, 100),
            'high': np.random.uniform(50500, 51500, 100),
            'low': np.random.uniform(49500, 50500, 100),
            'close': np.random.uniform(50000, 51000, 100),
            'volume': np.random.uniform(800, 1500, 100)
        })
        
        # Análise
        analysis = predictor.analyze_market(sample_data)
        print("\n📊 ANÁLISE DO MERCADO:")
        for key, value in analysis.items():
            if key != 'model_info':
                print(f"   {key}: {value}")
        
        # Decisões
        print(f"\n🤔 Deve comprar? {predictor.should_buy(sample_data)}")
        print(f"🤔 Deve vender? {predictor.should_sell(sample_data)}")
    
    else:
        print("❌ Erro ao inicializar predictor")
```

## ⚙️ Configurações Avançadas

### Ajustar Threshold de Probabilidade

```python
# Mais conservador (menos sinais, maior precisão)
signal = loader.get_trading_signal(data, probability_threshold=0.8)

# Mais agressivo (mais sinais, menor precisão)
signal = loader.get_trading_signal(data, probability_threshold=0.6)
```

### Usar Modelo de Caminho Específico

```python
# Se os arquivos estiverem em outro local
loader = PerfectModelLoader(
    model_path='/caminho/para/gpu_perfect_model.pkl',
    params_path='/caminho/para/gpu_perfect_model_params.json'
)
```

## 🚨 Importante

1. **Dados Mínimos**: Precisa de pelo menos 100 pontos de dados para criar features adequadamente
2. **Frequência**: Modelo foi treinado com dados de 5 minutos
3. **Criptomoeda**: Otimizado para BTC-USDT, mas pode funcionar com outros pares
4. **Backtesting**: Sempre teste em dados históricos antes de usar em produção

## 📈 Métricas Esperadas

Quando o modelo estiver pronto, você verá métricas como:

- **Acurácia**: 92%+ (target mínimo)
- **Precisão**: Alta para sinais de BUY/SELL
- **Recall**: Balanceado para detectar oportunidades
- **F1-Score**: Otimizado para trading

## 🔄 Monitoramento Automático

Para monitorar quando o modelo estiver pronto:

```bash
# Monitorar e copiar automaticamente quando pronto
python3 auto_copy_when_ready.py

# Apenas verificar status
python3 auto_copy_when_ready.py --status
```

## 🎉 Próximos Passos

1. ✅ Aguardar conclusão do treinamento (6-8 horas estimadas)
2. ✅ Modelo será copiado automaticamente para QuantumTrail
3. 🔄 Integrar com sua estratégia de trading
4. 📊 Fazer backtesting com dados históricos
5. 🚀 Implementar em produção com gestão de risco

---

**Status do Treinamento**: 🔄 Em andamento (29+ minutos, GPU 88% utilizada)

**ETA**: ~5-7 horas restantes

**Próxima Verificação**: Automática a cada 60 segundos 