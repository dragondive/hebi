import logging
import pandas
import os

class Multibeggar:
    def __init__(self) -> None:
        logging.basicConfig(format='%(levelname)s: %(message)s [%(funcName)s():%(lineno)s - %(asctime)s]', 
        datefmt='%Y/%m/%d %I:%M:%S %p', 
        handlers=[logging.FileHandler(os.path.join(os.getcwd(), 'multibeggar.log'), mode='w')])
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

    def compute_portfolio_complexity(self, transactions_filepath: str, make_plot: bool = True):
        transactions_list = pandas.read_excel(transactions_filepath, parse_dates=["Date"])

if __name__ == "__main__":
    multibeggar = Multibeggar()
