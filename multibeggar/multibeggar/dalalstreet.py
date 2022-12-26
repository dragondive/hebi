import os
import logging
from enum import Enum
import pandas
from fuzzywuzzy import fuzz
from multibeggar import goldenkatora

class StockExchange(Enum):
    """Stock exchanges supported by multibeggar."""
    BSE = "BSE" # Bombay Stock Exchange
    NSE = "NSE" # National Stock Exchange

    def __str__(self):
        return self.value

class CompaniesInfo:
    def __init__(self) -> None:
        # todo self: these log files should be managed better, this is a temporary hack to "reuse" the multibeggar.log
        logging.basicConfig(format='%(levelname)s: %(message)s [%(funcName)s():%(lineno)s - %(asctime)s]',
                            datefmt='%Y/%m/%d %I:%M:%S %p', 
                            handlers=[logging.FileHandler(os.path.join(os.getcwd(), 'multibeggar.log'), mode='w')])
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        golden_katora = goldenkatora.GoldenKatora()
        self.stock_exchange_to_info_map = {
            StockExchange.BSE: pandas.read_csv(golden_katora.get_cleaned_stocks_data_bse()),
            StockExchange.NSE: pandas.read_csv(golden_katora.get_cleaned_stocks_data_nse())
        }

    def get_stock_symbols(self, company_name) -> list[tuple[str, StockExchange]]:
        """Get known stock symbols of the company on the supported stock exchanges.

        Args:
            company_name: Name of the company

        Returns:
            - List of tuples consisting the known stock symbols and the respective stock exchange
            - Empty list if no stock symbol is found on any supported stock exchange
        """
        symbol_list = [(symbol, stock_exchange) 
                        for stock_exchange in self.stock_exchange_to_info_map.keys()
                        if (symbol := self.get_stock_symbol(company_name, stock_exchange)) is not None]
        return symbol_list

    def get_stock_symbol(self, company_name: str, exchange_name: StockExchange) -> str:
        """Get known stock symbol of the company on the stock exchange.

        Args:
            company_name: Name of the company
            exchange_name: Enum StockExchange representing the supported stock exchange

        Returns:
            - Stock symbol of the company on the stock exchange
            - None if stock symbol of the company is not found
        """
        def search_exact_match():
            """Helper inner function to search for the exactly matching company name in stock exchange data."""
            company_name_to_symbol_map = self.stock_exchange_to_info_map[exchange_name]
            matching_mask = company_name_to_symbol_map["Company Name"] == company_name
            matching_row = company_name_to_symbol_map[matching_mask]
            return matching_row["Stock Symbol"].array

        def search_best_match():
            """Helper inner function to perform fuzzy search for the company name in stock exchange data."""
            company_name_to_symbol_map = self.stock_exchange_to_info_map[exchange_name]
            match_ratios = company_name_to_symbol_map.apply(lambda row: fuzz.token_sort_ratio(row["Company Name"], company_name), axis=1)
            qualified_rows = match_ratios[lambda match_ratio: match_ratio >= 75]

            try:
                best_matching_row = company_name_to_symbol_map.loc[qualified_rows.idxmax()]
            except ValueError:
                return None # TODO raise exception instead
            else:
                return best_matching_row["Stock Symbol"]

        # First search for exactly matching company name. Try fuzzy matching only if exact match is not found.
        # This small optimization avoids fuzzy matching against all the companies in the stock exchange data if not necessary.
        symbol_list = search_exact_match()
        if (len(symbol_list) == 1):
            return symbol_list[0]
        else:
            return search_best_match()
