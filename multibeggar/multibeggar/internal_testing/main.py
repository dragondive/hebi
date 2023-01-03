from multibeggar import goldenkatora

# TODO: replace these with proper unittests later, but ok for now. :)
golden_katora = goldenkatora.GoldenKatora()
bse_file = golden_katora.get_cleaned_stocks_data_bse()
nse_file = golden_katora.get_cleaned_stocks_data_nse()
print(bse_file)
print(nse_file)
