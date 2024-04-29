## Orpheus

Orpheus is a trading advisor that uses advanced valuation techniques paired with machine learning to predict the future price of a stock. It uses a variety of features to make its predictions, including historical price data, technical indicators, and news sentiment analysis. The goal of Orpheus is to help traders make more informed decisions by providing them with accurate predictions of future stock prices.

## How to Run
First, you will need to set up a python virtual environment. You can do this by running the following command:
```
python -m venv venv
```
Next, you will need to activate the virtual environment by running the following command:

*For mac*:
```
source venv/bin/activate
```
*For windows*:
```
venv\Scripts\activate
```

To run Orpheus, you will need to install the required dependencies by running the following command:
```
pip install -r requirements.txt
```
Finally, you can run Orpheus by running the following command:
```
streamlit run main.py
```

This will start a local server that you can access in your web browser (it should automatically pop up, if not then expect terminal output for which port to access the webserver on). You can then input the stock symbol you want to predict and Orpheus will provide you with a prediction of the future price of that stock.