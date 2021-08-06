import pandas
import yfinance as yf
from fuzzywuzzy import fuzz


def get_stock_symbol_from_nse(company_name, with_suffix=False):
    if not hasattr(get_stock_symbol_from_nse, 'stock_symbol_name_map'): # ugly code, will be rewritten more cleanly
        get_stock_symbol_from_nse.stock_symbol_name_map = pandas.read_csv('equity_nse.csv', usecols=['SYMBOL', 'NAME OF COMPANY'])
        
    matching_mask_startswith = (get_stock_symbol_from_nse.stock_symbol_name_map['NAME OF COMPANY'].str.startswith(company_name))
    matching_row_startswith = get_stock_symbol_from_nse.stock_symbol_name_map[matching_mask_startswith]
    
    stock_symbol = None
    if matching_row_startswith.empty != True:
        stock_symbol = matching_row_startswith['SYMBOL'].values[0]
    else:
        matching_mask_fuzzy = get_stock_symbol_from_nse.stock_symbol_name_map.apply(lambda x: fuzz.token_sort_ratio(x['NAME OF COMPANY'], company_name), axis=1)
        qualified_rows = matching_mask_fuzzy[lambda x: x > 75]
        if qualified_rows.empty != True:
            best_matching_row = get_stock_symbol_from_nse.stock_symbol_name_map.loc[qualified_rows.idxmax()]
            stock_symbol = best_matching_row['SYMBOL']
            
    if with_suffix == True and stock_symbol is not None:
        stock_symbol += '.NS'
    
    print('nse company_name: ' + str(company_name) + ' symbol: ' + str(stock_symbol))
    return stock_symbol


def get_stock_symbol_from_bse(company_name, with_suffix=False):
    if not hasattr(get_stock_symbol_from_bse, 'stock_symbol_name_map'): # ugly code, will be rewritten more cleanly
        get_stock_symbol_from_bse.stock_symbol_name_map = pandas.read_csv('equity_bse.csv', usecols=['Security Name', 'Security Id'])
        
    matching_mask_startswith = (get_stock_symbol_from_bse.stock_symbol_name_map['Security Name'].str.startswith(company_name))
    matching_row_startswith = get_stock_symbol_from_bse.stock_symbol_name_map[matching_mask_startswith]
    
    stock_symbol = None
    if matching_row_startswith.empty != True:
        stock_symbol = matching_row_startswith['Security Id'].values[0]
    else:
        matching_mask_fuzzy = get_stock_symbol_from_bse.stock_symbol_name_map.apply(lambda x: fuzz.token_sort_ratio(x['Security Name'], company_name), axis=1)
        qualified_rows = matching_mask_fuzzy[lambda x: x > 75]
        if qualified_rows.empty != True:
            best_matching_row = get_stock_symbol_from_bse.stock_symbol_name_map.loc[qualified_rows.idxmax()]
            stock_symbol = best_matching_row['Security Id']
            
    if with_suffix == True and stock_symbol is not None:
        stock_symbol += '.BO'
    
    print('bse company_name: ' + str(company_name) + ' symbol: ' + str(stock_symbol))
    return stock_symbol


def fixup_company_names(transactions_list):
    fixup_company_names_map = pandas.read_csv('fixup_company_names2.csv')
    
    for index, row in fixup_company_names_map.iterrows():
        # print(row['Actual Name'] + ' : ' + row['Fixed Name'])
        transactions_list.replace({'Name' : row['Actual Name']}, row['Fixed Name'], inplace=True)


def get_stock_symbol(company_name, with_suffix=False):
    stock_symbol = [get_stock_symbol_from_nse(company_name, with_suffix),
                    get_stock_symbol_from_bse(company_name, with_suffix)]
    
    return stock_symbol


def get_closing_price(stock_symbol, date):
    print('stock_symbol: ' + str(stock_symbol))
    start_date = pandas.to_datetime(date)
    end_date = start_date + pandas.Timedelta(days=1)
    
    for symbol in stock_symbol:
        print('symbol: ' + str(symbol))
        
        if symbol is None:
            continue

        ticker = yf.Ticker(symbol)
        print('ticker type:' + str(type(ticker)))
        # exit(11)
        stock_data = ticker.history(start=start_date, end=end_date)
        
        if stock_data.empty == False:
            closing_price = stock_data['Close'].values[0]
            print('found closing price: ' + str(closing_price))
            return closing_price
            
    start_date_one_week_before = start_date - pandas.Timedelta(days=7)
    end_date_one_week_after = start_date + pandas.Timedelta(days=7)
    
    for symbol in stock_symbol:
        if symbol is None:
            continue

        ticker = yf.Ticker(symbol)
        stock_data_two_weeks = ticker.history(start=start_date_one_week_before, end=end_date_one_week_after)
        
        if stock_data_two_weeks.empty == False:
            closing_price = stock_data_two_weeks['Close'].mean()
            print('closing price from 2 week average: ' + str(closing_price))
            return closing_price
        
    return None
            
        
    # start_date = pandas.to_datetime(date)
    # end_date = start_date + pandas.Timedelta(days=1)
    # print('stock_symbol: ' + stock_symbol + ' start_date: ' + str(start_date) + ' end_date: ' + str(end_date))
    # print('date type: ' + str(type(date)))
    # # exit(1)
    
    # ticker = yf.Ticker(stock_symbol)
    # stock_data = ticker.history(start=start_date, end=end_date)
    # print(str(stock_data))
    # try:
        # closing_price = stock_data['Close'].values[0]
    # except IndexError:
        # start_date_one_week_before = start_date - pandas.Timedelta(days=7)
        # end_date_one_week_after = start_date + pandas.Timedelta(days=7)
        
        # stock_data_two_weeks = ticker.history(start=start_date_one_week_before, end=end_date_one_week_after)
        # # print('close data type: ' + str(type(stock_data_two_weeks['Close'])))
        # # print('close data:\n' + str(stock_data_two_weeks['Close']))
        
        # closing_price = stock_data_two_weeks['Close'].mean()
    
    # # print('closing_price: ' + str(closing_price))
    # return closing_price
    # # return yf.Ticker(stock_symbol).history(start=start_date, end=end_date)['Close'].values[0]
    
    
# print('close = ' + str(yf.Ticker("BAJFINANCE.NS").history(start="2021-07-01", end="2021-07-02")['Close'].values[0]))

# transactions_list = pandas.read_excel('test3.xlsx')
# fixup_company_names(transactions_list)

# transactions_list.to_excel('test3_after_fixup.xlsx')

# exit(1)

# df.replace({'A': 'b'}, 'e')

# import sys
# sys.stdout = open('test3_log.txt', 'w')

# matched = 0
# not_matched = 0
    
# for index, row in transactions_list.iterrows():
    # name = row['Name']
    
    # symbol = get_stock_symbol(name, with_suffix=True)
    
    # if symbol is not None:
        # print('name: ' + name + ' symbol: ' + symbol)
        # matched += 1
    # else:
        # print('name: ' + name + ' symbol: *** NOT FOUND ***')
        # not_matched += 1

# print('matched: ' + str(matched) + ' not matched: ' + str(not_matched) + ' match ratio: ' + str(matched/(matched + not_matched)))
        
# sys.stdout.close()
