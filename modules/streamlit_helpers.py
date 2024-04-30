import matplotlib.pyplot as plt
from matplotlib.patches import Wedge
import pandas as pd
import yfinance as yf
from neuralprophet import NeuralProphet

def draw_donut_circle(label: str, score: float) -> plt.Figure:
    """
    Draw a donut circle based on the given score.

    Parameters:
    label (str): The label to be displayed in the center of the donut circle.
    score (float): The score to be visualized in the donut circle.

    Returns:
    plt.Figure: The matplotlib figure object containing the donut circle.
    """
    # Normalize the score to the range -1 to 1 just in case!
    score = max(min(score, 1), -1)
    
    fig, ax = plt.subplots(figsize=(4, 4))  # Use a square figure to hold the circle

    # Base circle as background (the donut)
    base_circle = Wedge((0.5, 0.5), 0.4, 0, 360, width=0.1, facecolor='lightgrey')
    ax.add_artist(base_circle)

    # Color and extent of the fill based on the score
    color = 'green' if score >= 0 else 'red'
    extent = abs(score) * 360  # Full circle for score = 1 or -1

    # Create and add the filled portion of the circle (the colored part of the donut)
    filled_circle = Wedge((0.5, 0.5), 0.4, 0, extent, width=0.1, facecolor=color)
    ax.add_artist(filled_circle)

    # Add text in the center of the donut
    ax.text(0.5, 0.55, label, horizontalalignment='center', verticalalignment='center', fontsize=9, fontweight='bold')
    ax.text(0.5, 0.45, f"{score:.2f}", horizontalalignment='center', verticalalignment='center', fontsize=12, fontweight='bold')

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect('equal')
    ax.axis('off')  # Turn off the axis

    return fig


def build_info_table(info: dict, projected_price: float=None) -> pd.DataFrame:
    """
    Builds an information table based on the given info dictionary.

    Args:
        info (dict): A dictionary containing information about an item.
        projected_price (float, optional): The projected price of the item. Defaults to None.

    Returns:
        pandas.DataFrame: The information table.
    """
    val = "Value (USD, if applicable)"
    info_table = pd.DataFrame({
        'Item': list(info.keys()),
        val: list(info.values())
    })
    # get rid of index
    info_table.set_index('Item', inplace=True)
    # only keep current price, market cap, dividend rate, and dividend yield
    info_table = info_table[info_table.index.isin(['currentPrice', 'marketCap', 'dividendRate', 'dividendYield'])]
    # format currentPrice as currency
    info_table.loc['currentPrice', val] = f"${info_table.loc['currentPrice', val]:.2f}"
    # format marketcap
    # probably a better way to do this with a helper function, but this works for now
    market_cap = info_table.loc['marketCap', val]
    if market_cap >= 1_000_000_000 and market_cap < 1_000_000_000_000:
        info_table.loc['marketCap', val] = f"${market_cap / 1_000_000_000:.2f}B"
    elif market_cap >= 1_000_000_000:
        info_table.loc['marketCap', val] = f"${market_cap / 1_000_000_000_000:.2f}T"
    elif market_cap >= 1_000_000:
        info_table.loc['marketCap', val] = f"${market_cap / 1_000_000:.2f}M"
    elif market_cap < 1_000_000:
        info_table.loc['marketCap', val] = f"${market_cap:.2f}"
    # format dividendRate and dividendYield as percentage
    info_table.loc['dividendRate', val] = f"{info_table.loc['dividendRate', val] * 100:.2f}%"
    info_table.loc['dividendYield', val] = f"{info_table.loc['dividendYield', val] * 100:.2f}%"
    # rename the rows from camelCase to Title Case 
    info_table.rename(index={'currentPrice': 'Current Price',
                             'marketCap': 'Market Cap',
                             'dividendRate': 'Dividend Rate',
                             'dividendYield': 'Dividend Yield'}, inplace=True)
    if projected_price:
        info_table.loc['Our Projected Price', val] = f"${projected_price:.2f}"
        info_table.loc['Upside Potential', val] = f"{((projected_price - info['currentPrice']) / info['currentPrice']) * 100:.2f}%"

    return info_table


