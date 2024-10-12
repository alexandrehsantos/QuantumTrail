import sys
import joblib
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QMessageBox, QDateEdit, QMainWindow
from PyQt5.QtCore import QDate
from trading_system.trading_system import TradingSystem
from trading_system.data_sources.live_data_source import LiveDataSource
from trading_system.data_sources.historical_data_source import HistoricalDataSource
from trading_system.strategies.macd_strategy import MACDStrategy
from trading_system.strategies.mean_reversion_strategy import MeanReversionStrategy
from trading_system.strategies.machine_learning import MLStrategy
from trading_system.risk_management.risk_manager import RiskManager

class TradingUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Trading System')
        self.setGeometry(100, 100, 300, 200)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.symbol_input = QLineEdit(self)
        self.symbol_input.setPlaceholderText('Enter symbol (e.g., BTCUSD)')
        layout.addWidget(self.symbol_input)

        self.timeframe_combo = QComboBox(self)
        self.timeframe_combo.addItems(['1m', '5m', '15m', '30m', '1h', '4h', '1d'])
        layout.addWidget(self.timeframe_combo)

        self.strategy_combo = QComboBox(self)
        self.strategy_combo.addItems(['MACD', 'Mean Reversion', 'ML Strategy'])
        layout.addWidget(self.strategy_combo)

        self.start_button = QPushButton('Start Trading', self)
        self.start_button.clicked.connect(self.start_trading)
        layout.addWidget(self.start_button)

    def start_trading(self):
        symbol = self.symbol_input.text()
        timeframe = self._map_timeframe(self.timeframe_combo.currentText())
        strategy_name = self.strategy_combo.currentText()

        if not symbol:
            QMessageBox.warning(self, 'Input Error', 'Please enter a symbol.')
            return

        try:
            data_source = LiveDataSource(symbol=symbol, timeframe=timeframe)
            data_source.initialize()

            risk_manager = RiskManager(initial_balance=1000, risk_per_trade=0.01)

            if strategy_name == 'MACD':
                strategy = MACDStrategy(data_source, risk_manager, symbol, timeframe)
            elif strategy_name == 'Mean Reversion':
                strategy = MeanReversionStrategy(data_source, risk_manager, symbol, timeframe)
            elif strategy_name == 'ML Strategy':
                model = self.load_ml_model()
                features = ['macd', 'signal_line', 'rsi']
                strategy = MLStrategy(data_source, risk_manager, symbol, timeframe, model, features)
            else:
                raise ValueError(f"Unknown strategy: {strategy_name}")

            trading_system = TradingSystem(data_source, strategy, symbol, timeframe)
            trading_system.run()

            QMessageBox.information(self, 'Trading Started', f'Trading started for {symbol} with {strategy_name} strategy.')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'An error occurred: {str(e)}')

    def _map_timeframe(self, timeframe_str):
        mapping = {'1m': 1, '5m': 5, '15m': 15, '30m': 30, '1h': 60, '4h': 240, '1d': 1440}
        return mapping.get(timeframe_str, 1)

    def load_ml_model(self):
        try:
            model = joblib.load('ml_model.pkl')
            return model
        except FileNotFoundError:
            QMessageBox.critical(self, 'Error', 'Model file not found. Please ensure the model is trained and saved correctly.')
            raise
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'An error occurred while loading the model: {str(e)}')
            raise

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = TradingUI()
    ex.show()
    sys.exit(app.exec_())
