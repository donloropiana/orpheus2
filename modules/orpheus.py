import requests
import pandas as pd
import xmltodict
from bs4 import BeautifulSoup
import os, shutil
from lxml import etree
import numpy as np
import yfinance as yf
import datetime as dt
from neuralprophet import NeuralProphet, set_log_level
from neuralprophet import set_random_seed
from matplotlib import pyplot as plt
import time
import plotly.express as px
import statsmodels.api as sm
from pandas.tseries.holiday import USFederalHolidayCalendar
import re

# ================================================================================================================================================================================================== #

class valuation:
    def __init__(self, ticker):
        self.ticker = ticker
        self.valuation = None
        self.headers = {
            'User-Agent' : 'maxbushala@gmail.com'
        }
        
    def get_bond_data(self):
        bonds_url = 'https://www.worldgovernmentbonds.com/'
        bd_resp = requests.get(bonds_url, headers=self.headers)
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
    
    def print_bond_yields(self, bond_data):
        print("10yr Bond Yield:")
        for i in range(len(bond_data)):
            print(f"{bond_data.iloc[i]['Country']}: {bond_data.iloc[i]['10yr Bond Yield']}")
        return None
    
    def default_spread(self, bond_data, us_bond_yield):
        bond_data['Spread'] = bond_data['10yr Bond Yield'] - us_bond_yield
        return bond_data
    
    def expected_market_return(self, market_history):
        erm = market_history['Returns'].iloc[-1]
        return erm
    
    def get_CIKs(self) -> dict:
        """
        Companies are indexed by CIK number on SEC's EDGAR.

        get_CIKs retrieves all company CIKs from SEC's EDGAR

        Returns:
            dict: company CIKs from the SEC's EDGAR.
            "Failed to retrieve data" (str): returns error string if CIK data could not be accessed with HTTP request.
        """
        tickers_url = 'https://www.sec.gov/files/company_tickers.json'

        cik_response = requests.get(tickers_url, headers = self.headers)

        if cik_response.status_code == 200:
            companyTickers = cik_response.json()
            return companyTickers
        else:
            return "Failed to retrieve data."
        
    def get_company_CIK(self, company_ticker, sec_CIKs):
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
    
    def get_filing_data(self, company_CIK):
        """
        get_filing_data retrieves company filings for the company being searched.

        Params:
            company_CIK (str): CIK of the company being searched in EDGAR

        Returns:
            filingMetadata ()
        """
        filingMetadata = requests.get(f'https://data.sec.gov/submissions/CIK{company_CIK}.json', headers=self.headers)
        if filingMetadata.status_code == 200:
            return filingMetadata.json()
        return "Failed to retrieve data."
    
    def companyFacts(self, company_CIK):
        """
        companyFacts retrieves XBRL company facts for the company being searched.

        Params:
            company_CIK (str): CIK of the company being searched in EDGAR

        Returns:
            dict: JSON response containing XBRL company facts.
        """
        companyFacts = requests.get(f'https://data.sec.gov/api/xbrl/companyfacts/CIK{company_CIK}.json', headers=self.headers).json()
        return companyFacts
    #! Switch this to 10Qs and sum four for annual report
    
    def get_10K(self, filings_df):
        """
        get_10K filters a filings DataFrame for the most recent 10-K filing.

        Params:
            filings_df (pd.DataFrame): DataFrame containing filings data

        Returns:
            pd.Series: A pandas Series for the most recent 10-K filing.
        """
        df_10K = filings_df[filings_df['form'] == '10-K']
        most_recent_10K = df_10K.sort_values(by='reportDate', ascending=False).head(1)
        return most_recent_10K.iloc[0]
    
    def get_accession_number(self, most_recent_10K) -> str:
        """
        get_accession_number extracts the accession number from a Series representing the most recent 10-K filing.

        Params:
            most_recent_10K (pd.Series): A pandas Series representing the most recent 10-K filing.

        Returns:
            str: Accession number of the most recent 10-K filing.
        """
        return most_recent_10K['accessionNumber']

    def get_primaryDocument(self, most_recent_10K):
        """
        get_primaryDocument gets the primary document for the most recent 10K.

        """
        return most_recent_10K['primaryDocument']

    def get_report_date(self, most_recent_10K):
        return most_recent_10K['reportDate']

    def xml_to_dict(self, url):
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
        xml_response = requests.get(url, headers=self.headers)
        if xml_response.status_code == 200:
            xml_content = xml_response.content
            xml_dict = xmltodict.parse(xml_content)
            return xml_dict
        return None
    
    def save_doc(self, k, v, location):
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
    
    def save_data(self, financialdata, company_ticker):
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
            self.save_doc(k, v, location)
        return None
    
    def get_namespaces(self, url):
        # Fetch the content from the URL
        response = requests.get(url, headers = self.headers)
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

    def _get_file_name(self, report):
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


    def _is_statement_file(self, short_name_tag, long_name_tag, file_name):
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

    def get_statement_file_names_in_filing_summary(self, company_CIK, accession_number):
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
                filing_summary_link, headers=self.headers
            ).content.decode("utf-8")

            # Parse the filing summary
            filing_summary_soup = BeautifulSoup(filing_summary_response, "lxml-xml")
            statement_file_names_dict = {}
            # Extract file names for statements
            for report in filing_summary_soup.find_all("Report"):
                file_name = self._get_file_name(report)
                short_name, long_name = report.find("ShortName"), report.find("LongName")
                if self._is_statement_file(short_name, long_name, file_name):
                    statement_file_names_dict[short_name.text.lower()] = file_name
            return statement_file_names_dict
        except requests.RequestException as e:
            print(f"An error occurred: {e}")
            return {}

    def get_taxonomy(self, company_CIK, accession_number, primaryDocument_no_extension, namespaces):
        taxonomy_url = f"https://www.sec.gov/Archives/edgar/data/{company_CIK.lstrip('0')}/{accession_number}/{primaryDocument_no_extension}.xsd"
        taxonomy_resp = requests.get(taxonomy_url, headers=self.headers)
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

    def get_filing_matches(self, substring, taxonomy_defs):
        matches = []
        for _def in taxonomy_defs:
            text = _def.text
            if substring in text:
                matches.append(text)
        return list(set(matches))

    def get_statement_soup(self, ticker, accession_number, company_CIK, statement_name, statement_keys_map):
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
        statement_file_name_dict = self.get_statement_file_names_in_filing_summary(
            ticker, accession_number, self.headers
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
            statement_response = session.get(statement_link, headers=self.headers)
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

    def get_table_from_url(self, url):
        # Fetch the page content
        try:
            response = requests.get(url, headers=self.headers, verify=False)
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

    def get_second_table_from_url(self, url):
        try:
            response = requests.get(url, headers=self.headers, verify=False)
            response.raise_for_status()
        except Exception as e:
            print(f"Error fetching the page: {e}")
            return None

        soup = BeautifulSoup(response.content, 'html.parser')

        table = soup.find('table')

        df = pd.read_html(str(table))[1]

        return df

    # Function to search for the closest match
    def find_closest_match(self, countries, pattern):
        for country in countries:
            if pattern.search(country):
                return country
        return None

    def cost_of_capital_worksheet(self):
        equity_data = {
            'shares_outstanding' : 1,
            'market_price_per_share' : 1,
            'unlevered_beta' : 1,
            'risk_free_rate' : 1,
            'erp_for_cost_of_equity' : 1,
        }

        debt_data = {
            'book_value_of_straight_debt' : 1,
            'interest_expense_on_straight_debt' : 1,
            'avg_maturity_of_debt' : 1,
            'moodys_rating' : 1,
            'pretax_cost_of_debt' : 1,
            'tax_rate' : 1,
            'book_value_of_convertible_debt' : 1,
            'interest_expense_on_convertible_debt' : 1,
            'debt_value_of_operating_leases' : 1,
            'interest_coverage_ratio' : 1,
        }

        preferred_stock_data = {
            'preferred_shares' : 1,
            'preferred_share_market_price' : 1,
            'dividend_per_preferred_share' : 1, # preferred (I think), might be common
        }

        operating_countries_erp_data = {
            'Country 1' : {
                'Name' : 1,
                'Revenue' : 1,
                'ERP' : 1,
                'Weight' : 1,
                'Weighted ERP' : 1,
            },
            'Country 2' : {
                'Name' : 1,
                'Revenue' : 1,
                'ERP' : 1,
                'Weight' : 1,
                'Weighted ERP' : 1,
            },
            'Country 3' : {
                'Name' : 1,
                'Revenue' : 1,
                'ERP' : 1,
                'Weight' : 1,
                'Weighted ERP' : 1,
            },
            'Country 4' : {
                'Name' : 1,
                'Revenue' : 1,
                'ERP' : 1,
                'Weight' : 1,
                'Weighted ERP' : 1,
            },
            'Country 5' : {
                'Name' : 1,
                'Revenue' : 1,
                'ERP' : 1,
                'Weight' : 1,
                'Weighted ERP' : 1,
            },
            'Country 6' : {
                'Name' : 1,
                'Revenue' : 1,
                'ERP' : 1,
                'Weight' : 1,
                'Weighted ERP' : 1,
            },
            'Country 7' : {
                'Name' : 1,
                'Revenue' : 1,
                'ERP' : 1,
                'Weight' : 1,
                'Weighted ERP' : 1,
            },
            'Country 8' : {
                'Name' : 1,
                'Revenue' : 1,
                'ERP' : 1,
                'Weight' : 1,
                'Weighted ERP' : 1,
            },
            'Country 9' : {
                'Name' : 1,
                'Revenue' : 1,
                'ERP' : 1,
                'Weight' : 1,
                'Weighted ERP' : 1,
            },
            'Country 10' : {
                'Name' : 1,
                'Revenue' : 1,
                'ERP' : 1,
                'Weight' : 1,
                'Weighted ERP' : 1,
            },
            'Country 11' : {
                'Name' : 1,
                'Revenue' : 1,
                'ERP' : 1,
                'Weight' : 1,
                'Weighted ERP' : 1,
            },
            'Rest of World' : {
                'Name' : 'Rest of World', # this might be under many names, such as international, etc.
                'Revenue' : 1,
                'ERP' : 1,
                'Weight' : 1,
                'Weighted ERP' : 1,
            },
        }

        output_data = {
            '1' : {
                'estimated_market_value_of_straight_debt' : 1,
                'estimated_value_of_straight_debt_in_convertible' : 1,
                'value_of_debt_in_operating_leases' : 1,
                'estimated_value_of_equity_in_convertible' : 1,
                'levered_beta_for_equity' : 1,
            },
            '2' : {
                'equity' : {
                    'market_value' : 1,
                    'weight_in_cost_of_capital' : 1,
                    'cost_of_component' : 1,
                },
                'debt' : {
                    'market_value' : 1,
                    'weight_in_cost_of_capital' : 1,
                    'cost_of_component' : 1,
                },
                'preferred_stock' : {
                    'market_value' : 1,
                    'weight_in_cost_of_capital' : 1,
                    'cost_of_component' : 1,
                },
                'capital' : {
                    'market_value' : 1,
                    'weight_in_cost_of_capital' : 1,
                    'cost_of_component' : 1,
                }
            },
        }

        debt_data['pretax_cost_of_debt'] = equity_data['risk_free_rate'] + debt_data['moodys_rating']

        return equity_data, debt_data, preferred_stock_data, operating_countries_erp_data, output_data

    def fix_df(self, temp_df):
        # Check if the first row is numeric by attempting to convert it to numeric and checking for NaN
        first_row_numeric_check = temp_df.iloc[0].apply(lambda x: pd.to_numeric(x, errors='coerce'))

        # If the entire first row converts to numeric without any NaNs, assume it's not headers
        if not first_row_numeric_check.isna().any():
            # Drop the first row and reset the index
            temp_df = temp_df.drop(temp_df.index[0]).reset_index(drop=True)

        # Set the next row as headers
        temp_df.columns = temp_df.iloc[0]
        temp_df = temp_df.drop(temp_df.index[0])
        temp_df.reset_index(drop=True, inplace=True)

        # Converting data types in each column
        for column in temp_df.columns:
            if temp_df[column].dtype == 'object':
                # Handle percentages
                if temp_df[column].str.contains('%').any():
                    temp_df[column] = temp_df[column].str.replace('%', '').astype(float) / 100
                # Attempt to convert strings to numbers where possible, leave as strings otherwise
                else:
                    temp_df[column] = pd.to_numeric(temp_df[column], errors='ignore')

        return temp_df

    def operating_lease_converter(self, input_data, debt_data): # finished
        current_opls_expense = input_data['Operating Leases']['Current Year Operating Lease Expense']
        yr1_opls_commitment = input_data['Operating Leases']['Year 1 Operating Lease Commitment']
        yr2_opls_commitment = input_data['Operating Leases']['Year 2 Operating Lease Commitment']
        yr3_opls_commitment = input_data['Operating Leases']['Year 3 Operating Lease Commitment']
        yr4_opls_commitment = input_data['Operating Leases']['Year 4 Operating Lease Commitment']
        yr5_opls_commitment = input_data['Operating Leases']['Year 5 Operating Lease Commitment']
        yr5andbeyond_opls_commitment = input_data['Operating Leases']['Year 5 and Beyond Operating Lease Commitment']
        yr6andbeyond_opls_commitment = input_data['Operating Leases']['Year 6 and Beyond Operating Lease Commitment']
        pretax_cost_of_debt = debt_data['pretax_cost_of_debt']

        yrs_embedded_in_yr6_estimate = round(yr6andbeyond_opls_commitment / np.average([yr1_opls_commitment,yr2_opls_commitment,yr3_opls_commitment,yr4_opls_commitment,yr5_opls_commitment])) if yr6andbeyond_opls_commitment > 0 else 0 # =IF(yr6andbeyond_opls_commitment >0,ROUND(yr6andbeyond_opls_commitment /AVERAGE(yr1_opls_commitment : yr5_opls_commitment),0),0)

        opls_to_debt = {
            'year 1' : yr1_opls_commitment/((1+pretax_cost_of_debt)**1), # = Year 1 Commitment /(1 + Pretax Cost of Debt)^Year
            'year 2' : yr2_opls_commitment/((1+pretax_cost_of_debt)**2),
            'year 3' : yr3_opls_commitment/((1+pretax_cost_of_debt)**3),
            'year 4' : yr4_opls_commitment/((1+pretax_cost_of_debt)**4),
            'year 5' : yr5_opls_commitment/((1+pretax_cost_of_debt)**5),
            'year 6 and beyond' : ( yr6andbeyond_opls_commitment * ( 1 - ( 1 + pretax_cost_of_debt ) ** ( - yr6andbeyond_opls_commitment )) / pretax_cost_of_debt ) / ( 1 + pretax_cost_of_debt ) ** 5 if yrs_embedded_in_yr6_estimate > 0 else yr6andbeyond_opls_commitment / ( 1 + pretax_cost_of_debt ) ** 6, #=IF(yrs_embedded_in_yr6_estimate>0,(yr6andbeyond_opls_commitment*(1-(1+pretax_cost_of_debt)**(-yr6andbeyond_opls_commitment))/pretax_cost_of_debt)/(1+pretax_cost_of_debt)**5,yr6andbeyond_opls_commitment/(1+pretax_cost_of_debt)**6), #
        }

        debt_value_of_leases = sum(opls_to_debt.values())
        depreciation_on_opls_asset = debt_value_of_leases / (5+yrs_embedded_in_yr6_estimate) # =debt_value_of_leases/(5+yrs_embedded_in_yr6_estimate)
        operating_earnings_adjustment = depreciation_on_opls_asset - current_opls_expense # =depreciation_on_opls_asset-current_opls_expense
        total_debt_outstanding_adjustment = debt_value_of_leases
        depreciation_adjustment = debt_value_of_leases / ( 5 + yrs_embedded_in_yr6_estimate)
        return debt_value_of_leases, depreciation_on_opls_asset, operating_earnings_adjustment, total_debt_outstanding_adjustment, depreciation_adjustment

    def research_and_development(self): # BUILD THIS OUT
        research_asset_value = 1
        return research_asset_value



    def synthetic_rating_worksheet(self, input_data, debt_data, debt_value_of_operating_leases): # BUILD THIS OUT
        firm_type = None # 1 or 2 (small or large firm)
        ebit = None # =IF(input_data['Other Inputs']['Has Operating Leases']=True, input_data['Other Inputs']['EBIT'] + 'Operating lease converter'!F32,'Input sheet'!B12)
        current_interest_expense = input_data['ltm']['Interest Expense'] + debt_value_of_operating_leases * debt_data['pretax_cost_of_debt'] if input_data['Other Inputs']['Has Operating Leases'] else input_data['ltm']['Interest Expense'] # if(input_data['Other Inputs']['Has Operating Leases']=True, input_data['ltm']['Interest Expense'] + debt_value_of_operating_leases * debt_data['pretax_cost_of_debt'], input_data['ltm']['Interest Expense'])
        long_term_risk_free_rate = input_data['Other Inputs']['Risk Free Rate']
        return None


    def valuation_comps(self, valuation_output_dictionary, input_data):
        projection_table = valuation_output_dictionary['projection_table']
        summary_table = valuation_output_dictionary['summary_table']
        implied_variables_table = valuation_output_dictionary['implied_variables_table']

        # Setting up Implied Variables table
        implied_variables_table['base_year']['Invested Capital'] = None # total_debt_outstanding_adjustment
        implied_variables_table['future_years']['Year 1']['Sales to Capital Ratio'] = input_data['Other Inputs']['Sales to Capial Ratio Years 1 to 5']
        implied_variables_table['future_years']['Year 2']['Sales to Capital Ratio'] = input_data['Other Inputs']['Sales to Capial Ratio Years 1 to 5']
        implied_variables_table['future_years']['Year 3']['Sales to Capital Ratio'] = input_data['Other Inputs']['Sales to Capial Ratio Years 1 to 5']
        implied_variables_table['future_years']['Year 4']['Sales to Capital Ratio'] = input_data['Other Inputs']['Sales to Capial Ratio Years 1 to 5']
        implied_variables_table['future_years']['Year 5']['Sales to Capital Ratio'] = input_data['Other Inputs']['Sales to Capial Ratio Years 1 to 5']
        implied_variables_table['future_years']['Year 6']['Sales to Capital Ratio'] = input_data['Other Inputs']['Sales to Capial Ratio Years 6 to 10']
        implied_variables_table['future_years']['Year 7']['Sales to Capital Ratio'] = input_data['Other Inputs']['Sales to Capial Ratio Years 6 to 10']
        implied_variables_table['future_years']['Year 8']['Sales to Capital Ratio'] = input_data['Other Inputs']['Sales to Capial Ratio Years 6 to 10']
        implied_variables_table['future_years']['Year 9']['Sales to Capital Ratio'] = input_data['Other Inputs']['Sales to Capial Ratio Years 6 to 10']
        implied_variables_table['future_years']['Year 10']['Sales to Capital Ratio'] = input_data['Other Inputs']['Sales to Capial Ratio Years 6 to 10']



        # Terminal Growth Rate    # =IF('Input sheet'!B67="Yes",'Input sheet'!B68,IF('Input sheet'!B64="Yes",'Input sheet'!B65,'Input sheet'!B34))
        if input_data['Other Inputs']['Override Long Term Growth Rate Assumption'] == True:
            projection_table['terminal_year']['Revenue Growth Rate'] = input_data['Other Inputs']['Alt Perpetuity Growth Rate']
        elif input_data['Other Inputs']['Override Risk Free Rate Prevalence in Perpetuity Assumption'] == True:
            projection_table['terminal_year']['Revenue Growth Rate'] = input_data['Other Inputs']['Alt Risk Free Rate']

        # future years projections
        for year in range(10): # counts year 0 to 9
                if (year+1) == 1: # if year + 1 == 1, then the dictionary column name is (year + 1)
                    # Set all the growth rates for the table
                    projection_table['future_years'][f'Year {year+1}']['Revenue Growth Rate'] = input_data['Other Inputs']['Revenue Growth Rate for Next Year'] # revenue growth rate for next year same as base year
                    projection_table['future_years'][f'Year {year+2}']['Revenue Growth Rate'] = input_data['Other Inputs']['Revenue Growth Rate for Next Year'] # year 2
                    projection_table['future_years'][f'Year {year+3}']['Revenue Growth Rate'] = input_data['Other Inputs']['Revenue Growth Rate for Next Year'] # year 3
                    projection_table['future_years'][f'Year {year+4}']['Revenue Growth Rate'] = input_data['Other Inputs']['Revenue Growth Rate for Next Year'] # year 4
                    projection_table['future_years'][f'Year {year+5}']['Revenue Growth Rate'] = input_data['Other Inputs']['Revenue Growth Rate for Next Year'] # year 5
                    projection_table['future_years'][f'Year {year+6}']['Revenue Growth Rate'] = projection_table['future_years'][f'Year {year+5}']['Revenue Growth Rate'] - ((projection_table['future_years'][f'Year {year+5}']['Revenue Growth Rate'] - projection_table['terminal_year']['Revenue Growth Rate'])/5)
                    projection_table['future_years'][f'Year {year+7}']['Revenue Growth Rate'] = projection_table['future_years'][f'Year {year+6}']['Revenue Growth Rate'] - ((projection_table['future_years'][f'Year {year+5}']['Revenue Growth Rate'] - projection_table['terminal_year']['Revenue Growth Rate'])/5)*2
                    projection_table['future_years'][f'Year {year+8}']['Revenue Growth Rate'] = projection_table['future_years'][f'Year {year+7}']['Revenue Growth Rate'] - ((projection_table['future_years'][f'Year {year+5}']['Revenue Growth Rate'] - projection_table['terminal_year']['Revenue Growth Rate'])/5)*3
                    projection_table['future_years'][f'Year {year+9}']['Revenue Growth Rate'] = projection_table['future_years'][f'Year {year+8}']['Revenue Growth Rate'] - ((projection_table['future_years'][f'Year {year+5}']['Revenue Growth Rate'] - projection_table['terminal_year']['Revenue Growth Rate'])/5)*4
                    projection_table['future_years'][f'Year {year+10}']['Revenue Growth Rate'] = projection_table['future_years'][f'Year {year+9}']['Revenue Growth Rate'] - ((projection_table['future_years'][f'Year {year+5}']['Revenue Growth Rate'] - projection_table['terminal_year']['Revenue Growth Rate'])/5)*5

                    # Set all the revenues for the table
                    projection_table['future_years'][f'Year {year+1}']['Revenue'] = projection_table['base_year']['Revenue']*(1 + projection_table['future_years'][f'Year {year+1}']['Revenue Growth Rate'])
                    projection_table['future_years'][f'Year {year+2}']['Revenue'] = projection_table['future_years'][f'Year {year+1}']['Revenue']*(1 + projection_table['future_years'][f'Year {year+2}']['Revenue Growth Rate'])
                    projection_table['future_years'][f'Year {year+3}']['Revenue'] = projection_table['future_years'][f'Year {year+2}']['Revenue']*(1 + projection_table['future_years'][f'Year {year+3}']['Revenue Growth Rate'])
                    projection_table['future_years'][f'Year {year+4}']['Revenue'] = projection_table['future_years'][f'Year {year+3}']['Revenue']*(1 + projection_table['future_years'][f'Year {year+4}']['Revenue Growth Rate'])
                    projection_table['future_years'][f'Year {year+5}']['Revenue'] = projection_table['future_years'][f'Year {year+4}']['Revenue']*(1 + projection_table['future_years'][f'Year {year+5}']['Revenue Growth Rate'])
                    projection_table['future_years'][f'Year {year+6}']['Revenue'] = projection_table['future_years'][f'Year {year+5}']['Revenue']*(1 + projection_table['future_years'][f'Year {year+6}']['Revenue Growth Rate'])
                    projection_table['future_years'][f'Year {year+7}']['Revenue'] = projection_table['future_years'][f'Year {year+6}']['Revenue']*(1 + projection_table['future_years'][f'Year {year+7}']['Revenue Growth Rate'])
                    projection_table['future_years'][f'Year {year+8}']['Revenue'] = projection_table['future_years'][f'Year {year+7}']['Revenue']*(1 + projection_table['future_years'][f'Year {year+8}']['Revenue Growth Rate'])
                    projection_table['future_years'][f'Year {year+9}']['Revenue'] = projection_table['future_years'][f'Year {year+8}']['Revenue']*(1 + projection_table['future_years'][f'Year {year+9}']['Revenue Growth Rate'])
                    projection_table['future_years'][f'Year {year+10}']['Revenue'] = projection_table['future_years'][f'Year {year+9}']['Revenue']*(1 + projection_table['future_years'][f'Year {year+10}']['Revenue Growth Rate'])
                    projection_table['terminal_year']['Revenue'] = projection_table['future_years'][f'Year {year+10}']['Revenue']*(1 + projection_table['terminal_year']['Revenue Growth Rate'])

                    projection_table['future_years'][f'Year {year+1}']['Operating Margin'] = projection_table['base_year']['Operating Margin']
                    projection_table['future_years'][f'Year {year+1}']['Operating Income'] = projection_table['future_years'][f'Year {year+1}']['Operating Margin'] * projection_table['future_years'][f'Year {year+1}']['Revenue']
                    projection_table['future_years'][f'Year {year+1}']['Tax Rate'] = projection_table['base_year']['Tax Rate']

                    # setting the year 1 NOPAT line item
                    if(projection_table['future_years'][f'Year {year+1}'].get('Operating Income', 0).item() > 0): # .iloc[0]
                        if(projection_table['future_years'][f'Year {year+1}']['Operating Income'].item() < projection_table['base_year']['NOL']): #
                            projection_table['future_years'][f'Year {year+1}']['NOPAT'] = projection_table['future_years'][f'Year {year+1}']['Operating Income']
                        else:
                            projection_table['future_years'][f'Year {year+1}']['NOPAT'] = projection_table['future_years'][f'Year {year+1}']['Operating Income'] - (projection_table['future_years'][f'Year {year+1}']['Operating Income'] - projection_table['base_year']['NOL']) * projection_table['future_years'][f'Year {year+1}']['Tax Rate']
                    else:
                        projection_table['future_years'][f'Year {year+1}']['NOPAT'] = projection_table['future_years'][f'Year {year+1}']['Operating Income']


                    # Reinvestment Rate
                    # # Year 1
                    if input_data['Other Inputs']['Override One Year Reinvestment to Growth Lag']==False:
                        projection_table['future_years']['Year 1']['Reinvestment'] = (projection_table['future_years']['Year 2']['Revenue'] - projection_table['future_years']['Year 1']['Revenue']) / implied_variables_table['future_years']['Year 1']['Sales to Capital Ratio']
                    elif input_data['Other Inputs']['Alt Lag'] == 0:
                        projection_table['future_years']['Year 1']['Reinvestment'] = (projection_table['future_years']['Year 1']['Revenue'] - projection_table['base_year']['Revenue']) / implied_variables_table['future_years']['Year 1']['Sales to Capital Ratio']
                    elif input_data['Other Inputs']['Alt Lag'] == 2:
                        projection_table['future_years']['Year 1']['Reinvestment'] = (projection_table['future_years']['Year 3']['Revenue'] - projection_table['future_years']['Year 2']['Revenue']) / implied_variables_table['future_years']['Year 1']['Sales to Capital Ratio']
                    elif input_data['Other Inputs']['Alt Lag'] == 3:
                        projection_table['future_years']['Year 1']['Reinvestment'] = (projection_table['future_years']['Year 4']['Revenue'] - projection_table['future_years']['Year 3']['Revenue']) / implied_variables_table['future_years']['Year 1']['Sales to Capital Ratio']
                    else:
                        projection_table['future_years']['Year 1']['Reinvestment'] = (projection_table['future_years']['Year 2']['Revenue'] - projection_table['future_years']['Year 1']['Revenue']) / implied_variables_table['future_years']['Year 1']['Sales to Capital Ratio']

                    # # Year 2
                    if input_data['Other Inputs']['Override One Year Reinvestment to Growth Lag']==False:
                        projection_table['future_years']['Year 2']['Reinvestment'] = (projection_table['future_years']['Year 3']['Revenue'] - projection_table['future_years']['Year 2']['Revenue']) / implied_variables_table['future_years']['Year 2']['Sales to Capital Ratio']
                    elif input_data['Other Inputs']['Alt Lag'] == 0:
                        projection_table['future_years']['Year 2']['Reinvestment'] = (projection_table['future_years']['Year 2']['Revenue'] - projection_table['future_years']['Year 1']['Revenue']) / implied_variables_table['future_years']['Year 2']['Sales to Capital Ratio']
                    elif input_data['Other Inputs']['Alt Lag'] == 2:
                        projection_table['future_years']['Year 2']['Reinvestment'] = (projection_table['future_years']['Year 4']['Revenue'] - projection_table['future_years']['Year 3']['Revenue']) / implied_variables_table['future_years']['Year 2']['Sales to Capital Ratio']
                    elif input_data['Other Inputs']['Alt Lag'] == 3:
                        projection_table['future_years']['Year 2']['Reinvestment'] = (projection_table['future_years']['Year 5']['Revenue'] - projection_table['future_years']['Year 4']['Revenue']) / implied_variables_table['future_years']['Year 2']['Sales to Capital Ratio']
                    else:
                        projection_table['future_years']['Year 2']['Reinvestment'] = (projection_table['future_years']['Year 3']['Revenue'] - projection_table['future_years']['Year 2']['Revenue']) / implied_variables_table['future_years']['Year 2']['Sales to Capital Ratio']

                    # # Year 3
                    if input_data['Other Inputs']['Override One Year Reinvestment to Growth Lag']==False:
                        projection_table['future_years']['Year 3']['Reinvestment'] = (projection_table['future_years']['Year 4']['Revenue'] - projection_table['future_years']['Year 3']['Revenue']) / implied_variables_table['future_years']['Year 3']['Sales to Capital Ratio']
                    elif input_data['Other Inputs']['Alt Lag'] == 0:
                        projection_table['future_years']['Year 3']['Reinvestment'] = (projection_table['future_years']['Year 3']['Revenue'] - projection_table['future_years']['Year 2']['Revenue']) / implied_variables_table['future_years']['Year 3']['Sales to Capital Ratio']
                    elif input_data['Other Inputs']['Alt Lag'] == 2:
                        projection_table['future_years']['Year 3']['Reinvestment'] = (projection_table['future_years']['Year 5']['Revenue'] - projection_table['future_years']['Year 4']['Revenue']) / implied_variables_table['future_years']['Year 3']['Sales to Capital Ratio']
                    elif input_data['Other Inputs']['Alt Lag'] == 3:
                        projection_table['future_years']['Year 3']['Reinvestment'] = (projection_table['future_years']['Year 6']['Revenue'] - projection_table['future_years']['Year 5']['Revenue']) / implied_variables_table['future_years']['Year 3']['Sales to Capital Ratio']
                    else:
                        projection_table['future_years']['Year 3']['Reinvestment'] = (projection_table['future_years']['Year 4']['Revenue'] - projection_table['future_years']['Year 3']['Revenue']) / implied_variables_table['future_years']['Year 3']['Sales to Capital Ratio']

                    # # Year 4
                    if input_data['Other Inputs']['Override One Year Reinvestment to Growth Lag']==False:
                        projection_table['future_years']['Year 4']['Reinvestment'] = (projection_table['future_years']['Year 5']['Revenue'] - projection_table['future_years']['Year 4']['Revenue']) / implied_variables_table['future_years']['Year 4']['Sales to Capital Ratio']
                    elif input_data['Other Inputs']['Alt Lag'] == 0:
                        projection_table['future_years']['Year 4']['Reinvestment'] = (projection_table['future_years']['Year 4']['Revenue'] - projection_table['future_years']['Year 3']['Revenue']) / implied_variables_table['future_years']['Year 4']['Sales to Capital Ratio']
                    elif input_data['Other Inputs']['Alt Lag'] == 2:
                        projection_table['future_years']['Year 4']['Reinvestment'] = (projection_table['future_years']['Year 6']['Revenue'] - projection_table['future_years']['Year 5']['Revenue']) / implied_variables_table['future_years']['Year 4']['Sales to Capital Ratio']
                    elif input_data['Other Inputs']['Alt Lag'] == 3:
                        projection_table['future_years']['Year 4']['Reinvestment'] = (projection_table['future_years']['Year 7']['Revenue'] - projection_table['future_years']['Year 6']['Revenue']) / implied_variables_table['future_years']['Year 4']['Sales to Capital Ratio']
                    else:
                        projection_table['future_years']['Year 4']['Reinvestment'] = (projection_table['future_years']['Year 5']['Revenue'] - projection_table['future_years']['Year 4']['Revenue']) / implied_variables_table['future_years']['Year 4']['Sales to Capital Ratio']

                    # # Year 5
                    if input_data['Other Inputs']['Override One Year Reinvestment to Growth Lag']==False:
                        projection_table['future_years']['Year 5']['Reinvestment'] = (projection_table['future_years']['Year 6']['Revenue'] - projection_table['future_years']['Year 5']['Revenue']) / implied_variables_table['future_years']['Year 5']['Sales to Capital Ratio']
                    elif input_data['Other Inputs']['Alt Lag'] == 0:
                        projection_table['future_years']['Year 5']['Reinvestment'] = (projection_table['future_years']['Year 5']['Revenue'] - projection_table['future_years']['Year 4']['Revenue']) / implied_variables_table['future_years']['Year 5']['Sales to Capital Ratio']
                    elif input_data['Other Inputs']['Alt Lag'] == 2:
                        projection_table['future_years']['Year 5']['Reinvestment'] = (projection_table['future_years']['Year 7']['Revenue'] - projection_table['future_years']['Year 6']['Revenue']) / implied_variables_table['future_years']['Year 5']['Sales to Capital Ratio']
                    elif input_data['Other Inputs']['Alt Lag'] == 3:
                        projection_table['future_years']['Year 5']['Reinvestment'] = (projection_table['future_years']['Year 8']['Revenue'] - projection_table['future_years']['Year 7']['Revenue']) / implied_variables_table['future_years']['Year 5']['Sales to Capital Ratio']
                    else:
                        projection_table['future_years']['Year 5']['Reinvestment'] = (projection_table['future_years']['Year 6']['Revenue'] - projection_table['future_years']['Year 5']['Revenue']) / implied_variables_table['future_years']['Year 5']['Sales to Capital Ratio']

                    # # Year 6
                    if input_data['Other Inputs']['Override One Year Reinvestment to Growth Lag']==False:
                        projection_table['future_years']['Year 6']['Reinvestment'] = (projection_table['future_years']['Year 7']['Revenue'] - projection_table['future_years']['Year 6']['Revenue']) / implied_variables_table['future_years']['Year 6']['Sales to Capital Ratio']
                    elif input_data['Other Inputs']['Alt Lag'] == 0:
                        projection_table['future_years']['Year 6']['Reinvestment'] = (projection_table['future_years']['Year 6']['Revenue'] - projection_table['future_years']['Year 5']['Revenue']) / implied_variables_table['future_years']['Year 6']['Sales to Capital Ratio']
                    elif input_data['Other Inputs']['Alt Lag'] == 2:
                        projection_table['future_years']['Year 6']['Reinvestment'] = (projection_table['future_years']['Year 8']['Revenue'] - projection_table['future_years']['Year 7']['Revenue']) / implied_variables_table['future_years']['Year 6']['Sales to Capital Ratio']
                    elif input_data['Other Inputs']['Alt Lag'] == 3:
                        projection_table['future_years']['Year 6']['Reinvestment'] = (projection_table['future_years']['Year 9']['Revenue'] - projection_table['future_years']['Year 8']['Revenue']) / implied_variables_table['future_years']['Year 6']['Sales to Capital Ratio']
                    else:
                        projection_table['future_years']['Year 6']['Reinvestment'] = (projection_table['future_years']['Year 7']['Revenue'] - projection_table['future_years']['Year 6']['Revenue']) / implied_variables_table['future_years']['Year 6']['Sales to Capital Ratio']

                    # # Year 7
                    if input_data['Other Inputs']['Override One Year Reinvestment to Growth Lag']==False:
                        projection_table['future_years']['Year 7']['Reinvestment'] = (projection_table['future_years']['Year 8']['Revenue'] - projection_table['future_years']['Year 7']['Revenue']) / implied_variables_table['future_years']['Year 7']['Sales to Capital Ratio']
                    elif input_data['Other Inputs']['Alt Lag'] == 0:
                        projection_table['future_years']['Year 7']['Reinvestment'] = (projection_table['future_years']['Year 7']['Revenue'] - projection_table['future_years']['Year 6']['Revenue']) / implied_variables_table['future_years']['Year 7']['Sales to Capital Ratio']
                    elif input_data['Other Inputs']['Alt Lag'] == 2:
                        projection_table['future_years']['Year 7']['Reinvestment'] = (projection_table['future_years']['Year 9']['Revenue'] - projection_table['future_years']['Year 8']['Revenue']) / implied_variables_table['future_years']['Year 7']['Sales to Capital Ratio']
                    elif input_data['Other Inputs']['Alt Lag'] == 3:
                        projection_table['future_years']['Year 7']['Reinvestment'] = (projection_table['future_years']['Year 10']['Revenue'] - projection_table['future_years']['Year 9']['Revenue']) / implied_variables_table['future_years']['Year 7']['Sales to Capital Ratio']
                    else:
                        projection_table['future_years']['Year 7']['Reinvestment'] = (projection_table['future_years']['Year 8']['Revenue'] - projection_table['future_years']['Year 7']['Revenue']) / implied_variables_table['future_years']['Year 7']['Sales to Capital Ratio']

                    # # Year 8
                    if input_data['Other Inputs']['Override One Year Reinvestment to Growth Lag']==False:
                        projection_table['future_years']['Year 8']['Reinvestment'] = (projection_table['future_years']['Year 9']['Revenue'] - projection_table['future_years']['Year 8']['Revenue']) / implied_variables_table['future_years']['Year 8']['Sales to Capital Ratio']
                    elif input_data['Other Inputs']['Alt Lag'] == 0:
                        projection_table['future_years']['Year 8']['Reinvestment'] = (projection_table['future_years']['Year 8']['Revenue'] - projection_table['future_years']['Year 7']['Revenue']) / implied_variables_table['future_years']['Year 8']['Sales to Capital Ratio']
                    elif input_data['Other Inputs']['Alt Lag'] == 2:
                        projection_table['future_years']['Year 8']['Reinvestment'] = (projection_table['future_years']['Year 10']['Revenue'] - projection_table['future_years']['Year 9']['Revenue']) / implied_variables_table['future_years']['Year 8']['Sales to Capital Ratio']
                    elif input_data['Other Inputs']['Alt Lag'] == 3:
                        projection_table['future_years']['Year 8']['Reinvestment'] = (projection_table['terminal_year']['Revenue'] - projection_table['future_years']['Year 10']['Revenue']) / implied_variables_table['future_years']['Year 8']['Sales to Capital Ratio']
                    else:
                        projection_table['future_years']['Year 8']['Reinvestment'] = (projection_table['future_years']['Year 9']['Revenue'] - projection_table['future_years']['Year 8']['Revenue']) / implied_variables_table['future_years']['Year 8']['Sales to Capital Ratio']

                    # # Year 9
                    if input_data['Other Inputs']['Override One Year Reinvestment to Growth Lag']==False:
                        projection_table['future_years']['Year 9']['Reinvestment'] = (projection_table['future_years']['Year 10']['Revenue']-projection_table['future_years']['Year 9']['Revenue']) / implied_variables_table['future_years']['Year 9']['Sales to Capital Ratio']
                    elif input_data['Other Inputs']['Alt Lag'] == 0:
                        projection_table['future_years']['Year 9']['Reinvestment'] = (projection_table['future_years']['Year 9']['Revenue']-projection_table['future_years']['Year 8']['Revenue']) / implied_variables_table['future_years']['Year 9']['Sales to Capital Ratio']
                    elif input_data['Other Inputs']['Alt Lag'] == 2:
                        projection_table['future_years']['Year 9']['Reinvestment'] = (projection_table['future_years']['Year 10']['Revenue']*projection_table['future_years']['Year 10']['Revenue Growth Rate']) / implied_variables_table['future_years']['Year 9']['Sales to Capital Ratio']
                    elif input_data['Other Inputs']['Alt Lag'] == 3:
                        projection_table['future_years']['Year 9']['Reinvestment'] = (projection_table['terminal_year']['Revenue']*projection_table['terminal_year']['Revenue Growth Rate']) / implied_variables_table['future_years']['Year 9']['Sales to Capital Ratio']
                    else:
                        projection_table['future_years']['Year 9']['Reinvestment'] = (projection_table['future_years']['Year 10']['Revenue']-projection_table['future_years']['Year 9']['Revenue']) / implied_variables_table['future_years']['Year 9']['Sales to Capital Ratio']

                    # # Year 10
                    if input_data['Other Inputs']['Override One Year Reinvestment to Growth Lag']==False:
                        projection_table['future_years']['Year 9']['Reinvestment'] = (projection_table['terminal_year']['Revenue']-projection_table['future_years']['Year 10']['Revenue']) / implied_variables_table['future_years']['Year 10']['Sales to Capital Ratio']
                    elif input_data['Other Inputs']['Alt Lag'] == 0:
                        projection_table['future_years']['Year 9']['Reinvestment'] = (projection_table['future_years']['Year 10']['Revenue']-projection_table['future_years']['Year 9']['Revenue']) / implied_variables_table['future_years']['Year 10']['Sales to Capital Ratio']
                    elif input_data['Other Inputs']['Alt Lag'] == 2:
                        projection_table['future_years']['Year 9']['Reinvestment'] = (projection_table['terminal_year']['Revenue']*projection_table['terminal_year']['Revenue Growth Rate']) / implied_variables_table['future_years']['Year 10']['Sales to Capital Ratio']
                    elif input_data['Other Inputs']['Alt Lag'] == 3:
                        projection_table['future_years']['Year 9']['Reinvestment'] = (projection_table['future_years']['Year 9']['Reinvestment']*(1+projection_table['terminal_year']['Revenue Growth Rate']))
                    else:
                        projection_table['future_years']['Year 9']['Reinvestment'] = (projection_table['terminal_year']['Revenue']-projection_table['future_years']['Year 10']['Revenue']) / implied_variables_table['future_years']['Year 10']['Sales to Capital Ratio']

                    # # Terminal Year
                    if projection_table['terminal_year']['Revenue Growth Rate']>0:
                        projection_table['terminal_year']['Reinvestment'] = projection_table['terminal_year']['Revenue Growth Rate']/1

                    # projection_table['future_years'][f'{year+1}']['Reinvestment'] # WILL SET THIS AFTER, SINCE IT REQUIRES FUTURE REVENUES
                    # input_data['Other Inputs']['Override One Year Reinvestment to Growth Lag']
                    # =IF(input_data['Other Inputs']['Override One Year Reinvestment to Growth Lag']=FALSE,(projection_table['future_years'][f'Year 2']['Revenue']-projection_table['future_years'][f'Year 1']['Revenue'])/implied_variables_table['future_years']['Year 1']['Sales to Capital Ratio'],IF(input_data['Other Inputs']['Alt Lag']=0,projection_table['future_years']['Year 1']['Revenue']-projection_table['base_year']['Revenue'])/implied_variables_table['future_years']['Year 1']['Sales to Capital Ratio'],IF(input_data['Other Inputs']['Alt Lag']=2,(projection_table['future_years']['Year 3']['Revenue']-projection_table['future_years']['Year 2']['Revenue']))/implied_variables_table['future_years']['Year 1']['Sales to Capital Ratio'],IF(input_data['Other Inputs']['Alt Lag']=3,(projection_table['future_years']['Year 4']['Revenue']-projection_table['future_years']['Year 3']['Revenue'])/implied_variables_table['future_years']['Year 1']['Sales to Capital Ratio'],(projection_table['future_years']['Year 2']['Revenue']-projection_table['future_years']['Year 1']['Revenue'])/implied_variables_table['future_years']['Year 1']['Sales to Capital Ratio']))))

                    projection_table['future_years'][f'Year {year+1}']['FCFF']
                    projection_table['future_years'][f'Year {year+1}']['NOL']
                    projection_table['future_years'][f'Year {year+1}']['Cost of Capital']
                    projection_table['future_years'][f'Year {year+1}']['Cumulated Discount Factor']
                    projection_table['future_years'][f'Year {year+1}']['PV(FCFF)']
                    pass
                pass
        valuation_output_dictionary['projection_table'] = projection_table
        valuation_output_dictionary['summary_table'] = summary_table
        valuation_output_dictionary['implied_variables_table'] = implied_variables_table
        
        # terminal value projection
        return valuation_output_dictionary
    
    def get_valuation(self):
        pd.set_option('display.precision', 10)
        
        stock = self.ticker
        
        ticker = yf.Ticker(stock)
        info = ticker.info
        industry = info.get('industry')
        industryKey = info.get('industryKey')
        exchange = info.get('exchange')

        history = ticker.history(period="3y")
        closing_prices = history['Close'].astype(np.float64)
        returns = closing_prices.pct_change().astype(np.float64)
        variance_returns = np.var(returns.dropna())

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
        market_returns_variance = np.var(market_returns.dropna())

        index_data = {
            'Stock Close': closing_prices,
            'Stock Returns': returns,
            'Stock Returns 20-Day Trailing Variances': returns.rolling(window=20).var(),
            'Market Close': market_closing_prices,
            'Market Returns': market_returns,
            'Market Returns 20-Day Trailing Variances': market_returns.rolling(window=20).var()
        }

        aligned_index_data = pd.DataFrame(index_data)


        covariance = np.cov(market_returns.dropna().values, returns.dropna().values)[0, 1]

        levered_beta = covariance/variance_returns

        bond_data = self.get_bond_data()

        bond_data.style

        us_bond_yield = bond_data.loc[bond_data['Country'] == 'United States', '10yr Bond Yield'].values[0]

        spread_table = self.default_spread(bond_data, us_bond_yield)[['Country', '10yr Bond Yield', 'Spread']]

        erm = self.expected_market_return(market_history)

        us_mature_erp = erm - us_bond_yield

        today = dt.date.today()

        company_ticker = stock #VZ, AMZN, WMG

        pd.options.display.float_format = (
            lambda x: "{:,.0f}".format(x) if int(x) == x else "{:,.2f}".format(x)
        )

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

        sec_CIKs = self.get_CIKs()
        company_CIK = self.get_company_CIK(company_ticker, sec_CIKs)

        filingData = self.get_filing_data(company_CIK)

        company_facts = self.companyFacts(company_CIK)['facts']['us-gaap']
        labels_dict = {fact: details["label"] for fact, details in company_facts.items()}

        filing_dataframe = pd.DataFrame.from_dict(filingData['filings']['recent']) # all the recent filings

        current_10K = self.get_10K(filing_dataframe)

        accession_number = self.get_accession_number(current_10K).replace('-', '')
        primaryDocument = self.get_primaryDocument(current_10K)
        report_date = self.get_report_date(current_10K)

        primaryDocument_no_extension = str(primaryDocument).split('.')[0]

        form10K_url = f"https://www.sec.gov/Archives/edgar/data/{company_CIK}/{accession_number}/{primaryDocument_no_extension}_htm.xml"



        xml_parsed = self.xml_to_dict(form10K_url)

        financialdata = xml_parsed['xbrl'] # THIS WOULD BE THE ONE TO USe ARELLE / PYTHON-XBRL LIBRARIES ON!!!

        namespaces = self.get_namespaces(form10K_url)

        time_since_last_10K = float(((quarterly['income_statements'].keys()[0]-fiscal_year['income_statements'].keys()[0]).total_seconds()/(24*3600))/365)



        """# **Load Data (Do Once)**"""

        country_equity_risk_premiums = self.get_table_from_url('https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/ctryprem.html')
        rev_multiples = self.get_table_from_url('https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/psdata.html')
        sector_betas = self.get_table_from_url('https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/Betas.html')
        sector_cost_of_equity_and_capital = self.get_table_from_url('https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/wacc.htm')
        sector_price_and_value_to_book_ratio = self.get_table_from_url('https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/pbvdata.html')

        credit_default_ratings = self.get_table_from_url('https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/ratings.html')

        synthetic_default_ratings = credit_default_ratings[2:17].rename(columns=lambda x: credit_default_ratings.iloc[2, x]).reset_index(drop=True).iloc[1:, :]




        # https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/vebitda.html

        """# **In Development**

        # **Output Data Preparation**
        """

        equity_data, debt_data, preferred_stock_data, operating_countries_erp_data, output_data = self.cost_of_capital_worksheet()

        country_search_pattern = re.compile(r"united\s+states(\s*\([^)]*\))?", re.IGNORECASE)

        country_string = self.find_closest_match(country_equity_risk_premiums[0], country_search_pattern)

        us_erp_data = country_equity_risk_premiums[country_equity_risk_premiums[0] == country_string]
        us_corporate_tax_rate = us_erp_data.iloc[0, 4]

        substring = "Schedule of Operating Lease Liability Maturity"

        taxonomy_definitions = self.get_taxonomy(company_CIK, accession_number, primaryDocument_no_extension, namespaces)[1]

        statements_names = self.get_statement_file_names_in_filing_summary(company_ticker, accession_number)

        statement = financialdata.keys()

        # call cost of capital function here

        input_data = {
            '10K' : {
                'Total Revenue' : fiscal_year['income_statements'].loc['Total Revenue'],
                'Operating Income' : fiscal_year['income_statements'].loc['Operating Income'],
                'Interest Expense' : fiscal_year['income_statements'].loc['Interest Expense'],
                'Book Value of Equity' : fiscal_year['balance_sheets'].loc['Total Equity Gross Minority Interest'],
                'Book Value of Debt' : fiscal_year['balance_sheets'].loc['Total Debt'],
                'Cash and Marketable Securities' : fiscal_year['balance_sheets'].loc['Cash Cash Equivalents And Short Term Investments'],
                'Cross Holdings and Non-Operating Assets' : fiscal_year['balance_sheets'].loc['Long Term Equity Investment'] if 'Long Term Equity Investment' in fiscal_year['balance_sheets'].index else 0,
                'Minority Interest' : fiscal_year['balance_sheets'].loc['Minority Interest'],
                'Research and Development' : fiscal_year['income_statements'].loc['Research And Development'] if 'Research And Development' in fiscal_year['income_statements'].index else 0,
            },
            '10Q' : {
                'Total Revenue' : quarterly['income_statements'].loc['Total Revenue'],
                'Operating Income' : quarterly['income_statements'].loc['Operating Income'],
                'Interest Expense' : quarterly['income_statements'].loc['Interest Expense'],
                'Book Value of Equity' : quarterly['balance_sheets'].loc['Total Equity Gross Minority Interest'],
                'Book Value of Debt' : quarterly['balance_sheets'].loc['Total Debt'],
                'Cash and Marketable Securities' : quarterly['balance_sheets'].loc['Cash Cash Equivalents And Short Term Investments'],
                'Cross Holdings and Non-Operating Assets' : quarterly['balance_sheets'].loc['Long Term Equity Investment'] if 'Long Term Equity Investment' in quarterly['balance_sheets'].index else 0,
                'Minority Interest' : quarterly['balance_sheets'].loc['Minority Interest'],
                'Research and Development' : quarterly['income_statements'].loc['Research And Development'] if 'Research And Development' in quarterly['income_statements'].index else 0,
            },
            'ltm' : {
                'Total Revenue' : pd.Series(np.sum(quarterly['income_statements'].loc['Total Revenue']), index = [0]),
                'Operating Income' : pd.Series(np.sum(quarterly['income_statements'].loc['Operating Income']), index = [0]),
                'Interest Expense' : pd.Series(np.sum(quarterly['income_statements'].loc['Interest Expense']), index = [0]),
                'Book Value of Equity' : pd.Series(np.sum(quarterly['balance_sheets'].loc['Total Equity Gross Minority Interest']), index = [0]),
                'Book Value of Debt' : pd.Series(np.sum(quarterly['balance_sheets'].loc['Total Debt']), index = [0]),
                'Cash and Marketable Securities' : pd.Series(np.sum(quarterly['balance_sheets'].loc['Cash Cash Equivalents And Short Term Investments']), index = [0]),
                'Cross Holdings and Non-Operating Assets' : pd.Series(np.sum(quarterly['balance_sheets'].loc['Long Term Equity Investment']), index = [0]) if 'Long Term Equity Investment' in quarterly['balance_sheets'].index else 0,
                'Minority Interest' : quarterly['balance_sheets'].loc['Minority Interest'].iloc[0],
                'Research and Development' : pd.Series(np.sum(quarterly['income_statements'].loc['Research And Development']), index = [0]) if 'Research And Development' in quarterly['income_statements'].index else 0,
            },
            'Other Inputs' : {
                'Years Since Last 10K': time_since_last_10K if time_since_last_10K > 0 else 1,
                'Has R&D Expenses' : True if 'Minority Interest' in quarterly['balance_sheets'].index else False,
                'Has Operating Leases' : True,
                'Current Shares Outstanding' : info.get('sharesOutstanding'),
                'Current Stock Price' : closing_prices.iloc[-1],
                'Effective Tax Rate' : fiscal_year['income_statements'].loc['Tax Rate For Calcs'].iloc[0],
                'Marginal Tax Rate' : float(us_corporate_tax_rate.strip('%'))/100,
                'Revenue Growth Rate for Next Year' : (((pd.Series(np.sum(quarterly['income_statements'].loc['Total Revenue']), index = [0]))/(fiscal_year['income_statements'].loc['Total Revenue'][0]))**(1/time_since_last_10K)-1) if fiscal_year['income_statements'].loc['Total Revenue'][0] is not None and time_since_last_10K > 0 else 0, # = ((Revenues from LTM / Revenues from Last 10K) ^ (1 / Years Since Last 10K) - 1) if Revenues from Last 10K > 0 else "NA",
                'Pre-Tax Cost of Debt' : .2, # compute from cost of capital worksheet
                'Operating Margin for Next Year' : .14,
                'Compounded Annual Revenue Growth Rate Years 2 to 5' : .04,
                'Target Pre-Tax Operating Margin' : .14,
                'Year of Convergence for Margin' : 5, # Have input selection edit this
                'Sales to Capial Ratio Years 1 to 5' : 1.2,
                'Sales to Capial Ratio Years 6 to 10' : 1.2,
                'Risk Free Rate' : us_bond_yield,
                'Initial Cost of Capital' : .12,
                'Has Employee Options Outstanding' : False,
                'Average Strike Price' : 5,
                'Average Maturity' : 5,
                'Standard Deviation on Stock Price' : .25,
                'Override Cost of Capital Assumption' : True, # In stable growth, I will assume that your firm will have a cost of capital similar to that of typical mature companies (riskfree rate + 4.5%)
                'Alt Cost of Capital After Year 10' : 0.08, # If yes, enter the return on capital you expect after year 10
                'Override No Chance of Failure Assumption' : True, # I will assume that your firm has no chance of failure over the foreseeable future.
                'Alt Chance of Failure' : .12, # If yes, enter the probability of failure
                'What to Tie Proceeds in Failure To' : 'V',
                'Distress Proceeds as Percent of Book or Fair Value' : .50, # Enter the distress proceeds as percentage of book or fair value
                'Override One Year Reinvestment to Growth Lag' : False, # I assume that reinvestment in a year translates into growth in the next year, i.e., there is a one year lag between reinvesting and generating growth from that reinvestment.
                'Alt Lag' : 1, # 0 = no lag, 3 = lag of 3 years
                'Override Tax Rate Adjustment Assumption' : False, # I will assume that your effective tax rate will adjust to your marginal tax rate by your terminal year. If you override this assumption, I will leave the tax rate at your effective tax rate.
                'Override No NOL Carry Forwards Assumption' : False, # I will assume that you have no losses carried forward from prior years ( NOL) coming into the valuation. If you have a money losing company, you may want to override tis.
                'Alt NOL Carry Forward into Year 1' : 1,
                'Override Risk Free Rate Prevalence in Perpetuity Assumption' : False, # I will asssume that today's risk free rate will prevail in perpetuity. If you override this assumption, I will change the riskfree rate after year 10.
                'Alt Risk Free Rate' : 0.02, # Do a 10 year forecast
                'Override Long Term Growth Rate Assumption' : False, # I will assume that the growth rate in perpetuity will be equal to the risk free rate. This allows for both valuation consistency and prevents "impossible" growth rates.
                'Alt Perpetuity Growth Rate' : -0.05, #Be Very Careful! This can be negative, if you feel the company will decline (and disappear) after growth is done. If you let it exceed the risk free rate, you are on your own in uncharted territory.
                'Override No Trapped Cash Assumption' : False, # I have assumed that none of the cash is trapped (in foreign countries) and that there is no additional tax liability coming due and that cash is a neutral asset.
                'Alt Trapped Cash' : 1, # Cash that is trapped in foreign markets (and subject to additoinal tax) or cash that is being discounted by the market (because of management mistrust)
                'Avg Tax Rate of Foreign Markets where Cash is Trapped' : 0.15, # Additional tax rate due on trapped cash or discount being applied to cash balance because of mistrust.
            },
            'Operating Leases' : {
                'Current Year Operating Lease Expense' : 1,
                'Year 1 Operating Lease Commitment' : 1,
                'Year 2 Operating Lease Commitment' : 1,
                'Year 3 Operating Lease Commitment' : 1,
                'Year 4 Operating Lease Commitment' : 1,
                'Year 5 Operating Lease Commitment' : 1, # If there's no Year 5 and Beyond
                'Year 5 and Beyond Operating Lease Commitment' : 1, # If there's a Year 5 and Beyond and no Year 6 and Beyond
                'Year 6 and Beyond Operating Lease Commitment' : 1, # If there's a Year 6 and Beyond and no Year 5 and Beyond
            },
            'debt' : {}
        }


        input_10K_df = pd.DataFrame(input_data['10K']).T
        input_10Q_df = pd.DataFrame(input_data['10Q']).T
        input_ltm_df = pd.DataFrame(input_data['ltm']).T

        # Linear Inputs

        linear_input_df = pd.DataFrame([input_data['Other Inputs']]).T



        debt_value_of_operating_leases, depreciation_on_opls_asset, operating_earnings_adjustment, total_debt_outstanding_adjustment, depreciation_adjustment = self.operating_lease_converter(input_data, debt_data)

        research_asset_value = self.research_and_development()

        """# **Valuation**"""

        # need to create R&D converter
        r_and_d_output = {
            'adjustment_to_operating_income' : 0,
        }

        base_operating_income = (input_data['ltm']['Operating Income'] +
                                operating_earnings_adjustment +
                                r_and_d_output['adjustment_to_operating_income']
                                if input_data['Other Inputs']['Has R&D Expenses']
                                and input_data['Other Inputs']['Has Operating Leases']
                                else input_data['ltm']['Operating Income'] +
                                r_and_d_output['adjustment_to_operating_income']
                                if input_data['Other Inputs']['Has R&D Expenses']
                                else input_data['ltm']['Operating Income'] +
                                operating_earnings_adjustment if input_data['Other Inputs']['Has Operating Leases']
                                else input_data['ltm']['Operating Income']).iloc[0]

        base_operating_income = ((
            input_data['ltm']['Operating Income'] + operating_earnings_adjustment + r_and_d_output['adjustment_to_operating_income']
            if input_data['Other Inputs']['Has R&D Expenses']
            else input_data['ltm']['Operating Income'] + r_and_d_output['adjustment_to_operating_income']
            ) if input_data['Other Inputs']['Has Operating Leases'] else input_data['ltm']['Operating Income']).iloc[0]

        base_after_tax_operating_income = (
            base_operating_income *
            (1 - input_data['Other Inputs']['Effective Tax Rate'])
            if base_operating_income > 0
            else base_operating_income
        )

        valuation_output = {
            'projection_table': {
                'base_year': {
                    'Revenue' : input_data['ltm']['Total Revenue'].iloc[0],
                    'Operating Margin' : base_operating_income/input_data['ltm']['Total Revenue'].iloc[0],
                    'Operating Income' : base_operating_income,
                    'Tax Rate' : input_data['Other Inputs']['Effective Tax Rate'],
                    'NOPAT' : base_after_tax_operating_income, # NOPAT = Operating Income * (1 - Tax Rate)
                    'NOL' : input_data['Other Inputs']['Alt NOL Carry Forward into Year 1'] if input_data['Other Inputs']['Override No NOL Carry Forwards Assumption'] else 0,
                },
                'future_years': {
                    f'Year {year + 1}': {
                        'Revenue Growth Rate' : .14,
                        'Revenue': 1,
                        'Operating Margin': .14,
                        'Operating Income': .1,
                        'Tax Rate': .24,
                        'NOPAT': 1,
                        'Reinvestment': 1,
                        'FCFF': 1,
                        'NOL': 1,
                        'Cost of Capital': .1,
                        'Cumulated Discount Factor': .4,
                        'PV(FCFF)': .4,
                    } for year in range(10)
                },
                'terminal_year': {
                    'Revenue Growth Rate' : .14,
                    'Revenue' : 1.2,
                    'Operating Margin' : .15,
                    'Operating Income' : .1,
                    'Tax Rate' : .24,
                    'NOPAT' : 1, # NOPAT = Operating Income * (1 - Tax Rate)
                    'Reinvestment' : 1,
                    'FCFF' : 1,
                    'NOL' : 1,
                    'Cost of Capital' : 1,
                },
            },
            'summary_table' : {
                'Terminal Cash Flow' : 1,
                'Terminal Cost of Capital' : 1,
                'Terminal Value' : 1,
                'PV(Terminal Value)' : 1,
                'PV(CF over next 10 years)' : 1,
                'Sum of PV' : 1,
                'Probability of Failure' : 1,
                'Proceeds if Firm Fails' : 1,
                'Value of Operating Assets' : 1,
                'Debt' : 1,
                'Minority Interests' : 1,
                'Cash' : 1,
                'Non-Operating Assets' : 1,
                'Value of Equity' : 1,
                'Value of Options' : 1,
                'Value of Equity in Common Stock' : 1,
                'Estimated Value / Share' : 1,
                'Price per Share' : 1,
                'Price as % of Value' : 1,
            },
            'implied_variables_table': {
                'base_year' : {
                    'Invested Capital' : 1,
                    'Return on Invested Capital' : 1,
                },
                'future_years': {
                    f'Year {year + 1}' : {
                        'Sales to Capital Ratio': 1,
                        'Invested Capital': 1,
                        'Return on Invested Capital': 1,
                    } for year in range(10)
                },
                'terminal_year' : {
                    'Return on Invested Capital' : 1,
                },
            },
        }
        
        # ====================================================================================================================================================================================
        # ====================================================================================================================================================================================
        valuation_output = self.valuation_comps(valuation_output, input_data)
        self.valuation = valuation_output
        # ====================================================================================================================================================================================
        # ====================================================================================================================================================================================

        country_equity_risk_premiums = self.fix_df(country_equity_risk_premiums)
        country_equity_risk_premiums

        rev_multiples = self.fix_df(rev_multiples)

        rev_multiples

        sector_betas = self.fix_df(sector_betas)

        sector_betas

        sector_cost_of_equity_and_capital = self.fix_df(sector_cost_of_equity_and_capital)

        sector_cost_of_equity_and_capital

        sector_price_and_value_to_book_ratio = self.fix_df(sector_price_and_value_to_book_ratio)

        sector_price_and_value_to_book_ratio

        """*Note that the yahoo finance data does not have the most up to date 10Q, so the script will eventually pull the missing data from EDGAR's 10Q*

        # **Time Series Modeling**
        """

        # Disable logging messages unless there is an error
        set_log_level("ERROR")

        set_random_seed(0)

        # If 'Date' is not a column, reset the index to make it a column
        if 'Date' not in aligned_index_data.columns:
            aligned_index_data.reset_index(inplace=True)
            aligned_index_data.rename(columns={'index': 'Date'}, inplace=True)

        aligned_index_data = aligned_index_data.dropna()
        aligned_index_data.head(20)

        aligned_index_data.info()

        aligned_index_data.sample(30)

        aligned_index_data.describe()

        """**Stock Price Time Series Model**"""

        stock_price_time_series = pd.DataFrame([aligned_index_data['Date'],aligned_index_data['Stock Close']]).T.rename(columns={'Date' : 'ds', 'Stock Close' : 'y'})[['ds','y']]

        stock_price_time_series.head(20)

        stock_price_ts_model = NeuralProphet(daily_seasonality=False, seasonality_reg=1)

        stock_price_ts_model.set_plotting_backend("matplotlib")

        stock_price_metrics = stock_price_ts_model.fit(stock_price_time_series,
                            freq='D', epochs=10)

        stock_price_future = stock_price_ts_model.make_future_dataframe(stock_price_time_series, periods=365, n_historic_predictions=len(stock_price_time_series))

        stock_price_forecast = stock_price_ts_model.predict(stock_price_future)

        stock_price_forecast

        plt.plot(stock_price_forecast.ds, stock_price_forecast.y)
        plt.plot(stock_price_forecast.ds, stock_price_forecast.yhat1)

        fig = px.line(stock_price_forecast, x = 'ds',y = 'yhat1',title = 'Predicted Stock Price')
        fig.add_scatter(x=stock_price_time_series['ds'], y = stock_price_time_series['y'], mode='lines')
        fig.add_scatter(x=stock_price_time_series['ds'], y = stock_price_time_series['y'].rolling(window=12).mean(), mode='lines')

        fig.update_xaxes(
            rangeslider_visible= True
                        )
        # fig.show()

        stock_price_res = sm.tsa.seasonal_decompose(stock_price_time_series[['y']],
                                        model='additive', period=12)

        stock_price_res.plot()

        """**Stock Return Time Series Model**"""

        stock_return_time_series = pd.DataFrame([aligned_index_data['Date'],aligned_index_data['Stock Returns']]).T.rename(columns={'Date' : 'ds', 'Stock Returns' : 'y'})[['ds','y']]

        stock_return_time_series.head(20)

        stock_returns_ts_model = NeuralProphet()

        stock_returns_ts_model.set_plotting_backend("matplotlib")

        stock_returns_metrics = stock_returns_ts_model.fit(stock_return_time_series,
                            freq='D', epochs=10)

        stock_returns_future = stock_returns_ts_model.make_future_dataframe(stock_return_time_series, periods=365, n_historic_predictions=len(stock_return_time_series))

        stock_returns_forecast = stock_returns_ts_model.predict(stock_returns_future)

        stock_returns_forecast

        plt.plot(stock_returns_forecast.ds, stock_returns_forecast.y)
        plt.plot(stock_returns_forecast.ds, stock_returns_forecast.yhat1)

        fig = px.line(stock_returns_forecast, x = 'ds',y = 'yhat1',title = 'Predicted Stock Return')
        fig.add_scatter(x=stock_return_time_series['ds'], y = stock_return_time_series['y'], mode='lines')
        fig.add_scatter(x=stock_return_time_series['ds'], y = stock_return_time_series['y'].rolling(window=12).mean(), mode='lines')

        fig.update_xaxes(
            rangeslider_visible = True
                        )
        # fig.show()

        stock_return_res = sm.tsa.seasonal_decompose(stock_return_time_series[['y']],
                                        model='additive', period=12)

        stock_return_res.plot()

        """# **Graphs**"""

        # @title Stock Close
        aligned_index_data['Stock Close'].plot(kind='line', figsize=(8, 4), title='Stock Close')
        plt.gca().spines[['top', 'right']].set_visible(False)

        # @title Stock Returns
        aligned_index_data['Stock Returns'].plot(kind='line', figsize=(8, 4), title='Stock Returns')
        plt.gca().spines[['top', 'right']].set_visible(False)

        # @title Stock Returns Distribution
        aligned_index_data['Stock Returns'].plot(kind='hist', bins=20, title='Stock Returns')
        plt.gca().spines[['top', 'right',]].set_visible(False)

        # @title Stock Returns Variance
        aligned_index_data['Stock Returns 20-Day Trailing Variances'].plot(kind='line', figsize=(8, 4), title='Stock Returns 20-Day Trailing Variances')
        plt.gca().spines[['top', 'right']].set_visible(False)

        # @title Stock Close vs Stock Returns
        aligned_index_data.plot(kind='scatter', x='Stock Close', y='Stock Returns', s=32, alpha=.8)
        plt.gca().spines[['top', 'right',]].set_visible(False)

        # @title Market Close
        aligned_index_data['Market Close'].plot(kind='line', figsize=(8, 4), title='Market Close')
        plt.gca().spines[['top', 'right']].set_visible(False)

        # @title Market Returns
        aligned_index_data['Market Returns'].plot(kind='line', figsize=(8, 4), title='Market Returns')
        plt.gca().spines[['top', 'right']].set_visible(False)

        # @title Market Returns Distribution
        aligned_index_data['Market Returns'].plot(kind='hist', bins=20, title='Market Returns')
        plt.gca().spines[['top', 'right',]].set_visible(False)

        # @title Market Returns Variance
        aligned_index_data['Market Returns 20-Day Trailing Variances'].plot(kind='line', figsize=(8, 4), title='Market Returns 20-Day Trailing Variances')
        plt.gca().spines[['top', 'right']].set_visible(False)

        # @title Market Close vs Market Returns
        aligned_index_data.plot(kind='scatter', x='Market Close', y='Market Returns', s=32, alpha=.8)
        plt.gca().spines[['top', 'right',]].set_visible(False)

        # @title Market Return vs Stock Returns
        aligned_index_data.plot(kind='scatter', x='Market Returns', y='Stock Returns', s=32, alpha=.8)
        plt.gca().spines[['top', 'right',]].set_visible(False)

        """Data to include in multivariate model"""

        climate_data_url = 'https://developer.rms.com/climate-on-demand'
        # moodys api key in colab secret keys
        
        print(self.valuation)