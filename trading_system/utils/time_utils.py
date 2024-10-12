from typing import Union

class TimeFrameConverter:
    """
    A utility class for converting timeframe strings to minutes.
    """

    def to_minutes(self, timeframe: str) -> int:
        """
        Convert a timeframe string to minutes.

        Args:
            timeframe (str): A string representing a timeframe (e.g., '1m', '1h', '1d').

        Returns:
            int: The number of minutes in the given timeframe.

        Raises:
            ValueError: If the timeframe format is not supported.
        """
        timeframe = timeframe.lower()
        value, unit = self._parse_timeframe(timeframe)
        
        if unit == 'm':
            return value
        elif unit == 'h':
            return value * 60
        elif unit == 'd':
            return value * 1440
        else:
            raise ValueError(f"Unsupported timeframe unit: {unit}")

    def _parse_timeframe(self, timeframe: str) -> tuple[int, str]:
        """
        Parse the timeframe string into a value and unit.

        Args:
            timeframe (str): A string representing a timeframe.

        Returns:
            tuple[int, str]: A tuple containing the numeric value and the unit.

        Raises:
            ValueError: If the timeframe format is invalid.
        """
        if not timeframe[-1].isalpha() or not timeframe[:-1].isdigit():
            raise ValueError(f"Invalid timeframe format: {timeframe}")
        
        return int(timeframe[:-1]), timeframe[-1]

def convert_timeframe(timeframe: Union[str, int]) -> int:
    """
    Convert a timeframe to minutes.

    Args:
        timeframe (Union[str, int]): A string representing a timeframe or an integer (assumed to be minutes).

    Returns:
        int: The number of minutes in the given timeframe.
    """
    if isinstance(timeframe, int):
        return timeframe
    
    timeframe = timeframe.lower()
    if timeframe.endswith('m'):
        return int(timeframe[:-1])
    elif timeframe.endswith('h'):
        return int(timeframe[:-1]) * 60
    elif timeframe.endswith('d'):
        return int(timeframe[:-1]) * 1440
    else:
        raise ValueError(f"Unsupported timeframe format: {timeframe}")
