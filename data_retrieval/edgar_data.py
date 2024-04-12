__author__ = "Max Bushala"
__copyright__ = "Copyright 2024, Project Orpheus"
__credits__ = ["Max Bushala", "William Nichols", "Noah Perlmulter", "Dasha Malaya"]
__version__ = "0.0.1"
__maintainer__ = "Max Bushala"
__email__ = "maxbushala@gmail.com"
__status__ = "Production"

# Check out https://github.com/GGRusty/Edgar_Video_content/blob/main/Part_5/edgar_functions.py It is very similar.

import requests
import pandas as pd
import xmltodict
from bs4 import BeautifulSoup
import os, shutil
from lxml import etree
import numpy as np
import yfinance as yf
import datetime as dt

print("\n\n\n\n\n\n\n\n")
print("\n\n______________________________________________________________________________________________________________________________________________________________________________")
print("\nSTART OF edgar_data.py SCRIPT")
print("______________________________________________________________________________________________________________________________________________________________________________\n\n")

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

us_exchange_codes = {
    'NYQ' : ['NYSE', '^NYA'],
    'NMS' : ['NASDAQ Global Market Select', '^IXIC'],
    'NGM' : ['NASDAQ Global Market', '^IXIC'],
    'NCM' : ['NASDAQ Capital Market', '^IXIC'],
    'ASE' : ['NYSE American', '^XAX'], #NYSE American
} # https://www.sec.gov/files/company_tickers_exchange.json

# (NONE) (NYSE) (NASDAQ) (CHX) (BOX) (BX) (C2) (CBOE) (CboeBYX) (CboeBZX) (CboeEDGA) (CboeEDGX) (GEMX) (IEX) (ISE) (MIAX) (MRX) (NYSEAMER) (NYSEArca) (NYSENAT) (PEARL) (Phlx) 

market_index = str(us_exchange_codes[exchange][1])
market_ticker = yf.Ticker(market_index)
market_info = market_ticker.info

market_history = market_ticker.history(period="3y")
market_closing_prices = market_history['Close']
market_history['Returns'] = market_history['Close'].pct_change().dropna()
market_returns = market_closing_prices.pct_change().dropna()

covariance = np.cov(market_returns.dropna().values, returns.dropna().values)[0, 1]

levered_beta = covariance/variance_returns

def get_bond_data():
    bonds_url = 'https://www.worldgovernmentbonds.com/'
    bd_resp = requests.get(bonds_url)
    soup = BeautifulSoup(bd_resp.content, 'html.parser')
    bond_table = soup.find('table', {'class' : 'homeBondTable sortable w3-table money pd44 -f14'})

    bond_data = []
    for row in bond_table.find_all('tr'):
        row_data = []
        for cell in row.find_all('td'):
            row_data.append(cell.text)
        bond_data.append(row_data)
    bd_df = pd.DataFrame(bond_data).replace(r'\n|\t','',regex=True).replace('None', pd.NA)
    bd_df.drop(bd_df.columns[0],axis=1, inplace=True)
    bd_df = bd_df.drop([0,1])
    bd_df = bd_df[:-1]
    bd_df.columns = ['Country', 'S&P Rating', '10yr Bond Yield', 'Empty', 'Bank Rate', 'Spread vs Bund', 'Spread vs T-Note', 'Spread vs Bank Rate']
    bd_df = bd_df.replace(r"^ +| +$", r"", regex=True)
    bd_df['10yr Bond Yield'] = bd_df['10yr Bond Yield'].str.rstrip('%').astype('float')/100
    bd_df.drop('Empty', axis=1, inplace = True)
    return bd_df

bond_data = get_bond_data()

bond_data.style

# print(bond_data.iloc[0]['10yr Bond Yield'])

def print_bond_yields():
    print("10yr Bond Yield:")
    for i in range(len(bond_data)):
        print(f"{bond_data.iloc[i]['Country']}: {bond_data.iloc[i]['10yr Bond Yield']}")
    return None


us_bond_yield = bond_data.loc[bond_data['Country'] == 'United States', '10yr Bond Yield'].values[0]

def default_spread():
    bond_data['Spread'] = bond_data['10yr Bond Yield'] - us_bond_yield
    return bond_data

spread_table = default_spread()[['Country', '10yr Bond Yield', 'Spread']]

def expected_market_return():
    erm = market_history['Returns'].iloc[-1]
    return erm

