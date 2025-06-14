# 🚀 QUANTUM TRAIL - Sistema de Trading Automatizado

![QuantumTrail](https://img.shields.io/badge/QuantumTrail-v2.0-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.8+-green?style=for-the-badge)
![ML](https://img.shields.io/badge/ML-XGBoost-orange?style=for-the-badge)
![Accuracy](https://img.shields.io/badge/Accuracy-88.62%25-red?style=for-the-badge)

## 📋 Índice

- [Visão Geral](#-visão-geral)
- [Características](#-características)
- [Instalação](#-instalação)
- [Guia de Uso](#-guia-de-uso)
- [Componentes do Sistema](#-componentes-do-sistema)
- [Configurações](#-configurações)
- [Exemplos Práticos](#-exemplos-práticos)
- [Monitoramento](#-monitoramento)
- [FAQ](#-faq)
- [Suporte](#-suporte)

## 🎯 Visão Geral

O **QuantumTrail** é um sistema avançado de trading automatizado que utiliza Machine Learning para prever movimentos do Bitcoin com **88.62% de acurácia**. O sistema foi projetado para operar 24/7 com segurança máxima e controle total do usuário.

### 🏆 Principais Conquistas
- ✅ **88.62% de acurácia** em predições
- ✅ **113 indicadores técnicos** avançados
- ✅ **XGBoost GPU** para processamento rápido
- ✅ **Testnet Binance** para operação segura
- ✅ **Interface de controle** intuitiva

## 🌟 Características

### 🤖 Inteligência Artificial
- **Modelo XGBoost GPU** treinado com 78,984 amostras
- **113 features técnicas** incluindo RSI, MACD, Bollinger Bands
- **Predição de 0.2%** de lucro em janelas de 15 minutos
- **Análise de sentimento** de mercado em tempo real

### 🛡️ Segurança
- **Testnet Binance** - sem risco de capital real
- **Stop Loss automático** configurável
- **Take Profit inteligente** baseado em ML
- **Gestão de risco** por trade

### 📊 Monitoramento
- **Dashboard em tempo real** com estatísticas
- **Histórico completo** de sinais e trades
- **Relatórios detalhados** exportáveis
- **Alertas visuais** de performance

## 🔧 Instalação

### Pré-requisitos
```bash
# Python 3.8 ou superior
python3 --version

# Git para clonar o repositório
git --version
```

### 1. Clonar o Repositório
```bash
git clone https://github.com/seu-usuario/quantum-trail.git
cd quantum-trail/QuantumTrail
```

### 2. Instalar Dependências
```bash
# Instalar dependências Python
pip install -r requirements.txt

# Instalar TA-Lib (necessário para indicadores técnicos)
# Ubuntu/Debian:
sudo apt-get install libta-lib-dev
pip install TA-Lib

# macOS:
brew install ta-lib
pip install TA-Lib

# Windows: baixar binários do TA-Lib
```

### 3. Configurar API Binance
```bash
# Criar conta na Binance Testnet
# https://testnet.binance.vision/

# Obter suas chaves API
# Configurar no arquivo .env (será criado automaticamente)
```

## 🚀 Guia de Uso

### Início Rápido (3 passos)

#### 1️⃣ Centro de Controle
```bash
python3 quantum_control_center.py
```
**Interface principal** com todas as funcionalidades:
- Iniciar/parar trading
- Configurar parâmetros
- Monitorar performance
- Análise de sinais

#### 2️⃣ Monitor em Tempo Real
```bash
python3 quantum_monitor.py
```
**Dashboard visual** com:
- Preço atual do Bitcoin
- Sinais de trading ao vivo
- Estatísticas de performance
- Sentimento de mercado

#### 3️⃣ Sistema Otimizado
```bash
python3 quantum_trading_optimized.py
```
**Trading automatizado** com:
- Execução contínua
- Logs detalhados
- Gestão de risco automática

## 🧩 Componentes do Sistema

### 📁 Estrutura de Arquivos

```
QuantumTrail/
├── 🎛️ quantum_control_center.py    # Centro de controle principal
├── 📊 quantum_monitor.py            # Monitor em tempo real
├── 🚀 quantum_trading_optimized.py  # Sistema de trading otimizado
├── 🤖 quantum_model.py              # Modelo ML base
├── 📋 exemplo_integracao.py         # Exemplo de integração
├── 🗄️ gpu_perfect_model.pkl         # Modelo treinado (25MB)
├── ⚙️ gpu_perfect_model_params.json # Parâmetros do modelo
├── 📖 README.md                     # Esta documentação
├── 📦 requirements.txt              # Dependências Python
└── 🗃️ *.db                         # Bancos de dados SQLite
```

### 🎛️ Centro de Controle (`quantum_control_center.py`)

**Interface principal** para gerenciar todo o sistema:

```python
# Executar
python3 quantum_control_center.py

# Menu principal:
# 1. 🚀 Iniciar/Parar Trading
# 2. ⚙️ Configurar Parâmetros  
# 3. 📊 Monitor em Tempo Real
# 4. 📈 Análise de Sinal Único
# 5. 📋 Relatório de Performance
# 6. 🔧 Configurações Avançadas
# 7. 💾 Salvar/Carregar Config
# 8. 🚪 Sair
```

### 📊 Monitor (`quantum_monitor.py`)

**Dashboard visual** com atualizações em tempo real:

```bash
🚀 QUANTUM TRAIL - DASHBOARD EM TEMPO REAL
======================================================================
⏰ Timestamp: 2025-06-14 22:53:49
💰 Preço BTC: $104,593.89
📊 Mudança 24h: -0.53%
🎭 Sentimento: 📉 BEARISH

📡 SINAL ATUAL:
   ⏸️ Ação: HOLD
   📈 Probabilidade: 7.5%
   🔥 Confiança: HIGH

📊 ESTATÍSTICAS 24H:
   🔍 Total sinais: 6
   🚀 Sinais BUY: 0
   ⏸️ Sinais HOLD: 6
   📊 Prob. média: 9.0%

💼 PERFORMANCE TRADING:
   📈 Total trades: 0
   🔄 Trades ativos: 0
   💰 Lucro total: $0.00

📊 Probabilidade: [░░░░░░░░░░] 7.5%
🔧 Status Sistema: 🟢 ATIVO
```

### 🚀 Sistema Otimizado (`quantum_trading_optimized.py`)

**Motor de trading** com execução automática:

```python
# Configurações principais
quantum.config['min_confidence'] = 'MEDIUM'     # HIGH, MEDIUM, LOW
quantum.config['probability_threshold'] = 0.75  # 75% mínimo
quantum.config['max_risk_per_trade'] = 0.01     # 1% por trade
quantum.config['stop_loss'] = 0.001             # 0.1% stop loss
quantum.config['take_profit'] = 0.002           # 0.2% take profit
```

## ⚙️ Configurações

### 🎯 Parâmetros de Trading

| Parâmetro | Descrição | Valores | Padrão |
|-----------|-----------|---------|--------|
| `min_confidence` | Confiança mínima para executar trades | HIGH, MEDIUM, LOW | MEDIUM |
| `probability_threshold` | Probabilidade mínima (%) | 50-95 | 70 |
| `max_risk_per_trade` | Risco máximo por trade (%) | 0.1-5.0 | 2.0 |
| `stop_loss` | Stop loss automático (%) | 0.1-2.0 | 0.1 |
| `take_profit` | Take profit automático (%) | 0.1-5.0 | 0.2 |
| `cooldown_minutes` | Tempo entre trades (min) | 1-60 | 5 |

### 🔧 Configuração Avançada

```python
# Exemplo de configuração personalizada
config = {
    'min_confidence': 'HIGH',        # Apenas sinais de alta confiança
    'probability_threshold': 0.85,   # 85% de probabilidade mínima
    'max_risk_per_trade': 0.005,     # 0.5% de risco por trade
    'stop_loss': 0.0005,             # 0.05% stop loss (muito conservador)
    'take_profit': 0.003,            # 0.3% take profit
    'cooldown_minutes': 10           # 10 minutos entre trades
}
```

## 💡 Exemplos Práticos

### 🎯 Exemplo 1: Trading Conservador
```python
# Configuração para trading conservador
python3 quantum_control_center.py

# No menu:
# 2. ⚙️ Configurar Parâmetros
# 1. 🎯 Confiança Mínima -> HIGH
# 2. 📊 Threshold -> 90%
# 3. 💰 Risco -> 0.5%

# 1. 🚀 Iniciar Trading
```

### ⚡ Exemplo 2: Trading Agressivo
```python
# Configuração para trading agressivo
python3 quantum_control_center.py

# No menu:
# 2. ⚙️ Configurar Parâmetros
# 1. 🎯 Confiança Mínima -> MEDIUM
# 2. 📊 Threshold -> 65%
# 3. 💰 Risco -> 2.0%

# 1. 🚀 Iniciar Trading
```

### 📊 Exemplo 3: Análise de Sinal
```python
# Análise única sem trading
python3 quantum_control_center.py

# No menu:
# 4. 📈 Análise de Sinal Único
# Digite: BTCUSDT (ou outro par)

# Resultado:
# 🎯 Sinal: BUY/HOLD
# 📈 Probabilidade: XX.X%
# 🔒 Confiança: HIGH/MEDIUM/LOW
# 💰 Preço: $XX,XXX.XX
```

## 📈 Monitoramento

### 📊 Dashboard em Tempo Real

```bash
# Iniciar monitor
python3 quantum_monitor.py

# Escolher opção:
# 1. Monitor em tempo real    # Dashboard visual
# 2. Exportar relatório      # Relatório JSON
# 3. Sair
```

### 📋 Relatórios

O sistema gera relatórios automáticos em formato JSON:

```json
{
  "timestamp": "2025-06-14T22:53:49",
  "period": "24h",
  "summary": {
    "total_signals": 156,
    "buy_signals": 23,
    "hold_signals": 133,
    "avg_probability": 45.2,
    "max_probability": 94.1,
    "min_probability": 5.3
  },
  "trading": {
    "total_trades": 8,
    "active_trades": 2,
    "total_profit": 15.67
  }
}
```

### 🗄️ Banco de Dados

O sistema mantém histórico completo em SQLite:

- **`quantum_performance.db`** - Sinais e trades
- **`trading_system.db`** - Configurações do sistema
- **`trading_history.db`** - Histórico detalhado

## ❓ FAQ

### ❓ Como funciona a predição ML?

O modelo XGBoost analisa **113 indicadores técnicos** em tempo real:
- RSI (7, 14, 21, 30, 50 períodos)
- MACD e histograma
- Bollinger Bands (20, 30, 50 períodos)
- Médias móveis (SMA/EMA)
- Volatilidade e momentum
- Features temporais (hora, dia da semana)

### ❓ É seguro usar?

**100% seguro** - opera apenas na **Testnet Binance**:
- ✅ Sem risco de capital real
- ✅ Ambiente de teste oficial
- ✅ Mesma API da Binance real
- ✅ Dados de mercado reais

### ❓ Qual a performance esperada?

Baseado no backtesting:
- **88.62% de acurácia** nas predições
- **0.2% de lucro médio** por trade bem-sucedido
- **15 minutos** de horizonte temporal
- **23.67% de taxa de lucro** no dataset de teste

### ❓ Como personalizar estratégias?

```python
# Editar quantum_trading_optimized.py
def create_custom_strategy(self, signal):
    # Sua lógica personalizada aqui
    if signal['probability'] > 95 and signal['confidence'] == 'HIGH':
        return 'STRONG_BUY'
    elif signal['probability'] < 20:
        return 'STRONG_SELL'
    else:
        return 'HOLD'
```

### ❓ Como adicionar novos pares?

```python
# Modificar símbolo no código
signal = quantum.get_trading_signal('ETHUSDT')  # Ethereum
signal = quantum.get_trading_signal('ADAUSDT')  # Cardano
signal = quantum.get_trading_signal('DOTUSDT')  # Polkadot
```

### ❓ Como fazer backup?

```bash
# Backup completo
cp quantum_performance.db backup_$(date +%Y%m%d).db
cp quantum_config.json backup_config_$(date +%Y%m%d).json
cp *.log backup_logs/
```

## 🆘 Suporte

### 🐛 Problemas Comuns

#### Erro: "TA-Lib not found"
```bash
# Ubuntu/Debian
sudo apt-get install libta-lib-dev
pip install TA-Lib

# macOS
brew install ta-lib
pip install TA-Lib
```

#### Erro: "Feature names mismatch"
```bash
# Recriar modelo com features corretas
python3 quantum_model.py
```

#### Erro: "API connection failed"
```bash
# Verificar conexão internet
ping api.binance.com

# Verificar chaves API na Binance Testnet
```

### 📞 Contato

- **GitHub Issues**: Para bugs e melhorias
- **Email**: suporte@quantumtrail.com
- **Discord**: QuantumTrail Community
- **Telegram**: @QuantumTrailBot

### 🤝 Contribuições

Contribuições são bem-vindas! Por favor:

1. Fork o repositório
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

### 📄 Licença

Este projeto está licenciado sob a MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

---

## 🎉 Começar Agora

```bash
# 1. Clonar repositório
git clone https://github.com/seu-usuario/quantum-trail.git
cd quantum-trail/QuantumTrail

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Executar centro de controle
python3 quantum_control_center.py

# 4. Configurar e iniciar trading!
```

**🚀 Bem-vindo ao futuro do trading automatizado com QuantumTrail!**

---

*Última atualização: 14 de Junho de 2025*
*Versão: 2.0*
*Status: Produção* 