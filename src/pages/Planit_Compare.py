import numpy as np
import streamlit as st
import pandas as pd
import altair as alt

from common_components import footer, header, parameters_bar, display_amortization_pane, display_table_with_total_row, \
    plot_annual_amortization_monthly_line
from investments import MortgageRecycleInvestment, Investment, StocksMarketInvestment
from loan import Loan, LoanType
from mortgage import Mortgage

loan_type_keys = [enum_member.name for enum_member in LoanType]

def enter_mortgage_details():
    with st.container():
        if len(st.session_state.mortgages_df) == 0:
            return

        tabs = st.tabs(st.session_state.mortgages_name)
        for i in range(len(st.session_state.mortgages_df)):
            with tabs[i]:
                st.session_state.mortgages_name[i] = st.text_input('Name', value=st.session_state.mortgages_name[i], key=f'name_{st.session_state.mortgages_name[i]}{i}')
                st.session_state.mortgages_df[i] = st.data_editor(st.session_state.mortgages_df[i], key=f'data_{st.session_state.mortgages_name[i]}{i}',
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
                                                                  column_order=['loan_type', 'amount', 'num_of_months',
                                                                               'interest_rate',
                                                                               'grace_period', 'cpi'],
                                                                  use_container_width=True)


def plot_monthly_payments_graph_yearly(mortgages):
    yearly_amortizations = [Loan.get_yearly_amortization(mortgage.amortization_schedule) for mortgage in mortgages]
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Monthly Payment:")
        st.line_chart({mortgages[i].name: yearly_amortization['Monthly Payment']//12 for i, yearly_amortization in
                       enumerate(yearly_amortizations)})

    with col2:
        st.subheader("Remaining Balance:")
        st.line_chart({mortgages[i].name: yearly_amortization['Remaining Balance'] for i, yearly_amortization in
                       enumerate(yearly_amortizations)})


def plot_principal_interest_yearly(mortgages):
    st.subheader("Principal-Interest Payment:")
    yearly_amortizations = [Loan.get_yearly_amortization(mortgage.amortization_schedule) for mortgage in mortgages]

    cols = st.columns([1] * len(mortgages))
    # Plot for 'Before' in the first column
    for i, col in enumerate(cols):
        with col:
            st.write(mortgages[i].name)
            st.bar_chart({
                'Principal Payment': yearly_amortizations[i]['Principal Payment'] // 12,
                'Interest Payment': yearly_amortizations[i]['Interest Payment'] // 12
            }, color=['#FF5733', '#FFD700'])


def main_mortgage_comparison_report():
    if 'mortgages_df' not in st.session_state or len(st.session_state.mortgages_df) == 0:
        return
    else:
        valid_mortgage_dfs = any([len(mortage) > 0 and Mortgage.validate_dataframe(mortage) for
                                  mortage in st.session_state.mortgages_df])
    if not valid_mortgage_dfs:
        return

    mortgages = [Mortgage.from_dataframe(mortgage_df, st.session_state.CPI, name=st.session_state.mortgages_name[i])
                 for i, mortgage_df in enumerate(st.session_state.mortgages_df)]
    mortgages = [mortage for mortage in mortgages if not mortage.is_empty()]

    st.divider()

    mortgage_comparison_report_details(mortgages)

    st.divider()
    # saving_investment(mortgage, mortgage_after)


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


def mortgage_comparison_report_details(mortgages):
    st.subheader(f"Mortgages Information")
    summary_section(mortgages)

    with st.expander("Mortgages Info", expanded=True):
        for mortgage in mortgages:
            st.subheader(f"Mortgage Details: {mortgage.name}")
            display_table_with_total_row(mortgage.display_mortgage_info())

    st.divider()
    plot_monthly_payments_graph_yearly(mortgages)

    st.divider()
    plot_monthly_interest_graph_yearly(mortgages)

    st.divider()
    plot_principal_interest_yearly(mortgages)

    st.divider()
    display_amortization_pane(mortgages)


def plot_monthly_interest_graph_yearly(mortgages):
    yearly_amortizations = [Loan.get_yearly_amortization(mortgage.amortization_schedule) for mortgage in mortgages]

    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Monthly Interest")
        plot_annual_amortization_monthly_line(mortgages, 'Interest Payment')

    with col2:
        st.subheader("Accumulative Interest")
        st.line_chart(
            {f"{mortgages[i].name}": yearly_amortization['Interest Payment'].cumsum() for i, yearly_amortization in
             enumerate(yearly_amortizations)})


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


