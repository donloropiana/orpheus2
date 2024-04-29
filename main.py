import modules.orpheus as orpheus
import streamlit as st
import yfinance as yf
from modules.streamlit_helpers import draw_donut_circle, build_info_table
from modules.sentiment import company_sentiment

def main():
    PAGE_CONFIG = {"page_title": "Orpheus", "page_icon": ":chart_with_upwards_trend:", "layout": "centered"}
    st.set_page_config(**PAGE_CONFIG)
    st.title("Orpheus")
    st.subheader("A Trading Advisor")

    menu = ["Overview", "Fundamental Analysis", "Quantitative Analysis"]
    choice = st.sidebar.selectbox('Menu', menu)

    form = st.form(key='my_form')
    ticker = form.text_input(label='Enter Stock Ticker')
    submit_button = form.form_submit_button(label='Submit')


    # Initialize variables to store submitted ticker and retrieved data
    if 'submitted_ticker' not in st.session_state:
        st.session_state.submitted_ticker = None
    if 'valuation_table' not in st.session_state:
        st.session_state.valuation_table = None
    if 'sentiment' not in st.session_state:
        st.session_state.sentiment = None
    if 'info' not in st.session_state:
        st.session_state.info = None

    # Update stored data upon submission
    if submit_button and ticker:
        st.session_state.submitted_ticker = ticker
        valuation = orpheus.valuation(f"{str(ticker)}")
        valuation.get_valuation()
        st.session_state.valuation_table = valuation.valuation
        st.session_state.sentiment = company_sentiment(ticker)
        stock = yf.Ticker(ticker)
        st.session_state.info = stock.info
    
    if choice == 'Overview':
        if st.session_state.info:
            st.header(st.session_state.info['longName'])
            st.subheader("Company Summary")
            st.write(st.session_state.info['longBusinessSummary'])
            st.subheader("Company Information")
            info_table = build_info_table(st.session_state.info, st.session_state.valuation_table['summary_table']['Price per Share'] if st.session_state.valuation_table else None)
            st.table(info_table)
        if st.session_state.sentiment:
            st.subheader("News Sentiment")
            col1, col2 = st.columns([1, 1])
            with col1:
                st.write("The news sentiment score is a measure of the overall sentiment of news articles related to the stock. "
                          "A positive score indicates positive sentiment, while a negative score indicates negative sentiment. "
                          "The score ranges from -1 to 1. The score is generated by scraping recent press releases related to the stock and analyzing the sentiment of the text. "
                          "The sentiment score is not a recommendation to buy or sell the stock. It is merely a measure of the sentiment of the news.")
            with col2:
                fig = draw_donut_circle("News Sentiment Score:", st.session_state.sentiment)
                st.pyplot(fig)
    elif choice == 'Fundamental Analysis':
        st.header("Fundamental Analysis")
        if st.session_state.valuation_table:
            price = st.session_state.info['currentPrice']
            projection = st.session_state.valuation_table['summary_table']['Price per Share']
            st.subheader("Valuation Metrics")
            st.write(f"Current Price: ${price}")
            st.write(f"Projected Price: ${projection}")
            st.write(f"Upside Potential: {((projection - price) / price) * 100:.2f}%")
            st.subheader("Valuation Table")
            st.table(st.session_state.valuation_table)
    elif choice == 'Quantitative Analysis':
        st.header("Quantitative Analysis")
        st.write("coming soon...")

if __name__ == '__main__':
    main()
