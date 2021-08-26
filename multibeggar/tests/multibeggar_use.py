from multibeggar.multibeggar import Multibeggar
import os

mb = Multibeggar()
mb.load_transactions_from_excel_file(os.path.join(os.getcwd(), 'input', 'test_transactions_list_closing_price_unavailable_for_some_dates.xlsx'))
mb.plot_portfolio_complexity()

# mb.get_nse_symbol('Motilal Oswal MOSt Shares NASDAQ-100 ETF')