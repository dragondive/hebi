import os
import pandas
import yfinance
from fuzzywuzzy import fuzz

class Multibeggar:
    def __init__(self):
        self.script_dir = os.path.dirname(__file__)

        self.fixup_company_names_map = pandas.read_csv(os.path.join(self.script_dir, 'data', 'fixup_company_names.csv'))
        self.renamed_symbols_map = pandas.read_csv(os.path.join(self.script_dir, 'data', 'renamed_symbols.csv'))
        self.price_adjustment_list = pandas.read_csv(os.path.join(self.script_dir, 'data', 'price_adjustments.csv'), parse_dates=['Date'])

        self.nse_symbol_heading, self.nse_company_name_heading = 'SYMBOL', 'NAME OF COMPANY'
        self.nse_symbol_name_map = pandas.read_csv(os.path.join(self.script_dir, 'data', 'equity_nse.csv'), usecols=[self.nse_symbol_heading, self.nse_company_name_heading])
        self.nse_suffix = '.NS'
        
        self.bse_symbol_heading, self.bse_company_name_heading = 'Security Id', 'Security Name'
        self.bse_symbol_name_map = pandas.read_csv(os.path.join(self.script_dir, 'data', 'equity_bse.csv'), usecols=[self.bse_symbol_heading, self.bse_company_name_heading])
        self.bse_suffix = '.BO'


    def load_transactions_from_excel_file(self, excel_file_name):
        self.transactions_list = pandas.read_excel(excel_file_name)

    
    def plot_portfolio_complexity(self):
        self.__prepare_for_portfolio_complexity_calculation()
        self.__create_daywise_portfolio()
        self.__update_closing_prices()
        self.__compute_and_update_values()
        self.daywise_full_portfolio.to_excel(os.path.join(os.getcwd(), 'output', 'daywise_full_portfolio.xlsx'))
    
    def get_nse_symbol(self, company_name, with_suffix=True):

        def get_nse_symbol_by_startswith_company_name_match():
            matching_mask = self.nse_symbol_name_map[self.nse_company_name_heading].str.startswith(company_name)
            matching_row = self.nse_symbol_name_map[matching_mask]

            if len(matching_row.index) == 1:
                symbol = matching_row[self.nse_symbol_heading].values[0] # todo self: is values[0] required here?
                return symbol
            elif len(matching_row.index) > 1:
                # todo: log info about more than one company matching
                pass
                
            return None


        def get_nse_symbol_by_fuzzy_company_name_match():
            matching_mask = self.nse_symbol_name_map.apply(lambda x: fuzz.token_sort_ratio(x[self.nse_company_name_heading], company_name), axis=1)
            qualified_rows = matching_mask[lambda x: x > 75]
            
            try:
                best_matching_row = self.nse_symbol_name_map.loc[qualified_rows.idxmax()]
                symbol = best_matching_row[self.nse_symbol_heading]
                return symbol
            except ValueError:
                return None


        symbol = get_nse_symbol_by_startswith_company_name_match()
        
        if symbol is None:
            symbol = get_nse_symbol_by_fuzzy_company_name_match()
            
        if with_suffix and symbol is not None:
            symbol += self.nse_suffix
            
        return symbol


    def get_bse_symbol(self, company_name, with_suffix=True):
        
        def get_bse_symbol_by_startswith_company_name_match():
            matching_mask = self.bse_symbol_name_map[self.bse_company_name_heading].str.startswith(company_name)
            matching_row = self.bse_symbol_name_map[matching_mask]
            
            if len(matching_row.index) == 1:
                symbol = matching_row[self.bse_symbol_heading].values[0] # todo self: is values[0] required here?
                return symbol
            elif len(matching_row.index) > 1:
                # todo: log info about more than one company matching
                pass
                
            return None
            
            
        def get_bse_symbol_by_fuzzy_company_name_match():
            matching_mask = self.bse_symbol_name_map.apply(lambda x: fuzz.token_sort_ratio(x[self.bse_company_name_heading], company_name), axis=1)
            qualified_rows = matching_mask[lambda x: x > 75]

            try:
                best_matching_row = self.bse_symbol_name_map.loc[qualified_rows.idxmax()]
                symbol = best_matching_row[self.bse_symbol_heading]
                return symbol
            except ValueError:
                return None

 
        symbol = get_bse_symbol_by_startswith_company_name_match()
        
        if symbol is None:
            symbol = get_bse_symbol_by_fuzzy_company_name_match()
            
        if with_suffix and symbol is not None:
            symbol += self.bse_suffix
            
        return symbol


    def get_stock_symbols(self, company_name, with_suffix=True):
        symbols = [self.get_nse_symbol(company_name, with_suffix), self.get_bse_symbol(company_name, with_suffix)]
        return symbols


    def get_adjusted_closing_price(self, stock_symbol, date):
        return self.__get_adjusted_average_price(stock_symbol, date, offset_days=0)

    
    def get_renamed_symbol(self, stock_symbol):
        matching_row = self.renamed_symbols_map[self.renamed_symbols_map['Present Symbol'] == stock_symbol]

        try:
            old_symbol = matching_row['Old Symbol'].values[0]
            return old_symbol
        except IndexError:
            return None

    
    def de_adjust_price(self, adjusted_price, stock_symbol, date):
        if stock_symbol is None:
            return adjusted_price
            
        matching_row = self.price_adjustment_list[self.price_adjustment_list['Symbol'] == stock_symbol]
        try:
            adjustment_date = matching_row['Date'].values[0]
            if pandas.to_datetime(date) >= adjustment_date:
                return adjusted_price
            
            numerator = matching_row['Numerator'].values[0]
            denominator = matching_row['Denominator'].values[0]
        
            de_adjusted_price = adjusted_price * numerator / denominator
            return de_adjusted_price
        except IndexError:
            return adjusted_price


    def get_closing_price_by_symbol_list(self, symbol_list, date, fallback_to_average_price=True, fallback_offset=7, fallback_to_renamed_symbol=True):
        for symbol in symbol_list:            
            adjusted_closing_price = self.get_adjusted_closing_price(symbol, date)
            if adjusted_closing_price is not None:
                break
                
        if fallback_to_average_price and adjusted_closing_price is None:
            for symbol in symbol_list:
                adjusted_closing_price = self.__get_adjusted_average_price(symbol, date, offset_days=fallback_offset)
                if adjusted_closing_price is not None:
                    break
                    
        if fallback_to_renamed_symbol and adjusted_closing_price is None:
            renamed_symbol_list = [renamed_symbol for symbol in symbol_list if (renamed_symbol := self.get_renamed_symbol(symbol)) is not None]
            if renamed_symbol_list:
                adjusted_closing_price = self.get_closing_price_by_symbol_list(renamed_symbol_list, date)
        
        if adjusted_closing_price is None:
            return None
        
        for symbol in symbol_list:
            de_adjusted_closing_price = self.de_adjust_price(adjusted_closing_price, symbol, date)
            if de_adjusted_closing_price is not None:
                return de_adjusted_closing_price


    def __get_adjusted_average_price(self, stock_symbol, date, offset_days=7):
        if stock_symbol is None:
            return None

        start_date = pandas.to_datetime(date) - pandas.Timedelta(days=offset_days)
        end_date = pandas.to_datetime(date) + pandas.Timedelta(days=1+offset_days)
                
        ticker = yfinance.Ticker(stock_symbol)
        stock_data = ticker.history(start=start_date, end=end_date)
        
        if stock_data.empty:
            return None
            
        closing_price = stock_data['Close'].mean()
        return closing_price


    def __prepare_for_portfolio_complexity_calculation(self):

        def fixup_company_names():
            for __unused, row in self.fixup_company_names_map.iterrows():
                self.transactions_list.replace({'Name': row['Actual Name']}, row['Fixed Name'], inplace=True)


        def update_symbols():
            self.transactions_list['Symbol'] = self.transactions_list.apply(lambda x: self.get_stock_symbols(x['Name'], with_suffix=True), axis=1)
        
        
        def sort_by_date():
            self.transactions_list.sort_values(by='Date', inplace=True)
            
        
        def append_sentinel_row():
            self.transactions_list = self.transactions_list.append({'Date' : '0'}, ignore_index=True) 


        fixup_company_names()
        update_symbols()
        sort_by_date()
        append_sentinel_row()


    def __create_daywise_portfolio(self):
        ongoing_date = None
        daily_portfolio = self.transactions_list.iloc[0:0,:].copy() # create empty DataFrame with same columns as transactions_list
        self.daywise_full_portfolio = pandas.DataFrame()
        
        for __unused, row in self.transactions_list.iterrows():
            date = row['Date']
            
            if date != ongoing_date: # This is a new date, so update current daily_portfolio to daywise_full_portfolio
                daily_portfolio.drop(daily_portfolio[daily_portfolio['Shares'] == 0].index, inplace=True)
                self.daywise_full_portfolio = self.daywise_full_portfolio.append(daily_portfolio)
        
                daily_portfolio.replace({ongoing_date: date}, inplace=True)
                ongoing_date = date
                
            name = row['Name']
            mask = (daily_portfolio['Name'] == name)
            masked_rows = daily_portfolio[mask]
            
            if masked_rows.empty == True: # this is a new stock name, so append to daily_portfolio
                daily_portfolio = daily_portfolio.append(row)
            else: # this is already known stock, so update shares count in daily_portfolio
                shares = row['Shares']
                daily_portfolio.loc[mask, 'Shares'] += shares


    def __update_closing_prices(self):
        self.daywise_full_portfolio['Closing Price'] = self.daywise_full_portfolio.apply(lambda row: self.get_closing_price_by_symbol_list(row['Symbol'], row['Date']), axis=1)


    def __compute_and_update_values(self):
        self.daywise_full_portfolio['Value'] = self.daywise_full_portfolio['Shares'] * self.daywise_full_portfolio['Closing Price']
    
    
