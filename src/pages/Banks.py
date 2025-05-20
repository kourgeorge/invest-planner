import altair as alt
import streamlit as st
from common_components import header, footer, display_table_with_total_row, parameters_bar, mortgage_editor
from constants import CPI
from finance_utils import banks_monthly_data
from loan import Loan, LoanType
from mortgage import Mortgage
from pages.Planit_Compare import mortgage_comparison_report_details


def compare_with_banks(amount, years):
    dict= {'Fixed Non-Linked': (LoanType.FIXED, False),
           'Prime': (LoanType.PRIME, False),
           'Variable Non-Linked': (LoanType.VARIABLE, False),
           'Variable Index-Linked': (LoanType.VARIABLE, True),
           'Fixed Index-Linked': (LoanType.FIXED, True)
           }

    all_banks = list(banks_monthly_data['Bank'].unique())
    banks_monthly_data_temp = banks_monthly_data.copy()
    banks_monthly_data_temp['amount'] = banks_monthly_data_temp['Route Composition'] / 100 * amount
    banks_monthly_data_temp['Type'] = banks_monthly_data_temp['Interest Type'].apply(lambda x: dict[x][0].name)
    banks_monthly_data_temp['CPI'] = banks_monthly_data_temp['Interest Type'].apply(lambda x: CPI if dict[x][1] else 0)

    mortgages = []
    tabs_banks = st.tabs(all_banks)
    for b_i, bank in enumerate(all_banks):
        loans = []
        bank_maslolim = banks_monthly_data_temp[banks_monthly_data_temp['Bank'] == bank]
        for index, row in bank_maslolim.iterrows():
            loans += [Loan(row['amount'], years*12, interest_rate=row['Interest Rate'],
                           loan_type=row['Type'], cpi=row['CPI'])]
        bank_mortgage = Mortgage(loans, name=bank)
        with tabs_banks[b_i]:
            bank_mortgage_df = mortgage_editor(bank_mortgage.to_dataframe(), f'{bank}')
            mortgages.append(Mortgage.from_dataframe(bank_mortgage_df, st.session_state.CPI, bank))

    return mortgages


if __name__ == '__main__':

    st.set_page_config(page_title='Mortgage Recycling', layout='wide', page_icon="📈")

    header()
    cols = st.columns([1,1,3], gap='large')
    with cols[0]:
        amount = st.number_input(label="Amount", min_value=0, max_value=10000000, value=825000, step=100000)
    with cols[1]:
        years = st.number_input(label="Years", min_value=0, max_value=30, step=1, value=20)
    with cols[2]:
        parameters_bar()

    mortgages = compare_with_banks(amount, years)

    mortgage_comparison_report_details(mortgages)

    # Calculate the weighted interest rate for each row
    banks_monthly_data['Weighted Interest Rate'] = banks_monthly_data['Interest Rate'] * (
                banks_monthly_data['Route Composition'] / 100)

    st.divider()
    interest_color_scheme = ['#BFD9FF', '#7AB6E0', '#B6E07A', '#FFB6B6', '#E07A7A']

    st.header("Comparing Banks Mortgage Information according to BanK of Israel: January 2024")
    col1, col2 = st.columns(2,gap='large')
    with col1:
        chart = alt.Chart(banks_monthly_data).mark_bar().encode(
            y=alt.Y('Bank:N', title='Bank'),
            x=alt.X('sum(Route Composition):Q', stack='normalize', title='Route Composition'),
            color=alt.Color('Interest Type:N', title='Interest Type', scale=alt.Scale(range=interest_color_scheme)),
            order=alt.Order('Interest Type', sort='ascending')
        ).properties(
            width=600,
            height=400,
            title='Route Composition for Each Bank (Normalized)'
        )
        st.altair_chart(chart)

    with col2:

        chart2 = alt.Chart(banks_monthly_data).mark_bar().encode(
            y=alt.Y('Bank:N', title='Bank'),
            x=alt.X('sum(Weighted Interest Rate):Q', title='Weighted Interest'),
            color=alt.Color('Interest Type:N', title='Interest Type', scale=alt.Scale(range=interest_color_scheme)),
            order=alt.Order('Interest Type', sort='ascending'),
            tooltip = ['Interest Type', 'Route Composition', 'Interest Rate']
        ).properties(
            width=600,
            height=400,
            title='Weighted Interest by route',
        )
        st.altair_chart(chart2)

    bank_colors = ['#84AC35', '	#FFD700', '#ea1a23', '#c58e2a', '#4484f6', '#048148', '#eb9834']

    cols = st.columns([1,2,1])
    with cols[1]:
        chart_interest = alt.Chart(banks_monthly_data).mark_bar().encode(
            x=alt.X('Bank:N', title=''),
            y=alt.Y('Interest Rate:Q', title='Interest Rate'),
            color=alt.Color('Bank:N', title='',scale=alt.Scale(range=bank_colors)),
            column=alt.Column('Interest Type:N', title='', )
        ).properties(
            width=100,
            height=400,
            title='Interest Rate for Each Loan Type Across Banks'
        )

        st.altair_chart(chart_interest)

    footer()

