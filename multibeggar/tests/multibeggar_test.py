import pytest
from multibeggar.multibeggar import Multibeggar

import pandas
import math

@pytest.fixture(scope='module')
def get_multibeggar():
    yield Multibeggar()


@pytest.mark.parametrize(
'input_company_name, output_symbol', [
('Bajaj Finance', 'BAJFINANCE.NS'),
('Berger Paints India', 'BERGEPAINT.NS'),
('JFrog', None),
])
def test_get_nse_symbol(get_multibeggar, input_company_name, output_symbol):
    mb = get_multibeggar
    assert mb.get_nse_symbol(input_company_name) == output_symbol


@pytest.mark.parametrize(
'input_company_name, output_symbol', [
('Pidilite Industries', 'PIDILITIND.BO'),
('SBI Cards & Payments Services', 'SBICARD.BO'),
('Microsoft', None),
])
def test_get_bse_symbol(get_multibeggar, input_company_name, output_symbol):
    mb = get_multibeggar
    assert mb.get_bse_symbol(input_company_name) == output_symbol


@pytest.mark.parametrize(
'input_company_name, output_symbol', [
('Relaxo Footwears', ['RELAXO.NS', 'RELAXO.BO']),
('Central Depository Services', ['CDSL.NS', None]),
('Black Rose Industries', [None, 'BLACKROSE.BO']),
('Google', [None, None]),
])
def test_get_stock_symbols(get_multibeggar, input_company_name, output_symbol):
    mb = get_multibeggar
    assert mb.get_stock_symbols(input_company_name) == output_symbol


@pytest.fixture
def get_mock_ticker():
    def mock_ticker_closure(symbol):
        return MockTicker(symbol)


    class MockTicker:
        all_data = pandas.DataFrame([
            ['TITAN.NS', '2020/03/12', 650.25],
            ['TITAN.NS', '2020/03/13', 648.00],            
            ['TITAN.NS', '2020/03/16', 652.75],            
            ['TITAN.NS', '2020/03/17', 660.80],            
            ['TITAN.NS', '2020/03/18', 640.20],            
            ['TITAN.NS', '2020/03/19', 645.00],            
            ['TITAN.NS', '2020/03/20', 635.20],            
            ['TITAN.NS', '2020/03/23', 649.40],            
            ['TITAN.NS', '2020/03/24', 674.00],            
            ['TITAN.NS', '2020/03/25', 668.60],            
            ['TITAN.NS', '2020/03/26', 680.10],            
            ['TITAN.NS', '2020/03/27', 682.35],            
            ['TITAN.NS', '2020/03/30', 685.65],            
            ['TITAN.NS', '2020/03/31', 683.85],
            ['ASIANPAINT.BO', '2020/03/25', 2480],
        ], columns =['Symbol', 'Date', 'Close'])


        def __init__(self, symbol):
            self.symbol_data = MockTicker.all_data[MockTicker.all_data['Symbol'] == symbol]


        def history(self, start, end):
            date = pandas.to_datetime(self.symbol_data['Date'])
            selected_data = self.symbol_data[(start <= date) & (date < end)]
            return selected_data
    
    
    yield mock_ticker_closure


@pytest.mark.parametrize(
'input_stock_symbol, input_date, output_closing_price', [
('TITAN.NS', '2020/03/25', 668.60),
('TITAN.NS', '2020/03/21', None),
('TITAN.NS', '1900/01/01', None),
('TITAN.NS', '2200/12/31', None),
('SHUEISHA', '2021/01/03', None),
('SBIN.BO', '2020/03/19', None),
('ASIANPAINT.BO', '2020/03/25', 2480),
(None, '2021/08/15', None),
])
def test_get_adjusted_closing_price(get_multibeggar, mocker, get_mock_ticker, input_stock_symbol, input_date, output_closing_price):
    mock_ticker = get_mock_ticker(input_stock_symbol)
    mocker.patch('multibeggar.multibeggar.yfinance.Ticker', return_value=mock_ticker)
    mb = get_multibeggar
    assert mb.get_adjusted_closing_price(input_stock_symbol, input_date) == output_closing_price


@pytest.mark.parametrize(
'input_stock_symbol, output_stock_symbol', [
('MON100.NS', 'N100.NS'),
('MON100.BO', 'N100.BO'),
('ASTRAL.NS', None),
])
def test_get_renamed_symbol(get_multibeggar, input_stock_symbol, output_stock_symbol):
    mb = get_multibeggar
    assert mb.get_renamed_symbol(input_stock_symbol) == output_stock_symbol


@pytest.mark.parametrize(
'input_adjusted_price, input_stock_symbol, input_date, output_de_adjusted_price', [
(124, None, '2021/08/15', 124),
(1250, 'HDFCBANK.NS', '2019/09/18', 2500),
(1250, 'HDFCBANK.NS', '2019/09/19', 1250),
(1250, 'HDFCBANK.NS', '2019/09/20', 1250),
(84000, 'MRF.NS', '2021/08/15', 84000),
# ('invalid_price', 'MRF.NS', '2021/08/15', None),
# (488, 'KOTAKBANK.NS', 'invalid_date', None),
])
def test_de_adjust_price(get_multibeggar, input_adjusted_price, input_stock_symbol, input_date, output_de_adjusted_price):
    mb = get_multibeggar
    assert mb.de_adjust_price(input_adjusted_price, input_stock_symbol, input_date) == output_de_adjusted_price








