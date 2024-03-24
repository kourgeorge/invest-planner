import numpy as np
import pandas as pd
import streamlit as st
from common_components import header, footer, load_mortgage_csv, investment_parameters_bar, mortgage_editor, \
    display_amortization_table
from investments import RealEstateInvestment, MortgageRecycleInvestment, StocksMarketInvestment, Investment
from mortgage import Mortgage
from pages.Planit_Recycle import get_example_mortgage
from typing import List
import altair as alt


def main_compare_investments(investments: List[Investment]):
    summary_section(investments)
    yearly_amortizations = []

    for i, investment in enumerate(investments):
        yearly_amortization = Investment.get_yearly_amortization(investment.amortization_schedule)
        yearly_amortizations.append(yearly_amortization)


    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader('Avg. Monthly Cash Flow')
        st.line_chart({f"{investments[i].name}": (yearly_amortization['Income']-yearly_amortization['Expenses']) // 12 for i, yearly_amortization in
                      enumerate(yearly_amortizations)})

    with col2:
        st.subheader('Monthly Income', help="In the recycle, we assume that payment amount saved due to the recycle, will become an income to which will be invested in the stock market.")
        st.line_chart({f"{investments[i].name}": yearly_amortization['Income'] // 12 for i, yearly_amortization in
                       enumerate(yearly_amortizations)})


    with col3:
        st.subheader('Monthly Expenses')
        st.line_chart(
            {f"{investments[i].name}": yearly_amortization['Expenses'] // 12 for i, yearly_amortization in
             enumerate(yearly_amortizations)})

    col1, col2 = st.columns(2)
    with col1:
        st.subheader('Total Revenue')
        st.line_chart(
            {f"{investments[i].name}": yearly_amortization['Total Revenue'] for i, yearly_amortization in
             enumerate(yearly_amortizations)})

        st.subheader('Total Liabilities')
        st.line_chart(
            {f"{investments[i].name}": yearly_amortization['Total Liabilities'] for i, yearly_amortization in
             enumerate(yearly_amortizations)})

    with col2:
        st.subheader('Net Revenue')
        st.line_chart({f"{investments[i].name}": yearly_amortization['Net Revenue'] for i, yearly_amortization in
                       enumerate(yearly_amortizations)})

        st.subheader('Total Assets')
        st.line_chart({f"{investments[i].name}": yearly_amortization['Total Assets'] for i, yearly_amortization in
                       enumerate(yearly_amortizations)})


def real_estate_tab(investment_years):
    cols = st.columns(6)
    with cols[0]:
        new_apartment_price = st.number_input(label='Apartment Price', value=950000)
    with cols[1]:
        renovation_costs = st.number_input(label='Renovation Costs', value=15000)
    with cols[2]:
        monthly_rental = st.number_input(label='Monthly Rental', value=3500)
    with cols[3]:
        average_mortgage_interest_rate = st.number_input(label='Average Mortgage Interest', value=5.3)
    with cols[4]:
        mortgage_period = st.number_input(label='Mortgage Period', value=15)

    buying_costs = st.session_state.TaxBuyingPercentage / 100 * new_apartment_price

    REinvestment = RealEstateInvestment.quick_calculation(price=new_apartment_price, down_payment=initial_fund,
                                                          investment_years=investment_years,
                                                          interest_rate=average_mortgage_interest_rate,
                                                          mortgage_num_years=mortgage_period,
                                                          housing_index=st.session_state.CPI,
                                                          appreciation_rate=st.session_state.RealEstateAppreciations,
                                                          monthly_rental_income=st.session_state.MaintenanceRentalRatio * monthly_rental,
                                                          buying_costs=buying_costs+renovation_costs,
                                                          name='RE')

    return REinvestment


def preconstruction_real_estate_tab(investment_years):
    cols = st.columns(6)
    with cols[0]:
        new_apartment_price = st.number_input(label='New Apartment Price', value=2100000)
    with cols[1]:
        construction_period = st.number_input(label='Construction Period', value=4)
    with cols[2]:
        monthly_rental = st.number_input(label='Monthly Rental', value=7000)
    with cols[3]:
        average_mortgage_interest_rate = st.number_input(label='Average Mortgage Interest', value=5.3,
                                                         key='new_avg_motgage_interest')
    with cols[4]:
        mortgage_period = st.number_input(label='Mortgage Period', value=25, key='new_mortgage_period')

    buying_costs = st.session_state.TaxBuyingPercentage / 100 * new_apartment_price

    REinvestment = RealEstateInvestment.quick_calculation(price=new_apartment_price,
                                                                         down_payment=initial_fund,
                                                                         investment_years=investment_years,
                                                                         interest_rate=average_mortgage_interest_rate,
                                                                         mortgage_num_years=mortgage_period,
                                                                         grace=construction_period,
                                                                         housing_index = st.session_state.CPI,
                                                                         appreciation_rate=st.session_state.RealEstateAppreciations,
                                                                         monthly_rental_income=st.session_state.MaintenanceRentalRatio * monthly_rental,
                                                                         buying_costs=buying_costs,
                                                                         building_period=construction_period,
                                                                        name="Pre-con RE")

    return REinvestment


