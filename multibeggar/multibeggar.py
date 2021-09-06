import os
import logging
from math import exp
import pandas
import yfinance
from fuzzywuzzy import fuzz
from matplotlib import pyplot
from .stock_exchange import StockExchange, StockExchangeInfo


class Multibeggar:
    def __init__(self):
        logging.basicConfig(format='%(levelname)s: %(message)s [%(funcName)s():%(lineno)s - %(asctime)s]', datefmt='%Y/%m/%d %I:%M:%S %p', handlers=[logging.FileHandler(os.path.join(os.getcwd(), 'output', 'multibeggar.log'), mode='w')])
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        script_dir = os.path.dirname(__file__)

        self.fixup_company_names_map = pandas.read_csv(os.path.join(script_dir, 'data', 'fixup_company_names.csv')).set_index('Actual Name').to_dict('index')
        self.renamed_symbols_map = pandas.read_csv(os.path.join(script_dir, 'data', 'renamed_symbols.csv')).set_index('Present Symbol').to_dict('index')
        self.price_adjustment_map = pandas.read_csv(os.path.join(script_dir, 'data', 'price_adjustments.csv'), parse_dates=['Date']).set_index('Symbol').to_dict('index')

        self.stock_exchange_info_map = {
            StockExchange.NSE: StockExchangeInfo(companies_data_file_path=os.path.join(script_dir, 'data', 'equity_nse.csv'),
                                                 symbol_header='SYMBOL',
                                                 company_name_header='NAME OF COMPANY',
                                                 exchange_suffix='.NS'),
            StockExchange.BSE: StockExchangeInfo(companies_data_file_path=os.path.join(script_dir, 'data', 'equity_bse.csv'),
                                                 symbol_header='Security Id',
                                                 company_name_header='Security Name',
                                                 exchange_suffix='.BO'), }

        self.symbol_to_stock_data = {}

    def load_transactions_from_excel_file(self, excel_file_path):
        self.input_file_path = excel_file_path
        self.transactions_list = pandas.read_excel(excel_file_path, parse_dates=['Date'])

    def plot_portfolio_complexity(self):
        self.__prepare_for_portfolio_complexity_calculation()
        self.__compute_daywise_portfolio()

        input_file_name = os.path.splitext(os.path.basename(self.input_file_path))[0]
        self.daywise_full_portfolio.to_excel(os.path.join(os.getcwd(), 'output', input_file_name + '_daywise_full_portfolio.xlsx'))

        self.portfolio_complexity_data = self.daywise_full_portfolio.groupby('Date').apply(lambda group: self.compute_portfolio_complexity(group['Proportion'].dropna())).reset_index(name='Complexity')
        self.portfolio_complexity_data.to_excel(os.path.join(os.getcwd(), 'output', input_file_name + '_portfolio_complexity_data.xlsx'))

        self.portfolio_complexity_data.plot.line(x='Date', y='Complexity')
        pyplot.savefig(os.path.join(os.getcwd(), 'output', input_file_name + '_portfolio_complexity_line_graph.svg'))

    def compute_portfolio_complexity(self, proportions):
        sorted_proportions = sorted(proportions)
        self.logger.debug('sorted_proportions: %s', sorted_proportions)

        exponent_tuning_factor = 0.01

        portfolio_complexity = 0
        [portfolio_complexity := portfolio_complexity + value * exp(exponent_tuning_factor * index) for index, value in enumerate(sorted_proportions)]

        self.logger.info('portfolio_complexity: %s', portfolio_complexity)
        return portfolio_complexity

    def get_renamed_symbol(self, stock_symbol):
        try:
            old_symbol = self.renamed_symbols_map[stock_symbol]['Old Symbol']
            self.logger.info('stock_symbol: %s -> old_symbol: %s', stock_symbol, old_symbol)
            return old_symbol
        except KeyError:
            self.logger.warning('stock_symbol: %s -> no old_symbol found!', stock_symbol)
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

    def get_closing_price(self, symbol_list, date, use_fallback=True):
        start_date = pandas.to_datetime(date)
        end_date = pandas.to_datetime(date)

        adjusted_closing_price = self.__get_adjusted_closing_prices_for_date_range(symbol_list, start_date, end_date)

        if use_fallback and adjusted_closing_price is None:
            adjusted_closing_prices = self.__get_adjusted_closing_prices_for_date_range(symbol_list, start_date - pandas.Timedelta(days=7), end_date + pandas.Timedelta(days=7))
            if adjusted_closing_prices is not None:
                adjusted_closing_price = adjusted_closing_prices.mean()
                self.logger.warning('fallback to mean price! symbol_list: %s date: %s -> adjusted_closing_price: %s', symbol_list, date, adjusted_closing_price)

        if adjusted_closing_price is None:
            renamed_symbol_list = [renamed_symbol for symbol in symbol_list if (renamed_symbol := self.get_renamed_symbol(symbol)) is not None]
            self.logger.debug('symbol_list: %s -> renamed_symbol_list: %s', symbol_list, renamed_symbol_list)

            symbol_to_fetch_list = [symbol for symbol in renamed_symbol_list if symbol not in self.symbol_to_stock_data]
            if symbol_to_fetch_list:
                self.__fetch_stock_data(symbol_to_fetch_list)

            if renamed_symbol_list:
                adjusted_closing_price = self.get_closing_price(renamed_symbol_list, date)
                self.logger.debug('symbol_list: %s date: %s -> adjusted_closing_price: %s', symbol_list, date, adjusted_closing_price)

        if adjusted_closing_price is None:
            self.logger.warning('symbol_list: %s date: %s -> no closing_price found!', symbol_list, date)
            return None

        for symbol in symbol_list:
            de_adjustment_factor = self.get_de_adjustment_factor(symbol, date)
            if de_adjustment_factor is not None:
                de_adjusted_closing_price = adjusted_closing_price * de_adjustment_factor
                self.logger.info('symbol_list: %s date: %s symbol: %s -> closing_price: %s', symbol_list, date, symbol, de_adjusted_closing_price)
                return de_adjusted_closing_price

        self.logger.info('symbol_list: %s date: %s -> closing_price: %s', symbol_list, date, adjusted_closing_price)
        return adjusted_closing_price

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
        return None

    def __prepare_for_portfolio_complexity_calculation(self):

        def fixup_company_names():
            for actual_name, fixup_data in self.fixup_company_names_map.items():
                self.transactions_list.replace({'Name': actual_name}, fixup_data['Fixed Name'], inplace=True)

        def get_and_collect_stock_symbols(company_name):
            try:
                symbol_list = company_name_to_symbol_list_map[company_name]
            except KeyError:
                symbol_list = []
                for exchange_name, exchange_info in self.stock_exchange_info_map.items():
                    if symbol := exchange_info.get_symbol(company_name):
                        symbol_list.append(symbol)
                    self.logger.debug('company_name: %s exchange_name: %s -> symbol: %s', company_name, exchange_name, symbol)

                all_symbols.extend(symbol_list)
                company_name_to_symbol_list_map[company_name] = symbol_list
                self.logger.debug('added to memo. company_name: %s symbol_list: %s', company_name, symbol_list)
            else:
                self.logger.debug('read from memo. company_name: %s symbol_list: %s', company_name, symbol_list)
            finally:
                self.logger.info('company_name: %s -> symbol_list: %s', company_name, symbol_list)
                return symbol_list

        def append_stock_symbols():
            self.transactions_list['Symbol'] = self.transactions_list.apply(lambda x: get_and_collect_stock_symbols(x['Name']), axis=1)

        def sort_by_date():
            self.transactions_list.sort_values(by='Date', inplace=True)

        def append_sentinel_row():
            self.transactions_list = self.transactions_list.append({'Date': '0'}, ignore_index=True)

        all_symbols = []
        company_name_to_symbol_list_map = {}

        fixup_company_names()
        append_stock_symbols()
        sort_by_date()
        self.__fetch_stock_data(all_symbols)
        append_sentinel_row()

    def __fetch_stock_data(self, symbol_list):

        def get_adapted_end_date(end_date):
            adapted_end_date = end_date + pandas.Timedelta(days=1)
            return adapted_end_date

        start_date = self.transactions_list['Date'].iloc[0]
        end_date = get_adapted_end_date(pandas.to_datetime('today').normalize())

        stock_data = yfinance.download(symbol_list, group_by='Ticker', start=start_date, end=end_date)
        symbol_to_stock_data = {index: group.xs(index, level=0, axis=1) for index, group in stock_data.groupby(level=0, axis=1)}
        self.symbol_to_stock_data.update(symbol_to_stock_data)

        self.logger.debug('downloaded stock data from date: %s to date: %s for symbols...\n%s', start_date, end_date, symbol_list)

    def __compute_daywise_portfolio(self):

        def compute_and_append_daily_closing_prices_and_values():
            daily_portfolio['Closing Price'] = daily_portfolio.apply(lambda row: self.get_closing_price(row['Symbol'], row['Date']), axis=1, result_type='reduce')
            daily_portfolio['Value'] = daily_portfolio['Shares'] * daily_portfolio['Closing Price']

        def compute_and_append_daily_proportions():
            value_sum = daily_portfolio['Value'].sum()
            self.logger.debug('ongoing_date: %s value_sum: %s', ongoing_date, value_sum)

            try:
                daily_portfolio['Proportion'] = daily_portfolio['Value'] / value_sum
            except ZeroDivisionError:
                self.logger.warning('value_sum is zero, clearing daily_portfolio! ongoing_date: %s', ongoing_date)
                # clearing all rows causes strange runtime exception, hence using below workaround which is equivalent
                daily_portfolio.dropna(subset=['Value'], inplace=True)

        ongoing_date = None
        daily_portfolio = self.transactions_list.iloc[0:0, :].copy()  # create empty DataFrame with same columns as transactions_list
        self.daywise_full_portfolio = pandas.DataFrame()
        self.portfolio_complexity_data = pandas.DataFrame()

        for __unused, row in self.transactions_list.iterrows():
            date = row['Date']
            self.logger.debug('date: %s', date)

            if date != ongoing_date:  # this is a new date, so update current daily_portfolio to daywise_full_portfolio
                daily_portfolio.drop(daily_portfolio[daily_portfolio['Shares'] == 0].index, inplace=True)

                compute_and_append_daily_closing_prices_and_values()
                compute_and_append_daily_proportions()

                self.daywise_full_portfolio = self.daywise_full_portfolio.append(daily_portfolio)

                daily_portfolio.replace({ongoing_date: date}, inplace=True)
                self.logger.debug('ongoing_date changing from: %s to: %s', ongoing_date, date)
                ongoing_date = date

            company_name = row['Name']
            self.logger.debug('company_name: %s', company_name)

            mask = (daily_portfolio['Name'] == company_name)
            masked_rows = daily_portfolio[mask]
            self.logger.debug('masked_rows...\n%s', masked_rows.to_string())

            if masked_rows.empty:  # this is a new stock name, so append to daily_portfolio
                daily_portfolio = daily_portfolio.append(row)
                self.logger.debug('added to daily_portfolio company_name: %s for ongoing_date: %s', company_name, ongoing_date)
            else:  # this is already known stock, so update shares count in daily_portfolio
                transacted_shares = row['Shares']
                self.logger.debug('transacted_shares: %s', transacted_shares)
                daily_portfolio.loc[mask, 'Shares'] += transacted_shares
                self.logger.debug('company_name: %s updated shares count: %s', company_name, daily_portfolio.loc[mask, 'Shares'].array[0])
