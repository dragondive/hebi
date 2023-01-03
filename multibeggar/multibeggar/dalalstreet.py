import re
from enum import Enum
import pandas
from fuzzywuzzy import fuzz
from multibeggar import goldenkatora
from multibeggar import bahikhata


class StockExchange(Enum):
    """Stock exchanges supported by multibeggar."""

    BSE = "BSE"  # Bombay Stock Exchange
    NSE = "NSE"  # National Stock Exchange

    def __str__(self):
        return self.value


class CompaniesInfo:
    def __init__(self) -> None:
        golden_katora = goldenkatora.GoldenKatora()
        bahi_khata = bahikhata.BahiKhata()
        self.stock_exchange_to_info_map = {
            StockExchange.BSE: pandas.read_csv(golden_katora.get_cleaned_stocks_data_bse()),
            StockExchange.NSE: pandas.read_csv(golden_katora.get_cleaned_stocks_data_nse()),
        }

        self.symbol_change_map = pandas.read_csv(bahi_khata.filepath_symbol_change)
        self.__compute_price_adjustment_map(
            bahi_khata.filepath_bonus_issues, bahi_khata.filepath_stock_splits
        )

    def get_stock_symbols(self, company_name) -> list[tuple[str, StockExchange]]:
        """Get known stock symbols of the company on the supported stock exchanges.

        Args:
            company_name: Name of the company

        Returns:
            - List of tuples consisting the known stock symbols and the respective stock exchange
            - Empty list if no stock symbol is found on any supported stock exchange
        """
        symbol_list = [
            (symbol, stock_exchange)
            for stock_exchange in self.stock_exchange_to_info_map
            if (symbol := self.get_stock_symbol(company_name, stock_exchange)) is not None
        ]

        # Search in the symbol change data for the New Symbol. If it is found, then append the old
        # symbols as well to the list of symbols for this company name. Some stock data providers
        # may refer to the old symbol to provide the data.
        #
        # NOTE: I'm not sure if the below list comprehension is the best or the worst of the
        #  walrus operator! Is this even pythonic? ;-)
        renamed_symbol_list = [
            (search_renamed_symbol["Old Symbol"].array[0], stock_exchange)
            for (symbol, stock_exchange) in symbol_list
            if not (
                search_renamed_symbol := self.symbol_change_map[
                    self.symbol_change_map["New Symbol"] == symbol
                ]
            ).empty
        ]
        symbol_list.extend(renamed_symbol_list)
        return symbol_list

    def get_stock_symbol(self, company_name: str, exchange_name: StockExchange) -> str:
        """Get known stock symbol of the company on the stock exchange.

        Args:
            company_name: Name of the company
            exchange_name: Enum StockExchange representing the supported stock exchange

        Returns:
            - Stock symbol of the company on the stock exchange
            - None if stock symbol of the company is not found
        """

        def search_exact_match():
            """Searches for the exactly matching company name in stock exchange data."""
            company_name_to_symbol_map = self.stock_exchange_to_info_map[exchange_name]
            matching_mask = company_name_to_symbol_map["Company Name"] == company_name
            matching_row = company_name_to_symbol_map[matching_mask]
            return matching_row["Stock Symbol"].array

        def search_best_match():
            """Performs fuzzy search for the company name in stock exchange data."""
            company_name_to_symbol_map = self.stock_exchange_to_info_map[exchange_name]

            # optimization to fuzzy match with only a reduced subset of the companies
            # whose names start with the first word of the company name in transactions list
            company_name_to_symbol_map_reduced = company_name_to_symbol_map[
                company_name_to_symbol_map["Company Name"].str.startswith(company_name.split()[0])
            ]
            match_ratios = company_name_to_symbol_map_reduced.apply(
                lambda row: fuzz.token_sort_ratio(row["Company Name"], company_name),
                axis=1,
            )
            qualified_rows = match_ratios[lambda match_ratio: match_ratio >= 75]

            try:
                best_matching_row = company_name_to_symbol_map_reduced.loc[qualified_rows.idxmax()]
            except ValueError:
                return None  # TODO raise exception instead
            else:
                return best_matching_row["Stock Symbol"]

        # First search for exactly matching company name. Try fuzzy matching only if exact match
        # is not found. This small optimization avoids fuzzy matching against all the companies in
        # the stock exchange data if not necessary.
        symbol_list = search_exact_match()
        if len(symbol_list) == 1:
            return symbol_list[0]
        else:
            return search_best_match()

    def get_price_adjustment_data(
        self, stock_symbol: str, date: pandas.Timestamp
    ) -> pandas.DataFrame:
        return self.price_adjustment_map[
            (self.price_adjustment_map["Security Name"] == stock_symbol)
            & (self.price_adjustment_map["Ex Date"] > date)
        ]

    def __compute_price_adjustment_map(
        self, filepath_bonus_issues: str, filepath_stock_splits: str
    ) -> None:
        """Computes the price adjustment multipliers due to bonus issues and stock splits.

        The bonus issues and stock splits data is available from BSE in a csv file.
        This method uses regex parsing to extract the required information from these data files.
        Then it computes the multiplier factor to "reverse" the stock price adjustment, which would
        help in computing the actual values of that stock holding on dates before the bonus issue or
        stock split happened.

        When stock data providers are queried for the stock price, they usually provide the
        "adjusted" stock price to account for the bonus issues or stock splits that happened on
        future dates. Hence, to determine the actual price of the stock on the given date, we need
        to "reverse" this adjustment.

        This can be better explained with an example as below:

        Suppose an investor purchased 10 shares of ABCD company on 2017-01-01 at ₹ 1500 each.
        Hence, total investment was ₹ 15000 (₹1500 x 10).

        On 2018-01-01, ABCD company issued bonus shares in the ratio 1:2. This means, for
        every 1 share that the investor owns, he/she will receive 2 additional shares for free.
        The share price is adjusted accordingly. (For simplicity of explanation, throughout this
        example, ignore the fluctuations in the share price, and assume them to remain constant
        at the purchase price.) Hence, after the bonus issue, there are now 3x number of shares
        of company ABCD. The share price gets adjusted to ₹ 500 (₹ 1500 / 3).

        If we now query a stock data provider for the price of the ABCD company stock as
        on 2017-06-01, it will return the price as ₹ 500, adjusting for the bonus issue event that
        happened later. However, on the actual day 2017-06-01, the stock price was indeed ₹ 1500.
        Hence, the multiplier to reverse the price adjustment in case of bonus issue 1:2 would be
        (1 + 2)/1 == 3. More generally, for a bonus issue of M:N, the multiplier is (M + N)/N.

        Later, on 2019-01-01, ABCD company decided to split the stock, so that the face value
        changed from ₹ 10 to ₹ 2, that is, each stock is now split into 5 stocks. Thus, every
        investor now owns 5x number of stocks. The stock price now changes from ₹ 500 to ₹ 100.
        Once again, we need the multiplier to "reverse" the adjusted price,
        which would be 5 (₹ 10/₹ 2). More generally, for a stock split that changes the face value
        from ₹ N to ₹ M, the multiplier is N/M.
        """

        def extract_bonus_data(bonus_purpose_info: pandas.Series) -> float:
            match = re.search(r"Bonus issue (?P<first>\d+):(?P<second>\d+)", bonus_purpose_info)
            return (int(match["first"]) + int(match["second"])) / int(match["second"])

        bonus_issues_data = pandas.read_csv(
            filepath_bonus_issues,
            usecols=["Security Name", "Ex Date", "Purpose"],
            parse_dates=["Ex Date"],
        )
        bonus_issues_data = bonus_issues_data[
            bonus_issues_data["Purpose"].str.contains("Bonus issue")
        ]
        bonus_issues_data["Multiplier"] = bonus_issues_data["Purpose"].apply(extract_bonus_data)
        bonus_issues_data["Action Type"] = "Bonus"

        def extract_splits_data(split_purpose_info: pandas.Series) -> float:
            match = re.search(
                r"Stock  Split From Rs.(?P<first>\d+)/- to Rs.(?P<second>\d+)/-",
                split_purpose_info,
            )
            return int(match["first"]) / int(match["second"])

        stock_splits_data = pandas.read_csv(
            filepath_stock_splits,
            usecols=["Security Name", "Ex Date", "Purpose"],
            parse_dates=["Ex Date"],
        )
        stock_splits_data = stock_splits_data[
            stock_splits_data["Purpose"].str.contains("Stock  Split")
        ]
        stock_splits_data["Multiplier"] = stock_splits_data["Purpose"].apply(extract_splits_data)
        stock_splits_data["Action Type"] = "Split"

        self.price_adjustment_map = pandas.concat(
            [
                bonus_issues_data[["Security Name", "Ex Date", "Multiplier", "Action Type"]],
                stock_splits_data[["Security Name", "Ex Date", "Multiplier", "Action Type"]],
            ]
        )
        self.price_adjustment_map.sort_values(by=["Security Name", "Ex Date"], inplace=True)
