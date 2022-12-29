import os
from multibeggar import multibeggar
from multibeggar import goldenkatora

def multibeggar_use():
    mb = multibeggar.Multibeggar()
    mb.compute_portfolio_complexity(os.path.join(os.path.dirname(__file__), "inputs", "transactions_xs.xlsx"))

if __name__ == "__main__":
    multibeggar_use()