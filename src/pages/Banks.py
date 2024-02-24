import pandas as pd
import altair as alt
import streamlit as st
from common_components import header, footer


if __name__ == '__main__':

    st.set_page_config(page_title='Mortgage Recycling', layout='wide', page_icon="📈")

    header()

    banks_monthly_data = pd.read_csv('data/israel_banks_monthly.csv')
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
