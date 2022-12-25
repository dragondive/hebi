from enum import Enum
import logging
from multibeggar import goldenkatora
import pandas
import os

class StockExchange(Enum):
    NSE = "NSE"
    BSE = "BSE"

    def __str__(self):
        return self.value

class CompaniesInfo:
    def __init__(self) -> None:
        # todo self: these log files should be managed better, this is a temporary hack to "reuse" the multibeggar.log
        logging.basicConfig(format='%(levelname)s: %(message)s [%(funcName)s():%(lineno)s - %(asctime)s]',
                            datefmt='%Y/%m/%d %I:%M:%S %p', 
                            handlers=[logging.FileHandler(os.path.join(os.getcwd(), 'multibeggar.log'), mode='w')])
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        golden_katora = goldenkatora.GoldenKatora()
        self.stocks_info_map = {
            StockExchange.BSE: pandas.read_csv(golden_katora.get_cleaned_stocks_data_bse()),
            StockExchange.NSE: pandas.read_csv(golden_katora.get_cleaned_stocks_data_nse())
        }

        print(self.stocks_info_map[StockExchange.BSE])