def summary_section(mortgages):

    summary_data = {
        "Name": [mortgage.name for mortgage in mortgages],
        "Amount": [np.round(mortgage.loan_amount()) for mortgage in mortgages],
        "Period (Years)": [np.round(mortgage.num_of_months()/12,2) for mortgage in mortgages],
        "Interest+CPI": [np.round(mortgage.total_interest_payments()) for mortgage in mortgages],
        "First Payment": [np.round(mortgage.monthly_payment(0)) for mortgage in mortgages],
        "Maximum Payment": [np.round(mortgage.highest_monthly_payment()) for mortgage in mortgages],
        "Avg Interest Rate": [np.round(mortgage.average_interest_rate(), 2) for mortgage in mortgages],
        "Cost": [np.round(mortgage.total_payments()) for mortgage in mortgages],
        "Cost per Currency": [np.round(mortgage.cost_per_currency(),2) for mortgage in mortgages],
        "Risk": [round(mortgage.get_volatility()) for mortgage in mortgages]
    }
    summary_df_table = pd.DataFrame(summary_data)

    col_summary, col_metrics = st.columns([3, 2], gap='large')
    with col_summary:
        st.dataframe(summary_df_table.set_index('Name').transpose(), use_container_width=True, hide_index=False)

    with col_metrics:
        summary_df = summary_df_table.copy()
        summary_df["Inflation Payment"] = [np.round(mortgage.total_inflation_payments()) for mortgage in
                                                 mortgages]

        summary_df["Interest Only"] = summary_df["Interest+CPI"] - summary_df["Inflation Payment"]

        risk_scale = alt.Scale(domain=(summary_df["Risk"].min()-1, summary_df["Risk"].max()+1))
        interest_scale = alt.Scale(domain=(summary_df["Avg Interest Rate"].min()-1, summary_df["Avg Interest Rate"].max()+1))
        size_scale = alt.Scale(domain=(summary_df['First Payment'].min()*0.9, summary_df['First Payment'].max()))

        # Melt the DataFrame to make it suitable for a stacked bar chart
        melted_df = pd.melt(summary_df, id_vars=["Name"], value_vars=["Amount", "Interest Only", "Inflation Payment"])
        chart = alt.Chart(melted_df).mark_bar().encode(
            x=alt.X('sum(value)', axis=alt.Axis(title=None)),
            y=alt.Y('Name', sort='x', axis=alt.Axis(title=None)),
            color=alt.Color('variable', scale=alt.Scale(range=['#9ACD32', '#FFD700', '#FF6347'])),
            tooltip=['Name', 'variable', 'value']
        ).properties(
            title='Costs'
        )
        st.altair_chart(chart, use_container_width=True)


        c = (alt.Chart(summary_df).mark_circle()
             .encode(x=alt.Y("Risk", scale=risk_scale),
                     y=alt.X("Avg Interest Rate", scale=interest_scale),
                     size=alt.Size("First Payment", scale=size_scale),
                     color='Name', tooltip=["Risk", "Avg Interest Rate", "Maximum Payment"])).properties(
            width=200, height=200)

        st.altair_chart(c, use_container_width=True)


        # radar_chart = alt.Chart(summary_df).mark_line().encode(
        #     alt.Y('Name:N'),
        #     alt.X('Avg Interest Rate', title='Interest Rate'),
        #     alt.X2('Volatility Score', title='Volatility Score')
        # ).properties(
        #     title='Comparison of Loans'
        # )
        # st.altair_chart(radar_chart, use_container_width=True)


def load_mortgages_csv(max_files_uploads):
    files = st.file_uploader("Load a Mortgages Data", accept_multiple_files=True,
                             label_visibility="hidden", type=['csv', 'txt'])
    if files is None:
        return
    for i, file in enumerate(files[:max_files_uploads]):
        st.session_state.mortgages_df[i] = pd.read_csv(file,
                                                       dtype={'amount': float, 'num_of_months': int,
                                                             'interest_rate': float,
                                                             'loan_type': str,
                                                             'grace_period': int, 'cpi': str})

        st.session_state.mortgages_name[i] = f"{file.name}"
        continue


def main():
    st.session_state.max_num_mortgages = 5
    st.set_page_config(page_title='Mortgage Compare', layout='wide', page_icon="📈")

    header()
    st.title('Mortgage Comparison')

    st.session_state.mortgages_df = [
        pd.DataFrame(columns=list(Mortgage.columns_types().keys())).astype(Mortgage.columns_types()) for i in range(st.session_state.max_num_mortgages)]
    st.session_state.mortgages_name = [f"Mortgage {i + 1}" for i in range(st.session_state.max_num_mortgages)]

    col1, col2 = st.columns([1, 2])
    with col1:
        with st.expander('Upload Mortgage data', expanded=False):
            load_mortgages_csv(st.session_state.max_num_mortgages)
    with col2:
        parameters_bar()

    # if st.button(label='Add another Mortgage'):
    #     st.session_state.mortgages_df.append(pd.DataFrame(columns=list(Mortgage.columns_types().keys())).astype(Mortgage.columns_types()))
    #     st.session_state.mortgages_name.append("New Mortgage")

    col1, _ = st.columns([2, 1])
    with col1:
        enter_mortgage_details()

    main_mortgage_comparison_report()

    st.divider()
    footer()

if __name__ == "__main__":
    main()