erm = expected_market_return()

us_mature_erp = erm - us_bond_yield

today = dt.date.today()

company_ticker = stock #VZ, AMZN, WMG

pd.options.display.float_format = (
    lambda x: "{:,.0f}".format(x) if int(x) == x else "{:,.2f}".format(x)
)

headers = {
    'User-Agent' : 'maxbushala@gmail.com'
    }

# CHECK THIS OUT: https://www.sec.gov/Archives/edgar/data/1319161/000131916123000036/wmg-20230930.xsd
statement_keys_map = {
    "balance_sheet": [
        "balance sheet",
        "balance sheets",
        "statement of financial position",
        "consolidated balance sheets",
        "consolidated balance sheet",
        "consolidated financial position",
        "consolidated balance sheets - southern",
        "consolidated statements of financial position",
        "consolidated statement of financial position",
        "consolidated statements of financial condition",
        "combined and consolidated balance sheet",
        "condensed consolidated balance sheets",
        "consolidated balance sheets, as of december 31",
        "dow consolidated balance sheets",
        "consolidated balance sheets (unaudited)",
    ],
    "income_statement": [
        "income statement",
        "income statements",
        "statement of earnings (loss)",
        "statements of consolidated income",
        "consolidated statements of operations",
        "consolidated statement of operations",
        "consolidated statements of earnings",
        "consolidated statement of earnings",
        "consolidated statements of income",
        "consolidated statement of income",
        "consolidated income statements",
        "consolidated income statement",
        "condensed consolidated statements of earnings",
        "consolidated results of operations",
        "consolidated statements of income (loss)",
        "consolidated statements of income - southern",
        "consolidated statements of operations and comprehensive income",
        "consolidated statements of comprehensive income",
    ],
    "cash_flow_statement": [
        "cash flows statement",
        "cash flows statements",
        "statement of cash flows",
        "statements of consolidated cash flows",
        "consolidated statements of cash flows",
        "consolidated statement of cash flows",
        "consolidated statement of cash flow",
        "consolidated cash flows statements",
        "consolidated cash flow statements",
        "condensed consolidated statements of cash flows",
        "consolidated statements of cash flows (unaudited)",
        "consolidated statements of cash flows - southern",
    ],
}

statement_keys_map_scraped = None

operating_lease_items = ['LesseeOperatingLeaseLiabilityPaymentsDueNextTwelveMonths', 'us-gaap:LesseeOperatingLeaseLiabilityPaymentsDueYearTwo', 'us-gaap:LesseeOperatingLeaseLiabilityPaymentsDueYearThree', 'us-gaap:LesseeOperatingLeaseLiabilityPaymentsDueYearFour', 'us-gaap:LesseeOperatingLeaseLiabilityPaymentsDueYearFive', 'us-gaap:LesseeOperatingLeaseLiabilityPaymentsDueAfterYearSix']

def get_CIKs() -> dict:
    """
    Companies are indexed by CIK number on SEC's EDGAR.

    get_CIKs retrieves all company CIKs from SEC's EDGAR

    Returns:
        dict: company CIKs from the SEC's EDGAR.
        "Failed to retrieve data" (str): returns error string if CIK data could not be accessed with HTTP request.
    """
    
    tickers_url = 'https://www.sec.gov/files/company_tickers.json'

    cik_response = requests.get(tickers_url, headers = headers)

    if cik_response.status_code == 200:
        companyTickers = cik_response.json()
        return companyTickers
    else:
        return "Failed to retrieve data."
    
def get_company_CIK(company_ticker, sec_CIKs):
    """
    get_company_CIK retrieves a specific company's CIK using the company's ticker to search CIK from the list of CIKs in EDGAR.

    CIKs are 10 digit identifiers with leading 0s in the number. Company CIKs in the dictionary are missing leading 0s so we add them back.

    Params:
        company_ticker (str): company ticker to search
        sec_CIKs (dict): company CIKs for all companies listed in SEC's EDGAR
    
    Returns:
        company_CIK_adjusted (str): company CIK for the company being searched
        "No CIK found for {company_ticker}" (str): returns error string if company ticker is not listed in EDGAR.
    """
    sec_CIKs_length = len(sec_CIKs) - 1
    for i in range(0, sec_CIKs_length):
        if sec_CIKs[str(i)]['ticker'].lower() == company_ticker.lower():
            # add leading 0s
            company_CIK_adjusted = str(sec_CIKs[str(i)]['cik_str']).zfill(10)
            return company_CIK_adjusted
    return f"No CIK found for {company_ticker}"

