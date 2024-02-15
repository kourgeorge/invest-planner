import numpy as np
import streamlit as st
import pandas as pd
from matplotlib import pyplot as plt

import constants
from investments import MortgageRecycleInvestment, Investment
from loan import Loan
from mortgage import Mortgage
import altair as alt


def display_mortgage_info(mortgage):
    mortgage_info = mortgage.display_mortgage_info()

    st.table(mortgage_info.style.apply(
        lambda x: ['background-color: #CCCCCC' if x.name == mortgage_info.index[-1] else '' for _ in x], axis=1))


def display_amortization_pane(mortgage, mortgage_after):
    col1, _, col2 = st.columns([5, 1, 5])
    with col1:
        st.subheader("Amortization Tables")
    with col2:
        amortization_type = st.radio("Type", options=['Yearly', 'Monthly'])
    with st.expander("Mortgage Amortization", expanded=False):
        col1, _, col2 = st.columns([5, 1, 5])
        with col1:
            st.write("Before:")
            display_yearly_amortization_table(mortgage, amortization_type)
        with col2:
            st.write("After:")
            display_yearly_amortization_table(mortgage_after, amortization_type)


def display_yearly_amortization_table(mortgage, amortization_type):
    if amortization_type == 'Yearly':
        amortization = Loan.get_yearly_amortization(mortgage.amortization_schedule.reset_index())
    else:
        amortization = mortgage.amortization_schedule
    st.table(amortization)


def plot_monthly_payments_graph_yearly(yearly_amortization_before, yearly_amortization_after):
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Monthly Payment:")
        st.line_chart({"Before": yearly_amortization_before['Monthly Payment'],
                       "After": yearly_amortization_after['Monthly Payment']})
    with col2:
        st.subheader("Remaining Balance:")
        st.area_chart({"Before": yearly_amortization_before['Remaining Balance'],
                       "After": yearly_amortization_after['Remaining Balance']})


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


def main_mortgage_recycle_report():
    if st.session_state.mortgage_df is None:
        return
    else:
        mortgage = Mortgage.from_dataframe(st.session_state.mortgage_df, st.session_state.CPI)

    col1, col2, col3 = st.columns([6, 2, 2])

    # Add title in the first column
    with col1:
        st.subheader(f"Mortgage Information")

    # Add number input in the second column
    with col2:
        extra_payment = st.number_input('Enter Extra Amount:', min_value=0, value=100000, step=10000,
                                        max_value=mortgage.loan_amount())

    # Add selection list in the third column
    with col3:
        change = st.selectbox('Select Option:', ['Payment', 'Period'])

    mortgage_after = Mortgage.recycle_mortgage(mortgage=mortgage, extra_payment=extra_payment, change=change)

    mortgage_recycle_report_details(mortgage, mortgage_after)

    st.divider()
    saving_investment(mortgage, extra_payment)

    st.divider()


