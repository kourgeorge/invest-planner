import numpy as np
import streamlit as st
import pandas as pd
from common_components import footer, header, parameters_bar, display_amortization_pane, display_table_with_total_row, \
    recycle_strategy_help, plot_annual_amortization_monthly_line, convert_string_to_int, mortgage_editor
from investments import MortgageRecycleInvestment, Investment, StocksMarketInvestment
from loan import Loan, LoanType
from mortgage import Mortgage
import altair as alt


def enter_mortgage_details():
    with st.container():
        if len(st.session_state.mortgages_df) == 0:
            return
        tabs = st.tabs(st.session_state.mortgages_name)
        for i in range(len(st.session_state.mortgages_df)):
            with tabs[i]:
                st.session_state.mortgages_df[i] = mortgage_editor(st.session_state.mortgages_df[i], st.session_state.mortgages_name[i])
            st.session_state.mortgages[i] = Mortgage.from_dataframe(st.session_state.mortgages_df[i], name=st.session_state.mortgages_name[i])


def display_yearly_amortization_table(mortgage, amortization_type):
    if amortization_type == 'Yearly':
        amortization = Loan.get_yearly_amortization(mortgage.amortization_schedule.reset_index())
    else:
        amortization = mortgage.amortization_schedule
    st.table(amortization)


def plot_monthly_payments_graph_yearly(mortgages):
    yearly_amortizations = [Loan.get_yearly_amortization(mortgage.amortization_schedule) for mortgage in mortgages]

    col1, col2 = st.columns([1, 1], gap='large')
    with col1:
        st.subheader("Monthly Payment:")
        plot_annual_amortization_monthly_line(mortgages, 'Monthly Payment')
    with col2:
        st.subheader("Remaining Balance:")
        st.area_chart(
            {f"{mortgages[i].name}": yearly_amortization['Remaining Balance'] for i, yearly_amortization in
             enumerate(yearly_amortizations)})


def plot_monthly_interest_graph_yearly(mortgages):
    yearly_amortizations = [Loan.get_yearly_amortization(mortgage.amortization_schedule) for mortgage in mortgages]

    col1, col2 = st.columns([1, 1], gap='large')
    with col1:
        st.subheader("Monthly Interest")
        plot_annual_amortization_monthly_line(mortgages, 'Interest Payment')

    with col2:
        st.subheader("Accumulative Interest")
        st.area_chart(
            {f"{mortgages[i].name}": yearly_amortization['Interest Payment'].cumsum() for i, yearly_amortization in
             enumerate(yearly_amortizations)})


def plot_principal_interest_yearly(yearly_amortization_before, yearly_amortization_after):
    st.subheader("Principal-Interest Payment:")

    col_before, col_after = st.columns(2, gap='large')
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


def prepare_mortgage_recycle():
    # if st.session_state.mortgages_df is None or not Mortgage.validate_dataframe(st.session_state.mortgages_df[0]) or len(
    #         st.session_state.mortgages_df) == 0:
    #     return
    # else:

    st.session_state.mortgages[0] = Mortgage.from_dataframe(st.session_state.mortgages_df[0], st.session_state.CPI,
                                                            name="Before")

    st.session_state.mortgages[1] = Mortgage.recycle_mortgage(mortgage=st.session_state.mortgages[0],
                                                              extra_payment=st.session_state.extra_payment,
                                                              change=st.session_state.change) if st.session_state.extra_payment > 0 else \
    st.session_state.mortgages[0]
    st.session_state.mortgages_df[1] = st.session_state.mortgages[1].to_dataframe()

    st.session_state.extra_actual_monthly = (
                st.session_state.mortgages[0].monthly_payment(0) - st.session_state.mortgages[1].monthly_payment(0)
                + st.session_state.extra_monthly) if st.session_state.extra_monthly != 0 else 0

    st.session_state.mortgages[1] = Mortgage.recycle_mortgage_monthly(mortgage=st.session_state.mortgages[1],
                                                                      extra_payment=st.session_state.extra_actual_monthly) if st.session_state.extra_actual_monthly != 0 else \
    st.session_state.mortgages[1]
    st.session_state.mortgages_df[1] = st.session_state.mortgages[1].to_dataframe()
    st.session_state.mortgages[1].name = 'After'

    enter_mortgage_details()


