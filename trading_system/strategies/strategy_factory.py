from .macd_strategy import MACDStrategy
from .mean_reversion_strategy import MeanReversionStrategy
from .machine_learning import MLStrategy
from .xgb_strategy import XGBStrategy

class StrategyFactory:
    @staticmethod
    def get_strategy(strategy_name):
        if strategy_name == "MACD":
            return MACDStrategy
        elif strategy_name == "Mean Reversion":
            return MeanReversionStrategy
        elif strategy_name == "Machine Learning":
            return MLStrategy
        elif strategy_name == "XGB":
            return XGBStrategy
        else:
            raise ValueError(f"Invalid strategy selected: {strategy_name}")
