import numpy as np
import streamlit as st
import pandas as pd

import constants
from investments import MortgageRecycleInvestment, Investment
from loan import Loan
from mortgage import Mortgage
import altair as alt


def display_mortgage_info(mortgage):
    mortgage_info = mortgage.display_mortgage_info()

    st.table(mortgage_info.style.apply(
        lambda x: ['background-color: #CCCCCC' if x.name == mortgage_info.index[-1] else '' for _ in x], axis=1))


def plot_monthly_payments_graph_yearly(yearly_amortization_before, yearly_amortization_after):
    st.subheader("Monthly Payment:")
    st.line_chart({"Before": yearly_amortization_before['Monthly Payment'],
                   "After": yearly_amortization_after['Monthly Payment']})


def plot_principal_interest_yearly(yearly_amortization_before, yearly_amortization_after):
    st.subheader("Principal-Interest Payment:")

    col_before, col_after = st.columns(2)
    # Plot for 'Before' in the first column
    with col_before:
        st.subheader("Before")
        st.bar_chart({
            'Principal Payment': yearly_amortization_before['Principal Payment'],
            'Interest Payment': yearly_amortization_before['Interest Payment']
        }, color=['#FF5733', '#FFD700'])

    # Plot for 'After' in the second column
    with col_after:
        st.subheader("After")
        st.bar_chart({
            'Principal Payment': yearly_amortization_after['Principal Payment'],
            'Interest Payment': yearly_amortization_after['Interest Payment']
        }, color=['#FF5733', '#FFD700'])


def plot_monthly_interest_graph_yearly(yearly_amortization_before, yearly_amortization_after):
    st.subheader("Interest Payments:")
    st.area_chart({"Before": yearly_amortization_before['Interest Payment'].cumsum(),
                   "After": yearly_amortization_after['Interest Payment'].cumsum()})


def something_else(yearly_amortization_before, yearly_amortization_after):
    data = pd.concat([yearly_amortization_before['Monthly Payment'].to_frame().rename(
        columns={'Monthly Payment': 'Before'}),
        yearly_amortization_after['Monthly Payment'].to_frame().rename(
            columns={'Monthly Payment': 'After'})])

    # Reset index to use it as x-axis
    data.reset_index(inplace=True)

    melted_data = data.melt('index')
    # melted_data.sort_values(['index', 'variable'], inplace=True)
    melted_data['variable'] = pd.Categorical(melted_data['variable'], categories=['Before', 'After'], ordered=True)

    print(melted_data)
    # Create an Altair chart
    chart = alt.Chart(melted_data).mark_bar().encode(
        x=alt.X('variable:N', axis=alt.Axis(title='', labels=False)),
        y=alt.Y('value:Q', axis=alt.Axis(title='Monthly Payment Amount (Currency)', grid=False)),
        color=alt.Color('variable:N'),
        column=alt.Column('index:O', title='Year', header=alt.Header(labelOrient='bottom'))
    ).properties(
        width=60,
        height=400,
        title='Monthly Payment Comparison Before and After'
    )

    # Display the Altair chart using st.altair_chart
    st.altair_chart(chart, use_container_width=False)


def mortgage_recycle_report():
    if st.session_state.mortgage is None:
        return
    else:
        mortgage = st.session_state.mortgage

    col1, col2, col3 = st.columns([6, 2, 2])

    # Add title in the first column
    with col1:
        st.title(f"Mortgage Recycling")

    # Add number input in the second column
    with col2:
        extra_payment = st.number_input('Enter Extra Amount:', min_value=0, value=100000)

    # Add selection list in the third column
    with col3:
        change = st.selectbox('Select Option:', ['Payment', 'Period'])

    st.divider()

    mortgage_after = Mortgage.recycle_mortgage(mortgage=mortgage, extra_payment=extra_payment, change=change)

    mortgage_recycle_report_details(mortgage, mortgage_after)

    st.divider()
    saving_investment(mortgage, extra_payment, change)