# def get_stock_symbol_from_nse(company_name, with_suffix=False):
    # if not hasattr(get_stock_symbol_from_nse, 'stock_symbol_name_map'): # ugly code, will be rewritten more cleanly
        # get_stock_symbol_from_nse.stock_symbol_name_map = pandas.read_csv('equity_nse.csv', usecols=['SYMBOL', 'NAME OF COMPANY'])
        
    # matching_mask_startswith = (get_stock_symbol_from_nse.stock_symbol_name_map['NAME OF COMPANY'].str.startswith(company_name))
    # matching_row_startswith = get_stock_symbol_from_nse.stock_symbol_name_map[matching_mask_startswith]
    
    # stock_symbol = None
    # if matching_row_startswith.empty != True:
        # stock_symbol = matching_row_startswith['SYMBOL'].values[0]
    # else:
        # matching_mask_fuzzy = get_stock_symbol_from_nse.stock_symbol_name_map.apply(lambda x: fuzz.token_sort_ratio(x['NAME OF COMPANY'], company_name), axis=1)
        # qualified_rows = matching_mask_fuzzy[lambda x: x > 75]
        # if qualified_rows.empty != True:
            # best_matching_row = get_stock_symbol_from_nse.stock_symbol_name_map.loc[qualified_rows.idxmax()]
            # stock_symbol = best_matching_row['SYMBOL']
            
    # if with_suffix == True and stock_symbol is not None:
        # stock_symbol += '.NS'
    
    # print('nse company_name: ' + str(company_name) + ' symbol: ' + str(stock_symbol))
    # return stock_symbol


