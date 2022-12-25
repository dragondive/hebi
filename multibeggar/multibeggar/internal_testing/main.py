import os
from multibeggar import goldenkatora

golden_katora = goldenkatora.GoldenKatora()

testing_dir = os.getcwd()
data_dir = testing_dir.replace("internal_testing", "data")

bse_data_file = os.path.join(data_dir, "bse_securities.csv")
nse_data_file = os.path.join(data_dir, "nse_securities.csv")

golden_katora.cleanup_stocks_data(bse_data_file, nse_data_file)