def main_mortgage_recycle_report(mortgage, mortgage_after, extra_payment, extra_monthly):

    mortgage_recycle_report_details(mortgage, mortgage_after)

    st.divider()
    saving_investment(mortgage, extra_payment, extra_monthly)


def saving_investment(mortgage: Mortgage, extra_payment: int, monthly_extra:int=0):
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

    col1, col2 = st.columns([1, 1], gap='large')
    with col1:
        st.subheader(f"Annual Payment Savings (Acc.): ")
        st.write(f'Extra Payment={extra_payment}')
        st.line_chart({"Payment": yearly_amortization_payment['Monthly Extra'].cumsum(),
                       "Period": yearly_amortization_period['Monthly Extra'].cumsum()},
                      color=['#336699', '#66cc99'])

    with col2:
        col_21, col_22 = st.columns([3, 1])
        with col_21:
            st.subheader("Investing Payment Savings (Acc.):")
            col_21.write(
                f"Assuming Stocks Return={st.session_state.StocksMarketYearlyReturn}%, "
                f"Fees={st.session_state.StocksMarketFeesPercentage}%, "
                f"Tax={st.session_state.TaxGainPercentage}\%")
        with col_22:
            investment_field = st.selectbox('Showing', ['Net Revenue', 'Total Revenue', 'Monthly Income'],
                                            help='See Terminology Pane.')

        st.line_chart({"Payment": yearly_amortization_payment[investment_field],
                       "Period": yearly_amortization_period[investment_field],
                       f"Stock Market (No recycle)": yearly_amortization_stockmarket[investment_field]},
                      color=['#336699', '#66cc99', '#cc9900'])


def show_loans_recycling_details(mortgage_before, mortgage_after):
    df_before = mortgage_before.get_mortgage_info()
    df_after = mortgage_after.get_mortgage_info()
    # Merge dataframes on 'Loan #'
    merged_df = pd.merge(df_before, df_after, on=['Loan Type', 'Interest Rate'], suffixes=('_before', '_after'))

    columns_to_include = ['Loan Amount',  'First Payment', 'Number of Months', 'Total Interest', 'Total Cost']
    # Create a new DataFrame with formatted values
    formatted_df = pd.DataFrame()
    formatted_df['Loan Type'] = merged_df['Loan Type']

    for column in columns_to_include:
        formatted_df[column] = merged_df.apply(lambda row: "{:,.0f}".format(row[f'{column}_after'] - row[f'{column}_before']), axis=1)
    formatted_df['Cost to Currency'] = merged_df.apply(lambda row: "{:,.3f}".format(row['Cost to Currency_after'] - row['Cost to Currency_before']), axis=1)

    return formatted_df


