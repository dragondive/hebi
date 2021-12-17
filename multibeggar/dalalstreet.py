from enum import Enum
import logging
import os
import pandas
import yfinance
from fuzzywuzzy import fuzz


class StockExchange(Enum):
    NSE = 'NSE'
    BSE = 'BSE'

    def __str__(self):
        return self.value


class CompaniesInfo:
    def __init__(self):
        # todo self: these log files should be managed better, this is a temporary hack to "reuse" the multibeggar.log
        logging.basicConfig(format='%(levelname)s: %(message)s [%(funcName)s():%(lineno)s - %(asctime)s]',
                            datefmt='%Y/%m/%d %I:%M:%S %p', 
                            handlers=[logging.FileHandler(os.path.join(os.getcwd(), 'output', 'multibeggar.log'), mode='w')])
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        script_dir = os.path.dirname(__file__)

        # The column names are repeated below inside the [[]] to rearrange the columns in required order.
        # This is the officially documented approach in pandas.read_csv to avoid keeping the column order from the input.
        self.stocks_info_map = {
            StockExchange.NSE: pandas.read_csv(os.path.join(script_dir, 'data', 'equity_nse.csv'),
                                               usecols=['NAME OF COMPANY', 'SYMBOL'])[['NAME OF COMPANY', 'SYMBOL']],
            StockExchange.BSE: pandas.read_csv(os.path.join(script_dir, 'data', 'equity_bse.csv'),
                                               usecols=['Security Name', 'Security Id'])[['Security Name', 'Security Id']],
        }

        self.company_name_header = 'company_name'
        self.stock_symbol_header = 'stock_symbol'

        # read_csv() does not support renaming the columns while reading in the data, so do it separately below.
        for __unused, info in self.stocks_info_map.items():
            info.columns = [self.company_name_header, self.stock_symbol_header]

    def get_symbols(self, company_name):
        # return tuples consisting of the stock symbol along with the exchange name
        symbol_list = [(symbol, exchange_name)
                       for exchange_name, info in self.stocks_info_map.items()
                       if (symbol := self.get_symbol(company_name, exchange_name)) is not None]
        self.logger.info('company_name: %s -> symbol_list: %s', company_name, symbol_list)
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


