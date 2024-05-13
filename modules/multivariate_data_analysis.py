from sql import table_to_df
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import matplotlib.pyplot as plt
import yfinance as yf
import numpy as np

class MultivariateDataAnalysis:
    def __init__(self):
        pass
    
    def train_model(self):
        self.df = table_to_df("stock_data")
        self.X = self.df.drop(columns=['Ticker', 'Sector', 'Today Price'])
        self.y = self.df['Today Price']
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(self.X, self.y, test_size=0.2, random_state=42)
        self.model = GradientBoostingRegressor()
        self.model.fit(self.X_train, self.y_train)
        self.y_pred = self.model.predict(self.X_test)
        self.mse = mean_squared_error(self.y_test, self.y_pred)
        self.results = pd.DataFrame({
            'Actual': self.y_test,
            'Predicted': self.y_pred
        })
        
    
    def get_results(self):
        return self.results

    def get_mse(self):
        return self.mse
    
    def plot_actual_vs_predicted(self):
        plt.figure(figsize=(10, 6))
        plt.scatter(self.y_test, self.y_pred, color='blue')
        plt.title('Actual vs Predicted Stock Prices')
        plt.xlabel('Actual Prices')
        plt.ylabel('Predicted Prices')
        plt.grid(True)
        plt.show()


mda = MultivariateDataAnalysis()
mda.train_model()
print(mda.get_results())
print(mda.get_mse())
mda.plot_actual_vs_predicted()
