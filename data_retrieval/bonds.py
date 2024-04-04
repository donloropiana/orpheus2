import requests
from bs4 import BeautifulSoup
import pandas as pd

def convert_bp_to_decimal(string_value):
    # Remove ' bp' and convert to float
    numerical_part = float(string_value.replace(' bp', ''))
    # Convert basis points to decimal
    return numerical_part / 10000

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

print(bond_data)

us_bond_yield = bond_data.loc[bond_data['Country'] == 'United States', 'Spread vs T-Note'].values[0]

def default_spread():
    bond_data['Spread'] = bond_data['10yr Bond Yield'] - us_bond_yield
    return bond_data

spread_table = default_spread()[['Country', '10yr Bond Yield', 'Spread vs T-Note']]

print(spread_table)

# add spread over US bond