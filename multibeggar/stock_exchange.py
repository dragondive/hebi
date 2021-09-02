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


class StockExchangeInfo:
    def __init__(self, companies_data_file_path, symbol_header, company_name_header, exchange_suffix):
        # todo self: these log files should be managed better, this is a temporary hack to "reuse" the multibeggar.log
        logging.basicConfig(format='%(levelname)s: %(message)s [%(funcName)s():%(lineno)s - %(asctime)s]', datefmt='%Y/%m/%d %I:%M:%S %p', handlers=[logging.FileHandler(os.path.join(os.getcwd(), 'output', 'multibeggar.log'), mode='w')])
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        self.symbol_to_name = pandas.read_csv(companies_data_file_path, usecols=[symbol_header, company_name_header], index_col=False)
        self.symbol_to_name[company_name_header] = self.symbol_to_name[company_name_header].str.upper()
        self.symbol_header = symbol_header
        self.company_name_header = company_name_header
        self.exchange_suffix = exchange_suffix

        self.count = 0
        self.starting_with_count = 0
        self.best_matching_with_count = 0

    def get_symbol(self, company_name, with_suffix=True):
        symbol_list = self.get_symbols_for_company_name_starting_with(company_name, with_suffix)
        self.count += 1
        if len(symbol_list) == 1:
            self.starting_with_count += 1
            symbol = symbol_list[0]
        else:
            self.best_matching_with_count += 1
            symbol = self.get_symbol_for_company_name_best_matching_with(company_name, with_suffix)

        self.logger.info('company_name: %s -> symbol: %s', company_name, symbol)
        return symbol

    def get_symbols_for_company_name_starting_with(self, company_name, with_suffix=True):
        matching_mask = self.symbol_to_name[self.company_name_header].str.startswith(company_name)
        matching_row = self.symbol_to_name[matching_mask]
        symbol_list = matching_row[self.symbol_header].array

        if with_suffix:
            symbol_list = [symbol + self.exchange_suffix for symbol in matching_row[self.symbol_header].array]

        self.logger.info('company_name: %s -> symbol_list...\n%s', company_name, symbol_list)
        return symbol_list

    def get_symbol_for_company_name_best_matching_with(self, company_name, with_suffix=True):
        match_ratios = self.symbol_to_name.apply(lambda row: fuzz.token_sort_ratio(row[self.company_name_header], company_name), axis=1)
        qualified_rows = match_ratios[lambda x: x >= 75]
        self.logger.debug('company_name: %s -> qualified_rows...\n%s', company_name,
                          pandas.concat([self.symbol_to_name.loc[qualified_rows.index],
                                        match_ratios.loc[qualified_rows.index].rename('match_ratio')],
                                        axis=1).to_string())

        try:
            best_matching_row = self.symbol_to_name.loc[qualified_rows.idxmax()]
        except ValueError:
            self.logger.warning('company_name: %s -> no symbol matched!', company_name)
            return None  # todo self: raise exception instead and let caller decide what to do
        else:
            symbol = best_matching_row[self.symbol_header]

            if with_suffix:
                symbol += self.exchange_suffix

            self.logger.info('company_name: %s -> symbol: %s', company_name, symbol)
            return symbol
