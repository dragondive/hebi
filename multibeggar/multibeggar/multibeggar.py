import logging
import pandas
import os
from multibeggar import dalalstreet
from multibeggar import multichooser
from multibeggar import goldenkatora

class Multibeggar:
    def __init__(self) -> None:
        logging.basicConfig(format='%(levelname)s: %(message)s [%(funcName)s():%(lineno)s - %(asctime)s]', 
        datefmt='%Y/%m/%d %I:%M:%S %p', 
        handlers=[logging.FileHandler(os.path.join(os.getcwd(), 'multibeggar.log'), mode='w')])
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        self.companies_info = dalalstreet.CompaniesInfo()

    def compute_portfolio_complexity(self, transactions_filepath: str, make_plot: bool = True):
        transactions_list = pandas.DataFrame()
        all_stock_symbols = []

        def read_and_prepare_transactions_list():
            company_name_to_stock_symbols_memo = {}
            def get_stock_symbols_memoized(company_name):
                try:
                    # first lookup the company name in the memo
                    stock_symbols = company_name_to_stock_symbols_memo[company_name]
                except KeyError:
                    # if not found in memo, query companies_info and update memo
                    # Capitalize company names for easier matching
                    stock_symbols = self.companies_info.get_stock_symbols(company_name)
                    company_name_to_stock_symbols_memo[company_name] = stock_symbols

                    # also make note of all the known stock symbols to optimize stock data querying later
                    all_stock_symbols.extend(stock_symbols)

                return stock_symbols

            nonlocal transactions_list, all_stock_symbols
            transactions_list = pandas.read_excel(transactions_filepath, parse_dates=["Date"])
            goldenkatora.GoldenKatora().clean_transactions_data(transactions_list)

            # obtain the stock symbols for each company name that appears in the transactions list
            transactions_list["Stock Symbol"] = transactions_list.apply(lambda row: get_stock_symbols_memoized(row["Company Name"]), axis=1)

            # sort the transactions by date to ease the computation of daily portfolio
            transactions_list.sort_values(by="Date", inplace=True)

            # append a sentinel row at the end of the transactions list to simplify loop exit condition later
            transactions_list = pandas.concat([transactions_list, pandas.DataFrame([{"Date": "0"}])], ignore_index=True)
            # transactions_list.to_excel("out.xlsx")

        read_and_prepare_transactions_list()

        start_date = transactions_list["Date"].iloc[0]
        stock_prices_provider = multichooser.YfinanceStockPricesProvider(all_stock_symbols, start_date)

        def compute_daywise_portfolio():
            ongoing_date = None
            daily_portfolio = transactions_list.iloc[0:0, :].copy() # create empty DataFrame with same columns at transactions_list
            daywise_full_portfolio = pandas.DataFrame() # all the daywise portfolios will be appended to this DataFrame in order

            for __unused, row in transactions_list.iterrows(): # itertuples() doesn't work here due to spaces in column names
                date = row["Date"]

                if date != ongoing_date: # this is a new date, so finalize the current daily_portfolio, then append to daywise_full_portfolio
                    daily_portfolio.drop(daily_portfolio[daily_portfolio["Shares"] == 0].index, inplace=True) # Remove fully sold holdings from the daily_portfolio

                    # TODO compute the closing prices for all the holdings in the daily portfolio, then the proportions of holdings value.
                    daily_portfolio["Closing Price"] = daily_portfolio.apply(lambda row: stock_prices_provider.get_closing_price(row["Stock Symbol"], row["Date"]), axis=1, result_type="reduce")
                    daywise_full_portfolio = pandas.concat([daywise_full_portfolio, daily_portfolio], ignore_index=True)

                    # Reuse the daily_portfolio for this new date. The transactions on this new date will update the total shares
                    # as on the earlier date. Hence, it easier to find the total shares/units for each company in the daily_portfolio
                    # of the earlier date, as against looking it up again in the daily_full_portfolio.
                    daily_portfolio.replace({ongoing_date: date}, inplace=True)

                    ongoing_date = date # The earlier date is not required any more, so make this new date as the ongoing date now.

                company_name = row["Company Name"]
                matching_mask = daily_portfolio["Company Name"] == company_name
                matching_row = daily_portfolio[matching_mask] # search this company in current daily_portfolio

                if matching_row.empty:  # this company doesn't already exist in the daily_portfolio, so append it as a new row
                    daily_portfolio = pandas.concat([daily_portfolio, row.to_frame().T], ignore_index=True)
                else: # this company already exists in the daily_portfolio, so update its total shares count
                    transacted_shares = row["Shares"]
                    daily_portfolio.loc[matching_mask, "Shares"] += transacted_shares

            daywise_full_portfolio.to_excel("daywise_full.xlsx")

        compute_daywise_portfolio()

if __name__ == "__main__":
    multibeggar = Multibeggar()
