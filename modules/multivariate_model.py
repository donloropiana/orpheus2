import multivariate_data_fetch
import sql
from sklearn.neural_network import MLPRegressor
import warnings
warnings.filterwarnings("ignore")

def analysis():
    df = sql.table_to_df('stock_data').dropna()
    X = df.drop(columns=['Ticker', 'Sector'])
    y = df['Today Price']
    mlp = MLPRegressor()
    print(df.head())
    
analysis()