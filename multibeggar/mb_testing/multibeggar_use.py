import os
from multibeggar import bahikhata


def multibeggar_use():
    bahikhata_instance = bahikhata.BahiKhata()
    bahikhata_instance.filepath_input_transactions = os.path.join(
        os.path.dirname(__file__), "inputs", "transactions_3xl.xlsx"
    )
    bahikhata_instance.compute_portfolio_complexity()


if __name__ == "__main__":
    multibeggar_use()
