import numpy as np
import streamlit as st
import pandas as pd
from matplotlib import pyplot as plt

from common_components import footer, header, parameters_bar, display_amortization_pane, display_mortgage_info
from investments import MortgageRecycleInvestment, Investment, StocksMarketInvestment
from loan import Loan
from mortgage import Mortgage
import altair as alt


def enter_mortgage_details():
    with st.container():
        st.session_state.mortgages_df = st.data_editor(st.session_state.mortgages_df, num_rows="dynamic",
                                                       hide_index=True,
                                                       column_config={
                                                          'amount': st.column_config.NumberColumn('Amount',
                                                                                                  required=True),
                                                          'num_of_months': st.column_config.NumberColumn('Months',
                                                                                                         required=True,
                                                                                                         min_value=0,
                                                                                                         max_value=360,
                                                                                                         default=220),
                                                          'interest_rate': st.column_config.NumberColumn(
                                                              'Interest Rate',
                                                              required=True,
                                                              min_value=0,
                                                              max_value=20,
                                                              default=5.1),
                                                          'loan_type': st.column_config.TextColumn('Loan Type',
                                                                                                   required=True),
                                                          'grace_period': st.column_config.NumberColumn('Grace Period',
                                                                                                        required=True,
                                                                                                        min_value=0,
                                                                                                        max_value=50,
                                                                                                        default=0),
                                                          'cpi': st.column_config.CheckboxColumn(label='CPI',
                                                                                                 required=True,
                                                                                                 default=True)
                                                      },
                                                       column_order=['loan_type', 'amount', 'num_of_months',
                                                                    'interest_rate',
                                                                    'grace_period', 'cpi'],
                                                       use_container_width=True)


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
        st.write("Before")
        st.bar_chart({
            'Principal Payment': yearly_amortization_before['Principal Payment'] // 12,
            'Interest Payment': yearly_amortization_before['Interest Payment'] // 12
        }, color=['#FF5733', '#FFD700'])

    # Plot for 'After' in the second column
    with col_after:
        st.write("After")
        st.bar_chart({
            'Principal Payment': yearly_amortization_after['Principal Payment'] // 12,
            'Interest Payment': yearly_amortization_after['Interest Payment'] // 12
        }, color=['#FF5733', '#FFD700'])


