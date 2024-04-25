import orpheus
import streamlit as st

def main():
    PAGE_CONFIG = {"page_title":"Orpheus","page_icon":":chart_with_upwards_trend:","layout":"centered"}
    st.set_page_config(**PAGE_CONFIG)
    st.title("Orpheus")
    st.subheader("A Trading Advisor")
    menu = ["Overview","Fundamental Analysis", "Quantitative Analysis"]
    choice = st.sidebar.selectbox('Menu',menu)
    form = st.form(key='my_form')
    ticker = form.text_input(label='Enter Stock Ticker')
    submit_button = form.form_submit_button(label='Submit')
    valuation_table = None
    if submit_button:
        st.write("")
        valuation = orpheus.valuation(f"{str(ticker)}")
        valuation.get_valuation()
        valuation_table = valuation.valuation
    if choice == 'Overview':
        st.subheader("Overview")
        st.write("")
    elif choice == 'Fundamental Analysis':
        st.subheader("Fundamental Analysis")
        st.write(valuation_table)
    elif choice == 'Quantitative Analysis':
        st.subheader("Quantitative Analysis")
        st.write("")
        # slider_value = st.slider('Number of rows', min_value=3, max_value=1000)

        # df_movies = pd.read_sql("select * from movies LIMIT " + str(slider_value), con=engine_imdb)
        # fig = df_movies.rating[~df_movies.rating.isna()].plot().get_figure()
        # st.pyplot(fig)
        # show_dataframe = st.checkbox('Display Dataframe')
        # if show_dataframe:
        #     df_movies

if __name__ == '__main__':
    main()