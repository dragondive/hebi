import os
import logging
from math import exp
import pandas
from matplotlib import pyplot
from multibeggar.dalalstreet import CompaniesInfo, StockPricesDataProvider


class Multibeggar:
    def __init__(self):
        logging.basicConfig(format='%(levelname)s: %(message)s [%(funcName)s():%(lineno)s - %(asctime)s]', datefmt='%Y/%m/%d %I:%M:%S %p', handlers=[logging.FileHandler(os.path.join(os.getcwd(), 'output', 'multibeggar.log'), mode='w')])
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        script_dir = os.path.dirname(__file__)

        self.fixup_company_names_map = pandas.read_csv(os.path.join(script_dir, 'data', 'fixup_company_names.csv')).set_index('Actual Name').to_dict('index')

        self.companies_info = CompaniesInfo()
        self.stock_prices_data_provider = StockPricesDataProvider()

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

    def __prepare_for_portfolio_complexity_calculation(self):

        def fixup_company_names():
            for actual_name, fixup_data in self.fixup_company_names_map.items():
                self.transactions_list.replace({'Name': actual_name}, fixup_data['Fixed Name'], inplace=True)

        def get_and_collect_stock_symbols(company_name):
            try:
                symbol_list = company_name_to_symbol_list_map[company_name]
            except KeyError:
                symbol_list = self.companies_info.get_symbols(company_name)
                company_name_to_symbol_list_map[company_name] = symbol_list
                self.logger.debug('added to memo. company_name: %s symbol_list: %s', company_name, symbol_list)

                all_symbols.extend(symbol_list)
            else:
                self.logger.debug('read from memo. company_name: %s symbol_list: %s', company_name, symbol_list)

            self.logger.info('company_name: %s -> symbol_list: %s', company_name, symbol_list)
            return symbol_list

        def append_stock_symbols():
            self.transactions_list['Symbol'] = self.transactions_list.apply(lambda x: get_and_collect_stock_symbols(x['Name']), axis=1)

        def sort_by_date():
            self.transactions_list.sort_values(by='Date', inplace=True)

        def fetch_stock_prices():
            start_date = self.transactions_list['Date'].iloc[0]
            self.stock_prices_data_provider.fetch_stock_prices(all_symbols, start_date)

        def append_sentinel_row():
            self.transactions_list = self.transactions_list.append({'Date': '0'}, ignore_index=True)

        all_symbols = []
        company_name_to_symbol_list_map = {}

        fixup_company_names()
        append_stock_symbols()
        sort_by_date()
        fetch_stock_prices()
        append_sentinel_row()

    def __compute_daywise_portfolio(self):

        def compute_and_append_daily_closing_prices_and_values():
            daily_portfolio['Closing Price'] = daily_portfolio.apply(lambda row: self.stock_prices_data_provider.get_closing_price(row['Symbol'], row['Date']), axis=1, result_type='reduce')
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
