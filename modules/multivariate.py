from rich.console import Console
from rich.progress import Progress
import yfinance as yf
import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor
import time
import os
import warnings
import numpy as np

# Suppress specific FutureWarnings from pandas and yfinance
warnings.simplefilter(action='ignore', category=FutureWarning)

class multivariate:
    def __init__(self):
        self.headers = {'User-Agent': 'maxbushala@gmail.com'}
        self.console = Console()

    def get_sp500_stocks(self):
        sp500_url = 'https://www.slickcharts.com/sp500'
        resp = requests.get(sp500_url, headers=self.headers)
        tb = pd.read_html(resp.text)
        return tb[0]['Symbol'].tolist()

    def fetch_data_for_stock(self, stock):
        try:
            s = yf.Ticker(stock)
            info = s.info
            hist = s.history(period="2d")
            
            today_price = hist['Close'].iloc[-1] if not hist.empty else 'N/A'
            yesterday_price = hist['Close'].iloc[-2] if len(hist) > 1 else 'N/A'
            
            return {
                'Ticker': stock,
                'Sector': info.get('sector', np.nan),
                'Industry': info.get('industry', np.nan),
                'Today Price': today_price,
                'Yesterday Price': yesterday_price,
                'Market Cap': info.get('marketCap', np.nan),
                'Beta': info.get('beta', np.nan),
                'PE Ratio': info.get('trailingPE', np.nan),
                'EPS': info.get('trailingEps', np.nan),
                'ROE': info.get('returnOnEquity', np.nan),
                'EV/EBITDA': info.get('enterpriseToEbitda', np.nan),
                'Net Margin': info.get('profitMargins', np.nan),
                'Cash/Revenue Ratio': (info.get('totalCash', 0) / info.get('totalRevenue', 1)) if info.get('totalRevenue', 0) != 0 else 'N/A',
                'PEG Ratio': info.get('pegRatio', np.nan),
                'Price to Book': info.get('priceToBook', np.nan),
            }
            
        except Exception as e:
            self.console.print(f"[red]Error fetching data for {stock}: {e}")
            return None
        
    def get_stock_data(self, stocks, batch_size=5, sleep_time=10):
        results = []
        with Progress(console=self.console) as progress:
            task = progress.add_task("[cyan]Downloading stocks...", total=len(stocks))
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = {}
                for stock in stocks:
                    future = executor.submit(self.fetch_data_for_stock, stock)
                    futures[future] = stock
                for future in futures:
                    result = future.result()
                    if result:
                        # Convert 'N/A' to np.nan right after fetching the data
                        for key, value in result.items():
                            if value == 'N/A':
                                result[key] = np.nan
                        results.append(result)
                    progress.update(task, advance=1)
                    time.sleep(sleep_time / len(stocks))  # Adjust sleep to smooth out the rate limit
        df = pd.DataFrame(results)
        # Drop rows where any column has NaN
        clean_df = df.dropna()
        return clean_df

    def save_to_excel(self, dataframe, filename="stock_data.xlsx"):
        if not dataframe.empty:
            download_path = os.path.join(os.path.expanduser('~'), 'Downloads', filename)
            dataframe.to_excel(download_path, index=False)
            self.console.print(f"[green]Data saved to {download_path}")
        else:
            self.console.print("[red]No data was saved due to missing data.")


# Example usage
mv = multivariate()
tickers = mv.get_sp500_stocks()  # or a subset for testing, e.g., tickers[:10]
stock_data = mv.get_stock_data(tickers)
mv.save_to_excel(stock_data)  # Save the DataFrame to an Excel file
