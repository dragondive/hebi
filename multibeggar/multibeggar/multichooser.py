"""This module contains the stock prices data providers.
"""

from abc import ABC, abstractmethod
import pandas
import numpy
import yfinance
from multibeggar.dalalstreet import StockExchange, CompaniesInfo
from multibeggar.bahikhata import log


class StockPricesProvider(ABC):
    """Abstract base class for the StockPricesProvider"""

    def __init__(self, symbol_list, start_date, end_date) -> None:
        log.debug("Hello from multichooser")
        super().__init__()
        self.companies_info = CompaniesInfo()
        self.fetch_stock_prices(symbol_list, start_date, end_date)

    @abstractmethod
    def fetch_stock_prices(
        self, symbol_list: list[tuple[str, StockExchange]], start_date: str, end_date: str
    ) -> None:
        """Abstract method to fetch the stock prices when the provider is instantiated.

        The concrete provider instance should define how the stock data is fetched.
        Typically, the concrete provider is a wrapper around its corresponding API."""

    @abstractmethod
    def get_closing_price(
        self, symbol_list: list[tuple[str, StockExchange]], date: str
    ) -> numpy.float64:
        """Abstract method to get the closing price for the stock symbols of the company.

        Note:
            The caller should usually include symbols of the same company on different
            stock exchanges. The closing prices for these symbols will be queried on those
            stock exchanges in order. The concrete provider would usually return the first
            valid closing price. However, this interface neither requires nor guarantees
            this behaviour. The concrete provider may implement a different behaviour.

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

    def __init__(self, symbol_list, start_date, end_date=None) -> None:

        # yfinance API requires suffixing the symbol with the stock exchange identifier.
        self.exchange_to_suffix_map = {StockExchange.BSE: ".BO", StockExchange.NSE: ".NS"}

        self.stock_data = pandas.DataFrame()

        super().__init__(symbol_list, start_date, end_date)

    def fetch_stock_prices(
        self, symbol_list: list[tuple[str, StockExchange]], start_date: str, end_date: str = None
    ) -> None:
        suffixized_symbol_list = self.__suffixize_symbol_list(symbol_list)

        # Convert the start_date and end_date to the pandas Timestamp object.
        # If end_date is not specified, choose today's date as the end_date.
        start_date = pandas.to_datetime(start_date)
        if end_date is None:
            end_date = pandas.to_datetime("today").normalize()
        else:
            end_date = pandas.to_datetime(end_date)

        # yfinance requires end date to be one day after the actual desired end date
        adapted_end_date = end_date + pandas.Timedelta(days=1)
        self.stock_data = yfinance.download(
            suffixized_symbol_list, group_by="Ticker", start=start_date, end=adapted_end_date
        )
        # self.stock_data.to_excel("stock_data.xlsx")

    def get_closing_price(
        self, symbol_list: list[tuple[str, StockExchange]], date: str
    ) -> numpy.float64:
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
                    # de_adjust the closing price for bonus issues, stock splits.

                    # Use only the first stock symbol because dalalstreet.CompaniesInfo() does not
                    # currently have stock exchange specific data for splits and bonuses. Hence,
                    # the additional complexity of looping over all symbols serves no benefit.
                    # In the ugly [0][0] syntax below, the first [0] references the list,
                    # the second [0] references the tuple.
                    # TODO use namedtuple instead?
                    stock_symbol = symbol_list[0][0]
                    price_adjustment_data = self.companies_info.get_price_adjustment_data(
                        stock_symbol, date
                    )
                    if not price_adjustment_data.empty:
                        # The de_adjustment multiplier should be the product of all the multipliers
                        # in case of multiple bonuses or stock splits that happened after the date
                        # of transaction. However, due to a bug in yfinance, only the last bonus or
                        # split is used to adjusting the closing price. Hence, in de_adjustment, we
                        # consider only the latest multiplier.
                        #
                        # As dalalstreet.CompaniesInfo() sorts the price adjustment actions by date
                        # in ascending order, we can use tail(1) below to fetch the last row of the
                        # respective action. Even though in this case, it would be a single number,
                        # we use product() here so that we can easily "unfix" the below fix if/when
                        # the yfinance bug is fixed. Moreover, product() returns 1.0 as the
                        # multiplier in case of an empty DataFrame (that is, no relevant price
                        # adjustment action), so we don't need to do that check here.
                        bonus_multiplier = (
                            price_adjustment_data[price_adjustment_data["Action Type"] == "Bonus"]
                            .tail(1)["Multiplier"]
                            .product()
                        )
                        split_multiplier = (
                            price_adjustment_data[price_adjustment_data["Action Type"] == "Split"]
                            .tail(1)["Multiplier"]
                            .product()
                        )
                        closing_price *= bonus_multiplier * split_multiplier

                    return closing_price

        raise NoClosingPriceError

    def __suffixize_symbol_list(self, symbol_list: list[tuple[str, StockExchange]]) -> list[str]:
        """Applies the stock exchange suffix to every symbol in the list."""
        return [symbol + self.exchange_to_suffix_map[exchange] for symbol, exchange in symbol_list]


class NoClosingPriceError(Exception):
    """Raise when closing price is not found in the available stock data."""
