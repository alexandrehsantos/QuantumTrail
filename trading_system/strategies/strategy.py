from abc import ABC, abstractmethod
import pandas as pd

class Strategy(ABC):
    def __init__(self, df: pd.DataFrame):
        self.df = df

    @abstractmethod
    def apply(self) -> list:
        pass
