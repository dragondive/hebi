import os
from multibeggar.multibeggar import Multibeggar

mb = Multibeggar()
mb.load_transactions_from_excel_file(os.path.join(os.getcwd(), 'input', 'test_uppercase_mismatches.xlsx'))
mb.plot_portfolio_complexity()

mb.get_nse_symbol('Motilal Oswal MOSt Shares NASDAQ-100 ETF')

from fuzzywuzzy import fuzz

# company_name = 'HEG'
# company_name_in_data = 'HEG LTD.'
# match = fuzz.token_sort_ratio(company_name_in_data, company_name)
# print(match)