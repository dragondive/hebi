import os
from multibeggar import multibeggar

def multibeggar_use():
    mb = multibeggar.Multibeggar()
    mb.compute_portfolio_complexity(os.path.join(os.getcwd(), "inputs", "transactions_3xl.xlsx"))
