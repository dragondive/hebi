"""This module contains the stock prices data providers.
"""

from abc import ABC, abstractmethod
import pandas
import numpy
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

    @abstractmethod
    def get_closing_price(self, symbol_list: list[tuple[str, StockExchange]], date: str) -> numpy.float64:
        """Abstract method to get the closing price for the stock symbols of the company.
        
        Note:
            The caller should usually include symbols of the same company on different stock exchanges.
            The closing prices for these symbols will be queried on those stock exchanges in order.
            The concrete provider would usually return the first valid closing price. However, this interface
            neither requires nor guarantees this behaviour. The concrete provider may implement a different behaviour.

        Args:
            symbol_list: list of stock symbols with the respective stock exchange identifier.
            date: date for which the closing price is to be fetched.

        Returns:
            The closing price if available.
        
        Raises:
            NoClosingPriceError if the closing price was not available.
        """

class YfinanceStockPricesProvider(StockPricesProvider):
    """Stock prices provider that wraps the yfinance API."""

    def __init__(self, symbol_list, start_date, end_date = None) -> None:

        # yfinance API requires suffixing the symbol with the stock exchange identifier.
        self.exchange_to_suffix_map = {
            StockExchange.BSE: ".BO",
            StockExchange.NSE: ".NS"
        }

        self.stock_data = pandas.DataFrame()

        super().__init__(symbol_list, start_date, end_date)

    def fetch_stock_prices(self, symbol_list: list[tuple[str, StockExchange]], start_date: str, end_date: str = None) -> None:
        suffixized_symbol_list = self.__suffixize_symbol_list(symbol_list)

        # Convert the start_date and end_date to the pandas Timestamp object.
        # If end_date is not specified, choose today's date as the end_date.
        start_date = pandas.to_datetime(start_date)
        if end_date is None:
            end_date = pandas.to_datetime("today").normalize()
        else:
            end_date = pandas.to_datetime(end_date)

        adapted_end_date = end_date + pandas.Timedelta(days=1) # yfinance requires end date to be one day after the actual desired end date
        self.stock_data = yfinance.download(suffixized_symbol_list, group_by="Ticker", start=start_date, end=adapted_end_date)
        self.stock_data.to_excel("stock_data.xlsx")

    def get_closing_price(self, symbol_list: list[tuple[str, StockExchange]], date: str) -> numpy.float64:
        suffixized_symbol_list = self.__suffixize_symbol_list(symbol_list)
        date = pandas.to_datetime(date)

        # TODO: adjust the closing price for stock splits, bonuses, etc.
        for symbol in suffixized_symbol_list:
            try:
                closing_price = self.stock_data[symbol].loc[date, "Close"]
            except KeyError:
                # symbol not found in the data
                continue
            else:
                if not numpy.isnan(closing_price):
                    return closing_price

        return 9876543.21 # dummy value for easier debugging, will be removed when stable
        # raise NoClosingPriceError

    def __suffixize_symbol_list(self, symbol_list: list[tuple[str, StockExchange]]) -> list[str]:
        """Helper private function to apply the stock exchange suffix to every symbol in the list."""
        return [symbol + self.exchange_to_suffix_map[exchange] for symbol, exchange in symbol_list]

class NoClosingPriceError(Exception):
    """Raise when closing price is not found in the available stock data."""