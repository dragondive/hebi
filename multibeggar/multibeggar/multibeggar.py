import logging
import pandas
import os
from math import exp
import numpy
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

        self.exponent_tuning_factor = 0.01 # tuning factor to compute portfolio complexity

        self.__companies_info = dalalstreet.CompaniesInfo()
        self.__transactions_list = pandas.DataFrame()
        self.__all_stock_symbols = [] # all the stock symbols for which the stock provider should fetch the stock data
        self.__company_name_to_stock_symbols_memo = {} # used for memoization in updating the stock symbols from the company name
        self.__stock_prices_provider = None
        self.__date_to_complexity_map = dict() # the portfolio complexity on each date will be updated here
        self.__daywise_full_portfolio = pandas.DataFrame() # all the daywise portfolios will be appended to this DataFrame in order


    def compute_portfolio_complexity(self, transactions_filepath: str, make_plot: bool = True):
        self.__read_and_prepare_transactions_list(transactions_filepath)

        start_date = self.__transactions_list["Date"].iloc[0]
        self.__stock_prices_provider = multichooser.YfinanceStockPricesProvider(self.__all_stock_symbols, start_date)

        self.__compute_daywise_portfolio()

    def __read_and_prepare_transactions_list(self, transactions_filepath: str) -> None:
        self.__transactions_list = pandas.read_excel(transactions_filepath, parse_dates=["Date"])
        goldenkatora.GoldenKatora().clean_transactions_data(self.__transactions_list)

        # obtain the stock symbols for each company name that appears in the transactions list
        self.__transactions_list["Stock Symbol"] = self.__transactions_list.apply(lambda row: self.__get_stock_symbols_memoized(row["Company Name"]), axis=1)

        # sort the transactions by date to ease the computation of daily portfolio
        self.__transactions_list.sort_values(by="Date", inplace=True)

        # append a sentinel row at the end of the transactions list to simplify loop exit condition later
        self.__transactions_list = pandas.concat([self.__transactions_list, pandas.DataFrame([{"Date": "0"}])], ignore_index=True)

    def __compute_daywise_portfolio(self) -> None:
        daily_portfolio = self.__transactions_list.iloc[0:0, :].copy() # create empty DataFrame with same columns at transactions_list
        ongoing_date = None

        for __unused, row in self.__transactions_list.iterrows(): # itertuples() doesn't work here due to spaces in column names
            date = row["Date"]
            if date != ongoing_date: # the date has changed in the transactions list, so daily_portfolio of the current date is complete.
                daily_portfolio.drop(daily_portfolio[daily_portfolio["Shares"] == 0].index, inplace=True) # Remove fully sold holdings from the daily_portfolio

                # Fetch the closing price and compute the values for all the holdings in the daily_portfolio
                daily_portfolio["Closing Price"] = daily_portfolio.apply(lambda row: self.__get_closing_price(row), axis=1, result_type="reduce")
                daily_portfolio["Value"] = daily_portfolio["Shares"] * daily_portfolio["Closing Price"]

                self.__compute_proportions_and_complexity(ongoing_date, daily_portfolio)

                # All computations for the daily_portfolio are completed, so append it now to the daywise_full_portfolio.
                self.__daywise_full_portfolio = pandas.concat([self.__daywise_full_portfolio, daily_portfolio], ignore_index=True)

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

    def __get_stock_symbols_memoized(self, company_name: str) -> list[tuple[str, dalalstreet.StockExchange]]:
        try:
            # first lookup the company name in the memo
            stock_symbols = self.__company_name_to_stock_symbols_memo[company_name]
        except KeyError:
            # if not found in memo, query companies_info and update memo
            stock_symbols = self.__companies_info.get_stock_symbols(company_name)
            self.__company_name_to_stock_symbols_memo[company_name] = stock_symbols
            # also make note of all the known stock symbols to optimize stock data querying later
            self.__all_stock_symbols.extend(stock_symbols)

        return stock_symbols

    def __get_closing_price(self, transaction_row: pandas.Series) -> numpy.float64:
        try:
            return self.__stock_prices_provider.get_closing_price(transaction_row["Stock Symbol"], transaction_row["Date"])
        except multichooser.NoClosingPriceError:
            # If closing price is not available, we do not update it, that is, we use the previous known closing price.
            return transaction_row["Closing Price"]

    def __compute_proportions_and_complexity(self, date: pandas.Timestamp, daily_portfolio: pandas.DataFrame) -> None:
        value_sum = daily_portfolio["Value"].sum()
        try:
            daily_portfolio["Proportion"] = daily_portfolio["Value"] / value_sum
            sorted_proportions = sorted(daily_portfolio["Proportion"].dropna())
            self.__date_to_complexity_map[date] = sum([value * exp(self.exponent_tuning_factor * index) for index, value in enumerate(sorted_proportions)])
        except ZeroDivisionError:
            # this daily_portfolio has no valid value for any holding, so clear it completely.
            # NOTE: removing all rows using, for example, "daily_portfolio = daily_portfolio[0:0]" leads to a strange
            # runtime exception at the start of this method that daily_portfolio is not associated with a value.
            # Hence, use the below alternative instead.
            daily_portfolio.dropna(subset=["Value"], inplace=True)

if __name__ == "__main__":
    multibeggar = Multibeggar()