sec_CIKs = get_CIKs()
company_CIK = get_company_CIK(company_ticker, sec_CIKs)


def get_filing_data(company_CIK):
    """
    get_filing_data retrieves company filings for the company being searched.

    Params:
        company_CIK (str): CIK of the company being searched in EDGAR
    
    Returns:
        filingMetadata ()
    """
    filingMetadata = requests.get(f'https://data.sec.gov/submissions/CIK{company_CIK}.json', headers=headers)
    if filingMetadata.status_code == 200:
        return filingMetadata.json()
    return "Failed to retrieve data."

filingData = get_filing_data(company_CIK)

def companyFacts(company_CIK):
    """
    companyFacts retrieves XBRL company facts for the company being searched.

    Params:
        company_CIK (str): CIK of the company being searched in EDGAR
    
    Returns:
        dict: JSON response containing XBRL company facts.
    """
    companyFacts = requests.get(f'https://data.sec.gov/api/xbrl/companyfacts/CIK{company_CIK}.json', headers=headers).json()
    return companyFacts

company_facts = companyFacts(company_CIK)['facts']['us-gaap']
labels_dict = {fact: details["label"] for fact, details in company_facts.items()}

filing_dataframe = pd.DataFrame.from_dict(filingData['filings']['recent']) # all the recent filings



#! Switch this to 10Qs and sum four for annual report 
def get_10K(filings_df):
    """
    get_10K filters a filings DataFrame for the most recent 10-K filing.

    Params:
        filings_df (pd.DataFrame): DataFrame containing filings data
    
    Returns:
        pd.Series: A pandas Series for the most recent 10-K filing.
    """
    df_10K = filings_df[filings_df['form'] == '10-K']
    most_recent_10K = df_10K.sort_values(by='reportDate', ascending=False).head(1)
    # print(f"\nMost Recent 10K:\n{most_recent_10K}")
    return most_recent_10K.iloc[0]

def get_accession_number(most_recent_10K) -> str:
    """
    get_accession_number extracts the accession number from a Series representing the most recent 10-K filing.

    Params:
        most_recent_10K (pd.Series): A pandas Series representing the most recent 10-K filing.
    
    Returns:
        str: Accession number of the most recent 10-K filing.
    """
    return most_recent_10K['accessionNumber']

def get_primaryDocument(most_recent_10K):
    """
    get_primaryDocument gets the primary document for the most recent 10K.

    """
    return most_recent_10K['primaryDocument']

def get_report_date(most_recent_10K):
    return most_recent_10K['reportDate']

current_10K = get_10K(filing_dataframe)

accession_number = get_accession_number(current_10K).replace('-', '')
primaryDocument = get_primaryDocument(current_10K)
report_date = get_report_date(current_10K)

primaryDocument_no_extension = str(primaryDocument).split('.')[0]

form10K_url = f"https://www.sec.gov/Archives/edgar/data/{company_CIK}/{accession_number}/{primaryDocument_no_extension}_htm.xml"
#form10K_url = f"https://www.sec.gov/ixviewer/ix.html?doc=/Archives/edgar/data/{company_CIK}/{accession_number}/{primaryDocument}.htm"

def xml_to_dict(url):
    """
    Converts XML data from a specified URL to a JSON-like dictionary.
    
    Parameters:
    - url (str): The URL string of the XML data to be fetched and converted.
    
    Returns:
    - dict: A dictionary representing the parsed XML data. The structure of the dictionary
            matches the structure of the original XML, with tags as keys and tag contents
            as values.
    - None: Returns None if the request to the URL does not succeed (i.e., the HTTP status
            code is not 200).
    """
    xml_response = requests.get(url, headers=headers)
    if xml_response.status_code == 200:
        xml_content = xml_response.content
        # xml_json = json.dumps(xmltodict.parse(xml_content))
        xml_dict = xmltodict.parse(xml_content)
        return xml_dict
    return None

xml_parsed = xml_to_dict(form10K_url)

financialdata = xml_parsed['xbrl'] # THIS WOULD BE THE ONE TO USe ARELLE / PYTHON-XBRL LIBRARIES ON!!!
# print(financialdata.keys())