def plot_monthly_interest_graph_yearly(yearly_amortization_before, yearly_amortization_after):
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Monthly Interest")
        st.line_chart({"Before": yearly_amortization_before['Interest Payment'] // 12,
                       "After": yearly_amortization_after['Interest Payment'] // 12})

    with col2:
        st.subheader("Accumulative Interest")
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
    if st.session_state.mortgages_df is None or not Mortgage.validate_dataframe(st.session_state.mortgages_df) or len(
            st.session_state.mortgages_df) == 0:
        return
    else:
        mortgage = Mortgage.from_dataframe(st.session_state.mortgages_df, st.session_state.CPI)

    st.divider()
    col1, col2, col3 = st.columns([6, 2, 2])

    # Add title in the first column
    with col1:
        st.subheader(f"Recycle Information")

    # Add number input in the second column
    with col2:
        start_value = int(np.floor(np.min([100000, (mortgage.loan_amount() // 100000) * 10000])))
        extra_payment = st.number_input('Enter Extra Amount:', min_value=0, value=start_value, step=start_value // 10,
                                        max_value=int(np.ceil(mortgage.loan_amount())))

    # Add selection list in the third column
    with col3:
        change = st.selectbox('Select Option:', ['Payment', 'Period'])

    mortgage_after = Mortgage.recycle_mortgage(mortgage=mortgage, extra_payment=extra_payment, change=change)

    mortgage_recycle_report_details(mortgage, mortgage_after)

    st.divider()
    saving_investment(mortgage, extra_payment)


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

    stockmarket_schedule_payment = StocksMarketInvestment(initial_fund=extra_payment,
                                                          yearly_return=st.session_state.StocksMarketYearlyReturn,
                                                          yearly_fee_percent=st.session_state.StocksMarketFeesPercentage,
                                                          gain_tax=st.session_state.TaxGainPercentage).generate_amortization_schedule(
        mortgage.num_of_months() // 12 + 10)

    yearly_amortization_period = Investment.get_yearly_amortization(amortization_schedule_period)
    yearly_amortization_payment = Investment.get_yearly_amortization(amortization_schedule_payment)
    yearly_amortization_stockmarket = Investment.get_yearly_amortization(stockmarket_schedule_payment)

    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader(f"Yearly Savings (Agg.): ")
        st.write(f'Extra Payment={extra_payment}')
        st.line_chart({"Payment": yearly_amortization_payment['Monthly Extra'].cumsum(),
                       "Period": yearly_amortization_period['Monthly Extra'].cumsum()},
                      color=['#336699', '#66cc99'])

    with col2:
        col_21, col_22 = st.columns([1, 1])
        with col_21:
            st.subheader("Invested Savings (Agg.):")
            col_21.write(
                f"Assuming Stocks Return={st.session_state.StocksMarketYearlyReturn}%, "
                f"Fees={st.session_state.StocksMarketFeesPercentage}%, "
                f"Tax={st.session_state.TaxGainPercentage}\%")
        with col_22:
            investment_field = st.selectbox('Showing', ['Net Revenue', 'Total Revenue', 'Monthly Income'])

        st.line_chart({"Payment": yearly_amortization_payment[investment_field],
                       "Period": yearly_amortization_period[investment_field],
                       f"Stock Market (No recycle)": yearly_amortization_stockmarket[investment_field]},
                      color=['#336699', '#66cc99', '#cc9900'])


def mortgage_recycle_report_details(mortgage_before: Mortgage, mortgage_after: Mortgage):
    summary_section(mortgage_before, mortgage_after)

    with st.expander("Mortgage Info", expanded=True):
        # col1, col2 = st.columns([1,1])
        # with col1:
        st.subheader("Current Mortgage Details:")
        display_mortgage_info(mortgage_before)
        # with col2:
        st.subheader("Recycled Mortgage Details:")
        display_mortgage_info(mortgage_after)

    yearly_amortization_before = Loan.get_yearly_amortization(mortgage_before.amortization_schedule)
    yearly_amortization_after = Loan.get_yearly_amortization(mortgage_after.amortization_schedule)

    st.divider()
    plot_monthly_payments_graph_yearly(yearly_amortization_before, yearly_amortization_after)

    st.divider()
    plot_monthly_interest_graph_yearly(yearly_amortization_before, yearly_amortization_after)

    st.divider()
    plot_principal_interest_yearly(yearly_amortization_before, yearly_amortization_after)

    st.divider()
    display_amortization_pane([mortgage_before, mortgage_after])


def bars_summary_section(mortgage_before, mortgage_after):
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

    col1, col_gap, col2, col3 = st.columns([5, 1, 1, 1])
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


def load_mortgage_csv():
    st.session_state.files = st.file_uploader("Load a Mortgage Data", accept_multiple_files=False,
                                              label_visibility="hidden", type=['csv', 'txt'])

    if st.session_state.files is not None:
        st.session_state.mortgages_df = pd.read_csv(st.session_state.files,
                                                    dtype={'amount': float, 'num_of_months': int, 'interest_rate': float,
                                                          'loan_type': str,
                                                          'grace_period': int, 'cpi': str})

        print("Mortgage data loaded successfully!")


def main():
    st.set_page_config(page_title='Mortgage Recycling', layout='wide', page_icon="📈")

    header()

    st.session_state.mortgages_df = pd.DataFrame(columns=list(Mortgage.columns_types().keys())).astype(
        Mortgage.columns_types())

    col1, col2 = st.columns([1, 2])
    with col1:
        with st.expander("Upload Mortgage File"):
            load_mortgage_csv()
    with col2:
        parameters_bar()

    enter_mortgage_details()

    main_mortgage_recycle_report()

    st.divider()
    col1, col3 = st.columns([4, 2])
    with col1:
        footer()
    with col3:
        st.write('Terminology:')
        data = {
            'Term': ['Total Revenue', 'Net Revenue', 'Monthly Income'],
            'Meaning': [
                'The total assets minus the invested equity.',
                'Total revenue after deducting taxes.',
                'The investment gains over 12 months.'
            ]
        }
        df = pd.DataFrame(data)
        st.table(df.reset_index(drop=True))


if __name__ == "__main__":
    main()