def mortgage_recycle_report_details(mortgage_before: Mortgage, mortgage_after: Mortgage):
    st.divider()

    st.subheader(f"Mortgage Information")
    summary_section(mortgage_before, mortgage_after)

    st.divider()
    st.subheader("Recycling Plan")
    merged = show_loans_recycling_details(mortgage_before, mortgage_after)
    st.table(merged)

    with st.expander("Mortgages Data", expanded=False):
        # col1, col2 = st.columns([1,1])
        # with col1:
        # st.subheader("Current Mortgage Details:")
        # display_mortgage_info(mortgage_before)
        # # with col2:
        # st.subheader("Recycled Mortgage Details:")
        # display_mortgage_info(mortgage_after)

        cols = st.columns(2, gap='large')
        with cols[0]:
            st.write("Loans status Before")
            display_table_with_total_row(mortgage_before.display_mortgage_info()[
                                             ['Loan Type', 'Loan Amount', 'First Payment', 'Number of Months',
                                              'Total Interest', 'Total Cost', 'Cost to Currency']])
        with cols[1]:
            st.write("Loans After")
            # display_table_with_total_row(merged)
            display_table_with_total_row(mortgage_after.display_mortgage_info()[
                                             ['Loan Type', 'Loan Amount', 'First Payment', 'Number of Months',
                                              'Total Interest', 'Total Cost', 'Cost to Currency']])

    yearly_amortization_before = Loan.get_yearly_amortization(mortgage_before.amortization_schedule)
    yearly_amortization_after = Loan.get_yearly_amortization(mortgage_after.amortization_schedule)

    st.divider()
    plot_monthly_payments_graph_yearly([mortgage_before, mortgage_after])

    st.divider()
    plot_monthly_interest_graph_yearly([mortgage_before, mortgage_after])

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

    mortgages = [mortgage_before, mortgage_after]
    summary_data = {
        "Name": [mortgage.name for mortgage in mortgages],
        "Amount": [np.round(mortgage.loan_amount()) for mortgage in mortgages],
        "Period (Years)": [np.round(mortgage.num_of_months(),2) for mortgage in mortgages],
        "Interest": [np.round(mortgage.total_interest_payments()) for mortgage in mortgages],
        "Indexation": [np.round(mortgage.total_inflation_payments()) for mortgage in mortgages],
        "Cost": [np.round(mortgage.total_payments()) for mortgage in mortgages],
        "Cost per Currency": [np.round(mortgage.cost_per_currency(), 2) for mortgage in mortgages],
        "First Payment": [np.round(mortgage.monthly_payment(0)) for mortgage in mortgages],
        "Maximum Payment": [np.round(mortgage.highest_monthly_payment()) for mortgage in mortgages],
        "Total Predicted Interest (IRR)": [np.round(mortgage.get_irr(), 2) for mortgage in mortgages],
        "Risk": [round(mortgage.get_volatility()) for mortgage in mortgages]
    }

    # Add the savings row.
    summary_df = pd.DataFrame(summary_data)
    # Filter only numeric columns
    numeric_columns = summary_df.select_dtypes(include='number')
    # Add a new row which is the sum of the previous two rows for numeric columns
    new_row = numeric_columns.iloc[-2] - numeric_columns.iloc[-1]
    # Append the new row to the original DataFrame
    summary_df = pd.concat([summary_df, pd.DataFrame([new_row], columns=numeric_columns.columns)], ignore_index=True)
    extra = mortgage_before.loan_amount() - mortgage_after.loan_amount() # reduce the loan amount from the cost savings
    summary_df.at[summary_df.index[-1], 'Cost'] -=  extra
    summary_df.at[summary_df.index[-1], 'Name'] = 'Savings'
    savings_row = summary_df.iloc[-1]
    before_row = summary_df.iloc[0]
    after_row = summary_df.iloc[1]

    col1, col_gap, col2 = st.columns([3, 0.3, 2])

    with col1:
        st.dataframe(summary_df.set_index(keys='Name').transpose(), use_container_width=True, hide_index=False)
    with col2:
        st2_1, st2_2 = st.columns(2)

        with st2_1:
            st.metric(label='Interest Savings', value="{:,.0f}".format(savings_row["Interest"]),
                      delta=f'{-np.round(savings_row["Interest"] / before_row["Interest"] * 100, 2)}%',
                      delta_color='inverse')

            st.metric(label='Indexation Savings', value="{:,.0f}".format(savings_row["Indexation"]),
                      delta=f'{-np.round(savings_row["Indexation"] / before_row["Indexation"] * 100, 2)}%',
                      delta_color='inverse')

            st.metric(label='Cost Savings', value="{:,.0f}".format(savings_row["Cost"]),
                      delta=f'{-np.round(savings_row["Cost"] / (before_row["Cost"]-mortgage_before.loan_amount()) * 100, 2)}%',
                      delta_color='inverse')

        with st2_2:
            st.metric(label='First Monthly Payment', value="{:,.0f}".format(after_row["First Payment"]),
                      delta=f'{int(after_row["First Payment"] - before_row["First Payment"])} ILS', delta_color='inverse')

            st.metric(label='Risk', value="{:,.0f}".format(savings_row["Risk"]),
                      delta=f'{-np.round(savings_row["Risk"] / before_row["Risk"] * 100, 2)}%',
                      delta_color='inverse')

            st.metric(label='Period Change (Months)', value="{:,.0f}".format(savings_row["Period (Years)"]),
                      delta=f'{-np.round(savings_row["Period (Years)"] / before_row["Period (Years)"] * 100, 2)}%',
                      delta_color='inverse')

        # remove the savings row, melt the DataFrame to make it suitable for a stacked bar chart
        melted_df = pd.melt(summary_df.drop(index=summary_df.index[-1]), id_vars=["Name"], value_vars=["Amount", "Interest", "Indexation"])
        risk_chart = alt.Chart(melted_df).mark_bar().encode(
            x=alt.X('sum(value)', axis=alt.Axis(title=None)),
            y=alt.Y('Name', sort=['Before', 'After'] , axis=alt.Axis(title=None)),
            color=alt.Color('variable', scale=alt.Scale(range=['#9ACD32', '#FFD700', '#FF6347'])),
            tooltip=['Name', 'variable', 'value']
        ).properties(
            title='Costs'
        )
        st.altair_chart(risk_chart, use_container_width=True)


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


