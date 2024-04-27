# set up environment
import pandas as pd
from textblob import TextBlob
import requests
from bs4 import BeautifulSoup

def query_builder(search_string):
    query = "?keyword="
    split_string = search_string.split(' ')
    query += split_string[0]
    for remaining_words in split_string[1:]:
        query+= "%20" + remaining_words
    return query

def get_press_releases(input):
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
    return results

def get_pr_body(url):
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
    blob = TextBlob(text)
    return blob.polarity, blob.subjectivity
  

def press_release_df(company_name):
    df = pd.DataFrame(columns=["Company", "Link", "Title", "Body"])
    company_prs = get_press_releases(company_name)
    rows = [{"Company": company_name, "Link": "https://www.prnewswire.com" + pr['link'], "Title": pr['title']} for pr in company_prs]
    for row in rows:
        row["Body"] = get_pr_body(row["Link"])
        polarity, subjectivity = sentiment_analysis(row["Body"])
        row["Polarity"] = polarity
        row["Subjectivity"] = subjectivity
    new_rows_df = pd.DataFrame(rows)
    df = pd.concat([df, new_rows_df], ignore_index=True)
    return df

def company_sentiment(ticker: str) -> int:
    df = press_release_df(ticker)
    return df["Polarity"].mean()