def mortgage_recycle_tab(investment_years):
    st.session_state.mortgages_df = [get_example_mortgage()]

    mortgage_data = load_mortgage_csv()
    mortgages_name = 'Mortgage'

    mortgage_editor(st.session_state.mortgages_df[0], mortgages_name)

    mortgage = Mortgage.from_dataframe(st.session_state.mortgages_df[0], cpi=st.session_state.CPI,
                                       name=mortgages_name)

    MortgageRecycleInvestment_period = MortgageRecycleInvestment(initial_fund=initial_fund,
                                                                 mortgage=mortgage, investment_years=investment_years,
                                                                 investment_yearly_return=st.session_state.StocksMarketYearlyReturn,
                                                                 gain_tax=st.session_state.TaxGainPercentage,
                                                                 change='period', name="Rec. Period")



    MortgageRecycleInvestment_payment = MortgageRecycleInvestment(initial_fund=initial_fund,
                                                                  mortgage=mortgage,
                                                                  investment_years=investment_years,
                                                                  investment_yearly_return=st.session_state.StocksMarketYearlyReturn,
                                                                  gain_tax=st.session_state.TaxGainPercentage,
                                                                  change='payment', name="Rec. Payment")
    return MortgageRecycleInvestment_period, MortgageRecycleInvestment_payment


def summary_section(investments: List[Investment]):
    summary_data = {
        "Name": [mortgage.name for mortgage in investments],
        "Initial Cost (Fund + Buying Costs)": [np.round(investment.get_initial_investment()) for investment in investments],
        "Inv. Period (Y)": [investment.get_investment_years() for investment in investments],
        "Assets (EOP)": [investment.total_assets() for investment in investments],
        "Liabilities (EOP)": [investment.total_liabilities() for investment in investments],
        "Net Worth (EOP)": [np.round(investment.net_worth()) for investment in investments],
        "Average Monthly Cashflow": [
            np.round((investment.amortization_schedule['Income'] - investment.amortization_schedule['Expenses']).mean())
            for investment in investments],
        "Worst Monthly Cashflow": [np.round(investment.highest_cash_dept()) for investment in investments],
        "Total CashFlow": [np.round(investment.total_income_payments() -investment.total_expenses_payments())  for investment in investments],
        "Total Revenue": [np.round(investment.total_revenue()) for investment in investments],
        "IRR": [np.round(investment.get_irr(), 2) for investment in
                                           investments],
        # "Risk": [round(mortgage.get_volatility()) for investment in investments]
    }
    summary_df_table = pd.DataFrame(summary_data)

    col_summary, col_metrics = st.columns([3, 1], gap='large')
    with col_summary:
        st.dataframe(summary_df_table.set_index('Name').transpose(), use_container_width=True, hide_index=False)
        st.write("EOP: End of Investment Period")

    with col_metrics:
        st.subheader('IRR')
        chart_data = pd.DataFrame(
            {
                "Name": [investment.name for investment in investments],
                "IRR": [investment.get_irr() for investment in investments]
            }
        )

        st.bar_chart(chart_data, x='Name', y='IRR')

        # irr_chart = alt.Chart(chart_data).mark_bar().encode(
        #     x=alt.X('IRR', axis=alt.Axis(title=None)),
        #     y=alt.Y('Name', sort='x', axis=alt.Axis(title=None)),
        #
        # ).properties(
        #     title='IRR'
        # )
        # st.altair_chart(irr_chart, use_container_width=True)


if __name__ == '__main__':
    st.set_page_config(page_title='Mortgage Recycling', layout='wide', page_icon="📈")
    header()
    investment_parameters_bar()

    cols = st.columns([1, 1, 2])
    with cols[0]:
        initial_fund = st.number_input(label='Initial Fund', value=400000, step=100000, min_value=0,
                                       max_value=10000000000)

    with cols[1]:
        investment_years = st.number_input(label='Investment Years', value=25, step=1, min_value=2, max_value=50)

    tabs = st.tabs(["Real Estate", "Mortgage Recycling", "New Real Estate"])
    with tabs[0]:
        REinvestment = real_estate_tab(investment_years)

    with tabs[1]:
        # upload mortgage data
        MortgageRecycleInvestment_period, MortgageRecycleInvestment_payment = mortgage_recycle_tab(investment_years)

    with tabs[2]:
        PreConstREinvestment = preconstruction_real_estate_tab(investment_years)

    st.divider()

    EQInvestment = StocksMarketInvestment(initial_fund=initial_fund,
                                          yearly_return=st.session_state.StocksMarketYearlyReturn,
                                          monthly_extra=0,
                                          investment_years=investment_years)

    # investments = [REinvestment, NewREinvestment, MortgageRecycleInvestment_period, MortgageRecycleInvestment_payment,
    #                EQInvestment]
    investments = [REinvestment, PreConstREinvestment, EQInvestment]

    # main report
    main_compare_investments(investments)

    # Show Amortization Pane
    st.divider()
    col1, _, col2 = st.columns([5, 1, 5])
    with col1:
        st.subheader("Amortization Tables")
    with col2:
        amortization_type = st.radio("Type", options=['Annual', 'Monthly'])

    with st.expander("Investment Amortization", expanded=False):
        tabs = st.tabs([investment.name for investment in investments])

        for i in range(len(investments)):
            with tabs[i]:
                if amortization_type == 'Annual':
                    amortization = np.round(Investment.get_yearly_amortization(investments[i].amortization_schedule).astype(int))
                else:
                    amortization = np.round(
                        investments[i].amortization_schedule).astype(int)
                st.table(amortization.set_index('Month'))

    st.divider()

    footer()
