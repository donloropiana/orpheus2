import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import multivariate_data_fetch
import sql

def create_correlation_plot(df):
    """ Generate and return a correlation matrix plot. """
    plt.figure(figsize=(12, 10))
    correlation_matrix = df.corr()
    ax = sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', fmt=".2f")
    plt.title('Correlation Matrix of Features')
    plt.close()  # Close the plt figure to prevent it from showing immediately
    return ax.figure  # Return the figure object for later use

def build_model():
    # Assume sql.table_to_df fetches your data from a database
    df = sql.table_to_df('stock_data').dropna()
    
    # X and y variables
    X = df.drop(columns=['Ticker', 'Today Price'])
    y = df['Today Price']
    
    # Display columns for sanity check
    print("Columns used in X:", X.columns)

    # Generating the correlation matrix
    correlation_plot = create_correlation_plot(X)

    # Data Preprocessing
    numeric_features = X.select_dtypes(include=['int64', 'float64']).columns
    categorical_features = X.select_dtypes(include=['object']).columns
    numeric_transformer = StandardScaler()
    categorical_transformer = OneHotEncoder(handle_unknown='ignore')

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numeric_features),
            ('cat', categorical_transformer, categorical_features)
        ])

    # Pipeline with preprocessing and model
    pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('regressor', GradientBoostingRegressor(random_state=42))
    ])

    # Split data into train and test sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Fit and predict
    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)

    # Evaluate the model
    mse = mean_squared_error(y_test, y_pred)
    print(f'Mean Squared Error: {mse}')

    # Model Tuning with Grid Search
    param_grid = {
        'regressor__n_estimators': [100, 200],
        'regressor__learning_rate': [0.05, 0.1],
        'regressor__max_depth': [3, 4, 5]
    }
    grid_search = GridSearchCV(pipeline, param_grid, cv=5)
    grid_search.fit(X_train, y_train)
    print("Best parameters:", grid_search.best_params_)
    print("Best cross-validation score: {:.2f}".format(grid_search.best_score_))

    # Using the best estimator to evaluate on the test set
    best_model = grid_search.best_estimator_
    y_pred_best = best_model.predict(X_test)
    mse_best = mean_squared_error(y_test, y_pred_best)
    print(f'Improved Mean Squared Error: {mse_best}')
    
    return correlation_plot, best_model, mse_best, 
    
def predict_price(model, stock):
    stock_data = multivariate_data_fetch.fetch_data_for_stock(stock)
    stock_data = pd.DataFrame(stock_data, index=[0])
    predicted_price = model.predict(stock_data)
    actual_price = stock_data['Today Price']
    mse = mean_squared_error(actual_price, predicted_price)
    return predicted_price, actual_price, mse

if __name__ == '__main__':
    correlation_plot, model, model_mse = build_model()
    predicted_price, actual_price, predict_price_mse = predict_price(model, 'WMG')
    
    print(f"Model Mean Squared Error: {model_mse}")
    print(f"Predicted Price: {predicted_price}")
    print(f"Actual Price: {actual_price}")
    