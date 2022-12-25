"""Helper module for preprocessing and cleanup of data.
"""

import pandas
import os
from flashtext import KeywordProcessor

class GoldenKatora:
    """GoldenKatora provides various helpers to cleanup data for use with multibeggar."""

    def cleanup_stocks_data(self, filename_bsedata: str, filename_nsedata: str):
        """Cleans up companies names in stock data csv file obtained from BSE and NSE.
        
        BSE and NSE provide information about various stocks that can be exported to CSV.
        This method cleans up and standardizes the company names for easier processing
        later by multibeggar.
        
        Args:
            filename_bsedata: full file path of the BSE data CSV file.
            filename_nsedata: full file path of the NSE data CSV file.
        
        Returns:
            CSV files stored in __cache subdirectory, which contains the cleaned up data
            for further processing by multibeggar. These files are meant for internal use
            of multibeggar. Client code should not rely upon it as this implementation
            may change without notice.
        """

        def cleanup_stock_data_bse(company_name: str) -> str:
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

        def cleanup_stock_data_nse(company_name: str, stock_symbol: str) -> str:
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

        cache_filename_bsedata = os.path.join(os.path.dirname(filename_bsedata), "__cache", os.path.basename(filename_bsedata))
        if not os.path.exists(cache_filename_bsedata): # TODO also check if data is newer than cache, so it has to be regenerated
            bse_data = pandas.read_csv(filename_bsedata, index_col=False)

            # We only support Equity presently, so filter out the rest
            bse_data.drop(bse_data[bse_data["Instrument"] != "Equity"].index, inplace=True)

            bse_data["Security Name"] = bse_data["Security Name"].apply(lambda x: cleanup_stock_data_bse(x))

            os.makedirs(os.path.dirname(cache_filename_bsedata), exist_ok=True)
            bse_data.to_csv(cache_filename_bsedata, columns=["Security Name", "Security Id"], header=["Company Name", "Stock Symbol"])

        cache_filename_nsedata = os.path.join(os.path.dirname(filename_nsedata), "__cache", os.path.basename(filename_nsedata))
        if not os.path.exists(cache_filename_nsedata): # TODO also check if data is newer than cache, so it has to be regenerated
            nse_data = pandas.read_csv(filename_nsedata, index_col=False)

            nse_data["NAME OF COMPANY"] = nse_data.apply(lambda x: cleanup_stock_data_nse(x["NAME OF COMPANY"], x["SYMBOL"]), axis=1)

            os.makedirs(os.path.dirname(cache_filename_nsedata), exist_ok=True)
            nse_data.to_csv(cache_filename_nsedata, columns=["NAME OF COMPANY", "SYMBOL"], header=["Company Name", "Stock Symbol"])