# usgaap_financials = {k: v for k, v in xml_parsed['xbrl'].items() if k.startswith('us-gaap')}
# print("\nUS-GAAP Financial Statements:\n")
# print(usgaap_financials.keys())

def save_doc(k, v, location):
    html_file = open(f"{location}/{k}.html", "w")
    try:
        print(f"Wrote {k} to html file.")
        # print(f"{type(v)}")
        if(type(v) is list):
            for i in v:
                if(k=='dei:SecurityExchangeName'):
                    print(i)
                html_file.write(str(i))
        elif(type(v) is dict):
            if(k=='000'):
                print(str(v['#text']))
            html_file.write(str(v['#text']))
        if(k=='000'):
            print(f"{v}")
    except:
        print(f"\nError writing html for {k}.")
        print(f"{type(v)}")
        print(f"{v}")
        html_file.close()
        os.remove(f"{location}/{k}.html")
    html_file.close()
    return

def save_data(financialdata):
    root_path = os.path.expanduser('~')
    print(root_path)
    location = f'{root_path}/Downloads/{company_ticker}FinancialData'

    # Open folder
    if not os.path.exists(location):
        os.makedirs(location)
        print(f"\nFolder '{location}' created.")
    else:
        print(f"\nFolder '{location}' already exists.")
        shutil.rmtree(f'{location}')
        print(f"\nFolder '{location}' deleted.")
        os.makedirs(location)
        print(f"\nFolder '{location}' created.")

    # Save HTML files with financial data to the folder
    for k, v in financialdata.items():
        save_doc(k, v, location)
    return None

def get_namespaces(url):
    # Fetch the content from the URL
    response = requests.get(url, headers = headers)
    if response.status_code == 200:
        # Parse the XML content from the response
        tree = etree.fromstring(response.content)
        
        # Extract namespaces from the root element
        namespaces = tree.nsmap
        
        # Handle the default namespace, if necessary
        if None in namespaces:
            default_ns_uri = namespaces[None]
            namespaces['default'] = default_ns_uri
            del namespaces[None]
        
        return namespaces
    else:
        raise ValueError("Failed to retrieve content from URL")

namespaces = get_namespaces(form10K_url)

def _get_file_name(report):
    """
    Extracts the file name from an XML report tag.

    Args:
        report (Tag): BeautifulSoup tag representing the report.

    Returns:
        str: File name extracted from the tag.
    """
    html_file_name_tag = report.find("HtmlFileName")
    xml_file_name_tag = report.find("XmlFileName")
    # Return the appropriate file name
    if html_file_name_tag:
        return html_file_name_tag.text
    elif xml_file_name_tag:
        return xml_file_name_tag.text
    else:
        return ""


def _is_statement_file(short_name_tag, long_name_tag, file_name):
    """
    Determines if a given file is a financial statement file.

    Args:
        short_name_tag (Tag): BeautifulSoup tag for the short name.
        long_name_tag (Tag): BeautifulSoup tag for the long name.
        file_name (str): Name of the file.

    Returns:
        bool: True if it's a statement file, False otherwise.
    """
    return (
        short_name_tag is not None
        and long_name_tag is not None
        and file_name  # Ensure file_name is not an empty string
        and "Statement" in long_name_tag.text
    )

def get_statement_file_names_in_filing_summary(ticker, accession_number, headers=None):
    """
    Retrieves file names of financial statements from a filing summary.

    Args:
        ticker (str): Stock ticker symbol.
        accession_number (str): SEC filing accession number.
        headers (dict): Headers for HTTP request.

    Returns:
        dict: Dictionary mapping statement types to their file names.
    """
    try:
        # Set up request session and get filing summary
        session = requests.Session()
        cik = company_CIK
        base_link = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_number}"
        filing_summary_link = f"{base_link}/FilingSummary.xml"
        filing_summary_response = session.get(
            filing_summary_link, headers=headers
        ).content.decode("utf-8")

        # Parse the filing summary
        filing_summary_soup = BeautifulSoup(filing_summary_response, "lxml-xml")
        statement_file_names_dict = {}
        # Extract file names for statements
        for report in filing_summary_soup.find_all("Report"):
            file_name = _get_file_name(report)
            short_name, long_name = report.find("ShortName"), report.find("LongName")
            if _is_statement_file(short_name, long_name, file_name):
                statement_file_names_dict[short_name.text.lower()] = file_name
        return statement_file_names_dict
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return {}

