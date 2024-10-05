import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QMessageBox, QDateEdit
from PyQt5.QtCore import QDate

class TradingApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Trading System')
        self.setGeometry(100, 100, 400, 300)

        layout = QVBoxLayout()

        self.mode_label = QLabel('Mode:')
        self.mode_combo = QComboBox(self)
        self.mode_combo.addItem('Live', 'live')
        self.mode_combo.addItem('Backtest', 'backtest')
        self.mode_combo.currentIndexChanged.connect(self.toggle_date_inputs)

        self.symbol_label = QLabel('Symbol:')
        self.symbol_input = QLineEdit(self)

        self.timeframe_label = QLabel('Timeframe:')
        self.timeframe_input = QLineEdit(self)

        self.strategy_label = QLabel('Strategy:')
        self.strategy_combo = QComboBox(self)
        self.strategy_combo.addItem('MACD', 'macd')
        self.strategy_combo.addItem('Mean Reversion', 'mean_reversion')

        self.start_date_label = QLabel('Start Date:')
        self.start_date_input = QDateEdit(self)
        self.start_date_input.setCalendarPopup(True)
        self.start_date_input.setDate(QDate.currentDate())

        self.end_date_label = QLabel('End Date:')
        self.end_date_input = QDateEdit(self)
        self.end_date_input.setCalendarPopup(True)
        self.end_date_input.setDate(QDate.currentDate())

        self.start_button = QPushButton('Start Trading', self)
        self.start_button.clicked.connect(self.start_trading)

        layout.addWidget(self.mode_label)
        layout.addWidget(self.mode_combo)
        layout.addWidget(self.symbol_label)
        layout.addWidget(self.symbol_input)
        layout.addWidget(self.timeframe_label)
        layout.addWidget(self.timeframe_input)
        layout.addWidget(self.strategy_label)
        layout.addWidget(self.strategy_combo)
        layout.addWidget(self.start_date_label)
        layout.addWidget(self.start_date_input)
        layout.addWidget(self.end_date_label)
        layout.addWidget(self.end_date_input)
        layout.addWidget(self.start_button)

        self.setLayout(layout)
        self.toggle_date_inputs()  # Set initial state

    def toggle_date_inputs(self):
        mode = self.mode_combo.currentData()
        if mode == 'backtest':
            self.start_date_label.show()
            self.start_date_input.show()
            self.end_date_label.show()
            self.end_date_input.show()
        else:
            self.start_date_label.hide()
            self.start_date_input.hide()
            self.end_date_label.hide()
            self.end_date_input.hide()

    def start_trading(self):
        from trading_system.trading_system import TradingSystem
        from trading_system.data_sources.live_data_source import LiveDataSource
        from trading_system.data_sources.historical_data_source import HistoricalDataSource
        from trading_system.strategies.macd_strategy import MACDStrategy
        from trading_system.strategies.mean_reversion_strategy import MeanReversionStrategy

        mode = self.mode_combo.currentData()
        symbol = self.symbol_input.text()
        timeframe_text = self.timeframe_input.text()

        # Validate timeframe input
        try:
            timeframe = int(timeframe_text)
        except ValueError:
            QMessageBox.critical(self, 'Error', 'Timeframe must be an integer.')
            return

        strategy_name = self.strategy_combo.currentData()

        if strategy_name == 'macd':
            strategy_class = MACDStrategy
        elif strategy_name == 'mean_reversion':
            strategy_class = MeanReversionStrategy

        if mode == 'backtest':
            start_date = self.start_date_input.date().toString('yyyy-MM-dd')
            end_date = self.end_date_input.date().toString('yyyy-MM-dd')
            data_source = HistoricalDataSource()
            trading_system = TradingSystem(data_source, strategy_class)
            try:
                trading_system.run_backtest(symbol, timeframe, start_date, end_date)
                QMessageBox.information(self, 'Success', 'Backtest completed successfully.')
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Backtest failed: {e}')
        elif mode == 'live':
            data_source = LiveDataSource()
            if not data_source.initialize():
                QMessageBox.critical(self, 'Error', 'Failed to initialize LiveDataSource')
                return
            trading_system = TradingSystem(data_source, strategy_class)
            try:
                trading_system.start_automation(symbol, timeframe)
                QMessageBox.information(self, 'Success', 'Live trading started successfully.')
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Live trading failed: {e}')

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = TradingApp()
    ui.show()
    sys.exit(app.exec_())