def saving_investment(mortgage: Mortgage, extra_payment: int, change):
    amortization_schedule_period = MortgageRecycleInvestment(initial_fund=extra_payment,
                                                             mortgage=mortgage,
                                                             investment_yearly_return=constants.StocksMarketYearlyReturn,
                                                             change='period',
                                                             name="Mortgage Recycle Period change").generate_amortization_schedule(
        mortgage.num_of_months() // 12 + 10)

    amortization_schedule_payment = MortgageRecycleInvestment(initial_fund=extra_payment,
                                                              mortgage=mortgage,
                                                              investment_yearly_return=constants.StocksMarketYearlyReturn,
                                                              change='payment',
                                                              name="Mortgage Recycle payment change").generate_amortization_schedule(
        mortgage.num_of_months() // 12 + 10)

    yearly_amortization_period = Investment.get_yearly_amortization(amortization_schedule_period)
    yearly_amortization_payment = Investment.get_yearly_amortization(amortization_schedule_payment)

    st.subheader("Interest Savings (+Investments):")
    st.line_chart({"Savings(Payment)": yearly_amortization_payment['Monthly Extra'].cumsum(),
                   "Savings(Period)": yearly_amortization_period['Monthly Extra'].cumsum(),
                   "Investment(Payment)": yearly_amortization_payment['Total Revenue'],
                   "Investment(Period)": yearly_amortization_period['Total Revenue']},
                  color=['#ff4500', '#ff4599', '#008000', '#008099'])


def mortgage_recycle_report_details(mortgage_before: Mortgage, mortgage_after: Mortgage):
    with st.expander("Mortgage Info", expanded=False):
        st.subheader("Current Mortgage Details:")
        display_mortgage_info(mortgage_before)
        st.subheader("Recycled Mortgage Details:")
        display_mortgage_info(mortgage_after)

    yearly_amortization_before = Loan.get_yearly_amortization(mortgage_before.amortization_schedule)
    yearly_amortization_after = Loan.get_yearly_amortization(mortgage_after.amortization_schedule)

    st.divider()
    summary_section2(mortgage_before, mortgage_after)
    st.divider()

    plot_monthly_payments_graph_yearly(yearly_amortization_before, yearly_amortization_after)

    st.divider()
    plot_principal_interest_yearly(yearly_amortization_before, yearly_amortization_after)

    st.divider()
    plot_monthly_interest_graph_yearly(yearly_amortization_before, yearly_amortization_after)


def summary_section(mortgage_before, mortgage_after):
    # Function to display the bar graphs
    yearly_amortization_before = Loan.get_yearly_amortization(mortgage_before.amortization_schedule)
    yearly_amortization_after = Loan.get_yearly_amortization(mortgage_after.amortization_schedule)

    st.subheader("Summary:")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Period")
        st.bar_chart({
            'Before': mortgage_before.num_of_months(),
            'After': mortgage_after.num_of_months()
        }, color=['#add8e6'])

    with col2:
        st.subheader("Interest Payment")
        st.bar_chart({
            'Before': yearly_amortization_before["Interest Payment"].sum(),
            'After': yearly_amortization_after["Interest Payment"].sum()
        }, color=['#ebdf34'])

    with col3:
        st.subheader("Avg. Interest Rate")
        st.bar_chart({
            'Before': mortgage_before.average_interest_rate(),
            'After': mortgage_after.average_interest_rate()
        }, color=['#eb7734'])


def summary_section2(mortgage_before, mortgage_after):
    # Function to calculate relevant information
    yearly_amortization_before = Loan.get_yearly_amortization(mortgage_before.amortization_schedule)
    yearly_amortization_after = Loan.get_yearly_amortization(mortgage_after.amortization_schedule)

    # Use the last item in the dataframes for "Interest Payment"
    last_interest_payment_before = yearly_amortization_before["Interest Payment"].sum()
    last_interest_payment_after = yearly_amortization_after["Interest Payment"].sum()

    # Display the summary table
    st.subheader("Recycle Summary:")

    summary_data = {
        "Metric": ["Amount", "Period (Month)", "Interest Payment", "Avg. Interest Rate", "Monthly Payment"],
        "Before": [mortgage_before.loan_amount(), int(mortgage_before.num_of_months()), last_interest_payment_before,
                   np.round(mortgage_before.average_interest_rate(), 2),
                   np.round(mortgage_before.average_monthly_payment())],
        "After": [mortgage_after.loan_amount(), int(mortgage_after.num_of_months()), last_interest_payment_after,
                  np.round(mortgage_after.average_interest_rate(), 2),
                  np.round(mortgage_after.average_monthly_payment())],
        "Savings": [mortgage_before.loan_amount() - mortgage_after.loan_amount(),
                    int(mortgage_before.num_of_months()) - int(mortgage_after.num_of_months()),
                    last_interest_payment_before - last_interest_payment_after,
                    np.round(mortgage_before.average_interest_rate() - mortgage_after.average_interest_rate(), 2),
                    np.round(mortgage_before.average_monthly_payment() - mortgage_after.average_monthly_payment())]
    }


    summary_df = pd.DataFrame(summary_data)

    st.dataframe(summary_df,
                 use_container_width=True, hide_index=True)


# Rest of your code


def load_mortgage_csv():
    uploaded_file = st.file_uploader("Load a Mortgage Data", accept_multiple_files=False)
    if uploaded_file is not None:
        st.session_state.mortgage = Mortgage.read_csv(uploaded_file)


def side_bar():
    with st.sidebar:
        st.title("Constants")

        # Define default values for constants

        constants.CPI = st.number_input("CPI", value=constants.CPI)
        constants.TaxGainPercentage = st.number_input("Tax Gain Percentage", value=constants.TaxGainPercentage)
        constants.TaxBuyingPercentage = st.number_input("Tax Buying Percentage", value=constants.TaxBuyingPercentage)
        constants.RealEstateYearlyAppreciation = st.number_input("Real Estate Yearly Appreciation",
                                                                 value=constants.RealEstateYearlyAppreciation)
        # constants.StocksMarketYearlyReturn = st.slider("Stocks Market Yearly Return", min_value=0.0, max_value=20, step=0.01,
        #                                                      value=constants.StocksMarketYearlyReturn)
        constants.StocksMarketYearlyReturn = st.slider("Stocks Market Yearly Return", 0, 30,
                                                       value=constants.StocksMarketYearlyReturn)

        constants.StocksMarketFeesPercentage = st.number_input("Stocks Market Fees Percentage",
                                                               value=constants.StocksMarketFeesPercentage)


def main():
    st.set_page_config(page_title='Mortgage Recycling Calculator', layout='wide')

    st.image('resources/banner2.png', use_column_width=True)
    # side_bar()

    st.session_state.mortgage = None

    load_mortgage_csv()

    mortgage_recycle_report()


if __name__ == "__main__":
    main()