# def get_stock_symbol_from_bse(company_name, with_suffix=False):
    # if not hasattr(get_stock_symbol_from_bse, 'stock_symbol_name_map'): # ugly code, will be rewritten more cleanly
        # get_stock_symbol_from_bse.stock_symbol_name_map = pandas.read_csv('equity_bse.csv', usecols=['Security Name', 'Security Id'])
        
    # matching_mask_startswith = (get_stock_symbol_from_bse.stock_symbol_name_map['Security Name'].str.startswith(company_name))
    # matching_row_startswith = get_stock_symbol_from_bse.stock_symbol_name_map[matching_mask_startswith]
    
    # stock_symbol = None
    # if matching_row_startswith.empty != True:
        # stock_symbol = matching_row_startswith['Security Id'].values[0]
    # else:
        # matching_mask_fuzzy = get_stock_symbol_from_bse.stock_symbol_name_map.apply(lambda x: fuzz.token_sort_ratio(x['Security Name'], company_name), axis=1)
        # qualified_rows = matching_mask_fuzzy[lambda x: x > 75]
        # if qualified_rows.empty != True:
            # best_matching_row = get_stock_symbol_from_bse.stock_symbol_name_map.loc[qualified_rows.idxmax()]
            # stock_symbol = best_matching_row['Security Id']
            
    # if with_suffix == True and stock_symbol is not None:
        # stock_symbol += '.BO'
    
    # print('bse company_name: ' + str(company_name) + ' symbol: ' + str(stock_symbol))
    # return stock_symbol


# def get_stock_symbol(company_name, with_suffix=False):
    # stock_symbol = [get_stock_symbol_from_nse(company_name, with_suffix),
                    # get_stock_symbol_from_bse(company_name, with_suffix)]
    
    # return stock_symbol
    

# def fixup_company_names(transactions_list):    
    # for index, row in fixup_company_names_map.iterrows():
        # print(row['Actual Name'] + ' : ' + row['Fixed Name'])
        # transactions_list.replace({'Name' : row['Actual Name']}, row['Fixed Name'], inplace=True)
        