def invested_savings_options_terminology():
    with st.expander('Terminology', expanded=False):
        data = {
            'Term': ['Total Revenue', 'Net Revenue', 'Monthly Income'],
            'Meaning': [
                'The total assets minus the invested equity (initial and monthly).',
                'Total Revenue after deducting stocks selling taxes.',
                'The investment gains over 12 months.'
            ]
        }
        df = pd.DataFrame(data)
        st.table(df.reset_index(drop=True))

def get_example_mortgage():
    return pd.DataFrame([[158334, 180, 5.149, LoanType.FIXED.name, 0, False],
                         [158333, 180, 5.55, LoanType.PRIME.name, 0, False],
                         [158333, 180, 3.06, LoanType.PRIME.ARM.name, 0, True]],
                        columns=list(Mortgage.columns_types().keys())).astype(
        Mortgage.columns_types())


def main():
    st.set_page_config(page_title='Mortgage Recycling', layout='wide', page_icon="📈")

    header()
    st.title('Mortgage Recycling Calculator')
    st.session_state.mortgages_df = [get_example_mortgage(), get_example_mortgage()]
    st.session_state.mortgages = [Mortgage.from_dataframe(get_example_mortgage()), Mortgage.from_dataframe(get_example_mortgage()),]
    st.session_state.mortgages_name = ['Before', 'After']

    col1, col2 = st.columns([1, 2])
    with col1:
        with st.expander("Upload Mortgage File"):
            load_mortgage_csv()
    with col2:
        parameters_bar()

    col1, col2, col3 = st.columns([3, 1, 1], gap='large')
    with col2:
        start_value = int(np.floor(np.min([100000, (st.session_state.mortgages_df[0]['amount'].sum() // 100000) * 10000])))
        st.session_state.extra_payment = st.number_input('Extra Amount:', min_value=0, value=start_value, step=start_value // 10,
                                        max_value=int(np.ceil(st.session_state.mortgages_df[0]['amount'].sum())))

        st.session_state.is_adding_monthly = st.checkbox('Monthly Extra')
        st.session_state.extra_payment_monthly = st.number_input('extra', min_value=-2000, value=0,
                                                step=start_value // 1000,
                                                max_value=int(np.ceil(st.session_state.mortgages_df[0]['amount'].sum())),
                                                key="monthly_extra", disabled=not st.session_state.is_adding_monthly, label_visibility="collapsed")

    st.session_state.extra_monthly = 0 if not st.session_state.is_adding_monthly else st.session_state.extra_payment_monthly
    with col3:
        st.session_state.change = st.selectbox('Reduce:', ['Payment', 'Period'], help=recycle_strategy_help, disabled=(st.session_state.extra_payment==0))


    with col1:
        prepare_mortgage_recycle()


    main_mortgage_recycle_report(st.session_state.mortgages[0], st.session_state.mortgages[1], st.session_state.extra_payment, st.session_state.extra_monthly)

    st.divider()
    invested_savings_options_terminology()
    footer()


if __name__ == "__main__":
    main()
