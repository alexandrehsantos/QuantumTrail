from .macd_strategy import MACDStrategy
from .mean_reversion_strategy import MeanReversionStrategy
from .machine_learning import MLStrategy
from .xgb_strategy import XGBStrategy
from .chart_pattern_strategy import ChartPatternStrategy
from .high_frequency_strategy import HighFrequencyStrategy
from .top_bottom_strategy import TopBottomStrategy
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class StrategyFactory:
    @staticmethod
    def create_strategy(strategy_name, data_source, risk_manager, symbol, timeframe, **kwargs):
        strategy_class = StrategyFactory.get_strategy_class(strategy_name)

        logging.info(f"Creating strategy: {strategy_name}. Parameters: {kwargs.get('start_date')} - {kwargs.get('end_date')}")
        # Prepare common parameters
        common_params = {
            'data_source': data_source,
            'risk_manager': risk_manager,
            'symbol': symbol,
            'timeframe': timeframe,
            'initial_balance': kwargs.get('initial_balance', 10000),
            'start_date': kwargs.get('start_date'),
            'end_date': kwargs.get('end_date')
        }
        
        # Add strategy-specific parameters
        if strategy_name in ["Machine Learning", "XGB"]:
            common_params['model'] = kwargs.get('model')
            common_params['features'] = kwargs.get('features')
        
        if 'start_with_min_volume' in strategy_class.__init__.__code__.co_varnames:
            common_params['start_with_min_volume'] = kwargs.get('start_with_min_volume', False)
        
        if 'auto_trade' in strategy_class.__init__.__code__.co_varnames:
            common_params['auto_trade'] = kwargs.get('auto_trade', False)
        
        return strategy_class(**common_params)

    @staticmethod
    def get_strategy_class(strategy_name):
        if strategy_name == "MACD":
            return MACDStrategy
        elif strategy_name == "Mean Reversion":
            return MeanReversionStrategy
        elif strategy_name == "Machine Learning":
            return MLStrategy
        elif strategy_name == "XGB":
            return XGBStrategy
        elif strategy_name == "Chart Pattern":
            return ChartPatternStrategy
        elif strategy_name == "High Frequency":
            return HighFrequencyStrategy
        elif strategy_name == "TopBottom":
            return TopBottomStrategy
        else:
            raise ValueError(f"Invalid strategy selected: {strategy_name}")
