import os
import logging
from math import exp
import pandas
import yfinance
from fuzzywuzzy import fuzz
from matplotlib import pyplot


class Multibeggar:
    def __init__(self):
        logging.basicConfig(format='%(levelname)s: %(message)s [%(funcName)s():%(lineno)s - %(asctime)s]', datefmt='%Y/%m/%d %I:%M:%S %p', handlers=[logging.FileHandler(os.path.join(os.getcwd(), 'output', 'multibeggar.log'), mode='w')])
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        script_dir = os.path.dirname(__file__)

        self.fixup_company_names_map = pandas.read_csv(os.path.join(script_dir, 'data', 'fixup_company_names.csv'))
        self.renamed_symbols_map = pandas.read_csv(os.path.join(script_dir, 'data', 'renamed_symbols.csv'))
        self.price_adjustment_list = pandas.read_csv(os.path.join(script_dir, 'data', 'price_adjustments.csv'), parse_dates=['Date'])

        self.nse_symbol_heading, self.nse_company_name_heading = 'SYMBOL', 'NAME OF COMPANY'
        self.nse_symbol_name_map = pandas.read_csv(os.path.join(script_dir, 'data', 'equity_nse.csv'), usecols=[self.nse_symbol_heading, self.nse_company_name_heading])
        self.nse_suffix = '.NS'

        self.bse_symbol_heading, self.bse_company_name_heading = 'Security Id', 'Security Name'
        self.bse_symbol_name_map = pandas.read_csv(os.path.join(script_dir, 'data', 'equity_bse.csv'), usecols=[self.bse_symbol_heading, self.bse_company_name_heading])
        self.bse_suffix = '.BO'

    def load_transactions_from_excel_file(self, excel_file_path):
        self.input_file_path = excel_file_path
        self.transactions_list = pandas.read_excel(excel_file_path, parse_dates=['Date'])

    def plot_portfolio_complexity(self):
        self.__prepare_for_portfolio_complexity_calculation()
        self.__compute_daywise_portfolio()

        input_file_name = os.path.splitext(os.path.basename(self.input_file_path))[0]
        self.daywise_full_portfolio.to_excel(os.path.join(os.getcwd(), 'output', input_file_name + '_daywise_full_portfolio.xlsx'))

        self.portfolio_complexity_data = self.daywise_full_portfolio.groupby('Date').apply(lambda group: self.compute_portfolio_complexity(group['Proportion'])).reset_index(name='Complexity')
        self.portfolio_complexity_data.to_excel(os.path.join(os.getcwd(), 'output', input_file_name + '_portfolio_complexity_data.xlsx'))

        self.portfolio_complexity_data.plot.line(x='Date', y='Complexity')
        pyplot.savefig(os.path.join(os.getcwd(), 'output', input_file_name + '_portfolio_complexity_line_graph.svg'))

    def compute_portfolio_complexity(self, proportions):
        sorted_proportions = sorted(proportions)
        self.logger.debug('sorted_proportions: ' + str(sorted_proportions))

        exponent_tuning_factor = 0.01

        portfolio_complexity = 0
        [portfolio_complexity := portfolio_complexity + value * exp(exponent_tuning_factor * index) for index, value in enumerate(sorted_proportions)]

        self.logger.info('portfolio_complexity: ' + str(portfolio_complexity))
        return portfolio_complexity

    def get_nse_symbol(self, company_name, with_suffix=True):

        def get_nse_symbol_by_startswith_company_name_match():
            matching_mask = self.nse_symbol_name_map[self.nse_company_name_heading].str.startswith(company_name)
            matching_row = self.nse_symbol_name_map[matching_mask]

            if len(matching_row.index) == 1:
                symbol = matching_row[self.nse_symbol_heading].values[0]  # todo self: is values[0] required here?
                self.logger.info('company_name: ' + str(company_name) + ' -> symbol: ' + str(symbol))
                return symbol
            
            if len(matching_row.index) > 1:
                self.logger.warning('company_name: ' + str(company_name) + ' -> multiple symbols matched!')
                self.logger.debug('company_name: ' + str(company_name) + ' -> matching symbols...\n' + str(matching_row[self.nse_symbol_heading].array))
                return None

            self.logger.info('company_name: ' + str(company_name) + ' -> no symbol matched.')
            return None

        def get_nse_symbol_by_fuzzy_company_name_match():
            match_ratios = self.nse_symbol_name_map.apply(lambda x: fuzz.token_sort_ratio(x[self.nse_company_name_heading], company_name), axis=1)
            qualified_rows = match_ratios[lambda x: x >= 75]
            self.logger.debug('company_name: ' + str(company_name) + ' -> qualified_rows...\n' + pandas.concat([self.nse_symbol_name_map.loc[qualified_rows.index], match_ratios.loc[qualified_rows.index].rename('match_ratio')], axis=1).to_string())
            
            try:
                best_matching_row = self.nse_symbol_name_map.loc[qualified_rows.idxmax()]
                symbol = best_matching_row[self.nse_symbol_heading]

                self.logger.info('company_name: ' + str(company_name) + ' -> symbol: ' + str(symbol))
                return symbol
            except ValueError:
                self.logger.warning('company_name: ' + str(company_name) + ' -> no symbol matched!')
                return None

        symbol = get_nse_symbol_by_startswith_company_name_match()

        if symbol is None:
            symbol = get_nse_symbol_by_fuzzy_company_name_match()

        if with_suffix and symbol is not None:
            symbol += self.nse_suffix

        self.logger.info('company_name: ' + str(company_name) + ' -> symbol: ' + str(symbol))
        return symbol

    def get_bse_symbol(self, company_name, with_suffix=True):

        def get_bse_symbol_by_startswith_company_name_match():
            matching_mask = self.bse_symbol_name_map[self.bse_company_name_heading].str.startswith(company_name)
            matching_row = self.bse_symbol_name_map[matching_mask]

            if len(matching_row.index) == 1:
                symbol = matching_row[self.bse_symbol_heading].values[0]  # todo self: is values[0] required here?
                self.logger.info('company_name: ' + str(company_name) + ' -> symbol: ' + str(symbol))
                return symbol
            
            if len(matching_row.index) > 1:
                self.logger.warning('company_name: ' + str(company_name) + ' -> multiple symbols matched!')
                self.logger.debug('company_name: ' + str(company_name) + ' -> matching symbols...\n' + str(matching_row[self.bse_symbol_heading].array))
                return None

            self.logger.info('company_name: ' + str(company_name) + ' -> no symbol matched.')
            return None

        def get_bse_symbol_by_fuzzy_company_name_match():
            match_ratios = self.bse_symbol_name_map.apply(lambda x: fuzz.token_sort_ratio(x[self.bse_company_name_heading], company_name), axis=1)
            qualified_rows = match_ratios[lambda x: x >= 75]
            self.logger.debug('company_name: ' + str(company_name) + ' -> qualified_rows...\n' + pandas.concat([self.bse_symbol_name_map.loc[qualified_rows.index], match_ratios.loc[qualified_rows.index].rename('match_ratio')], axis=1).to_string())

            try:
                best_matching_row = self.bse_symbol_name_map.loc[qualified_rows.idxmax()]
                symbol = best_matching_row[self.bse_symbol_heading]

                self.logger.info('company_name: ' + str(company_name) + ' -> symbol: ' + str(symbol))
                return symbol
            except ValueError:
                self.logger.warning('company_name: ' + str(company_name) + ' -> no symbol matched!')
                return None

        symbol = get_bse_symbol_by_startswith_company_name_match()

        if symbol is None:
            symbol = get_bse_symbol_by_fuzzy_company_name_match()

        if with_suffix and symbol is not None:
            symbol += self.bse_suffix

        self.logger.info('company_name: ' + str(company_name) + ' -> symbol: ' + str(symbol))
        return symbol

    def get_stock_symbols(self, company_name, with_suffix=True):
        symbols = [self.get_nse_symbol(company_name, with_suffix), self.get_bse_symbol(company_name, with_suffix)]

        self.logger.info('company_name: ' + str(company_name) + ' -> symbols: ' + str(symbols))
        return symbols

    def get_adjusted_closing_price(self, stock_symbol, date):
        adjusted_closing_price = self.__get_adjusted_average_price(stock_symbol, date, offset_days=0)

        self.logger.info('stock_symbol: ' + str(stock_symbol) + ' date: ' + str(date) + ' -> adjusted_closing_price: ' + str(adjusted_closing_price))
        return adjusted_closing_price

    def get_renamed_symbol(self, stock_symbol):
        matching_row = self.renamed_symbols_map[self.renamed_symbols_map['Present Symbol'] == stock_symbol]

        try:
            old_symbol = matching_row['Old Symbol'].values[0]
            self.logger.info('stock_symbol: ' + str(stock_symbol) + ' -> old_symbol: ' + str(old_symbol))
            return old_symbol
        except IndexError:
            self.logger.warning('stock_symbol: ' + str(stock_symbol) + ' -> no old_symbol found!')
            return None

    def de_adjust_price(self, adjusted_price, stock_symbol, date):
        if stock_symbol is None:
            self.logger.warning('stock_symbol is None! date: ' + str(date) + ' -> unchanged adjusted_price: ' + str(adjusted_price))
            return adjusted_price

        matching_row = self.price_adjustment_list[self.price_adjustment_list['Symbol'] == stock_symbol]
        try:
            adjustment_date = matching_row['Date'].values[0]
            if pandas.to_datetime(date) >= adjustment_date:
                self.logger.info('date: ' + str(date) + ' on or after adjustment_date: ' + str(adjustment_date) + ' stock_symbol: ' + str(stock_symbol) + ' -> unchanged adjusted price: ' + str(adjusted_price))
                return adjusted_price

            numerator = matching_row['Numerator'].values[0]
            denominator = matching_row['Denominator'].values[0]
            de_adjusted_price = adjusted_price * numerator / denominator

            self.logger.debug('numerator: ' + str(numerator) + ' denominator: ' + str(denominator))
            self.logger.info('adjusted_price: ' + str(adjusted_price) + ' stock_symbol: ' + str(stock_symbol) + ' date: ' + str(date) + ' -> de_adjusted_price: ' + str(de_adjusted_price))
            return de_adjusted_price
        except IndexError:
            self.logger.info('no price adjustment. stock_symbol: ' + str(stock_symbol) + ' date: ' + str(date) + ' -> unchanged adjusted_price: ' + str(adjusted_price))
            return adjusted_price

    def get_closing_price_by_symbol_list(self, symbol_list, date, fallback_to_average_price=True, fallback_offset=7, fallback_to_renamed_symbol=True):
        adjusted_closing_price = self.__get_adjusted_closing_price_by_symbol_list_from_prefetched_stock_data(symbol_list, date)
        self.logger.debug('symbol_list: ' + str(symbol_list) + ' date: ' + str(date) + ' -> adjusted_closing_price: ' + str(adjusted_closing_price))

        if adjusted_closing_price is None:
            for symbol in symbol_list:
                adjusted_closing_price = self.get_adjusted_closing_price(symbol, date)
                if adjusted_closing_price is not None:
                    self.logger.debug('symbol: ' + str(symbol) + ' date: ' + str(date) + ' -> adjusted_closing_price: ' + str(adjusted_closing_price))
                    break

        if fallback_to_average_price and adjusted_closing_price is None:
            for symbol in symbol_list:
                adjusted_closing_price = self.__get_adjusted_average_price(symbol, date, offset_days=fallback_offset)
                if adjusted_closing_price is not None:
                    self.logger.warning('fallback to average price! symbol: ' + str(symbol) + ' date: ' + str(date) + ' -> adjusted_closing_price: ' + str(adjusted_closing_price))
                    break

        if fallback_to_renamed_symbol and adjusted_closing_price is None:
            renamed_symbol_list = [renamed_symbol for symbol in symbol_list if (renamed_symbol := self.get_renamed_symbol(symbol)) is not None]
            self.logger.debug('symbol_list: ' + str(symbol_list) + ' -> renamed_symbol_list: ' + str(renamed_symbol_list))
            if renamed_symbol_list:
                adjusted_closing_price = self.get_closing_price_by_symbol_list(renamed_symbol_list, date)
                self.logger.debug('symbol: ' + str(symbol) + ' date: ' + str(date) + ' -> adjusted_closing_price: ' + str(adjusted_closing_price))

        if adjusted_closing_price is None:
            self.logger.warning('symbol_list: ' + str(symbol_list) + ' date: ' + str(date) + ' -> no closing_price found!')
            return None

        for symbol in symbol_list:
            de_adjusted_closing_price = self.de_adjust_price(adjusted_closing_price, symbol, date)
            if de_adjusted_closing_price is not None:
                self.logger.info('symbol_list: ' + str(symbol_list) + ' date: ' + str(date) + ' symbol: ' + str(symbol) + ' -> closing_price: ' + str(de_adjusted_closing_price))
                return de_adjusted_closing_price

    def __get_adjusted_average_price(self, stock_symbol, date, offset_days=7):
        if stock_symbol is None:
            self.logger.warning('stock_symbol is None!')
            return None

        start_date = pandas.to_datetime(date) - pandas.Timedelta(days=offset_days)
        end_date = pandas.to_datetime(date) + pandas.Timedelta(days=1 + offset_days)
        self.logger.debug('stock_symbol: ' + str(stock_symbol) + ' date: ' + str(date) + ' start_date: ' + str(start_date) + ' end_date: ' + str(end_date))

        ticker = yfinance.Ticker(stock_symbol)
        stock_data = ticker.history(start=start_date, end=end_date)
        self.logger.debug('stock_symbol: ' + str(stock_symbol) + ' date: ' + str(date) + ' stock_data...\n' + stock_data.to_string())

        if stock_data.empty:
            self.logger.warning('stock_symbol: ' + str(stock_symbol) + ' date: ' + str(date) + ' -> no stock data!')
            return None

        closing_price = stock_data['Close'].mean()
        self.logger.info('stock_symbol: ' + str(stock_symbol) + ' date: ' + str(date) + ' -> closing_price: ' + str(closing_price))
        return closing_price

    def __get_adjusted_closing_price_by_symbol_list_from_prefetched_stock_data(self, symbol_list, date):
        for symbol in symbol_list:
            try:
                adjusted_closing_price = self.prefetched_stock_data.loc[date, (symbol, 'Close')]
            except KeyError:
                self.logger.warning('symbol: ' + str(symbol) + ' date: ' + str(date) + ' -> no closing_price found!')
            else:
                if not pandas.isnull(adjusted_closing_price):
                    self.logger.debug('symbol: ' + str(symbol) + ' date: ' + str(date) + ' -> adjusted_closing_price: ' + str(adjusted_closing_price))
                    return adjusted_closing_price

        self.logger.warning('symbol_list: ' + str(symbol_list) + ' date: ' + str(date) + ' -> no closing_price found!')
        return None

    def __prepare_for_portfolio_complexity_calculation(self):

        def fixup_company_names():
            for __unused, row in self.fixup_company_names_map.iterrows():
                self.transactions_list.replace({'Name': row['Actual Name']}, row['Fixed Name'], inplace=True)

        def get_and_collect_stock_symbols(company_name):
            symbol_list = self.get_stock_symbols(company_name)
            symbol_set.update(symbol_list)
            return symbol_list

        def append_stock_symbols():
            self.transactions_list['Symbol'] = self.transactions_list.apply(lambda x: get_and_collect_stock_symbols(x['Name']), axis=1)

        def sort_by_date():
            self.transactions_list.sort_values(by='Date', inplace=True)

        def prefetch_stock_data():
            first_date = self.transactions_list['Date'].iloc[0]
            last_date = self.transactions_list['Date'].iloc[-1]
            symbols_str = ' '.join([str(symbol) for symbol in symbol_set])
            self.prefetched_stock_data = yfinance.download(symbols_str, group_by='Ticker', start=first_date, end=last_date + pandas.Timedelta(days=1))

            self.logger.debug('downloaded stock data from date: ' + str(first_date) + ' to date: ' + str(last_date) + ' for symbols...\n' + symbols_str)

        def append_sentinel_row():
            self.transactions_list = self.transactions_list.append({'Date': '0'}, ignore_index=True)

        symbol_set = set()

        fixup_company_names()
        append_stock_symbols()
        sort_by_date()
        prefetch_stock_data()
        append_sentinel_row()

    def __compute_daywise_portfolio(self):

        def compute_and_append_daily_closing_prices_and_values():
            daily_portfolio['Closing Price'] = daily_portfolio.apply(lambda row: self.get_closing_price_by_symbol_list(row['Symbol'], row['Date']), axis=1, result_type='reduce')
            daily_portfolio['Value'] = daily_portfolio['Shares'] * daily_portfolio['Closing Price']

        def compute_and_append_daily_proportions():
            value_sum = daily_portfolio['Value'].sum()
            self.logger.debug('ongoing_date: ' + str(ongoing_date) + ' value_sum: ' + str(value_sum))

            try:
                daily_portfolio['Proportion'] = daily_portfolio['Value'] / value_sum
            except ZeroDivisionError:
                self.logger.warning('value_sum is zero, clearing daily_portfolio! ongoing_date: ' + str(ongoing_date))
                # clearing all rows causes strange runtime exception, hence using below workaround which is equivalent
                daily_portfolio.dropna(subset=['Value'], inplace=True)

        ongoing_date = None
        daily_portfolio = self.transactions_list.iloc[0:0, :].copy()  # create empty DataFrame with same columns as transactions_list
        self.daywise_full_portfolio = pandas.DataFrame()
        self.portfolio_complexity_data = pandas.DataFrame()

        for __unused, row in self.transactions_list.iterrows():
            date = row['Date']
            self.logger.debug('date: ' + str(date))

            if date != ongoing_date:  # this is a new date, so update current daily_portfolio to daywise_full_portfolio
                daily_portfolio.drop(daily_portfolio[daily_portfolio['Shares'] == 0].index, inplace=True)

                compute_and_append_daily_closing_prices_and_values()
                compute_and_append_daily_proportions()

                self.daywise_full_portfolio = self.daywise_full_portfolio.append(daily_portfolio)

                daily_portfolio.replace({ongoing_date: date}, inplace=True)
                self.logger.debug('ongoing_date changing from: ' + str(ongoing_date) + ' to: ' + str(date))
                ongoing_date = date

            company_name = row['Name']
            self.logger.debug('company_name: ' + str(company_name))

            mask = (daily_portfolio['Name'] == company_name)
            masked_rows = daily_portfolio[mask]
            self.logger.debug('masked_rows...\n' + masked_rows.to_string())

            if masked_rows.empty:  # this is a new stock name, so append to daily_portfolio
                daily_portfolio = daily_portfolio.append(row)
                self.logger.debug('added to daily_portfolio company_name: ' + str(company_name) + ' for ongoing_date: ' + str(ongoing_date))
            else:  # this is already known stock, so update shares count in daily_portfolio
                transacted_shares = row['Shares']
                self.logger.debug('transacted_shares: ' + str(transacted_shares))
                daily_portfolio.loc[mask, 'Shares'] += transacted_shares
                self.logger.debug('company_name: ' + str(company_name) + ' updated shares count: ' + str(daily_portfolio.loc[mask, 'Shares'].array[0]))
