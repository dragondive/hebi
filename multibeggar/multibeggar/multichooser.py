"""This module contains the stock prices data providers.
"""

from abc import ABC, abstractmethod
import pandas
import yfinance
from multibeggar.dalalstreet import StockExchange

class StockPricesProvider(ABC):
    """Abstract base class for the StockPricesProvider"""

    def __init__(self, symbol_list, start_date, end_date) -> None:
        super().__init__()
        self.fetch_stock_prices(symbol_list, start_date, end_date)

    @abstractmethod
    def fetch_stock_prices(self, symbol_list: list[tuple[str, StockExchange]], start_date: str, end_date: str) -> None:
        """Abstract method to fetch the stock prices when the provider is instantiated.

        The concrete provider instance should define how the stock data is fetched.
        Typically, the concrete provider is a wrapper around its corresponding API."""
        pass


class YfinanceStockPricesProvider(StockPricesProvider):
    """Stock prices provider that wraps the yfinance API."""

    def __init__(self, symbol_list, start_date, end_date) -> None:

        # yfinance API requires suffixing the symbol with the stock exchange identifier.
        self.exchange_to_suffix_map = {
            StockExchange.BSE: ".BO",
            StockExchange.NSE: ".NS"
        }

        super().__init__(symbol_list, start_date, end_date)

    def fetch_stock_prices(self, symbol_list: list[tuple[str, StockExchange]], start_date: str, end_date: str = None) -> None:
        def suffixize_symbol_list():
            """Helper inner function to apply the stock exchange suffix to every symbol in the list."""
            return [symbol + self.exchange_to_suffix_map[exchange] for symbol, exchange in symbol_list]

        suffixized_symbol_list = suffixize_symbol_list()

        # Convert the start_date and end_date to the pandas Timestamp object.
        # If end_date is not specified, choose today's date as the end_date.
        start_date = pandas.to_datetime(start_date)
        if end_date is None:
            end_date = pandas.to_datetime("today").normalize()
        else:
            end_date = pandas.to_datetime(end_date)

        adapted_end_date = end_date + pandas.Timedelta(days=1) # yfinance requires end date to be one day after the actual desired end date
        stock_data = yfinance.download(suffixized_symbol_list, group_by="Ticker", start=start_date, end=adapted_end_date)