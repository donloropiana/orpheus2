# https://github.com/farhadab/sec-edgar-financials

import yfinance as yf
import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
import numpy as np
# import equity_val_edgar as evedgar

stock = "WMG"

ticker = yf.Ticker(stock)
info = ticker.info
industry = info.get('industry')
industryKey = info.get('industryKey')
exchange = info.get('exchange')
# exchange = evedgar.financialdata['dei:SecurityExchangeName']['#text'] # Use fuzzywuzzy to find most similar document name to SecurityExchangeName

history = ticker.history(period="3y")
closing_prices = history['Close']
returns = closing_prices.pct_change()
variance_returns = np.var(returns.dropna().values)

fiscal_year = {'income_statements' : ticker.financials,
               'balance_sheets' : ticker.balance_sheet,
               'cash_flows' : ticker.cashflow}

quarterly = {'income_statements' : ticker.quarterly_financials,
               'balance_sheets' : ticker.quarterly_balance_sheet,
               'cash_flows' : ticker.quarterly_cashflow}

print ('\nFiscal Year')
print('______________\n')
print(fiscal_year['income_statements'])
print('')
print(fiscal_year['balance_sheets'])
print('')
print(fiscal_year['cash_flows'])
print('')

print ('\nQuarterly')
print('______________\n')
print('\nIncome Statements')
print(quarterly['income_statements'])
print('\nBalance Sheets')
print(quarterly['balance_sheets'])
print('\nCash Flows')
print(quarterly['cash_flows'])
print('')

revenues = ''
operating_income = ''
bv_equity = ''
bv_debt = ''
operating_lease = True
cash_and_cross_holdings = ''
non_operating_assets = ''
minority_interests = ''
shares_outstanding = '' 
current_stock_price = ''
effective_tax_rate = ''
marginal_tax_rate = ''
cagr_4yr = ''
target_pretax_operating_margin = ''
sales_to_capital_ratio = ''
risk_free_rate = '' # find this by understanding which countries the business operates in as well as these countries' country risks. #us-gaap/SegmentReportingDisclosureTextBlock
initial_cost_of_capital = ''
employee_options = {
    'outstanding' : '',
    'avg_strike_price' : '',
    'avg_maturity' : '',
    'std_dev_stock_price' : ''
                    }

# us-gaap:RevenueFromContractWithCustomerTextBlock.html
# us-gaap:ScheduleOfDebtInstrumentsTextBlock.html
# SegmentReportingDisclosureTextBlock.html
# us-gaap:DisaggregationOfRevenueTableTextBlock

print('\nBalance Sheets')
print(quarterly['balance_sheets'].index)
print('\nIncome Statements')
print(quarterly['income_statements'].index)
print('\nCash Flows')
print(quarterly['cash_flows'].index)
print()

# print(quarterly['income_statements'].loc['Total Revenue'])

# Use fuzzy wuzzy to match line items to line items
# quarterly_input_data = {
#     'industry' : industry,
#     'total_revenue' : quarterly['income_statements'].loc['Total Revenue'],
#     'operating_income' : quarterly['income_statements'].loc['Operating Income'],
#     'bv_equity' : quarterly['balance_sheets'].loc['Stockholders Equity'],
#     'bv_debt' : quarterly['balance_sheets'].loc['Total Debt'], # Total Debt for security. More often than not, net debt is not listed.
#     'operating_lease_commitments' : 'yes',
#     'cash_and_cross_holdings' : (), # might need to use SEC data
#     'non_operating_assets' : None,
#     'minority_interests' : None,
#     'shares_outstanding' : None,
#     'current_stock_price' : None,
#     'effective_tax_rate' : None,
#     'marginal_tax_rate' : None,
#     'cagr_5yr' : None,
#     'target_pretax_operating_margin' : None,
#     'sales_to_capital_ratio' : None,
#     'risk_free_rate' : None,
#     'initial_cost_of_capital' : None,
#     'employee_options' : {
#         'status' : False,
#         'options_outstanding' : None,
#         'avg_strike_price' : None,
#         'avg_maturity' : None
#         },
#     'stock_price_std_dev' : None
#     }

# print(quarterly_input_data['total_revenue'])
# https://www.alphavantage.co/documentation/

# april presentation of AswathGPT
# Volatility and Risk Institute — AI conference with Vasant Dhar

print(info)

print(exchange)

us_exchange_codes = {
    'NYQ' : ['NYSE', '^NYA'],
    'NMS' : ['NASDAQ Global Market Select', '^IXIC'],
    'NGM' : ['NASDAQ Global Market', '^IXIC'],
    'NCM' : ['NASDAQ Capital Market', '^IXIC'],
    'ASE' : ['NYSE American', '^XAX'], #NYSE American
} # https://www.sec.gov/files/company_tickers_exchange.json

market_index = str(us_exchange_codes[exchange][1])
market_ticker = yf.Ticker(market_index)
market_info = market_ticker.info

market_history = market_ticker.history(period="3y")
market_closing_prices = market_history['Close']
market_history['Returns'] = market_history['Close'].pct_change().dropna()
market_returns = market_closing_prices.pct_change().dropna()

covariance = np.cov(market_returns.dropna().values, returns.dropna().values)[0, 1]

levered_beta = covariance/variance_returns

print("Beta: " + str(levered_beta))

# best way to do this is to get the 

# https://github.com/ranaroussi/yfinance Smart cache
