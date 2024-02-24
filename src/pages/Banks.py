import pandas as pd
import altair as alt
import streamlit as st
from common_components import header, footer, display_table_with_total_row, parameters_bar
from constants import CPI
from finance_utils import banks_monthly_data
from loan import Loan, LoanType
from mortgage import Mortgage


def compare_with_banks(amount, years):
    dict= {'Fixed Non-Linked': (LoanType.FIXED, False),
           'Prime': (LoanType.PRIME, False),
           'Variable Non-Linked': (LoanType.ARM, False),
           'Variable Index-Linked': (LoanType.ARM, True),
           'Fixed Index-Linked': (LoanType.FIXED, True)
           }

    all_banks = banks_monthly_data['Bank'].unique()
    banks_monthly_data_temp = banks_monthly_data.copy()
    banks_monthly_data_temp['amount'] = banks_monthly_data_temp['Route Composition'] / 100 * amount
    banks_monthly_data_temp['Type'] = banks_monthly_data_temp['Interest Type'].apply(lambda x: dict[x][0].name)
    banks_monthly_data_temp['CPI'] = banks_monthly_data_temp['Interest Type'].apply(lambda x: CPI if dict[x][1] else 0)

    tabs_banks = st.tabs(list(all_banks))
    for b_i, bank in enumerate(all_banks):
        loans = []
        bank_maslolim = banks_monthly_data_temp[banks_monthly_data_temp['Bank'] == bank]
        for index, row in bank_maslolim.iterrows():
            loans += [Loan(row['amount'], years*12, interest_rate=row['Interest Rate'],
                           loan_type=row['Type'], cpi=row['CPI'])]
        bank_mortgage = Mortgage(loans, name=bank)
        with tabs_banks[b_i]:
            display_table_with_total_row(bank_mortgage.display_mortgage_info())


if __name__ == '__main__':

    st.set_page_config(page_title='Mortgage Recycling', layout='wide', page_icon="📈")

    header()
    cols = st.columns([1,1,3], gap='large')
    with cols[0]:
        amount = st.number_input(label="Amount", min_value=0, max_value=10000000, value=500000, step=100000)
    with cols[1]:
        years = st.number_input(label="Years", min_value=0, max_value=30, step=1, value=20)
    with cols[2]:
        parameters_bar()

    compare_with_banks(amount, years)

    # Calculate the weighted interest rate for each row
    banks_monthly_data['Weighted Interest Rate'] = banks_monthly_data['Interest Rate'] * (
                banks_monthly_data['Route Composition'] / 100)
    col1, col2 = st.columns(2,gap='large')
    st.subheader("Comparing Bank Data")
    with col1:
        chart = alt.Chart(banks_monthly_data).mark_bar().encode(
            y=alt.Y('Bank:N', title='Bank'),
            x=alt.X('sum(Route Composition):Q', stack='normalize', title='Route Composition'),
            color=alt.Color('Interest Type:N', title='Interest Type'),
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
            color=alt.Color('Interest Type:N', title='Interest Type'),
            order=alt.Order('Interest Type', sort='ascending'),
            tooltip = ['Interest Type', 'Route Composition', 'Interest Rate']
        ).properties(
            width=600,
            height=400,
            title='Weighted Interest by route',
        )
        st.altair_chart(chart2)



    # # Group by Bank and calculate the weighted average Interest Rate
    # weighted_avg_df = banks_monthly_data.groupby('Bank').agg({'Weighted Interest Rate': 'sum', 'Route Composition': 'sum'})
    # weighted_avg_df['IRR'] = weighted_avg_df['Weighted Interest Rate']
    # weighted_avg_df['Interest Type'] = 'IRR'
    # weighted_avg_df.reset_index(inplace=True)
    # # Create a new row for IRR in the original dataframe for each bank
    #
    # # Create a new DataFrame for IRR rows
    # irr_rows = weighted_avg_df[['Bank', 'IRR', 'Route Composition', 'Interest Type']].rename(
    #     columns={'IRR': 'Interest Rate'})
    #
    #
    # # Concatenate the original DataFrame with the new DataFrame for IRR rows
    # df_with_irr = pd.concat([banks_monthly_data, irr_rows], ignore_index=True)

    chart_interest = alt.Chart(banks_monthly_data).mark_bar().encode(
        x=alt.X('Bank:N', title='Bank'),
        y=alt.Y('Interest Rate:Q', title='Interest Rate'),
        color=alt.Color('Bank:N', title=''),
        column=alt.Column('Interest Type:N', title='', )
    ).properties(
        width=100,
        height=400,
        title='Interest Rate for Each Loan Type Across Banks'
    )

    st.altair_chart(chart_interest)

    footer()

