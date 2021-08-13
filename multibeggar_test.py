import pytest
from multibeggar import Multibeggar

import pandas



@pytest.mark.parametrize(
'input_company_name,output_symbol', [
('Bajaj Finance', 'BAJFINANCE.NS'),
('Berger Paints India', 'BERGEPAINT.NS'),
('JFrog', None),
])
def test_get_nse_symbol(input_company_name, output_symbol):
    mb = Multibeggar()
    assert mb.get_nse_symbol(input_company_name) == output_symbol


@pytest.mark.parametrize(
'input_company_name,output_symbol', [
('Pidilite Industries', 'PIDILITIND.BO'),
('SBI Cards & Payments Services', 'SBICARD.BO'),
('Microsoft', None),
])
def test_get_bse_symbol(input_company_name, output_symbol):
    mb = Multibeggar()
    assert mb.get_bse_symbol(input_company_name) == output_symbol


@pytest.mark.parametrize(
'input_company_name,output_symbol', [
('Relaxo Footwears', ['RELAXO.NS', 'RELAXO.BO']),
('Central Depository Services', ['CDSL.NS', None]),
('Black Rose Industries', [None, 'BLACKROSE.BO']),
('Google', [None, None]),
])
def test_get_stock_symbols(input_company_name, output_symbol):
    mb = Multibeggar()
    assert mb.get_stock_symbols(input_company_name) == output_symbol


@pytest.fixture
def mock_ticker():
    def _mock_ticker(symbol):
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
        ], columns =['Symbol', 'Date', 'Close'])

        def __init__(self, symbol):
            print('symbol: ' + str(symbol))
            self.symbol_data = MockTicker.all_data[MockTicker.all_data['Symbol'] == symbol]


        def history(self, start, end):
            print('mock_ticker history')
            print('start_date: ' + str(start))
            print('end_date: ' + str(end))
            date = pandas.to_datetime(self.symbol_data['Date'])
            selected_data = self.symbol_data[(start <= date) & (date < end)]
            print('selected_data: \n' + str(selected_data))
            return selected_data
            
            
    yield _mock_ticker
    
    
@pytest.mark.parametrize(
'input_stock_symbol, input_date, output_closing_price', [
('TITAN.NS', '2020/03/25', 1500),
])
def test_get_adjusted_closing_price(mocker, mock_ticker, input_stock_symbol, input_date, output_closing_price):
    my_mock_ticker = mock_ticker(input_stock_symbol)
    mocker.patch('multibeggar.yfinance.Ticker', return_value=my_mock_ticker)
    mb = Multibeggar()
    assert mb.get_adjusted_closing_price(input_stock_symbol, input_date) == output_closing_price
    

# def test_normal():
    # mb = Multibeggar()
    # mb.get_adjusted_closing_price('TITAN.NS', '2020/03/25')


# @pytest.fixture
# def tester():
    # # Create a closure on the Tester object
    # def _tester(first_param, second_param):
        # # use the above params to mock and instantiate things
        # return MyTester(first_param, second_param)
    
    # # Pass this closure to the test
    # yield _tester 


# @pytest.mark.parametrize(['param_one', 'param_two'], [(1,2), (1000,2000)])
# def test_tc1(tester, param_one, param_two):
    # # run the closure now with the desired params
    # my_tester = tester(param_one, param_two)
    # # assert code here