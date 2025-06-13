import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QLineEdit, QPushButton, QComboBox, QMessageBox, QDateEdit
from PyQt5.QtCore import QThread, pyqtSignal, QObject, QDate
from trading_system.data_sources.historical_data_source import HistoricalDataSource
from trading_system.strategies.strategy_factory import StrategyFactory
from trading_system.risk_management.risk_manager import RiskManager
from datetime import datetime
import MetaTrader5 as mt5

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class BacktestWorker(QObject):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, strategy_name, symbol, timeframe, start_date, end_date):
        super().__init__()
        self.strategy_name = strategy_name
        self.symbol = symbol
        self.timeframe = timeframe
        self.start_date = start_date
        self.end_date = end_date

    def run(self):
        try:
            # Initialize data source
            data_source = HistoricalDataSource()
            data_source.initialize()

            # Set up risk manager
            risk_manager = RiskManager(
                initial_balance=10000,
                risk_per_trade=0.02,
                max_risk_per_trade=0.05,
                min_lot_size=0.01,
                max_lot_size=1.0
            )

            # Create strategy
            strategy = StrategyFactory.create_strategy(
                self.strategy_name,
                data_source,
                risk_manager,
                self.symbol,
                self.timeframe,
                initial_balance=10000,
                start_date=self.start_date,
                end_date=self.end_date
            )

            # Run backtest
            result = strategy.apply()
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

class BacktestUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Backtest UI")
        self.setGeometry(100, 100, 400, 300)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems(["MACD", "RSI", "BollingerBands"])
        layout.addWidget(QLabel("Strategy:"))
        layout.addWidget(self.strategy_combo)

        self.symbol_input = QLineEdit("BTCUSD")  # Set BTCUSD as default
        layout.addWidget(QLabel("Symbol:"))
        layout.addWidget(self.symbol_input)

        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems(["1m", "5m", "15m", "30m", "1h", "4h", "1d"])
        self.timeframe_combo.setCurrentText("1m")  # Set 1m as default
        layout.addWidget(QLabel("Timeframe:"))
        layout.addWidget(self.timeframe_combo)

        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-30))  # Default to 30 days ago
        layout.addWidget(QLabel("Start Date:"))
        layout.addWidget(self.start_date)

        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())  # Default to today
        layout.addWidget(QLabel("End Date:"))
        layout.addWidget(self.end_date)

        self.run_button = QPushButton("Run Backtest")
        self.run_button.clicked.connect(self.run_backtest)
        layout.addWidget(self.run_button)

        central_widget.setLayout(layout)

    def run_backtest(self):
        strategy_name = self.strategy_combo.currentText()
        symbol = self.symbol_input.text()
        timeframe = self.timeframe_combo.currentText()
        start_date = self.start_date.date().toPyDate()
        end_date = self.end_date.date().toPyDate()

        self.backtest_thread = QThread()
        self.backtest_worker = BacktestWorker(strategy_name, symbol, timeframe, start_date, end_date)
        self.backtest_worker.moveToThread(self.backtest_thread)
        self.backtest_thread.started.connect(self.backtest_worker.run)
        self.backtest_worker.finished.connect(self.backtest_thread.quit)
        self.backtest_worker.finished.connect(self.backtest_worker.deleteLater)
        self.backtest_thread.finished.connect(self.backtest_thread.deleteLater)
        self.backtest_worker.finished.connect(self.display_results)
        self.backtest_worker.error.connect(self.display_error)
        self.backtest_thread.start()

        self.run_button.setEnabled(False)

    def display_results(self, results):
        QMessageBox.information(self, "Backtest Results", str(results))
        self.run_button.setEnabled(True)

    def display_error(self, error_message):
        QMessageBox.critical(self, "Error", error_message)
        self.run_button.setEnabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BacktestUI()
    window.show()
    sys.exit(app.exec_())
