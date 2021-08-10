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


def get_adjusted_closing_price(stock_symbol, date):
    print('stock_symbol: ' + str(stock_symbol) + ' date: ' + str(date))
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
            print('2 week closing price data:\n' + str(stock_data_two_weeks['Close']))
            print('closing price from 2 week average: ' + str(closing_price))
            return closing_price
        
    if not hasattr(get_adjusted_closing_price, 'renamed_symbols_list'): # ugly code, will be rewritten later
        get_adjusted_closing_price.renamed_symbols_list = pandas.read_csv('renamed_symbols.csv')
        print('renamed_symbols_list:\n' + str(get_adjusted_closing_price.renamed_symbols_list))
        
    for symbol in stock_symbol:
        if symbol is None:
            continue
            
        mask = get_adjusted_closing_price.renamed_symbols_list['Present Symbol'] == symbol
        masked_rows = get_adjusted_closing_price.renamed_symbols_list[mask]
            
        print('masked rows: \n' + str(masked_rows))
        print('masked rows type: ' + str(type(masked_rows)))
        
        if masked_rows.empty == False:
            old_symbol = masked_rows['Old Symbol'].values[0]
            print('old symbol: ' + str(old_symbol))
            closing_price = get_adjusted_closing_price([old_symbol], date)
            print('closing price from old symbol: ' + str(closing_price))
            return closing_price

    return None


def deadjust_price(adjusted_price, stock_symbol, date):
    print('deadjust_price: ' + 'adjusted_price: ' + str(adjusted_price) + ' stock_symbol: ' + str(stock_symbol) + ' date: ' + str(date))
    
    if not hasattr(deadjust_price, 'price_adjustment_list'): # ugly code, will be rewritten
        deadjust_price.price_adjustment_list = pandas.read_csv('split_bonus.csv', parse_dates=['Date'])
        print('price_adjustment_list:\n' + str(deadjust_price.price_adjustment_list))

    for symbol in stock_symbol:
        if symbol is None:
            continue

        mask = deadjust_price.price_adjustment_list['Symbol'] == symbol
        masked_rows = deadjust_price.price_adjustment_list[mask]
        
        print('masked rows: \n' + str(masked_rows))
        print('masked rows type: ' + str(type(masked_rows)))
    
        if masked_rows.empty == False:
            adjust_date = masked_rows['Date'].values[0]
            numerator = masked_rows['Numerator'].values[0]
            denominator = masked_rows['Denominator'].values[0]
            
            # print('adjust date: ' + str(adjust_date) + ' date: ' + str(date))
            # print('date is before split: ' + str(date <= adjust_date))
            
            # print('adjust_date type: ' + str(type(adjust_date)) + ' numerator type: ' + str(type(numerator)) + ' denominator type: ' + str(type(denominator)))
            # print('adjust_date:\n' + str(adjust_date) + '\nnumerator:\n' + str(numerator) + '\ndenominator:\n' + str(denominator))
            
            if date < adjust_date:
                deadjusted_price = adjusted_price * numerator / denominator
                print('symbol: ' + str(symbol) + ' date: ' + str(date) + ' deadjusted_price: ' + str(deadjusted_price))
                return deadjusted_price
            
    return adjusted_price


def get_closing_price(stock_symbol, date):
    print('date type: ' + str(type(date)))
    adjusted_closing_price = get_adjusted_closing_price(stock_symbol, date)
    closing_price = deadjust_price(adjusted_closing_price, stock_symbol, date)
    return closing_price
