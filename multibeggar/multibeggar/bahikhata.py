import logging
import os


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
        self.cache_dir = os.path.join(self.data_dir, "__cache")
        os.makedirs(self.cache_dir, exist_ok=True)

        self.filepath_bsedata = os.path.join(self.data_dir, "bse_securities.csv")
        self.filepath_nsedata = os.path.join(self.data_dir, "nse_securities.csv")
        self.filepath_cache_bsedata = os.path.join(self.cache_dir, "bse_securities.csv")
        self.filepath_cache_nsedata = os.path.join(self.cache_dir, "nse_securities.csv")

        self.filepath_full_portfolio = os.path.join(self.output_dir, "full_portfolio.xlsx")


log = BahiKhata().logger
