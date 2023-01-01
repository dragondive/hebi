import os
from multibeggar import multibeggar


def multibeggar_use():
    multibeggar_instance = multibeggar.Multibeggar()
    multibeggar_instance.compute_portfolio_complexity(
        os.path.join(os.path.dirname(__file__), "inputs", "transactions_xs.xlsx")
    )


if __name__ == "__main__":
    multibeggar_use()