def get_taxonomy():
    taxonomy_url = f"https://www.sec.gov/Archives/edgar/data/{company_CIK.lstrip('0')}/{accession_number}/{primaryDocument_no_extension}.xsd"
    taxonomy_resp = requests.get(taxonomy_url, headers=headers)
    root = etree.fromstring(taxonomy_resp.content)
    nsmap = {'link': namespaces['link']}
    definitions = root.xpath('//link:definition', namespaces=nsmap)
    organized_list = []
    for _def in definitions:
        text = _def.text
        parts = text.split(' - ')
        organized_list.append(parts[1:])
    unique_tags = set([sublist[0] for sublist in organized_list])
    return [organized_list, definitions]

def get_filing_matches(substring, taxonomy_defs):
    matches = []
    for _def in taxonomy_defs:
        text = _def.text
        if substring in text:
            matches.append(text)
    return list(set(matches))

def get_statement_soup(ticker, accession_number, statement_name, headers, statement_keys_map):
    """
    Retrieves the BeautifulSoup object for a specific financial statement.

    Args:
        ticker (str): Stock ticker symbol.
        accession_number (str): SEC filing accession number.
        statement_name (str): has to be 'balance_sheet', 'income_statement', 'cash_flow_statement'
        headers (dict): Headers for HTTP request.
        statement_keys_map (dict): Mapping of statement names to keys.

    Returns:
        BeautifulSoup: Parsed HTML/XML content of the financial statement.

    Raises:
        ValueError: If the statement file name is not found or if there is an error fetching the statement.
    """
    session = requests.Session()
    base_link = f"https://www.sec.gov/Archives/edgar/data/{company_CIK}/{accession_number}"
    # Get statement file names
    statement_file_name_dict = get_statement_file_names_in_filing_summary(
        ticker, accession_number, headers
    )
    statement_link = None
    # Find the specific statement link
    for possible_key in statement_keys_map.get(statement_name.lower(), []):
        file_name = statement_file_name_dict.get(possible_key.lower())
        if file_name:
            statement_link = f"{base_link}/{file_name}"
            break
    if not statement_link:
        raise ValueError(f"Could not find statement file name for {statement_name}")
    # Fetch the statement
    try:
        statement_response = session.get(statement_link, headers=headers)
        statement_response.raise_for_status()  # Check for a successful request
        # Parse and return the content
        if statement_link.endswith(".xml"):
            return BeautifulSoup(
                statement_response.content, "lxml-xml", from_encoding="utf-8"
            )
        else:
            return BeautifulSoup(statement_response.content, "lxml")
    except requests.RequestException as e:
        raise ValueError(f"Error fetching the statement: {e}")

def get_table_from_url(url):
    # Fetch the page content
    try:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()  # Check for HTTP request errors
    except Exception as e:
        print(f"Error fetching the page: {e}")
        return None

    # Parse the HTML content
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find the first table
    table = soup.find('table')
    
    # Read the table into a DataFrame
    df = pd.read_html(str(table))[0]
    
    return df

country_equity_risk_premiums = get_table_from_url('https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/ctryprem.html')
rev_multiples = get_table_from_url('https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/psdata.html')
sector_betas = get_table_from_url('https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/Betas.html')
sector_cost_of_equity_and_capital = get_table_from_url('https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/wacc.htm')
sector_price_and_value_to_book_ratio = get_table_from_url('https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/pbvdata.html')


us_erp_data = country_equity_risk_premiums[country_equity_risk_premiums[0] == 'United States']
us_corporate_tax_rate = us_erp_data.iloc[0, 4]

input_data = {
    'Total Revenue' : fiscal_year['income_statements'].loc['Total Revenue'],
    'Operating Income' : fiscal_year['income_statements'].loc['Operating Income'],
    'Interest Expense' : fiscal_year['income_statements'].loc['Interest Expense'],
    'Book Value of Equity' : fiscal_year['balance_sheets'].loc['Total Equity Gross Minority Interest'],
    'Book Value of Debt' : fiscal_year['balance_sheets'].loc['Total Debt'],
    'Cash and Marketable Securities' : fiscal_year['balance_sheets'].loc['Cash Cash Equivalents And Short Term Investments'],
    'Cross Holdings and Non-Operating Assets' : fiscal_year['balance_sheets'].loc['Long Term Equity Investment'],
    'Minority Interest' : fiscal_year['balance_sheets'].loc['Minority Interest']
}



