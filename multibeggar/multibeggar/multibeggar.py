import logging
import pandas
import os
from multibeggar import dalalstreet

class Multibeggar:
    def __init__(self) -> None:
        logging.basicConfig(format='%(levelname)s: %(message)s [%(funcName)s():%(lineno)s - %(asctime)s]', 
        datefmt='%Y/%m/%d %I:%M:%S %p', 
        handlers=[logging.FileHandler(os.path.join(os.getcwd(), 'multibeggar.log'), mode='w')])
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        self.companies_info = dalalstreet.CompaniesInfo()

    def compute_portfolio_complexity(self, transactions_filepath: str, make_plot: bool = True):
        all_stock_symbols = []
        company_name_to_stock_symbols_memo = {}
        def get_stock_symbols_memoized(company_name):
            try:
                # first lookup the company name in the memo
                stock_symbols = company_name_to_stock_symbols_memo[company_name]
            except KeyError:
                # if not found in memo, query companies_info and update memo
                # Capitalize company names for easier matching
                stock_symbols = self.companies_info.get_stock_symbols(company_name.upper())
                company_name_to_stock_symbols_memo[company_name] = stock_symbols

                # also make note of all the known stock symbols to optimize stock data querying later
                all_stock_symbols.extend(stock_symbols)

            return stock_symbols

        transactions_list = pandas.read_excel(transactions_filepath, parse_dates=["Date"])

        transactions_list["Stock Symbol"] = transactions_list.apply(lambda row: self.companies_info.get_stock_symbols(row["Company Name"].upper()), axis=1)

        transactions_list.sort_values(by="Date", inplace=True)
        # append a sentinel row at the end of the transactions list to simplify loop exit condition later
        transactions_list = pandas.concat([transactions_list, pandas.DataFrame([{"Date": "0"}])], ignore_index=True)

if __name__ == "__main__":
    multibeggar = Multibeggar()
