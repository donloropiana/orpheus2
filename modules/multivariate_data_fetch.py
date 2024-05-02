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
from modules.sql import get_db_connection, get_cursor

# Suppress specific FutureWarnings from pandas and yfinance
warnings.simplefilter(action='ignore', category=FutureWarning)



def get_sp500_stocks():
    headers = {'User-Agent': 'maxbushala@gmail.com'}
    sp500_url = 'https://www.slickcharts.com/sp500'
    resp = requests.get(sp500_url, headers=headers)
    tb = pd.read_html(resp.text)
    return tb[0]['Symbol'].tolist()

def fetch_data_for_stock(stock):
    console = Console()
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
        console.print(f"[red]Error fetching data for {stock}: {e}")
        return None

def get_stock_data(stocks, batch_size=5, sleep_time=10):
    results = []
    console = Console()
    with Progress(console=console) as progress:
        task = progress.add_task("[cyan]Downloading stocks...", total=len(stocks))
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {}
            for stock in stocks:
                future = executor.submit(fetch_data_for_stock, stock)
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

def save_to_sql(df):
    with get_db_connection() as conn, get_cursor(conn) as cursor:
        cursor.execute("DROP TABLE IF EXISTS stock_data")
        cursor.execute("""
            CREATE TABLE stock_data (
                Ticker VARCHAR(10),
                Sector VARCHAR(50),
                Industry VARCHAR(50),
                `Today Price` FLOAT,
                `Yesterday Price` FLOAT,
                `Market Cap` BIGINT,
                Beta FLOAT,
                `PE Ratio` FLOAT,
                EPS FLOAT,
                ROE FLOAT,
                `EV/EBITDA` FLOAT,
                `Net Margin` FLOAT,
                `Cash/Revenue Ratio` FLOAT,
                `PEG Ratio` FLOAT,
                `Price to Book` FLOAT
            )
        """)
        for _, row in df.iterrows():
            print(row)
            cursor.execute("""
                INSERT INTO stock_data VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, tuple(row))
            print('Inserted')
        conn.commit()

def print_sql_data():
    with get_db_connection() as conn, get_cursor(conn) as cursor:
        cursor.execute("SELECT * FROM stock_data")
        for row in cursor.fetchall():
            print(row)


if __name__ == '__main__':
    stocks = get_sp500_stocks()
    data = get_stock_data(stocks)
    save_to_sql(data)
    print_sql_data()