def saving_investment(mortgage: Mortgage, extra_payment: int):
    amortization_schedule_period = MortgageRecycleInvestment(initial_fund=extra_payment,
                                                             mortgage=mortgage,
                                                             investment_yearly_return=st.session_state.StocksMarketYearlyReturn,
                                                             change='period',
                                                             stocks_yearly_fee_percent=st.session_state.StocksMarketFeesPercentage,
                                                             gain_tax=st.session_state.TaxGainPercentage,
                                                             name="Mortgage Recycle Period change").generate_amortization_schedule(
        mortgage.num_of_months() // 12 + 10)

    amortization_schedule_payment = MortgageRecycleInvestment(initial_fund=extra_payment,
                                                              mortgage=mortgage,
                                                              investment_yearly_return=st.session_state.StocksMarketYearlyReturn,
                                                              change='payment',
                                                              stocks_yearly_fee_percent=st.session_state.StocksMarketFeesPercentage,
                                                              gain_tax=st.session_state.TaxGainPercentage,
                                                              name="Mortgage Recycle payment change").generate_amortization_schedule(
        mortgage.num_of_months() // 12 + 10)

    yearly_amortization_period = Investment.get_yearly_amortization(amortization_schedule_period)
    yearly_amortization_payment = Investment.get_yearly_amortization(amortization_schedule_payment)

    col1,col2 = st.columns([1,1])
    with col1:

        st.subheader("Monthly Savings:")
        st.line_chart({"Savings(Payment)": yearly_amortization_payment['Monthly Extra'].cumsum(),
                   "Savings(Period)": yearly_amortization_period['Monthly Extra'].cumsum()},
                  color=['#336699', '#66cc99'])

    with col2:
        st.subheader("Monthly Savings - Invested:")
        st.line_chart({"Investment(Payment)": yearly_amortization_payment['Net Revenue'],
                       "Investment(Period)": yearly_amortization_period['Net Revenue']},
                      color=['#336699', '#66cc99'])
        #'#ff4599', '#cc9900',

def mortgage_recycle_report_details(mortgage_before: Mortgage, mortgage_after: Mortgage):
    with st.expander("Mortgage Info", expanded=True):
        st.subheader("Current Mortgage Details:")
        display_mortgage_info(mortgage_before)
        st.subheader("Recycled Mortgage Details:")
        display_mortgage_info(mortgage_after)

    display_amortization_pane(mortgage_before, mortgage_after)

    yearly_amortization_before = Loan.get_yearly_amortization(mortgage_before.amortization_schedule)
    yearly_amortization_after = Loan.get_yearly_amortization(mortgage_after.amortization_schedule)

    st.divider()
    summary_section(mortgage_before, mortgage_after)

    st.divider()
    plot_monthly_interest_graph_yearly(yearly_amortization_before, yearly_amortization_after)

    st.divider()
    plot_monthly_payments_graph_yearly(yearly_amortization_before, yearly_amortization_after)

    st.divider()
    plot_principal_interest_yearly(yearly_amortization_before, yearly_amortization_after)


def bars_summary_section(mortgage_before, mortgage_after):
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


def summary_section(mortgage_before, mortgage_after):
    # Use the last item in the dataframes for "Interest Payment"
    total_interest_payment_before = mortgage_before.total_interest_payments()
    total_interest_payment_after = mortgage_after.total_interest_payments()

    st.subheader("Recycle Summary:")

    summary_data = {
        "Metric": ["Cost", "Period (Month)", "Interest Payment", "Avg. Interest Rate", "Monthly Payment"],
        "Before": [np.round(mortgage_before.total_payments()), int(mortgage_before.num_of_months()),
                   np.round(total_interest_payment_before),
                   np.round(mortgage_before.average_interest_rate(), 2),
                   np.round(mortgage_before.average_monthly_payment())],
        "After": [np.round(mortgage_after.total_payments()), int(mortgage_after.num_of_months()),
                  np.round(total_interest_payment_after),
                  np.round(mortgage_after.average_interest_rate(), 2),
                  np.round(mortgage_after.average_monthly_payment())],
        "Savings": [np.round(mortgage_before.total_payments() - mortgage_after.total_payments()),
                    int(mortgage_before.num_of_months()) - int(mortgage_after.num_of_months()),
                    np.round(total_interest_payment_before - total_interest_payment_after),
                    np.round(mortgage_before.average_interest_rate() - mortgage_after.average_interest_rate(), 2),
                    np.round(mortgage_before.average_monthly_payment() - mortgage_after.average_monthly_payment())]
    }

    summary_df = pd.DataFrame(summary_data)
    explode = (0, 0.1)

    col1, col_gap, col2, col3 = st.columns([8, 1, 2, 2])
    width = 3
    height = 3
    with col1:
        st.dataframe(summary_df,
                     use_container_width=True, hide_index=True)
    with col2:
        st.write('Before')

        fig1, ax1 = plt.subplots(figsize=(width, height))
        ax1.pie([mortgage_before.total_interest_payments(), mortgage_before.total_principal_payments()],
                explode=explode,
                labels=['Interest', 'Principle'], autopct='%1.1f%%', textprops={'fontsize': 18},
                shadow=False, startangle=0, colors=['lightcoral', 'lightblue'])
        ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        st.pyplot(fig1, use_container_width=True)

        # # Altair chart
        # data = {
        #     'Category': ['Interest', 'Principle'],
        #     'Values': [mortgage_before.total_interest_payments(), mortgage_before.total_principal_payments()]
        # }
        # df = pd.DataFrame(data)
        # chart = alt.Chart(df).mark_arc(size=200).encode(
        #  theta ='Values',
        # color='Category'
        # )
        #
        # # Display the Altair pie chart using st.altair_chart
        # st.altair_chart(chart, use_container_width=True)

    with col3:
        st.write('After')
        fig2, ax2 = plt.subplots(figsize=(width, height))
        ax2.pie([mortgage_after.total_interest_payments(), mortgage_after.total_principal_payments()], explode=explode,
                labels=['Interest', 'Principle'], autopct='%1.1f%%', textprops={'fontsize': 18},
                shadow=False, startangle=0, colors=['lightcoral', 'lightblue'])
        ax2.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        st.pyplot(fig2, use_container_width=True)


# Rest of your code


def load_mortgage_csv():
    uploaded_file = st.file_uploader("Load a Mortgage Data", accept_multiple_files=False)
    if uploaded_file is not None:
        st.session_state.file = uploaded_file
        st.session_state.mortgage_df = pd.read_csv(st.session_state.file)


def parameters_bar():
    cols = st.columns([1, 1, 1])
    with cols[0]:
        st.session_state.CPI = st.number_input("CPI", value=constants.CPI)

        st.session_state.StocksMarketFeesPercentage = st.number_input("Stocks Market Fees %",
                                                               value=constants.StocksMarketFeesPercentage)
    with cols[1]:
        st.session_state.TaxGainPercentage = st.number_input("Sell Tax %", value=constants.TaxGainPercentage, )
        st.session_state.TaxBuyingPercentage = st.number_input("Buy Tax %", value=constants.TaxBuyingPercentage, )
    with cols[2]:
        st.session_state.RealEstateYearlyAppreciation = st.number_input("RE Appreciation",
                                                                 value=constants.RealEstateYearlyAppreciation)
        st.session_state.StocksMarketYearlyReturn = st.number_input("Stocks Market Return",
                                                             value=constants.StocksMarketYearlyReturn)


def main():
    st.set_page_config(page_title='Mortgage Recycling Calculator', layout='wide')

    st.image('resources/banner.png', use_column_width=True)

    st.session_state.mortgage_df = None

    col1, col2 = st.columns([1, 1])
    with col1:
        load_mortgage_csv()
    with col2:
        parameters_bar()

    st.divider()

    main_mortgage_recycle_report()

    st.divider()
    st.write("© All rights reserved to George Kour. 2024 (v0.3)")
    st.write("Disclaimer: The use of this mortgage application is at your own risk. "
             "The information and results provided on this application are for informational purposes only and do not constitute financial advice or consultation. "
             "Users are advised to independently verify any data and consult with qualified professionals for personalized financial guidance. "
             "We do not assume any responsibility for the accuracy, completeness, or suitability of the information provided. "
             "By using this application, you acknowledge and accept that your financial decisions are solely your responsibility.")


if __name__ == "__main__":
    main()
