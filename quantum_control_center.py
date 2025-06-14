#!/usr/bin/env python3
"""
🎛️ QUANTUM TRAIL - CENTRO DE CONTROLE AVANÇADO
Sistema de controle total com ajustes em tempo real
"""

import os
import json
import time
import threading
from datetime import datetime
import sqlite3
from quantum_trading_optimized import QuantumTradingSystem
from quantum_monitor import QuantumMonitor

class QuantumControlCenter:
    def __init__(self):
        self.quantum = QuantumTradingSystem()
        self.monitor = QuantumMonitor()
        self.running = False
        self.trading_thread = None
        self.config_file = 'quantum_config.json'
        
        self.load_config()
        
    def load_config(self):
        """Carrega configurações salvas"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.quantum.config.update(config)
                    print("✅ Configurações carregadas")
            else:
                self.save_config()
        except Exception as e:
            print(f"⚠️ Erro ao carregar config: {e}")
    
    def save_config(self):
        """Salva configurações atuais"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.quantum.config, f, indent=2)
            print("💾 Configurações salvas")
        except Exception as e:
            print(f"❌ Erro ao salvar config: {e}")
    
    def display_main_menu(self):
        """Exibe menu principal"""
        os.system('clear' if os.name == 'posix' else 'cls')
        
        print("🎛️ QUANTUM TRAIL - CENTRO DE CONTROLE")
        print("=" * 60)
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Status atual
        status = "🟢 RODANDO" if self.running else "🔴 PARADO"
        print(f"🔧 Status: {status}")
        
        # Configurações atuais
        print("\n⚙️ CONFIGURAÇÕES ATUAIS:")
        print(f"   🎯 Confiança mínima: {self.quantum.config['min_confidence']}")
        print(f"   📊 Threshold prob.: {self.quantum.config['probability_threshold']*100:.0f}%")
        print(f"   💰 Risco por trade: {self.quantum.config['max_risk_per_trade']*100:.1f}%")
        print(f"   🛡️ Stop Loss: {self.quantum.config['stop_loss']*100:.1f}%")
        print(f"   🎯 Take Profit: {self.quantum.config['take_profit']*100:.1f}%")
        print(f"   ⏰ Cooldown: {self.quantum.config['cooldown_minutes']} min")
        
        print("\n📋 OPÇÕES:")
        print("1. 🚀 Iniciar/Parar Trading")
        print("2. ⚙️ Configurar Parâmetros")
        print("3. 📊 Monitor em Tempo Real")
        print("4. 📈 Análise de Sinal Único")
        print("5. 📋 Relatório de Performance")
        print("6. 🔧 Configurações Avançadas")
        print("7. 💾 Salvar/Carregar Config")
        print("8. 🚪 Sair")
        print("=" * 60)
    
    def configure_parameters(self):
        """Menu de configuração de parâmetros"""
        while True:
            os.system('clear' if os.name == 'posix' else 'cls')
            print("⚙️ CONFIGURAÇÃO DE PARÂMETROS")
            print("=" * 50)
            
            print("1. 🎯 Confiança Mínima")
            print("2. 📊 Threshold de Probabilidade")
            print("3. 💰 Risco por Trade")
            print("4. 🛡️ Stop Loss")
            print("5. 🎯 Take Profit")
            print("6. ⏰ Cooldown entre Trades")
            print("7. 🔙 Voltar")
            
            choice = input("\nEscolha: ").strip()
            
            if choice == '1':
                self.set_confidence_level()
            elif choice == '2':
                self.set_probability_threshold()
            elif choice == '3':
                self.set_risk_per_trade()
            elif choice == '4':
                self.set_stop_loss()
            elif choice == '5':
                self.set_take_profit()
            elif choice == '6':
                self.set_cooldown()
            elif choice == '7':
                break
    
    def set_confidence_level(self):
        """Configura nível de confiança"""
        print("\n🎯 CONFIGURAR CONFIANÇA MÍNIMA:")
        print("1. LOW - Aceita sinais de baixa confiança")
        print("2. MEDIUM - Apenas sinais médios e altos")
        print("3. HIGH - Apenas sinais de alta confiança")
        
        choice = input("Escolha (1-3): ").strip()
        
        levels = {'1': 'LOW', '2': 'MEDIUM', '3': 'HIGH'}
        if choice in levels:
            self.quantum.config['min_confidence'] = levels[choice]
            print(f"✅ Confiança definida para: {levels[choice]}")
            input("Pressione Enter para continuar...")
    
    def set_probability_threshold(self):
        """Configura threshold de probabilidade"""
        try:
            current = self.quantum.config['probability_threshold'] * 100
            print(f"\n📊 Threshold atual: {current:.0f}%")
            new_threshold = float(input("Novo threshold (50-95): "))
            
            if 50 <= new_threshold <= 95:
                self.quantum.config['probability_threshold'] = new_threshold / 100
                print(f"✅ Threshold definido para: {new_threshold:.0f}%")
            else:
                print("❌ Valor deve estar entre 50 e 95")
                
            input("Pressione Enter para continuar...")
        except ValueError:
            print("❌ Valor inválido")
            input("Pressione Enter para continuar...")
    
    def set_risk_per_trade(self):
        """Configura risco por trade"""
        try:
            current = self.quantum.config['max_risk_per_trade'] * 100
            print(f"\n💰 Risco atual: {current:.1f}%")
            new_risk = float(input("Novo risco por trade (0.1-5.0): "))
            
            if 0.1 <= new_risk <= 5.0:
                self.quantum.config['max_risk_per_trade'] = new_risk / 100
                print(f"✅ Risco definido para: {new_risk:.1f}%")
            else:
                print("❌ Valor deve estar entre 0.1 e 5.0")
                
            input("Pressione Enter para continuar...")
        except ValueError:
            print("❌ Valor inválido")
            input("Pressione Enter para continuar...")
    
    def set_stop_loss(self):
        """Configura stop loss"""
        try:
            current = self.quantum.config['stop_loss'] * 100
            print(f"\n🛡️ Stop Loss atual: {current:.1f}%")
            new_stop = float(input("Novo stop loss (0.1-2.0): "))
            
            if 0.1 <= new_stop <= 2.0:
                self.quantum.config['stop_loss'] = new_stop / 100
                print(f"✅ Stop Loss definido para: {new_stop:.1f}%")
            else:
                print("❌ Valor deve estar entre 0.1 e 2.0")
                
            input("Pressione Enter para continuar...")
        except ValueError:
            print("❌ Valor inválido")
            input("Pressione Enter para continuar...")
    
    def set_take_profit(self):
        """Configura take profit"""
        try:
            current = self.quantum.config['take_profit'] * 100
            print(f"\n🎯 Take Profit atual: {current:.1f}%")
            new_tp = float(input("Novo take profit (0.1-5.0): "))
            
            if 0.1 <= new_tp <= 5.0:
                self.quantum.config['take_profit'] = new_tp / 100
                print(f"✅ Take Profit definido para: {new_tp:.1f}%")
            else:
                print("❌ Valor deve estar entre 0.1 e 5.0")
                
            input("Pressione Enter para continuar...")
        except ValueError:
            print("❌ Valor inválido")
            input("Pressione Enter para continuar...")
    
    def set_cooldown(self):
        """Configura cooldown"""
        try:
            current = self.quantum.config['cooldown_minutes']
            print(f"\n⏰ Cooldown atual: {current} min")
            new_cooldown = int(input("Novo cooldown (1-60 min): "))
            
            if 1 <= new_cooldown <= 60:
                self.quantum.config['cooldown_minutes'] = new_cooldown
                print(f"✅ Cooldown definido para: {new_cooldown} min")
            else:
                print("❌ Valor deve estar entre 1 e 60")
                
            input("Pressione Enter para continuar...")
        except ValueError:
            print("❌ Valor inválido")
            input("Pressione Enter para continuar...")
    
    def toggle_trading(self):
        """Liga/desliga trading"""
        if not self.running:
            print("🚀 Iniciando sistema de trading...")
            self.running = True
            self.trading_thread = threading.Thread(
                target=self.run_trading_background,
                daemon=True
            )
            self.trading_thread.start()
            print("✅ Trading iniciado!")
        else:
            print("⏸️ Parando sistema de trading...")
            self.running = False
            if self.trading_thread:
                self.trading_thread.join(timeout=5)
            print("✅ Trading parado!")
        
        input("Pressione Enter para continuar...")
    
    def run_trading_background(self):
        """Executa trading em background"""
        try:
            while self.running:
                signal = self.quantum.get_trading_signal('BTCUSDT')
                
                if signal['signal'] == 'BUY':
                    trade = self.quantum.execute_trade(signal)
                    if trade:
                        self.log_trade(trade)
                
                time.sleep(30)  # Intervalo de 30 segundos
                
        except Exception as e:
            print(f"❌ Erro no trading: {e}")
            self.running = False
    
    def log_trade(self, trade):
        """Registra trade no banco"""
        try:
            conn = sqlite3.connect(self.monitor.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO trades (timestamp, entry_price, position_size, stop_loss, take_profit, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                trade['timestamp'],
                trade['entry_price'],
                trade['position_size'],
                trade['stop_loss'],
                trade['take_profit'],
                trade['status']
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"❌ Erro ao registrar trade: {e}")
    
    def single_signal_analysis(self):
        """Análise de sinal único"""
        print("📈 ANÁLISE DE SINAL ÚNICO")
        print("=" * 40)
        
        symbol = input("Símbolo (BTCUSDT): ").strip() or 'BTCUSDT'
        
        print(f"\n🔍 Analisando {symbol}...")
        signal = self.quantum.get_trading_signal(symbol)
        
        print("\n📊 RESULTADO:")
        print(f"   🎯 Sinal: {signal['signal']}")
        print(f"   📈 Probabilidade: {signal['probability']:.2f}%")
        print(f"   🔒 Confiança: {signal['confidence']}")
        print(f"   💰 Preço: ${signal['price']:,.2f}")
        print(f"   ⏰ Timestamp: {signal['timestamp']}")
        
        if signal['signal'] == 'BUY':
            print(f"   🎯 Lucro esperado: {signal['expected_profit']:.1f}%")
            print(f"   ⏰ Horizonte: {signal['time_horizon']} min")
        
        input("\nPressione Enter para continuar...")
    
    def advanced_settings(self):
        """Configurações avançadas"""
        while True:
            os.system('clear' if os.name == 'posix' else 'cls')
            print("🔧 CONFIGURAÇÕES AVANÇADAS")
            print("=" * 40)
            
            print("1. 🔄 Resetar Configurações")
            print("2. 📊 Estatísticas do Modelo")
            print("3. 🗄️ Limpar Banco de Dados")
            print("4. 🔙 Voltar")
            
            choice = input("\nEscolha: ").strip()
            
            if choice == '1':
                self.reset_config()
            elif choice == '2':
                self.show_model_stats()
            elif choice == '3':
                self.clear_database()
            elif choice == '4':
                break
    
    def reset_config(self):
        """Reseta configurações para padrão"""
        confirm = input("⚠️ Resetar todas as configurações? (s/N): ").strip().lower()
        if confirm == 's':
            self.quantum.config = {
                'min_confidence': 'MEDIUM',
                'max_risk_per_trade': 0.02,
                'stop_loss': 0.001,
                'take_profit': 0.002,
                'cooldown_minutes': 5,
                'probability_threshold': 0.70
            }
            self.save_config()
            print("✅ Configurações resetadas!")
        input("Pressione Enter para continuar...")
    
    def show_model_stats(self):
        """Mostra estatísticas do modelo"""
        print("📊 ESTATÍSTICAS DO MODELO:")
        print("=" * 40)
        print("🤖 Algoritmo: XGBoost GPU")
        print("🎯 Acurácia: 88.62%")
        print("💰 Target: 0.2% em 15min")
        print("🔥 Features: 113 indicadores")
        print("📈 Amostras treino: 78,984")
        print("⚡ GPU: Habilitado")
        print("📅 Treinado: 2025-06-14")
        
        input("\nPressione Enter para continuar...")
    
    def clear_database(self):
        """Limpa banco de dados"""
        confirm = input("⚠️ Limpar todo o histórico? (s/N): ").strip().lower()
        if confirm == 's':
            try:
                conn = sqlite3.connect(self.monitor.db_path)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM signals")
                cursor.execute("DELETE FROM trades")
                conn.commit()
                conn.close()
                print("✅ Banco de dados limpo!")
            except Exception as e:
                print(f"❌ Erro: {e}")
        input("Pressione Enter para continuar...")
    
    def run(self):
        """Loop principal do centro de controle"""
        while True:
            self.display_main_menu()
            choice = input("\nEscolha uma opção: ").strip()
            
            if choice == '1':
                self.toggle_trading()
            elif choice == '2':
                self.configure_parameters()
            elif choice == '3':
                print("🔄 Iniciando monitor...")
                self.monitor.run_monitor(refresh_seconds=5)
            elif choice == '4':
                self.single_signal_analysis()
            elif choice == '5':
                print("📊 Gerando relatório...")
                self.monitor.export_report()
                input("Pressione Enter para continuar...")
            elif choice == '6':
                self.advanced_settings()
            elif choice == '7':
                self.save_config()
                input("Pressione Enter para continuar...")
            elif choice == '8':
                if self.running:
                    print("⏸️ Parando trading...")
                    self.running = False
                print("👋 Saindo do centro de controle...")
                break
            else:
                print("❌ Opção inválida!")
                input("Pressione Enter para continuar...")

def main():
    control_center = QuantumControlCenter()
    control_center.run()

if __name__ == "__main__":
    main() 