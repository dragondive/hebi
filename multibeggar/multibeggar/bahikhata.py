import os
import logging
import pandas
from multibeggar import goldenkatora


class BahiKhata:
    def __init__(self) -> None:
        self.output_dir = os.path.join(os.getcwd(), "outputs")
        os.makedirs(os.path.join(self.output_dir), exist_ok=True)
        self.logger = logging
        self.logger.basicConfig(
            format="%(message)s [%(module)s.%(funcName)s():%(lineno)s] %(levelname)s",
            level=logging.DEBUG,
            handlers=[
                logging.FileHandler(os.path.join(self.output_dir, "multibeggar.log"), mode="w")
            ],
        )

        self.data_dir = os.path.join(os.path.dirname(__file__), "data")

        self.filepath_bsedata = os.path.join(self.data_dir, "bse_securities.csv")
        self.filepath_nsedata = os.path.join(self.data_dir, "nse_securities.csv")
        self.filepath_symbol_change = os.path.join(self.data_dir, "symbol_change.csv")
        self.filepath_bonus_issues = os.path.join(self.data_dir, "bonus_issues.csv")
        self.filepath_stock_splits = os.path.join(self.data_dir, "stock_splits.csv")

        self.cache_dir = os.path.join(self.data_dir, "__cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        self.filepath_cache_bsedata = os.path.join(self.cache_dir, "bse_securities.csv")
        self.filepath_cache_nsedata = os.path.join(self.cache_dir, "nse_securities.csv")

        self.init_cache_stock_data()

        self.filepath_full_portfolio = os.path.join(self.output_dir, "full_portfolio.xlsx")

    def init_cache_stock_data(self):
        golden_katora = goldenkatora.GoldenKatora()

        if not os.path.exists(self.filepath_cache_bsedata):
            bse_data = pandas.read_csv(self.filepath_bsedata, index_col=False)
            cleaned_bse_data = golden_katora.get_cleaned_stocks_data_bse(bse_data)
            cleaned_bse_data.to_csv(self.filepath_cache_bsedata)

        if not os.path.exists(self.filepath_cache_nsedata):
            nse_data = pandas.read_csv(self.filepath_nsedata, index_col=False)
            cleaned_nse_data = golden_katora.get_cleaned_stocks_data_nse(nse_data)
            cleaned_nse_data.to_csv(self.filepath_cache_nsedata)

log = BahiKhata().logger
