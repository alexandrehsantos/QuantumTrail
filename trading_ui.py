import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import joblib
import logging
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QMessageBox, QMainWindow, QCheckBox
from PyQt5.QtCore import QThread, pyqtSignal, QObject
from trading_system.trading_system import TradingSystem
from trading_system.data_sources.live_data_source import LiveDataSource
from trading_system.data_sources.historical_data_source import HistoricalDataSource
from trading_system.strategies.strategy_factory import StrategyFactory
from trading_system.risk_management.risk_manager import RiskManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TradingWorker(QObject):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, trading_system):
        super().__init__()
        self.trading_system = trading_system

    def run(self):
        try:
            result = self.trading_system.run()
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

class TradingUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Trading System')
        self.setGeometry(100, 100, 300, 400)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.symbol_label = QLabel('Symbol:')
        self.symbol_input = QLineEdit('BTCUSD')
        layout.addWidget(self.symbol_label)
        layout.addWidget(self.symbol_input)

        self.timeframe_label = QLabel('Timeframe:')
        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems(['1m', '5m', '15m', '30m', '1h', '4h', '1d'])
        layout.addWidget(self.timeframe_label)
        layout.addWidget(self.timeframe_combo)

        self.strategy_label = QLabel('Strategy:')
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItem("MACD")
        self.strategy_combo.addItem("Mean Reversion")
        self.strategy_combo.addItem("Machine Learning")
        self.strategy_combo.addItem("XGB")
        self.strategy_combo.addItem("Chart Pattern")
        self.strategy_combo.addItem("High Frequency")
        self.strategy_combo.addItem("TopBottom")
        layout.addWidget(self.strategy_label)
        layout.addWidget(self.strategy_combo)

        # Add a ComboBox for data source selection
        self.data_source_label = QLabel('Data Source:')
        self.data_source_combo = QComboBox()
        self.data_source_combo.addItem("Live")
        self.data_source_combo.addItem("History")  # Add the "History" option
        layout.addWidget(self.data_source_label)
        layout.addWidget(self.data_source_combo)

        # Add a checkbox for starting with minimum volume
        self.min_volume_checkbox = QCheckBox("Start with Minimum Volume", self)
        layout.addWidget(self.min_volume_checkbox)

        self.start_button = QPushButton('Start Trading')
        self.start_button.clicked.connect(self.start_trading)
        layout.addWidget(self.start_button)

        self.terminate_button = QPushButton('Exit System')
        self.terminate_button.clicked.connect(self.terminate_system)
        layout.addWidget(self.terminate_button)

        self.show()

    def start_trading(self):
        strategy_name = self.strategy_combo.currentText()
        data_source_type = self.data_source_combo.currentText()
        symbol = self.symbol_input.text()
        timeframe = self.timeframe_combo.currentText()

        # Choose the data source based on user selection
        if data_source_type == "Live":
            data_source = LiveDataSource()
        else:
            data_source = HistoricalDataSource()

        risk_manager = RiskManager(
            initial_balance=10000,
            risk_per_trade=0.02,
            max_risk_per_trade=0.05,
            min_lot_size=0.01,
            max_lot_size=1.0
        )

        start_with_min_volume = self.min_volume_checkbox.isChecked()

        try:
            strategy_params = {
                'initial_balance': 10000,
                'start_date': None,
                'end_date': None,
                'start_with_min_volume': start_with_min_volume,
                'auto_trade': True
            }

            if strategy_name in ["Machine Learning", "XGB"]:
                model_path = "training/xgboost_model.pkl"
                model = joblib.load(model_path)
                features = ['macd', 'signal_line', 'rsi', 'log_tick_volume', 'log_spread', 'high_low_range', 'close_open_range']
                strategy_params.update({
                    'model': model,
                    'features': features
                })

            strategy = StrategyFactory.create_strategy(
                strategy_name,
                data_source,
                risk_manager,
                symbol,
                timeframe,
                **strategy_params
            )
            trading_system = TradingSystem(strategy)

            self.worker = TradingWorker(trading_system)
            self.thread = QThread()
            self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.worker.finished.connect(self.trading_finished)
            self.worker.error.connect(self.trading_error)
            self.thread.start()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to initialize strategy: {str(e)}")

    def trading_finished(self, result):
        self.start_button.setEnabled(True)
        QMessageBox.information(self, "Success", f"Trading completed successfully. Final balance: {result['balance']:.2f}")

    def trading_error(self, error_message):
        self.start_button.setEnabled(True)
        QMessageBox.critical(self, "Error", f"An error occurred: {error_message}")

    def _map_timeframe(self, timeframe_str):
        mapping = {'1m': 1, '5m': 5, '15m': 15, '30m': 30, '1h': 60, '4h': 240, '1d': 1440}
        return mapping.get(timeframe_str, 1)

    def load_ml_model(self):
        try:
            model = joblib.load('training/ml_model.pkl')
            return model
        except FileNotFoundError:
            QMessageBox.critical(self, 'Error', 'Model file not found. Please ensure the model is trained and saved correctly.')
            raise
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'An error occurred while loading the model: {str(e)}')
            raise

    def start_automation(self):
        self.automation_running = True

    def terminate_system(self):
        reply = QMessageBox.question(self, 'Terminate System', 
                                     "Are you sure you want to terminate the system?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            logging.info("System termination initiated by user.")
            if self.thread and self.thread.isRunning():
                self.thread.quit()
                self.thread.wait()
            QApplication.quit()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = TradingUI()
    sys.exit(app.exec_())