# def deadjust_price(adjusted_price, stock_symbol, date):
    # print('deadjust_price: ' + 'adjusted_price: ' + str(adjusted_price) + ' stock_symbol: ' + str(stock_symbol) + ' date: ' + str(date))
    
    # if not hasattr(deadjust_price, 'price_adjustment_list'): # ugly code, will be rewritten
        # deadjust_price.price_adjustment_list = pandas.read_csv('split_bonus.csv', parse_dates=['Date'])
        # print('price_adjustment_list:\n' + str(deadjust_price.price_adjustment_list))

    # for symbol in stock_symbol:
        # if symbol is None:
            # continue

        # mask = deadjust_price.price_adjustment_list['Symbol'] == symbol
        # masked_rows = deadjust_price.price_adjustment_list[mask]
        
        # print('masked rows: \n' + str(masked_rows))
        # print('masked rows type: ' + str(type(masked_rows)))
    
        # if masked_rows.empty == False:
            # adjust_date = masked_rows['Date'].values[0]
            # numerator = masked_rows['Numerator'].values[0]
            # denominator = masked_rows['Denominator'].values[0]
            
            # print('adjust date: ' + str(adjust_date) + ' date: ' + str(date))
            # print('date is before split: ' + str(date <= adjust_date))
            
            # print('adjust_date type: ' + str(type(adjust_date)) + ' numerator type: ' + str(type(numerator)) + ' denominator type: ' + str(type(denominator)))
            # print('adjust_date:\n' + str(adjust_date) + '\nnumerator:\n' + str(numerator) + '\ndenominator:\n' + str(denominator))
            
            # if date < adjust_date:
                # deadjusted_price = adjusted_price * numerator / denominator
                # print('symbol: ' + str(symbol) + ' date: ' + str(date) + ' deadjusted_price: ' + str(deadjusted_price))
                # return deadjusted_price
            
    # return adjusted_price
    
# def get_adjusted_closing_price(stock_symbol, date):
    # print('stock_symbol: ' + str(stock_symbol) + ' date: ' + str(date))
    # start_date = pandas.to_datetime(date)
    # end_date = start_date + pandas.Timedelta(days=1)
    
    # for symbol in stock_symbol:
        # print('symbol: ' + str(symbol))
        
        # if symbol is None:
            # continue

        # ticker = yf.Ticker(symbol)
        # print('ticker type:' + str(type(ticker)))
        # exit(11)
        # stock_data = ticker.history(start=start_date, end=end_date)
        
        # if stock_data.empty == False:
            # closing_price = stock_data['Close'].values[0]
            # print('found closing price: ' + str(closing_price))
            # return closing_price
            
    # start_date_one_week_before = start_date - pandas.Timedelta(days=7)
    # end_date_one_week_after = start_date + pandas.Timedelta(days=7)
    
    # for symbol in stock_symbol:
        # if symbol is None:
            # continue

        # ticker = yf.Ticker(symbol)
        # stock_data_two_weeks = ticker.history(start=start_date_one_week_before, end=end_date_one_week_after)
        
        # if stock_data_two_weeks.empty == False:
            # closing_price = stock_data_two_weeks['Close'].mean()
            # print('2 week closing price data:\n' + str(stock_data_two_weeks['Close']))
            # print('closing price from 2 week average: ' + str(closing_price))
            # return closing_price
        
    # if not hasattr(get_adjusted_closing_price, 'renamed_symbols_list'): # ugly code, will be rewritten later
        # get_adjusted_closing_price.renamed_symbols_list = pandas.read_csv('renamed_symbols.csv')
        # print('renamed_symbols_list:\n' + str(get_adjusted_closing_price.renamed_symbols_list))
        
    # for symbol in stock_symbol:
        # if symbol is None:
            # continue
            
        # mask = get_adjusted_closing_price.renamed_symbols_list['Present Symbol'] == symbol
        # masked_rows = get_adjusted_closing_price.renamed_symbols_list[mask]
            
        # print('masked rows: \n' + str(masked_rows))
        # print('masked rows type: ' + str(type(masked_rows)))
        
        # if masked_rows.empty == False:
            # old_symbol = masked_rows['Old Symbol'].values[0]
            # print('old symbol: ' + str(old_symbol))
            # closing_price = get_adjusted_closing_price([old_symbol], date)
            # print('closing price from old symbol: ' + str(closing_price))
            # return closing_price

    # return None


# def get_closing_price(stock_symbol, date):
    # print('date type: ' + str(type(date)))
    # adjusted_closing_price = get_adjusted_closing_price(stock_symbol, date)
    # closing_price = deadjust_price(adjusted_closing_price, stock_symbol, date)
    # return closing_price