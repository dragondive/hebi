import pandas

def get_stock_symbol_from_nse(company_name, with_suffix=False):
    if not hasattr(get_stock_symbol_from_nse, 'stock_symbol_name_map'): # ugly code, will be rewritten more cleanly
        get_stock_symbol_from_nse.stock_symbol_name_map = pandas.read_csv('equity_nse.csv', usecols=['SYMBOL', 'NAME OF COMPANY'])
    
    matching_mask = (get_stock_symbol_from_nse.stock_symbol_name_map['NAME OF COMPANY'].str.startswith(company_name))
    matching_row = get_stock_symbol_from_nse.stock_symbol_name_map[matching_mask]
    if matching_row.empty == True:
        return None
    
    stock_symbol = matching_row['SYMBOL'].values[0]
    
    if with_suffix == True:
        stock_symbol += ".NS"
        
    return stock_symbol


def get_stock_symbol_from_bse(company_name, with_suffix=False):
    if not hasattr(get_stock_symbol_from_bse, 'stock_symbol_name_map'): # ugly code, will be rewritten more cleanly
        get_stock_symbol_from_bse.stock_symbol_name_map = pandas.read_csv('equity_bse.csv', usecols=['Security Name', 'Security Id'])
    
    matching_mask = (get_stock_symbol_from_bse.stock_symbol_name_map['Security Name'].str.startswith(company_name))
    matching_row = get_stock_symbol_from_bse.stock_symbol_name_map[matching_mask]
    if matching_row.empty == True:
        return None
    
    stock_symbol = matching_row['Security Id'].values[0]
    
    if with_suffix == True:
        stock_symbol += ".BO"
        
    return stock_symbol


def get_stock_symbol(company_name, with_suffix=False):
    stock_symbol = get_stock_symbol_from_nse(company_name, with_suffix)
    if stock_symbol is None:
        stock_symbol = get_stock_symbol_from_bse(company_name, with_suffix)
    
    return stock_symbol

transactions_list = pandas.read_excel('test3.xlsx')

import sys
sys.stdout = open('test3_log.txt', 'w')

matched = 0
not_matched = 0
    
for index, row in transactions_list.iterrows():
    name = row['Name']
    
    symbol = get_stock_symbol(name, with_suffix=True)
    
    if symbol is not None:
        print('name: ' + name + ' symbol: ' + symbol)
        matched += 1
    else:
        print('name: ' + name + ' symbol: *** NOT FOUND ***')
        not_matched += 1

print('matched: ' + str(matched) + ' not matched: ' + str(not_matched) + ' match ratio: ' + str(matched/(matched + not_matched)))
        
sys.stdout.close()
