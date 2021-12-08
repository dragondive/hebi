from enum import Enum
import logging
import os
import pandas
from fuzzywuzzy import fuzz


class StockExchange(Enum):
    NSE = 'NSE'
    BSE = 'BSE'

    def __str__(self):
        return self.value

class CompaniesInfo:
    def __init__(self):
        # todo self: these log files should be managed better, this is a temporary hack to "reuse" the multibeggar.log
        logging.basicConfig(format='%(levelname)s: %(message)s [%(funcName)s():%(lineno)s - %(asctime)s]', datefmt='%Y/%m/%d %I:%M:%S %p', handlers=[logging.FileHandler(os.path.join(os.getcwd(), 'output', 'multibeggar.log'), mode='w')])
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        script_dir = os.path.dirname(__file__)

        # The column names are repeated below inside the [[]] to rearrange the columns in required order.
        # This is the officially documented approach in pandas.read_csv to avoid keeping the column order from the input.
        self.stocks_info_map = {
            StockExchange.NSE: pandas.read_csv(os.path.join(script_dir, 'data', 'equity_nse.csv'), usecols=['NAME OF COMPANY', 'SYMBOL'])[['NAME OF COMPANY', 'SYMBOL']],
            StockExchange.BSE: pandas.read_csv(os.path.join(script_dir, 'data', 'equity_bse.csv'), usecols=['Security Name', 'Security Id'])[['Security Name', 'Security Id']],
        }

        self.company_name_header = 'company_name'
        self.stock_symbol_header = 'stock_symbol'

        # read_csv() does not support renaming the columns while reading in the data, so do it separately below.
        for name, info in self.stocks_info_map.items():
            info.columns = [self.company_name_header, self.stock_symbol_header]
        # print(self.stocks_info_map)

    def get_symbols(self, company_name):
        # return tuples consisting of the stock symbol along with the exchange name
        symbol_list = [(symbol, exchange_name) for exchange_name, info in self.stocks_info_map.items() if (symbol := self.get_symbol(company_name, exchange_name)) is not None]
        self.logger.info('company_name: %s -> symbol: %s', company_name, symbol)
        return symbol_list

    def get_symbol(self, company_name, exchange_name):
        symbol_list = self.get_symbols_for_company_name_starting_with(company_name, exchange_name)

        if len(symbol_list) == 1:
            symbol = symbol_list[0]
        else:
            symbol = self.get_symbol_for_company_name_best_matching_with(company_name, exchange_name)

        self.logger.info('company_name: %s, exchange_name: %s -> symbol: %s', company_name, exchange_name, symbol)
        return symbol

    def get_symbols_for_company_name_starting_with(self, company_name, exchange_name):
        name_to_symbol = self.stocks_info_map[exchange_name]
        matching_mask = name_to_symbol[self.company_name_header].str.startswith(company_name)
        matching_row = name_to_symbol[matching_mask]
        symbol_list = matching_row[self.stock_symbol_header].array

        self.logger.info('company_name: %s, exchange_name: %s -> symbol_list...\n%s', company_name, exchange_name, symbol_list)
        return symbol_list

    def get_symbol_for_company_name_best_matching_with(self, company_name, exchange_name):
        name_to_symbol = self.stocks_info_map[exchange_name]
        match_ratios = name_to_symbol.apply(lambda row: fuzz.token_sort_ratio(row[self.company_name_header], company_name), axis=1)
        qualified_rows = match_ratios[lambda x: x >= 75]
        self.logger.debug('company_name: %s, exchange_name: %s -> qualified_rows...\n%s', company_name, exchange_name,
                          pandas.concat([name_to_symbol.loc[qualified_rows.index],
                                        match_ratios.loc[qualified_rows.index].rename('match_ratio')],
                                        axis=1).to_string())

        try:
            best_matching_row = name_to_symbol.loc[qualified_rows.idxmax()]
        except ValueError:
            self.logger.warning('company_name: %s, exchange_name: %s -> no symbol matched!', company_name, exchange_name)
            return None  # todo self: raise exception instead and let caller decide what to do
        else:
            symbol = best_matching_row[self.stock_symbol_header]

            self.logger.info('company_name: %s, exchange_name: %s -> symbol: %s', company_name, exchange_name, symbol)
            return symbol
