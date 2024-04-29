import modules.orpheus as orpheus
import streamlit as st
from modules.streamlit_functions import draw_donut_circle
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

    # Update stored data upon submission
    if submit_button and ticker:
        st.session_state.submitted_ticker = ticker
        valuation = orpheus.valuation(f"{str(ticker)}")
        valuation.get_valuation()
        st.session_state.valuation_table = valuation.valuation
        st.session_state.sentiment = company_sentiment(ticker)

    # Use stored data when rendering pages
    if choice == 'Overview':
        st.subheader("Overview")
        st.write("")
        if st.session_state.sentiment:
            fig = draw_donut_circle(st.session_state.sentiment)
            st.pyplot(fig)
    elif choice == 'Fundamental Analysis':
        st.subheader("Fundamental Analysis")
        st.write(st.session_state.valuation_table)
    elif choice == 'Quantitative Analysis':
        st.subheader("Quantitative Analysis")
        st.write("")

if __name__ == '__main__':
    main()
