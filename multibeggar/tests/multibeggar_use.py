from multibeggar.multibeggar import Multibeggar
import os

mb = Multibeggar()
mb.load_transactions_from_excel_file(os.path.join(os.getcwd(), 'input', 'test_transactions_list_small.xlsx'))
mb.plot_portfolio_complexity()