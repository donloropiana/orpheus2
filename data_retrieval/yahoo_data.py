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

print('\nBalance Sheets')
print(quarterly['balance_sheets'].index)
print('\nIncome Statements')
print(quarterly['income_statements'].index)
print('\nCash Flows')
print(quarterly['cash_flows'].index)
print()

print(info)

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

print("\nExchange:\n"+str(us_exchange_codes[exchange][0]))

print("\nBeta:\n " + str(levered_beta))

# best way to do this is to get the 

# https://github.com/ranaroussi/yfinance Smart cache
