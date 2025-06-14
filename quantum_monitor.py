#!/usr/bin/env python3
"""
📊 QUANTUM TRAIL - MONITOR EM TEMPO REAL
Sistema de monitoramento avançado para o bot de trading
"""

import os
import time
import json
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import requests
from quantum_trading_optimized import QuantumTradingSystem

class QuantumMonitor:
    def __init__(self):
        self.quantum = QuantumTradingSystem()
        self.db_path = 'quantum_performance.db'
        self.init_database()
        
    def init_database(self):
        """Inicializa banco de dados para histórico"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                signal TEXT,
                probability REAL,
                confidence TEXT,
                price REAL,
                symbol TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                entry_price REAL,
                position_size REAL,
                stop_loss REAL,
                take_profit REAL,
                status TEXT,
                profit REAL DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_signal(self, signal):
        """Salva sinal no banco"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO signals (timestamp, signal, probability, confidence, price, symbol)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            signal['timestamp'],
            signal['signal'],
            signal['probability'],
            signal['confidence'],
            signal['price'],
            signal.get('symbol', 'BTCUSDT')
        ))
        
        conn.commit()
        conn.close()
    
    def get_market_sentiment(self):
        """Analisa sentimento do mercado"""
        try:
            # Últimos 24h de dados
            url = "https://api.binance.com/api/v3/ticker/24hr"
            params = {'symbol': 'BTCUSDT'}
            
            response = requests.get(url, params=params, timeout=5)
            data = response.json()
            
            price_change = float(data['priceChangePercent'])
            volume = float(data['volume'])
            
            if price_change > 2:
                sentiment = "🚀 MUITO BULLISH"
            elif price_change > 0.5:
                sentiment = "📈 BULLISH"
            elif price_change > -0.5:
                sentiment = "⚖️ NEUTRO"
            elif price_change > -2:
                sentiment = "📉 BEARISH"
            else:
                sentiment = "💥 MUITO BEARISH"
            
            return {
                'sentiment': sentiment,
                'price_change_24h': price_change,
                'volume_24h': volume
            }
            
        except:
            return {
                'sentiment': "❓ DESCONHECIDO",
                'price_change_24h': 0,
                'volume_24h': 0
            }
    
    def get_performance_stats(self):
        """Calcula estatísticas de performance"""
        conn = sqlite3.connect(self.db_path)
        
        # Sinais das últimas 24h
        signals_24h = pd.read_sql_query('''
            SELECT * FROM signals 
            WHERE datetime(timestamp) > datetime('now', '-1 day')
            ORDER BY timestamp DESC
        ''', conn)
        
        # Trades
        trades = pd.read_sql_query('SELECT * FROM trades', conn)
        
        conn.close()
        
        stats = {
            'total_signals_24h': len(signals_24h),
            'buy_signals_24h': len(signals_24h[signals_24h['signal'] == 'BUY']),
            'hold_signals_24h': len(signals_24h[signals_24h['signal'] == 'HOLD']),
            'avg_probability': signals_24h['probability'].mean() if len(signals_24h) > 0 else 0,
            'total_trades': len(trades),
            'active_trades': len(trades[trades['status'] == 'OPEN']),
            'total_profit': trades['profit'].sum() if len(trades) > 0 else 0
        }
        
        return stats
    
    def display_dashboard(self):
        """Exibe dashboard em tempo real"""
        os.system('clear' if os.name == 'posix' else 'cls')
        
        print("🚀 QUANTUM TRAIL - DASHBOARD EM TEMPO REAL")
        print("=" * 70)
        
        # Obter dados atuais
        signal = self.quantum.get_trading_signal('BTCUSDT')
        sentiment = self.get_market_sentiment()
        stats = self.get_performance_stats()
        
        # Salvar sinal
        if signal['signal'] != 'ERROR':
            self.save_signal(signal)
        
        # Informações atuais
        print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"💰 Preço BTC: ${signal['price']:,.2f}")
        print(f"📊 Mudança 24h: {sentiment['price_change_24h']:+.2f}%")
        print(f"🎭 Sentimento: {sentiment['sentiment']}")
        print()
        
        # Sinal atual
        signal_emoji = "🚀" if signal['signal'] == 'BUY' else "⏸️" if signal['signal'] == 'HOLD' else "❌"
        confidence_emoji = "🔥" if signal['confidence'] == 'HIGH' else "⚡" if signal['confidence'] == 'MEDIUM' else "💤"
        
        print("📡 SINAL ATUAL:")
        print(f"   {signal_emoji} Ação: {signal['signal']}")
        print(f"   📈 Probabilidade: {signal['probability']:.1f}%")
        print(f"   {confidence_emoji} Confiança: {signal['confidence']}")
        print()
        
        # Estatísticas 24h
        print("📊 ESTATÍSTICAS 24H:")
        print(f"   🔍 Total sinais: {stats['total_signals_24h']}")
        print(f"   🚀 Sinais BUY: {stats['buy_signals_24h']}")
        print(f"   ⏸️ Sinais HOLD: {stats['hold_signals_24h']}")
        print(f"   📊 Prob. média: {stats['avg_probability']:.1f}%")
        print()
        
        # Performance de trading
        print("💼 PERFORMANCE TRADING:")
        print(f"   📈 Total trades: {stats['total_trades']}")
        print(f"   🔄 Trades ativos: {stats['active_trades']}")
        print(f"   💰 Lucro total: ${stats['total_profit']:.2f}")
        print()
        
        # Barra de probabilidade visual
        prob_bars = int(signal['probability'] / 10)
        prob_visual = "█" * prob_bars + "░" * (10 - prob_bars)
        print(f"📊 Probabilidade: [{prob_visual}] {signal['probability']:.1f}%")
        print()
        
        # Status do sistema
        system_status = "🟢 ATIVO" if signal['signal'] != 'ERROR' else "🔴 ERRO"
        print(f"🔧 Status Sistema: {system_status}")
        
        if signal['signal'] == 'ERROR':
            print(f"❌ Erro: {signal.get('error', 'Desconhecido')}")
        
        print("=" * 70)
        print("Pressione Ctrl+C para parar o monitoramento")
    
    def run_monitor(self, refresh_seconds=10):
        """Executa monitoramento contínuo"""
        try:
            while True:
                self.display_dashboard()
                time.sleep(refresh_seconds)
                
        except KeyboardInterrupt:
            print("\n⏸️ Monitoramento interrompido pelo usuário")
        except Exception as e:
            print(f"\n❌ Erro no monitoramento: {e}")
    
    def export_report(self):
        """Exporta relatório detalhado"""
        conn = sqlite3.connect(self.db_path)
        
        # Dados das últimas 24h
        signals = pd.read_sql_query('''
            SELECT * FROM signals 
            WHERE datetime(timestamp) > datetime('now', '-1 day')
            ORDER BY timestamp DESC
        ''', conn)
        
        trades = pd.read_sql_query('SELECT * FROM trades', conn)
        conn.close()
        
        # Criar relatório
        report_file = f"quantum_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'period': '24h',
            'summary': {
                'total_signals': len(signals),
                'buy_signals': len(signals[signals['signal'] == 'BUY']),
                'hold_signals': len(signals[signals['signal'] == 'HOLD']),
                'avg_probability': float(signals['probability'].mean()) if len(signals) > 0 else 0,
                'max_probability': float(signals['probability'].max()) if len(signals) > 0 else 0,
                'min_probability': float(signals['probability'].min()) if len(signals) > 0 else 0
            },
            'trading': {
                'total_trades': len(trades),
                'active_trades': len(trades[trades['status'] == 'OPEN']),
                'total_profit': float(trades['profit'].sum()) if len(trades) > 0 else 0
            },
            'signals_data': signals.to_dict('records') if len(signals) > 0 else [],
            'trades_data': trades.to_dict('records') if len(trades) > 0 else []
        }
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📊 Relatório exportado: {report_file}")
        return report_file

def main():
    monitor = QuantumMonitor()
    
    print("🚀 QUANTUM TRAIL MONITOR")
    print("Escolha uma opção:")
    print("1. Monitor em tempo real")
    print("2. Exportar relatório")
    print("3. Sair")
    
    choice = input("\nOpção: ").strip()
    
    if choice == '1':
        print("\n🔄 Iniciando monitoramento em tempo real...")
        monitor.run_monitor(refresh_seconds=5)
    elif choice == '2':
        print("\n📊 Gerando relatório...")
        monitor.export_report()
    else:
        print("\n👋 Saindo...")

if __name__ == "__main__":
    main() 