linear_input_data = {
    'Has R&D Expenses' : True,
    'Has Operating Leases' : True,
    'Current Shares Outstanding' : info.get('sharesOutstanding'),
    'Current Stock Price' : closing_prices.iloc[-1],
    'Effective Tax Rate' : fiscal_year['income_statements'].loc['Tax Rate For Calcs'].iloc[0],
    'Marginal Tax Rate' : 0,
}

substring = "Schedule of Operating Lease Liability Maturity"

taxonomy_definitions = get_taxonomy()[1]

statements_names = get_statement_file_names_in_filing_summary(company_ticker, accession_number, headers)

statement = financialdata.keys()

input_df = pd.DataFrame(input_data).T

linear_input_df = pd.DataFrame([linear_input_data]).T

################################################################################################################################################################################################################################
# RUNNING SCRIPT

print("\n______________________________________________________________________________________________________________________________________________________________________________")
print(f"____________________________________________________________________________VALUATION OF {company_ticker}__________________________________________________________________________________")
print("______________________________________________________________________________________________________________________________________________________________________________\n")

print("\nCompany Information:\n"+str(info))

print("\nExchange:\n"+str(exchange))

print("\nMost Recent Market Return:\n"+str(erm))

print("\nBeta:\n" + str(levered_beta))

print(f"\nSpreads:\n{spread_table}")

print(f"\nUS Bond Yield:\n{us_bond_yield}")

print(f"\nMature Market Equity Risk Premium:\n {us_mature_erp}")

print(f"\nReport Data Frame:\n{filing_dataframe['reportDate']}")

# save_data(financialdata)

print("\ncompany_CIK:\n" + str(company_CIK))

print("\naccession_number:\n" + str(accession_number))

print("\nprimaryDocument:\n" + str(primaryDocument))

print("\nreportDate:\n" + str(report_date))

print("\nNamespaces:\n" + str(namespaces))

print(f"\nMost Recent 10K:\n{current_10K}")

print("\nForm 10K URL:\n" + str(form10K_url))

# print(f"\n{financialdata.keys()}")

print("\nFinancial Statements:\n" + str(statements_names))

# print(f"\nMatch for {substring}:\n" + str(get_filing_matches(substring, taxonomy_definitions)[0]))

print("\nFinancial Statement Keys:\n" + str(statement))

print("\n______________________________________________________________________________________________________________________________________________________________________________\n")

print('\nFinancial Statement Data:\n')
print('\nIncome Statements')
print(quarterly['income_statements'].index)
print('\nBalance Sheets')
print(quarterly['balance_sheets'].index)
print('\nCash Flows')
print(quarterly['cash_flows'].index)
print()

print ('\nFiscal Year\n______________\n')
print('\nIncome Statements')
print(fiscal_year['income_statements'])
print('\nBalance Sheets')
print(fiscal_year['balance_sheets'])
print('\nCash Flows')
print(fiscal_year['cash_flows'])
print('')

print ('\nQuarterly\n______________\n')
print('\nIncome Statements')
print(quarterly['income_statements'])
print('\nBalance Sheets')
print(quarterly['balance_sheets'])
print('\nCash Flows')
print(quarterly['cash_flows'])
print('')

print("\n______________________________________________________________________________________________________________________________________________________________________________\n")

print ('\nExternal Data (from Aswath Damodaran):\n__________________________________')

print("\nCountry Equity Risk Premium Data:\n" + str(country_equity_risk_premiums))

print("\nUS Sector Revenue Multiples Data:\n" + str(rev_multiples))

print("\nUS Sector Beta Data:\n" + str(sector_betas))

print("\nUS Sector Cost of Equity and Capital Data:\n" + str(sector_cost_of_equity_and_capital))

print("\nUS Sector Price and Value to Book Ratio Data:\n" + str(sector_price_and_value_to_book_ratio))

print("\n______________________________________________________________________________________________________________________________________________________________________________\n")

print ('\nInput Data to Return:\n______________')

print("\nInput Data\n" + str(input_df))

print("\nLinear Input Data\n" + str(linear_input_df))



print("US Corporate Tax Rate" + str(type(us_corporate_tax_rate)))