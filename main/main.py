################################################################################################################################################################################################################################
# 
#                                                                               !!!!!READ ME!!!!!
#
#                                           CURRENTLY MIGRATING equity_val_edgar.py AND equity_val_yfinance.py INTO MULTIPLE FILES
#
#                               Using: https://pages.stern.nyu.edu/~adamodar/New_Home_Page/spreadsh.htm#ginzumodels:~:text=fcffsimpleginzu.xlsx
#
#       Migrating from this structure:
#
#          Orpheus
#          ├── equity_val_edgar.py              #equity_val_edgar.py is currently doing all the work for equity_val_yfinance and more, which it should not do.
#          └── equity_val_yfinance.py
#
#       Migrating to the structure below:
#
#           Orpheus2/
#           ├── data_processing/
#           │   ├── data_processing.py
#           │   └── feature_engineering.py
#           ├── data_retrieval/
#           │   ├── bonds.py
#           │   ├── failure_rates.py
#           │   ├── equity_risk_premiums.py
#           │   ├── data_sync.py
#           │   ├── edgar_data.py
#           │   └── yahoo_data.py
#           ├── equity_valuation/
#           │   └── equity_valuation.py
#           ├── gui/
#           │   └── gui.py
#           ├── machine_learning/
#           │   ├── data_preparation.py
#           │   ├── model_evaluation.py
#           │   └── models/
#           │       ├── (ensemble.py)
#           │       ├── (ltsm.py)
#           │       ├── (random_forest.py)
#           │       └── (time_series.py)
#           ├── main/
#           │   ├── analysis.py
#           │   └── main.py
#           └── utils/
#               └── utils.py
#
#
#       REASON:
#           The goal behind this migration is to better execute equity valuation and stock price prediction.
#           The current issue behind this migration stems from the lack of readability, modularity, and difficulty of adding features to one file.
#       
#       OBJECTIVE:
#           Estimate the fundamental equity value of a stock and predict its price tomorrow with a machine learning model to suggest a purchase or sale decision to maximize return.
#
#       TASKS:
#           1. edgar_data.py: Obtain data from SEC EDGAR for equity_valuation.py inputs, such as operating lease commitments, employee stock options, credit rating, 
#                   net operating losses carried forward, minority interests and other data that can't be directly obtained from yahoo finance.
#                   This should be able to retrieve data such as the NOL carried into the next period or the pretax cost of debt / credit rating from the most recent 10K
#                   (i.e. 'us-gaap:OperatingLossCarryforwards' or 'us-gaap:LesseeOperatingLeaseLiabilityPaymentsDueNextTwelveMonths').
#                   Currently, it is able to retrieve all those documents that correspond to the data we need. We need to connect the data to the variables being returned by edgar_data.py
#           2. yahoo_data.py: Obtain Trailing Twelve Month and Fiscal Year data from Yahoo Finance API for equity_valuation.py inputs, such as revenues, operating income, etc.
#           3. bonds.py: Gets bond ratings for countries, failure rates by bond rating, 
#           ... the rest of the structure needs to be reviewed and done according to fcffsimpleginzu
#           n-2. equity_valuation.py: compute the fundamental equity value of the stock
#           n-1. time_series: time series model for tomorrow's price prediction based on past prices
#           n. analysis.py: make a recommendation on whether to buy, sell or hold the stock based on the equity value and the stock price prediction.
#
################################################################################################################################################################################################################################


import analysis
import datetime as dt

ticker = None
today = None

def setup():
    ticker = input("Enter the stock ticker: ")
    today = dt.date.today()
    return ticker, today

def main():
    ticker, today = setup()
    pass

if __name__ == "__main__":
    main()