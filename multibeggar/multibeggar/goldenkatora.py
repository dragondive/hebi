"""Helper module for preprocessing and cleanup of data.
"""
import os
import pandas
from flashtext import KeywordProcessor
from PIL import Image


class GoldenKatora:
    """GoldenKatora provides various helpers to cleanup data for use with multibeggar."""

    def __init__(self) -> None:
        pass

    def get_cleaned_stocks_data_bse(self, bse_data: pandas.DataFrame) -> pandas.DataFrame:
        """Cleans up companies names in stock data CSV file obtained from BSE.

        This method cleans up and standardizes the company names for easier processing
        later by multibeggar.

        Args:
            bse_data: Stocks data obtained from BSE.

        Returns:
            DataFrame with the cleaned up data.
        """

        def cleanup_company_name_bse(company_name: str) -> str:
            """Helper inner method to cleanup the company name in BSE data."""
            # convert to uppercase for better name matching in multibeggar
            company_name = company_name.upper()

            # remove parenthesis for better name matching in multibeggar
            company_name = company_name.translate({ord(x): None for x in "()"})

            # Remove "Limited", "Ltd", etc. for better name matching in multibeggar
            # RANT: Why are they so lazy with their data entries?
            # NOTE: (WORKAROUND) flashtext requires the keywords to be mapped to a non-empty string.
            # It replaces the keywords with the mapped non-empty string.
            # Hence, map the unwanted keywords to a single space, which we will trim in next step.
            #
            # replace & with AND for better name matching in multibeggar.
            # NOTE: This replacement only happens when & is separated by space on both sides,
            # hence, names like S&P will not be affected.
            keyword_processor = KeywordProcessor()
            remove_keywords_dict = {
                " ": ["LTD", "LTD.", "LTD-$", "LTD.-$", "LIMITED", "LIMITED-$", "THE"],
                "AND": ["&"],
            }
            keyword_processor.add_keywords_from_dict(remove_keywords_dict)
            company_name = keyword_processor.replace_keywords(company_name)

            # Call the flashtext replace_keyword again to replace "CO." and "CORP.".
            # The replacement doesn't properly happen when combined into the above call because some
            # company names have "CO.LTD.", "CORP.LTD.", etc. (without spaces after CO. or CORP.),
            # so these are not considered as keywords for replacement. Strangely this doesn't
            # affect the "LTD." though.
            remove_keywords_dict = {"COMPANY": ["CO."], "CORPORATION": ["CORP."]}
            keyword_processor.add_keywords_from_dict(remove_keywords_dict)
            company_name = keyword_processor.replace_keywords(company_name)

            # NOTE: The below pythonic one-liner " ".join(x.split()) replaces multiple spaces in x
            # with a single space.
            company_name = " ".join(company_name.split())

            # strip any leading and trailing spaces that the previous steps may have introduced
            company_name = company_name.strip()

            return company_name

        # We only support Equity presently, so filter out the rest
        bse_data.drop(bse_data[bse_data["Instrument"] != "Equity"].index, inplace=True)

        bse_data["Security Name"] = bse_data["Security Name"].apply(cleanup_company_name_bse)
        return bse_data[["Security Name", "Security Id"]].rename(
            columns={"Security Name": "Company Name", "Security Id": "Stock Symbol"}
        )

    def get_cleaned_stocks_data_nse(self, nse_data: pandas.DataFrame) -> pandas.DataFrame:
        """Cleans up companies names in stock data CSV file obtained from NSE.

        This method cleans up and standardizes the company names for easier processing
        later by multibeggar.

        Args:
            bse_data: Stocks data obtained from NSE.

        Returns:
            DataFrame with the cleaned up data.
        """

        def cleanup_company_name_nse(company_name: str, stock_symbol: str) -> str:
            """Helper inner method to cleanup the company name in NSE data"""
            # convert to uppercase for better name matching in multibeggar
            company_name = company_name.upper()

            # remove parenthesis for better name matching in multibeggar
            company_name = company_name.translate({ord(x): None for x in "()"})

            # Remove "Limited", "The", etc. for better name matching in multibeggar
            # NOTE: (WORKAROUND) flashtext requires the keywords to be mapped to a non-empty string.
            # It replaces the keywords with the mapped non-empty string.
            # Hence, map the unwanted keywords to a single space, which we will trim in next step.
            #
            # replace & with AND for better name matching in multibeggar.
            # NOTE: This replacement only happens when & is separated by space on both sides,
            # hence, names like S&P will not be affected.
            keyword_processor = KeywordProcessor()
            remove_keywords_dict = {" ": ["LIMITED", "LTD", "LTD.", "THE"], "AND": ["&"]}
            keyword_processor.add_keywords_from_dict(remove_keywords_dict)

            # Call the flashtext replace_keyword again to replace "CO.". The replacement doesn't
            # properly happen when combined into the above call because some company names have
            # "CO.LTD.", etc. (without spaces after CO.), so these are not considered as keywords
            # for replacement. Strangely this doesn't affect the "LTD." though.
            remove_keywords_dict = {"COMPANY": ["CO."]}
            keyword_processor.add_keywords_from_dict(remove_keywords_dict)
            company_name = keyword_processor.replace_keywords(company_name)

            # NSE list the same company name for DVR stocks and normal stocks, so we modify the
            # company name for the DVR stocks to enable better name matching in multibeggar.
            if "DVR" in stock_symbol:
                company_name += " DVR"

            # NOTE: Below pythonic one-liner " ".join(x.split()) replaces multiple spaces in x
            # with a single space.
            company_name = " ".join(keyword_processor.replace_keywords(company_name).split())

            # strip any leading and trailing spaces that the previous steps may have introduced
            company_name = company_name.strip()

            return company_name

        nse_data["NAME OF COMPANY"] = nse_data.apply(
            lambda x: cleanup_company_name_nse(x["NAME OF COMPANY"], x["SYMBOL"]), axis=1
        )

        return nse_data[["NAME OF COMPANY", "SYMBOL"]].rename(
            columns={"NAME OF COMPANY": "Company Name", "SYMBOL": "Stock Symbol"}
        )

    def clean_transactions_data(self, transactions_data: pandas.DataFrame) -> None:
        """Cleans up companies names in the transactions data.

        Note:
            Presently only supports transactions data exported from Value Research.

        Args:
            transactions_data: DataFrame that contains the transactions data.

        Returns:
            None. (transactions_data is updated inline.)
        """

        def cleanup_company_name_transactions(company_name: str) -> str:
            """Helper inner method to cleanup the company name in transactions data."""
            # convert to uppercase for better name matching in multibeggar
            company_name = company_name.upper()

            # remove parenthesis for better name matching in multibeggar
            company_name = company_name.translate({ord(x): None for x in "()"})

            # Remove "Limited", "Ltd.", etc. for better name matching in multibeggar
            # NOTE: (WORKAROUND) flashtext requires the keywords to be mapped to a non-empty string.
            # It replaces the keywords with the mapped non-empty string.
            # Hence, map the unwanted keywords to a single space, which we will trim in next step.
            #
            # replace "ICICI PRU" with "ICICI PRUDENTIAL" and "ETF-G", "ETF-IDCW" with "ETF".
            # replace "MOTILAL OSWAL NASDAQ 100 ETF FUND" with
            # "MOTILAL OSWAL MOST SHARES NASDAQ-100 ETF" :headbang:
            #
            # replace & with AND for better name matching in multibeggar.
            # NOTE: This replacement only happens when & is separated by space on both sides,
            # hence, names like S&P will not be affected.
            keyword_processor = KeywordProcessor()
            remove_keywords_dict = {
                " ": ["LTD.", "LIMITED", "THE"],
                "ICICI PRUDENTIAL": ["ICICI PRU"],
                "ETF": ["ETF-G", "ETF-IDCW"],
                "MOTILAL OSWAL MOST SHARES NASDAQ-100 ETF": ["MOTILAL OSWAL NASDAQ 100 ETF FUND"],
                "AND": ["&"],
            }
            keyword_processor.add_keywords_from_dict(remove_keywords_dict)

            # NOTE: The below pythonic one-liner " ".join(x.split()) replaces multiple spaces
            # in x with a single space.
            company_name = " ".join(keyword_processor.replace_keywords(company_name).split())

            # strip any leading and trailing spaces that the previous steps may have introduced
            company_name = company_name.strip()

            return company_name

        transactions_data["Company Name"] = transactions_data["Company Name"].apply(
            cleanup_company_name_transactions
        )

    def what_is(self):
        meme = Image.open(
            os.path.join(os.path.dirname(__file__), "data", "memes", "goldenkatora.jpg")
        )
        meme.show()
