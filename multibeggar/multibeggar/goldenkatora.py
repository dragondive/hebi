"""Helper module for preprocessing and cleanup of data.
"""

import pandas
import os
from flashtext import KeywordProcessor

class GoldenKatora:
    """GoldenKatora provides various helpers to cleanup data for use with multibeggar."""
    def __init__(self) -> None:
        data_dir = os.path.join(os.path.dirname(__file__), "data")
        self.filepath_bsedata = os.path.join(data_dir, "bse_securities.csv")
        self.filepath_nsedata = os.path.join(data_dir, "nse_securities.csv")

        cache_dir = os.path.join(data_dir, "__cache")
        os.makedirs(cache_dir, exist_ok=True)
        self.cache_filepath_bsedata = os.path.join(cache_dir, "bse_securities.csv")
        self.cache_filepath_nsedata = os.path.join(cache_dir, "nse_securities.csv")

    def get_cleaned_stocks_data_bse(self) -> str:
        """Returns path to the cleaned BSE stocks data CSV file.

        Args:
            None

        Returns:
            Path to the CSV file where cleaned BSE stocks data is stored.
        """
        if not os.path.exists(self.cache_filepath_bsedata):
            self.clean_stocks_data_bse()

        return self.cache_filepath_bsedata

    def clean_stocks_data_bse(self):
        """Cleans up companies names in stock data CSV file obtained from BSE.

        This method cleans up and standardizes the company names for easier processing
        later by multibeggar.

        The client code must access the cleaned stocks data through `get_cleaned_stocks_data_bse()` only.
        """

        def cleanup_company_name_bse(company_name: str) -> str:
            """Helper inner method to cleanup the company name in BSE data
            """
            # convert to uppercase for better name matching in multibeggar
            company_name = company_name.upper()

            # Remove "Limited", "Ltd", etc. for better name matching in multibeggar
            # NOTE: (WORKAROUND) flashtext requires the keywords to be mapped to a non-empty string.
            # It replaces the keywords with the mapped non-empty string.
            # Hence, map the unwanted keywords to a single space, which we will trim in next step.
            keyword_processor = KeywordProcessor()
            remove_keywords_dict = { " ": ["LTD", "LTD.", "LTD-$", "LTD.-$", "LIMITED", "LIMITED-$"] }
            keyword_processor.add_keywords_from_dict(remove_keywords_dict)

            # NOTE: The below pythonic one-liner " ".join(x.split()) replaces multiple spaces in x with a single space.
            company_name = " ".join(keyword_processor.replace_keywords(company_name).split())
            return company_name

        bse_data = pandas.read_csv(self.filepath_bsedata, index_col=False)

        # We only support Equity presently, so filter out the rest
        bse_data.drop(bse_data[bse_data["Instrument"] != "Equity"].index, inplace=True)

        bse_data["Security Name"] = bse_data["Security Name"].apply(lambda x: cleanup_company_name_bse(x))

        bse_data.to_csv(self.cache_filepath_bsedata, columns=["Security Name", "Security Id"], header=["Company Name", "Stock Symbol"])

    def get_cleaned_stocks_data_nse(self) -> str:
        """Returns path to the cleaned NSE stocks data CSV file.

        Args:
            None

        Returns:
            Path to the CSV file where cleaned NSE stocks data is stored.
        """
        if not os.path.exists(self.cache_filepath_nsedata):
            self.clean_stocks_data_nse()

        return self.cache_filepath_nsedata

    def clean_stocks_data_nse(self):
        """Cleans up companies names in stock data CSV file obtained from NSE.

        This method cleans up and standardizes the company names for easier processing
        later by multibeggar.

        The client code must access the cleaned stocks data through `get_cleaned_stocks_data_nse()` only.
        """

        def cleanup_company_name_nse(company_name: str, stock_symbol: str) -> str:
            """Helper inner method to cleanup the company name in NSE data
            """
            # convert to uppercase for better name matching in multibeggar
            company_name = company_name.upper()

            # Remove "Limited" for better name matching in multibeggar
            # NOTE: (WORKAROUND) flashtext requires the keywords to be mapped to a non-empty string.
            # It replaces the keywords with the mapped non-empty string.
            # Hence, map the unwanted keywords to a single space, which we will trim in next step.
            keyword_processor = KeywordProcessor()
            remove_keywords_dict = { " ": ["LIMITED"] }
            keyword_processor.add_keywords_from_dict(remove_keywords_dict)

            # NOTE: The below pythonic one-liner " ".join(x.split()) replaces multiple spaces in x with a single space.
            company_name = " ".join(keyword_processor.replace_keywords(company_name).split())

            # NSE list the same company name for DVR stocks and normal stocks, so we modify the company name
            # for the DVR stocks to enable better name matching in multibeggar.
            if "DVR" in stock_symbol:
                company_name += " DVR"

            return company_name

        nse_data = pandas.read_csv(self.filepath_nsedata, index_col=False)

        nse_data["NAME OF COMPANY"] = nse_data.apply(lambda x: cleanup_company_name_nse(x["NAME OF COMPANY"], x["SYMBOL"]), axis=1)

        nse_data.to_csv(self.cache_filepath_nsedata, columns=["NAME OF COMPANY", "SYMBOL"], header=["Company Name", "Stock Symbol"])
