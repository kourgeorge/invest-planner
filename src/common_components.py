import numpy as np
import streamlit as st

import constants
from loan import Loan


def header():
    st.image('resources/banner.png', use_column_width=True)


def footer():
    st.write("© All rights reserved to George Kour. 2024 (v0.3)")
    st.write("Disclaimer: The use of this application is at your own risk. "
             "The information and results provided on this application are for informational purposes only and do not constitute financial advice or consultation. "
             "Users are advised to independently verify any data and consult with qualified professionals for personalized financial guidance. "
             "We do not assume any responsibility for the accuracy, completeness, or suitability of the information provided. "
             "By using this application, you acknowledge and accept that your financial decisions are solely your responsibility.")


def parameters_bar():
    with st.expander("Parameters", expanded=False):
        cols = st.columns([1, 1, 1, 1, 1, 1])
        with cols[0]:
            st.session_state.CPI = st.number_input("CPI", value=constants.CPI)
        with cols[1]:
            st.session_state.StocksMarketYearlyReturn = st.number_input("Stocks Market Return",
                                                                        value=constants.StocksMarketYearlyReturn)
        with cols[2]:
            st.session_state.StocksMarketFeesPercentage = st.number_input("Stocks Market Fees %",
                                                                          value=constants.StocksMarketFeesPercentage)
        with cols[3]:
            st.session_state.TaxBuyingPercentage = st.number_input("Buy Tax %", value=constants.TaxBuyingPercentage)
        with cols[4]:
            st.session_state.TaxGainPercentage = st.number_input("Sell Tax %", value=constants.TaxGainPercentage)
        with cols[5]:
            st.session_state.RealEstateYearlyAppreciation = st.number_input("RE Appreciation",
                                                                            value=constants.RealEstateYearlyAppreciation)


def display_amortization_table(mortgage, amortization_type):
    if amortization_type == 'Annual':
        amortization = Loan.get_yearly_amortization(mortgage.amortization_schedule)
    else:
        amortization = np.round(mortgage.amortization_schedule.astype(int))
    st.table(amortization.set_index('Month'))


def display_amortization_pane(mortgages):
    col1, _, col2 = st.columns([5, 1, 5])
    with col1:
        st.subheader("Amortization Tables")
    with col2:
        amortization_type = st.radio("Type", options=['Annual', 'Monthly'])

    with st.expander("Mortgage Amortization", expanded=False):
        cols = st.columns([1] * len(mortgages), gap="large")
        for i, col in enumerate(cols):
            with col:
                st.write(f"{mortgages[i].name}")
                display_amortization_table(mortgages[i], amortization_type)


def display_mortgage_info(mortgage):
    mortgage_info = mortgage.display_mortgage_info()

    def convert_string_to_int(number_string):
        # Remove commas and convert to int
        return int(number_string.replace(',', ''))

    def apply_background_color(row):
        bg_color = ''
        # Check if the row is the last row
        if row.name == mortgage_info.index[-1]:
            bg_color = 'background-color: #E0E0E0'

        # Check if the 'amount' column is equal to 0

        elif convert_string_to_int(row['Loan Amount']) == int(0):
            bg_color = 'background-color: #add8e6'  # Use 'lightblue' instead of 'blue'

        return [bg_color] * len(row)

    st.table(mortgage_info.style.apply(apply_background_color, axis=1))


def plot_annual_amortization_monthly_line(mortgages, field):
    yearly_amortizations = [Loan.get_yearly_amortization(mortgage.amortization_schedule) for mortgage in mortgages]
    st.line_chart({f"{mortgages[i].name}": yearly_amortization[field] // 12 for i, yearly_amortization in
     enumerate(yearly_amortizations)})


recycle_strategy_help = "The recycling strategy. Choosing 'Payment' will decrease your monthly payment while keeping the loan duration constant. " \
                        "The 'Period' option will maintain a relatively consistent monthly payment but reduce the overall mortgage period"