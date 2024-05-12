# set up environment
import pandas as pd
from textblob import TextBlob
import requests
from bs4 import BeautifulSoup

def query_builder(search_string):
    """
    Builds a query string for a search based on the given search string.

    Args:
        search_string (str): The search string to build the query from.

    Returns:
        str: The query string.

    Example:
        >>> query_builder("hello world")
        '?keyword=hello%20world'
    """
    query = "?keyword="
    split_string = search_string.split(' ')
    query += split_string[0]
    for remaining_words in split_string[1:]:
        query+= "%20" + remaining_words
    return query

def get_press_releases(input, num_press_releases=5):
    """
    Retrieves press releases from PR Newswire based on the input query.

    Args:
        input (str): The query string for the press releases.

    Returns:
        list: A list of dictionaries containing the link and title of each press release.
    """
    headers = {
        'User-Agent': 'Noah Perelmuter',
        'Email': 'np2446@stern.nyu.edu',
        'Organization': 'New York University'
    }
    query_string = query_builder(input)
    url = "https://www.prnewswire.com/search/all/" + query_string
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, 'html.parser')
    results = []
    for tag in soup.find_all('div', {'class': "row newsCards"}):  # Use find_all to iterate over all matching divs
        a_tag = tag.find('a')
        if a_tag:
            link = a_tag.get('href', '')  # Use .get() to safely extract attribute values
            title = a_tag.text
            results.append({'link': link, 'title': title})      
            if len(results) == num_press_releases:
                break
    return results

def get_pr_body(url):
    """
    Retrieves the body text of a pull request from the given URL.

    Args:
        url (str): The URL of the pull request.

    Returns:
        str: The body text of the pull request.
    """
    headers = {
    'User-Agent': 'Noah Perelmuter',
    'Email': 'np2446@stern.nyu.edu',
    'Organization': 'New York University'
    }
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, 'html.parser')
    div_we_need = soup.find('div', {'class': "col-lg-10 col-lg-offset-1"})
    text = ""
    if div_we_need:
        for p in div_we_need.find_all('p'):
            if p: text += p.text
    return text

def sentiment_analysis(text):
    """
    Perform sentiment analysis on the given text.

    Args:
        text (str): The text to analyze.

    Returns:
        tuple: A tuple containing the polarity and subjectivity scores of the text.
               The polarity score ranges from -1 to 1, where -1 indicates negative sentiment,
               0 indicates neutral sentiment, and 1 indicates positive sentiment.
               The subjectivity score ranges from 0 to 1, where 0 indicates objective text
               and 1 indicates subjective text.
    """
    blob = TextBlob(text)
    return blob.polarity, blob.subjectivity
  

def press_release_df(company_name, num_press_releases=5):
    """
    Retrieves press releases for a given company, performs sentiment analysis on the press release body,
    and returns a pandas DataFrame containing the company name, link, title, body, polarity, and subjectivity.

    Args:
        company_name (str): The name of the company.

    Returns:
        pandas.DataFrame: A DataFrame containing the press release information.
    """
    df = pd.DataFrame(columns=["Title", "Link"])
    company_prs = get_press_releases(company_name, num_press_releases)
    rows = [{"Title": pr['title'], "Link": "https://www.prnewswire.com" + pr['link']} for pr in company_prs]
    for row in rows:
        body = get_pr_body(row["Link"])
        polarity, subjectivity = sentiment_analysis(body)
        row["Polarity"] = polarity
        row["Subjectivity"] = subjectivity
    new_rows_df = pd.DataFrame(rows)
    df = pd.concat([df, new_rows_df], ignore_index=True)
    return df

#returns Debt-to-Equity, Current Ratio, Quick Ratio
def get_ratios(ticker):
  url = "https://financialmodelingprep.com/api/v3/balance-sheet-statement/"+str(ticker)+"?period=annual&apikey=mqrLB9Dge9VSTV02TZeTrq3w2VSc6OLA"
  r = requests.get(url)
  if r.status_code == 200:
    bsdata = r.json()
    tca = bsdata[0]["totalCurrentAssets"]
    tcl = bsdata[1]["totalCurrentLiabilities"]
    current_ratio = tca / tcl
    total_debt = bsdata[0]["totalDebt"]
    total_equity = bsdata[1]["totalEquity"]
    debt_to_equity = total_debt/total_equity
    inventory = bsdata[0]["inventory"]
    quick_ratio = (tca - inventory)/tcl
    return [debt_to_equity, current_ratio, quick_ratio]
  else:
    print("an error has occured")
      
def company_sentiment(ticker: str) -> int:
    """
    Calculate the sentiment polarity of a company's press releases.

    Args:
        ticker (str): The ticker symbol of the company.

    Returns:
        int: The average sentiment polarity of the company's press releases.
    """
    df = press_release_df(ticker)
    try:
        polarity = df["Polarity"].mean()
    except KeyError:
        polarity = -2
    return polarity
