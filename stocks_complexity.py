import pandas
import matplotlib
from math import exp


def portfolio_complexity(proportions):
    proportions.sort()
    weight_exponent = 0.01

    weighted_proportions = [
        p * exp(weight_exponent * index) for index, p in enumerate(proportions)
    ]


    total = 0
    [total := total + x * exp(weight_exponent * index) for index, x in enumerate(proportions)]
    
    return total

transactions_list = pandas.read_excel('test.xlsx')
# print(transactions_list)

sorted_by_date_list = transactions_list.sort_values(by='Date')
print(sorted_by_date_list)

ongoing_date = None
ongoing_portfolio = pandas.DataFrame()
out_portfolio = pandas.DataFrame()

plot_data = pandas.DataFrame(columns=['Date', 'Complexity'])

for index, row in sorted_by_date_list.iterrows():
    date = row['Date']
    
    if date != ongoing_date:
        print("Date change from: " + str(ongoing_date) + " to: " + str(date))
        print("\nOngoing portfolio: \n" + str(ongoing_portfolio))
        
        # try: # ugly coding by exception, to be removed later
        if 'Amount' in ongoing_portfolio.columns:
            sum_amount = ongoing_portfolio['Amount'].sum()
            print("sum_amount = " + str(sum_amount))
            ongoing_portfolio['Proportion'] = ongoing_portfolio['Amount']/sum_amount
            
            print("ongoing_portfolio after proportion:\n" + str(ongoing_portfolio))
            
            complexity = portfolio_complexity(ongoing_portfolio['Proportion'].tolist())
            print("complexity = " + str(complexity))
            
            plot_data = plot_data.append({'Date' : ongoing_date, 'Complexity' : complexity}, ignore_index = True)
        # except KeyError:
            # pass

        out_portfolio = out_portfolio.append(ongoing_portfolio)    
        ongoing_portfolio.replace({ongoing_date: date}, inplace=True)
        ongoing_date = date
        
    try: # todo remove this try except later
        name = row['Name']
        print("name = " + name)
        mask = (ongoing_portfolio['Name'] == name)
        # mask = (sorted_by_date_list['Name'] == name)
        print("mask: \n" + str(mask))
        print("\nmask empty: " + str(mask.empty))
        print("\nmask size: " + str(mask.size))
        
        print("\nongoing_portfolio[mask] =\n" + str(ongoing_portfolio[mask]))

        masked_rows = ongoing_portfolio[mask]
        if masked_rows.empty == True: # this is a new Name
            print("mask is empty, appending new row")
            ongoing_portfolio = ongoing_portfolio.append(row)
        else:
            print("mask is not empty, updating existing row")
            amount = row['Amount']
            # ongoing_portfolio['Amount'][mask] = 0
            ongoing_portfolio.loc[mask, 'Amount'] += amount

            # print("amount: " + str(amount) + " ongoing_amount: " + str(ongoing_amount)) 
            # total = amount + ongoing_amount
            # print("total: " + total)
        # print("mask = ", ongoing_portfolio['Name'] == name)
    except KeyError: # ugly code, coding by exception should be removed
        ongoing_portfolio = ongoing_portfolio.append(row)
    # matching_row = ongoing_portfolio[mask]


print("ongoing portfolio:\n" + str(ongoing_portfolio))

sum_amount = ongoing_portfolio['Amount'].sum()
ongoing_portfolio['Proportion'] = ongoing_portfolio['Amount']/sum_amount
print("ongoing portfolio after proportion:\n" + str(ongoing_portfolio))

complexity = portfolio_complexity(ongoing_portfolio['Proportion'].tolist())
plot_data = plot_data.append({'Date' : ongoing_date, 'Complexity' : complexity}, ignore_index = True)

print("plot_data:\n" + str(plot_data))

out_portfolio = out_portfolio.append(ongoing_portfolio)    
print("out_portfolio:\n" + str(out_portfolio))

plot_data.plot.line(x='Date', y='Complexity')
matplotlib.pyplot.show()

# ongoing_date = None
# ongoing_portfolio = pandas.DataFrame()

# out_portfolio = pandas.DataFrame()

# for index, row in sorted_by_date_list.iterrows():
    # # print(index, row)
    # date = row['Date']
    # if date != ongoing_date:
        # print ("Date has changed to " + str(date))
        
        # out_portfolio = out_portfolio.append(ongoing_portfolio)
        
        # print("ongoing_date: " + str(ongoing_date) + " date: " + str(date))
        # ongoing_portfolio.replace({ongoing_date: date}, inplace=True)
        # print("ongoing_portfolio:\n" + str(ongoing_portfolio))
        
        # ongoing_date = date
        
    # # print("row:\n" + str(row))
    # ongoing_portfolio = ongoing_portfolio.append(row)
    # name = row['Name']
    # print("Name: " + name)
    
    # try: 
        # mask = ongoing_portfolio['Name'] == name
        # print("mask: \n" + str(ongoing_portfolio[mask]))
        
        # amount = row['Amount']
        # x = ongoing_portfolio[mask]['Amount'] + amount
        # print("x = " + x)
    # except KeyError:
        # pass

    # # print("ongoing portfolio:\n" + str(ongoing_portfolio))
    # print("\n")
        
   
# out_portfolio = out_portfolio.append(ongoing_portfolio) 
# print("portfolio:" + str(out_portfolio))
        
        
        
    

# sorted_list = transactions_list.sort_values(by=['Name', 'Date'])
# print(sorted_list)

# sorted_list['Total'] = sorted_list.groupby('Name').cumsum()
# print(sorted_list)

# sorted_by_date = sorted_list.sort_values(by='Date')
# print(sorted_by_date)

# print(sorted_by_date.groupby('Date').sum())


    