def stock_chart(ticker: str, period: str='1y', projected_price: float=None) -> plt.Figure:
    """
    Display a stock chart for the given stock ticker.

    Args:
        ticker (str): The stock ticker symbol.
        period (str, optional): The period for which to display the stock chart. Defaults to '1y'.
    """
    # Fetch the historical stock data
    data = yf.download(ticker, period=period)

    # Create a new figure
    fig, ax = plt.subplots(figsize=(10, 6))

    #reformat ticker to all caps just in case
    ticker = ticker.upper()

    #rename data['Close'] key  to Close Price
    data.rename(columns={'Close': 'Price at Close'}, inplace=True)
    # Plot the closing price of the stock
    data['Price at Close'].plot(ax=ax, title=f'{ticker} Stock Price', ylabel='Price (USD)')

    # Add the projected price to the plot as a horizontal line colored red
    if projected_price:
        ax.axhline(projected_price, color='r', linestyle='--', label=f'Projected Price: ${projected_price:.2f}')
    
    # make chart look sleek
    ax.legend()
    ax.set_xlabel('Date')
    ax.set_ylabel('Close Price (USD)')
    ax.set_title(f'{ticker} Stock Price')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('grey')
    ax.spines['bottom'].set_color('grey')
    ax.tick_params(axis='x', colors='grey')
    ax.tick_params(axis='y', colors='grey')
    ax.yaxis.label.set_color('grey')
    ax.xaxis.label.set_color('grey')
    ax.title.set_color('grey')

    # return the figure
    return fig

def earnings_calendar(ticker: str) -> pd.DataFrame:
    """
    Display the earnings calendar for the given stock ticker.

    Args:
        ticker (str): The stock ticker symbol.
    """
    # Fetch the earnings calendar for the given stock ticker
    earnings = yf.Ticker(ticker).calendar

    # Display the earnings calendar
    df = pd.DataFrame(earnings)

    # format Revenue High, Revenue Low, and Revenue Average as currency
    df['Revenue High'] = df['Revenue High'].map('${:,.2f}'.format)
    df['Revenue Low'] = df['Revenue Low'].map('${:,.2f}'.format)
    df['Revenue Average'] = df['Revenue Average'].map('${:,.2f}'.format)

    # format Earnings High, Earnings Low, and Earnings Average as currency
    df['Earnings High'] = df['Earnings High'].map('${:,.2f}'.format)
    df['Earnings Low'] = df['Earnings Low'].map('${:,.2f}'.format)
    df['Earnings Average'] = df['Earnings Average'].map('${:,.2f}'.format)

    # rename earnings to EPS high, EPS low, and EPS average
    df.rename(columns={'Earnings High': 'EPS High',
                       'Earnings Low': 'EPS Low',
                       'Earnings Average': 'EPS Average'}, inplace=True)
    
    # get rid of Dividend Date and Ex-Dividend Date
    df.drop(columns=['Dividend Date', 'Ex-Dividend Date'], inplace=True)

    return df


def neural_prophet_forecast_chart(ticker: str, periods: int) -> plt.Figure:
    """
    Perform a forecast using the NeuralProphet model.
    Args:
        ticker (str): The stock ticker symbol.
        periods (int): The number of periods to forecast into the future.
    Returns:
        plt.Figure: The forecast chart.
    """
    # Fetch historical stock data
    data = yf.download(ticker, start="2010-01-01", end="2024-04-28")
    
    # We typically use Adjusted Close prices for predictions
    data = data[['Adj Close']]
    data.reset_index(inplace=True)  # Reset index to use the date as a column
    data.rename(columns={'Date': 'ds', 'Adj Close': 'y'}, inplace=True)  # NeuralProphet expects columns 'ds' and 'y'
    
    
    # Create a NeuralProphet model
    model = NeuralProphet()
    
    # Fit the model to the data
    model.fit(data, freq='B', epochs=100)
    
    # Make a future dataframe for forecasting
    future = model.make_future_dataframe(data, periods=periods)
    
    # Forecast the future values
    forecast = model.predict(future)
    
    # Plot the forecasted values, with the historical data colored black and the forecasted data colored red
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(data['ds'], data['y'], color='black', label='Historical Data')
    ax.plot(forecast['ds'], forecast['yhat1'], color='red', label='Forecasted Data')
    ax.set_xlabel('Date')
    ax.set_ylabel('Price (USD)')
    ax.set_title(f'{ticker} Forecast')
    ax.legend()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('grey')
    ax.spines['bottom'].set_color('grey')
    ax.tick_params(axis='x', colors='grey')
    ax.tick_params(axis='y', colors='grey')
    ax.yaxis.label.set_color('grey')
    ax.xaxis.label.set_color('grey')
    ax.title.set_color('grey')
    
    return fig