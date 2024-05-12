import modules.orpheus as orpheus
import streamlit as st
import yfinance as yf
from modules.streamlit_helpers import draw_donut_circle, build_info_table, stock_chart, earnings_calendar, neural_prophet_forecast_chart
from modules.sentiment import company_sentiment, press_release_df
from modules.sql import username_exists, verify_password, create_user

def run_app():
    st.title("Orpheus")
    st.subheader("A Trading Advisor")

    menu = ["Overview", "Fundamental Analysis", "Quantitative Analysis"]
    choice = st.sidebar.selectbox('Menu', menu)

    form = st.form(key='my_form')
    ticker = form.text_input(label='Enter Stock Ticker (only works with WMG for now)')
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
        st.session_state.sentiment = company_sentiment(ticker)
        stock = yf.Ticker(ticker)
        st.session_state.info = stock.info
    
    if choice == 'Overview':
        if st.session_state.info:
            # display name
            st.header(st.session_state.info['longName'])

            # display company summary
            st.subheader("Company Summary")
            st.write(st.session_state.info['longBusinessSummary'])

            # display company information (price, projected price, market cap, dividend info)
            st.subheader("Company Information")
            info_table = build_info_table(st.session_state.info)
            st.table(info_table)

            # display stock chart
            st.subheader("Stock Chart")
            chart_range = st.selectbox("Select Range", ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"], index=5)
            fig = stock_chart(ticker, chart_range)
            st.pyplot(fig)

        if st.session_state.sentiment:
            # display news sentiment
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

            # display recent press releases
            st.subheader("Recent Press Releases")
            # Update the session state every time the slider is changed
            recent_press_releases = press_release_df(ticker)
            # Display the table of recent press releases
            st.table(recent_press_releases)

            # display earnings calendar
            cal = earnings_calendar(ticker)
            st.subheader("Earnings Calendar")
            st.table(cal)

            # display prediction chart
            st.subheader("Prediction Chart")
            periods = st.slider("Select Number of Periods to Predict", 1, 365, 365, 5)
            forecast_figure = neural_prophet_forecast_chart(ticker, periods)
            st.pyplot(forecast_figure)

    # elif choice == 'Fundamental Analysis':
    #     st.header("Fundamental Analysis")
    #     if st.session_state.valuation_table:
    #         price = st.session_state.info['currentPrice']
    #         # projection = st.session_state.projected_price
    #         st.subheader("Valuation Metrics")
    #         st.write(f"Current Price: ${price}")
    #         st.write(f"Projected Price: ${projection}")
    #         st.write(f"Upside Potential: {((projection - price) / price) * 100:.2f}%")
    #         st.subheader("Valuation Table")
    #         st.table(st.session_state.valuation_table)
    # elif choice == 'Quantitative Analysis':
    #     st.header("Quantitative Analysis")
    #     st.write("coming soon...")


def main():
    PAGE_CONFIG = {"page_title": "Orpheus", "page_icon": ":chart_with_upwards_trend:", "layout": "centered"}
    st.set_page_config(**PAGE_CONFIG)
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
   
    login_bucket = st.empty()

    if not st.session_state.logged_in:

        with login_bucket.form('login_form'):
            st.markdown("## Enter your credentials")

            username_input = st.text_input("Username")
            password_input = st.text_input("Password", type="password")
            login_button = st.form_submit_button("Login")
        # Check if login button is clicked
        if login_button:
            user_exists = username_exists(username_input)
            if user_exists:
                # Verify password
                if verify_password(username_input, password_input):
                    st.success("Login successful!")
                    st.session_state.logged_in = True
                else:
                    st.error("Invalid username or password")
            else:
                st.error("Invalid username or password")
    
    if st.session_state.logged_in:
        login_bucket.empty()
        run_app()

            

    # #sidebar for registration
    # st.sidebar.title("Register")
    # username_input = st.sidebar.text_input("Register Username")
    # password_input = st.sidebar.text_input("Register Password", type="password")
    # register_button = st.sidebar.button("Register")

    # # Check if register button is clicked
    # if register_button:
    #     user = username_exists(username_input)
    #     if user:
    #         st.error("Username already exists")
    #     else:
    #         create_user(username_input, password_input)
    #         st.success("Registration successful!")
    #         run_app()

if __name__ == '__main__':
    main()
