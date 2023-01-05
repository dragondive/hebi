import os
import logging.config
import pandas
from multibeggar import goldenkatora
from multibeggar import dalalstreet
from multibeggar import multibeggar


class BahiKhata:
    def __init__(self) -> None:
        self.filepath_input_transactions = None
        self.output_dir = os.path.join(os.getcwd(), "outputs")
        self.filepath_full_portfolio = os.path.join(self.output_dir, "full_portfolio.xlsx")

        os.makedirs(os.path.join(self.output_dir), exist_ok=True)
        logging.basicConfig(
            format="%(message)s [%(module)s.%(funcName)s():%(lineno)s] %(levelname)s",
            level=logging.DEBUG,
            handlers=[
                logging.FileHandler(os.path.join(self.output_dir, "multibeggar.log"), mode="w")
            ],
        )

        self.__data_dir = os.path.join(os.path.dirname(__file__), "data")

        self.__filepath_bsedata = os.path.join(self.__data_dir, "bse_securities.csv")
        self.__filepath_nsedata = os.path.join(self.__data_dir, "nse_securities.csv")
        self.__filepath_bonus_issues = os.path.join(self.__data_dir, "bonus_issues.csv")
        self.__filepath_stock_splits = os.path.join(self.__data_dir, "stock_splits.csv")
        self.__filepath_symbol_change = os.path.join(self.__data_dir, "symbol_change.csv")

        self.__cache_dir = os.path.join(self.__data_dir, "__cache")
        os.makedirs(self.__cache_dir, exist_ok=True)
        self.__filepath_cache_bsedata = os.path.join(self.__cache_dir, "bse_securities.csv")
        self.__filepath_cache_nsedata = os.path.join(self.__cache_dir, "nse_securities.csv")

        self.__init_cache_stock_data()
        self.__companies_info = self.__init_companies_info()

    def __init_cache_stock_data(self):
        golden_katora = goldenkatora.GoldenKatora()

        if not os.path.exists(self.__filepath_cache_bsedata):
            bse_data = pandas.read_csv(self.__filepath_bsedata, index_col=False)
            cleaned_bse_data = golden_katora.get_cleaned_stocks_data_bse(bse_data)
            cleaned_bse_data.to_csv(self.__filepath_cache_bsedata)

        if not os.path.exists(self.__filepath_cache_nsedata):
            nse_data = pandas.read_csv(self.__filepath_nsedata, index_col=False)
            cleaned_nse_data = golden_katora.get_cleaned_stocks_data_nse(nse_data)
            cleaned_nse_data.to_csv(self.__filepath_cache_nsedata)

    def __init_companies_info(self):
        bse_companies_data = pandas.read_csv(self.__filepath_cache_bsedata)
        nse_companies_data = pandas.read_csv(self.__filepath_cache_nsedata)
        bonus_issues_data = pandas.read_csv(
            self.__filepath_bonus_issues,
            usecols=["Security Name", "Ex Date", "Purpose"],
            parse_dates=["Ex Date"],
        ).rename(columns={"Security Name": "Company Name"})
        stock_splits_data = pandas.read_csv(
            self.__filepath_stock_splits,
            usecols=["Security Name", "Ex Date", "Purpose"],
            parse_dates=["Ex Date"],
        ).rename(columns={"Security Name": "Company Name"})
        symbol_change_data = pandas.read_csv(self.__filepath_symbol_change)
        return dalalstreet.CompaniesInfo(
            bse_companies_data,
            nse_companies_data,
            bonus_issues_data,
            stock_splits_data,
            symbol_change_data,
        )

    def compute_portfolio_complexity(self):
        if self.filepath_input_transactions is None or not os.path.exists(
            self.filepath_input_transactions
        ):
            raise InvalidInputFileException

        multibeggar_instance = multibeggar.Multibeggar(self.__companies_info)
        multibeggar_instance.compute_portfolio_complexity(self.filepath_input_transactions)


class InvalidInputFileException(Exception):
    pass
