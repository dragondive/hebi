import pandas
from math import exp
from matplotlib import pyplot

import multibeggar

import sys

log_file = open("test2_log.txt","w")
sys.stdout = log_file


def portfolio_complexity(proportions):
    proportions.sort()
    exponent_tuning_factor = 0.01

    total = 0
    [total := total + value * exp(exponent_tuning_factor * index) for index, value in enumerate(proportions)]
    
    return total
    
    
def compute_value_and_update_proportion(portfolio):
    portfolio.drop(portfolio[portfolio['Shares'] == 0].index, inplace=True)

    portfolio['Closing Price'] = portfolio.apply(lambda x: multibeggar.get_closing_price(x['Symbol'], x['Date']), axis=1)
    portfolio['Value'] = portfolio['Shares'] * portfolio['Closing Price']
    value_sum = portfolio['Value'].sum()
    print('value_sum: ' + str(value_sum))

    portfolio['Proportion'] = portfolio['Value'] / value_sum


transactions_list = pandas.read_excel('transactions_20210802_reduced.xlsx')

multibeggar.fixup_company_names(transactions_list)
print('input transactions list after fixup of company names:\n' + str(transactions_list))

transactions_list['Symbol'] = transactions_list.apply(lambda x: multibeggar.get_stock_symbol(x['Name'], with_suffix=True), axis=1)
print('transactions_list after updating symbols:\n' + str(transactions_list))

sorted_by_date_list = transactions_list.sort_values(by='Date')
print('transactions list sorted ascending by date:\n' + str(sorted_by_date_list))

ongoing_date = None
daily_portfolio = pandas.DataFrame()
full_portfolio = pandas.DataFrame()
plot_data = pandas.DataFrame()

for index, row in sorted_by_date_list.iterrows():
    date = row['Date']
    print('date: ' + str(date))
    
    if date != ongoing_date:
        print('date changed from: ' + str(ongoing_date) + ' to: ' + str(date))
        print('previous date: ' + str(ongoing_date) + ' daily portfolio:\n' + str(daily_portfolio))
        
        try: # ugly coding by exception, to be removed later
            compute_value_and_update_proportion(daily_portfolio)
            print('previous date: ' + str(ongoing_date) +  ' daily portfolio after updating value and proportion:\n' + str(daily_portfolio))
            
            complexity = portfolio_complexity(daily_portfolio['Proportion'].tolist())
            print('previous date: ' + str(ongoing_date) + ' complexity: ' + str(complexity))
            
            plot_data = plot_data.append({'Date' : ongoing_date, 'Complexity' : complexity}, ignore_index = True)
        except KeyError:
            pass

        full_portfolio = full_portfolio.append(daily_portfolio)
        print('after portfolio update for date: ' + str(ongoing_date) + ' full portfolio:\n' + str(full_portfolio))
        
        daily_portfolio.replace({ongoing_date: date}, inplace=True)
        ongoing_date = date
        
    try: # todo remove this try except later
        name = row['Name']
        print('stock name: ' + name)

        mask = (daily_portfolio['Name'] == name)
        masked_rows = daily_portfolio[mask]
        print('masked_rows in daily_portfolio =\n' + str(masked_rows))

        if masked_rows.empty == True: # this is a new Name
            print('mask is empty, appending new row')
            daily_portfolio = daily_portfolio.append(row)
        else:
            print('mask is not empty, updating existing row')
            shares = row['Shares']
            daily_portfolio.loc[mask, 'Shares'] += shares
            print('for date: ' + str(ongoing_date) + ' stock name: ' + str(name) + ' shares: ' + str(shares) + ' updated shares: ' + str(daily_portfolio.loc[mask, 'Shares'].values[0]))

    except KeyError: # ugly code, coding by exception should be removed
        print('mask is empty, appending new row')
        daily_portfolio = daily_portfolio.append(row)


print('previous date: ' + str(ongoing_date) + ' daily portfolio:\n' + str(daily_portfolio))
compute_value_and_update_proportion(daily_portfolio)

complexity = portfolio_complexity(daily_portfolio['Proportion'].tolist())
print('previous date: ' + str(ongoing_date) + ' complexity: ' + str(complexity))

plot_data = plot_data.append({'Date' : ongoing_date, 'Complexity' : complexity}, ignore_index = True) 
print('plot_data =\n' + str(plot_data))

full_portfolio = full_portfolio.append(daily_portfolio)    
print('after portfolio update for date: ' + str(ongoing_date) + ' full portfolio:\n' + str(full_portfolio))


sorted_by_date_list.to_excel('test2_sorted_by_date.xlsx')
full_portfolio.to_excel('test2_full_portfolio.xlsx')
plot_data.to_excel('test2_plot_data.xlsx')

plot_data.plot.line(x='Date', y='Complexity')
pyplot.show()
log_file.close()
