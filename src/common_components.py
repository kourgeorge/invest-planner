import numpy as np
import pandas as pd
import streamlit as st

import constants
from loan import Loan, LoanType


def header():
    st.image('resources/banner_small.png', use_container_width=True)


def footer():
    st.write("© All rights reserved to George Kour. 2024 (v0.9)")
    st.write("Disclaimer: The use of this application is at your own risk. "
             "The information and results provided on this application are for informational purposes only and do not constitute financial advice or consultation. "
             "Users are advised to independently verify any data and consult with qualified professionals for personalized financial guidance. "
             "We do not assume any responsibility for the accuracy, completeness, or suitability of the information provided. "
             "By using this application, you acknowledge and accept that your financial decisions are solely your responsibility.")


def parameters_bar():
    with st.expander("Parameters", expanded=False):
        cols = st.columns([1, 1, 1, 1])
        with cols[0]:
            st.session_state.CPI = st.number_input("CPI", value=constants.CPI, help="Expected Customer Price Index")
        with cols[1]:
            st.session_state.StocksMarketYearlyReturn = st.number_input("Stocks Return %",
                                                                        value=constants.StocksMarketYearlyReturn, help='Expected Annual Stocks Market Returns')
        with cols[2]:
            st.session_state.StocksMarketFeesPercentage = st.number_input("Trading Fees %",
                                                                          value=constants.StocksMarketFeesPercentage, help='Annual Stocks Market Fees %')
        with cols[3]:
            st.session_state.TaxGainPercentage = st.number_input("Sell Tax %", value=constants.TaxGainPercentage)


def investment_parameters_bar():
    with st.expander("Parameters", expanded=False):
        cols = st.columns(5)
        with cols[0]:
            st.session_state.CPI = st.number_input("CPI", value=constants.CPI, help="Expected Customer Price Index")
        with cols[1]:
            st.session_state.TaxGainPercentage = st.number_input("Sell Tax %", value=constants.TaxGainPercentage)
        with cols[2]:
            st.session_state.RealEstateAppreciations = st.number_input("RE Appreciation %", value=constants.RealEstateYearlyAppreciation)
        with cols[3]:
            st.session_state.MaintenanceRentalRatio = st.number_input("Adjusted Rental Ratio", value=constants.MaintenanceRentalRatio, max_value=1.0, min_value=0.1)
        with cols[4]:
            st.session_state.TaxBuyingPercentage = st.number_input("Property Buying Tax %", value=constants.TaxBuyingPercentage)


def load_mortgage_csv():
    st.session_state.files = st.file_uploader("Load a Mortgage Data", accept_multiple_files=False,
                                              label_visibility="hidden", type=['csv', 'txt'])

    if st.session_state.files is not None:
        st.session_state.mortgages_df[0] = pd.read_csv(st.session_state.files,
                                                    dtype={'amount': float, 'num_of_months': int,
                                                           'interest_rate': float,
                                                           'loan_type': str,
                                                           'grace_period': int, 'cpi': str})

        print("Mortgage data loaded successfully!")


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


def convert_string_to_int(number_string):
        # Remove commas and convert to int
        return int(number_string.replace(',', ''))


def display_table_with_total_row(mortgage_info):

    def apply_background_color(row):
        bg_color = ''
        # Check if the row is the last row
        if row.name == mortgage_info.index[-1]:
            bg_color = 'background-color: #E0E0E0'

        return [bg_color] * len(row)

    st.table(mortgage_info.style.apply(apply_background_color, axis=1))


def plot_annual_amortization_monthly_line(mortgages, field):
    yearly_amortizations = [Loan.get_yearly_amortization(mortgage.amortization_schedule) for mortgage in mortgages]
    st.line_chart({f"{mortgages[i].name}": yearly_amortization[field] // 12 for i, yearly_amortization in
     enumerate(yearly_amortizations)})


loan_type_keys = [enum_member.name for enum_member in LoanType]
def mortgage_editor(mortgages_df:pd.DataFrame, name):
    return st.data_editor(mortgages_df, key=name,
                   num_rows="dynamic",
                   hide_index=True,
                   column_config={
                       'amount': st.column_config.NumberColumn('Amount',
                                                               required=True,
                                                               min_value=0,
                                                               max_value=50000000
                                                               ),
                       'num_of_months': st.column_config.NumberColumn(
                           'Months',
                           required=True,
                           min_value=0,
                           max_value=360,
                           default=240),
                       'interest_rate': st.column_config.NumberColumn(
                           'Interest Rate',
                           required=True,
                           min_value=0,
                           max_value=20,
                           default=5.1),
                       'loan_type': st.column_config.SelectboxColumn(
                           label='Loan Type', options=loan_type_keys,
                           required=True),
                       'grace_period': st.column_config.NumberColumn(
                           'Grace Period',
                           required=True,
                           min_value=0,
                           max_value=50,
                           default=0),
                       'cpi': st.column_config.CheckboxColumn(label='CPI',
                                                              required=True,
                                                              default=True)
                   },
                   column_order=['loan_type', 'cpi', 'amount', 'num_of_months',
                                 'interest_rate',
                                 'grace_period'],
                   use_container_width=True)


recycle_strategy_help = "The recycling strategy. Choosing 'Payment' will decrease your monthly payment while keeping the loan duration constant. " \
                        "The 'Period' option will maintain a relatively consistent monthly payment but reduce the overall mortgage period."