# todo: better module management is required here, this should be moved to a separate file
class StockPricesDataProvider:
    def __init__(self):
        # todo self: these log files should be managed better, this is a temporary hack to "reuse" the multibeggar.log
        logging.basicConfig(format='%(levelname)s: %(message)s [%(funcName)s():%(lineno)s - %(asctime)s]',
                            datefmt='%Y/%m/%d %I:%M:%S %p',
                            handlers=[logging.FileHandler(os.path.join(os.getcwd(), 'output', 'multibeggar.log'), mode='w')])
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        script_dir = os.path.dirname(__file__)

        self.renamed_symbols_map = pandas.read_csv(os.path.join(script_dir, 'data', 'renamed_symbols.csv')).set_index('Present Symbol').to_dict('index')
        self.price_adjustment_map = pandas.read_csv(os.path.join(script_dir, 'data', 'price_adjustments.csv'), parse_dates=['Date']).set_index('Symbol').to_dict('index')
        self.today_date = pandas.to_datetime('today').normalize()

        self.symbol_to_stock_data = {}

        # todo: this implemented is specific to yfinance, to be refactored.
        # symbol_to_stock_data should map the stock data directly to the (stock_symbol, exchange) tuple
        # stock data here is mapped to the suffixized symbol for convenience of prototyping, but this approach
        # doesn't work when using other API which may use a different suffix for the exchange.
        self.exchange_to_suffix = {
            StockExchange.NSE: ".NS",
            StockExchange.BSE: ".BO",
        }

    def fetch_stock_prices(self, symbol_list, start_date, end_date=None):
        if end_date is None:
            end_date = self.today_date

        # todo: this implementation is specific to yfinance, should be refactored to use any API.
        suffixized_symbol_list = self.__suffixize_symbol_list(symbol_list)
        adapted_end_date = end_date + pandas.Timedelta(days=1)  # yfinance API requires the end date to be "one after" the actual desired end date.
        stock_data = yfinance.download(suffixized_symbol_list, group_by='Ticker', start=start_date, end=adapted_end_date)

        symbol_to_stock_data = {index: group.xs(index, level=0, axis=1) for index, group in stock_data.groupby(level=0, axis=1)}
        self.symbol_to_stock_data.update(symbol_to_stock_data)

        self.logger.debug('downloaded stock data from date: %s to date: %s for symbols...\n%s', start_date, end_date, suffixized_symbol_list)
        
    def get_renamed_symbol(self, stock_symbol):
        try:
            old_symbol = self.renamed_symbols_map[stock_symbol]['Old Symbol']
            self.logger.info('stock_symbol: %s -> old_symbol: %s', stock_symbol, old_symbol)
            return old_symbol
        except KeyError:
            self.logger.warning('stock_symbol: %s -> no old_symbol found!', stock_symbol)
            return None

    def get_closing_price(self, symbol_list, date_string):

        def from_single_date():
            try:
                adjusted_closing_prices = self.__get_adjusted_closing_prices_for_date_range(suffixized_symbol_list, start_date=date, end_date=date)
            except NoClosingPriceError:
                return None
            else:
                adjusted_closing_price = adjusted_closing_prices.array[0]
                self.logger.debug('symbol_list: %s date: %s -> adjusted_closing_price: %s', symbol_list, date, adjusted_closing_price)
                return adjusted_closing_price

        def from_range_of_dates():
            try:
                adjusted_closing_prices = self.__get_adjusted_closing_prices_for_date_range(
                                            suffixized_symbol_list,
                                            start_date=date - pandas.Timedelta(days=7),
                                            end_date=date + pandas.Timedelta(days=7))
            except NoClosingPriceError:
                return None
            else:
                adjusted_closing_price = adjusted_closing_prices.mean()
                self.logger.warning('fallback to mean price! symbol_list: %s date: %s -> adjusted_closing_price: %s', symbol_list, date, adjusted_closing_price)
                return adjusted_closing_price

        def from_renamed_symbol_list():
            renamed_symbol_list = [(renamed_symbol, exchange) for symbol, exchange in symbol_list if (renamed_symbol := self.get_renamed_symbol(symbol))]
            self.logger.debug('symbol_list: %s -> renamed_symbol_list: %s', symbol_list, renamed_symbol_list)

            symbol_to_fetch_list = [symbol for symbol in renamed_symbol_list if self.__suffixize_symbol(symbol[0], symbol[1]) not in self.symbol_to_stock_data]
            if symbol_to_fetch_list:
                self.fetch_stock_prices(symbol_to_fetch_list, date)

            if renamed_symbol_list:
                adjusted_closing_price = self.get_closing_price(renamed_symbol_list, date)
                self.logger.debug('symbol_list: %s date: %s -> adjusted_closing_price: %s', symbol_list, date, adjusted_closing_price)
                return adjusted_closing_price

            return None

        def get_de_adjusted_price():
            for symbol in suffixized_symbol_list:
                de_adjustment_factor = self.get_de_adjustment_factor(symbol, date)
                if de_adjustment_factor is not None:
                    de_adjusted_closing_price = adjusted_closing_price * de_adjustment_factor
                    self.logger.debug('symbol_list: %s date: %s symbol: %s -> de_adjusted_closing_price: %s', symbol_list, date, symbol, de_adjusted_closing_price)
                    return de_adjusted_closing_price

            self.logger.debug('symbol_list: %s date: %s -> de_adjusted_closing_price: %s', symbol_list, date, adjusted_closing_price)
            return adjusted_closing_price

        suffixized_symbol_list = self.__suffixize_symbol_list(symbol_list)
        date = pandas.to_datetime(date_string)

        adjusted_closing_price = from_single_date() or from_range_of_dates() or from_renamed_symbol_list()
        if adjusted_closing_price is not None:
            closing_price = get_de_adjusted_price()
            self.logger.info('symbol_list: %s date: %s -> closing_price: %s', symbol_list, date, closing_price)
            return closing_price
        else:
            self.logger.warning('symbol_list: %s date: %s -> no closing price found!', symbol_list, date)
            return None

    def get_de_adjustment_factor(self, stock_symbol, date):
        # todo: this data is directly available from yfinance api, need to check its reliability
        try:
            matching_data = self.price_adjustment_map[stock_symbol]
            adjustment_date = matching_data['Date']
            numerator = matching_data['Numerator']
            denominator = matching_data['Denominator']
        except KeyError:
            self.logger.info('no price adjustment. stock_symbol: %s date: %s', stock_symbol, date)
            return None  # todo: raise exception here? but is this really an exception?
        else:
            if pandas.to_datetime(date) >= adjustment_date:
                self.logger.info('no price adjustment. date: %s on or after adjustment_date: %s stock_symbol: %s', date, adjustment_date, stock_symbol)
                return None

            adjustment_factor = numerator / denominator
            self.logger.info('stock_symbol: %s date: %s -> adjustment_factor: %s', stock_symbol, date, adjustment_factor)
            return adjustment_factor

    def __suffixize_symbol(self, symbol, exchange):
        return symbol + self.exchange_to_suffix[exchange]

    def __suffixize_symbol_list(self, symbol_list):
        return [self.__suffixize_symbol(symbol, exchange) for symbol, exchange in symbol_list]

    def __get_adjusted_closing_prices_for_date_range(self, symbol_list, start_date, end_date):
        for symbol in symbol_list:
            try:
                adjusted_closing_prices = self.symbol_to_stock_data[symbol].loc[start_date:end_date, 'Close']
            except KeyError:
                self.logger.debug('no prefetched data. symbol_list: %s start_date: %s end_date: %s symbol: %s', symbol_list, start_date, end_date, symbol)
                continue
            else:
                if not adjusted_closing_prices.empty and not adjusted_closing_prices.isnull().array.all():
                    self.logger.info('symbol_list: %s start_date: %s end_date: %s -> closing_prices...\n%s', symbol_list, start_date, end_date, adjusted_closing_prices.to_string())
                    return adjusted_closing_prices

        self.logger.warning('symbol_list: %s start_date: %s end_date: %s -> no closing_price_found!', symbol_list, start_date, end_date)
        raise NoClosingPriceError(f'no closing price found for symbol_list: {symbol_list} start_date: {start_date} end_date: {end_date}')


class NoClosingPriceError(Exception):
    """Raise when closing price is not found in the available stock data."""
