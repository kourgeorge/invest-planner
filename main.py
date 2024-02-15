import copy

import pandas as pd

import constants
from constants import *
from graphs import *
from investments import StocksMarketInvestment, MortgageRecycleInvestment


def Ritta():
    loan1 = Loan(loan_type="Kalatz", amount=550000, num_of_months=264, interest_rate=4.95, grace_period=0)
    loan2 = Loan(loan_type="Prime", amount=390000, num_of_months=300, interest_rate=5.6, grace_period=0, cpi=0)
    loan3 = Loan(loan_type="Mishtana", amount=150000, num_of_months=240, interest_rate=3.1, grace_period=0)

    mortgage = Mortgage([loan1, loan2, loan3])
    mortgage.display_mortgage_info()

    mortgage.to_dataframe().to_csv('./customers/ritta.csv', index=False)

    print("\nTotal Interest Payments: ${:,.2f}".format(mortgage.total_interest_payments()))
    print("Total Mortgage Payments: ${:,.2f}".format(mortgage.total_payments()))
    print("Remaining Mortgage Balance: ${:,.2f}".format(mortgage.remaining_balance(200)))

    print_amortization_schedule_yearly(mortgage.amortization_schedule)

    plot_monthly_payments_graph_yearly(mortgage.amortization_schedule)
    plot_remaining_balance_yearly(mortgage.amortization_schedule)
    plot_interest_principal_graph_yearly(mortgage.amortization_schedule)


def get_nariman_mortgage():
    loan1 = Loan(loan_type="KvoaTsmoda", amount=237436, num_of_months=161, interest_rate=2.36, grace_period=0)
    loan2 = Loan(loan_type="Prime", amount=202966, num_of_months=185, interest_rate=5.05, grace_period=0, cpi=0)
    loan3 = Loan(loan_type="Tsmoda", amount=201178, num_of_months=185, interest_rate=2.49, grace_period=0)

    mortgage = Mortgage([loan1, loan2, loan3])
    return mortgage


def NarimanRecycle():
    mortgage = get_nariman_mortgage()
    mortgage.display_mortgage_info()

    # plot_interest_principal_graph_yearly(mortgage.amortization_schedule)
    # mortgage = Mortgage.recycle_mortgage(mortgage, 50000, change='period')
    #
    # mortgage.display_mortgage_info()
    #
    EQinvestment = StocksMarketInvestment(initial_fund=50000)
    MortgageRecycleinvestmentPayement = MortgageRecycleInvestment(initial_fund=50000, mortgage=mortgage,
                                                                  change='monthly payment', name='Reduce Payment')
    MortgageRecycleinvestmentPeriod = MortgageRecycleInvestment(initial_fund=50000, mortgage=mortgage,
                                                                change='period', name='Reduce Period')

    print("Lower Payement")
    MortgageRecycleinvestmentPayement.recycled_mortgage.display_mortgage_info()
    print("Shorter Period")
    MortgageRecycleinvestmentPeriod.recycled_mortgage.display_mortgage_info()

    plot_compare_investment_revenue_graph_yearly([MortgageRecycleinvestmentPayement, MortgageRecycleinvestmentPeriod],
                                                 field="Total Revenue")

    # plot_interest_principal_graph_yearly(mortgage.amortization_schedule)
    #
    #
    # plot_monthly_payments_graph_yearly(mortgage.amortization_schedule)
    # plot_remaining_balance_yearly(mortgage.amortization_schedule)
    # plot_interest_principal_graph_yearly(mortgage.amortization_schedule)

    return


def get_george_mortgage() -> Mortgage:
    loansBY = []
    loansTS = []
    loansAL = []

    loansBY.append(Loan(loan_type="PrimeBY", amount=32302 + 37911, num_of_months=62, interest_rate=P - 0.85, cpi=0))
    loansBY.append(Loan(loan_type="KalatzBY", amount=17360, num_of_months=17, interest_rate=2.24))
    loansBY.append(Loan(loan_type="TsamodKvoaBY", amount=55338, num_of_months=17, interest_rate=0.65))

    loansTS.append(Loan(loan_type="KalatzTS", amount=11883 + 27452, num_of_months=43, interest_rate=2.32))
    loansTS.append(Loan(loan_type="PrimeTS", amount=13388 + 19864, num_of_months=43, interest_rate=P - 0.7, cpi=0))
    loansTS.append(Loan(loan_type="TsamodKvoaTS", amount=13233 + 30564, num_of_months=43, interest_rate=2))

    loansAL.append(Loan(loan_type="KalatzAL", amount=59222, num_of_months=190, interest_rate=3))
    loansAL.append(Loan(loan_type="PrimeAL1", amount=57753, num_of_months=190, interest_rate=P - 0.6, cpi=0))
    loansAL.append(Loan(loan_type="TsamodMishtanaAL", amount=64060, num_of_months=190, interest_rate=2.55))
    loansAL.append(Loan(loan_type="TsamodKvoaAL", amount=188321, num_of_months=165, interest_rate=1.7))
    loansAL.append(Loan(loan_type="PrimeAL2", amount=28034 + 59468, num_of_months=190, interest_rate=P - 0.55, cpi=0))

    mortgage = Mortgage(loansBY + loansTS + loansAL)
    mortgage.display_mortgage_info()

    return mortgage


def get_george_new_apartment_mortgage():
    mortgage = get_george_mortgage()
    mortgage.display_mortgage_info()
    old_mortgage = copy.deepcopy(mortgage)

    new_loan = Loan(loan_type="newPrime", amount=475000, num_of_months=15 * 12, interest_rate=5.4)
    mortgage.add_loan(new_loan)
    mortgage.display_mortgage_info()
    print_amortization_schedule_yearly(mortgage.amortization_schedule)

    plot_monthly_payments_graph_yearly(mortgage.amortization_schedule)
    plot_remaining_balance_yearly(mortgage.amortization_schedule)
    plot_interest_principal_graph_yearly(mortgage.amortization_schedule)

    x = 1


def alfred_alternatives_450k():
    new_apartment_price = 950000
    REinvestment = RealEstateInvestment.quick_calculation(price=new_apartment_price, down_payment=450000,
                                                          interest_rate=5.3,
                                                          mortgage_num_years=20,
                                                          appreciation_rate=RealEstateYearlyAppreciation,
                                                          monthly_rental_income=RentalMonthlyRatio * 3500,
                                                          buying_costs=TaxBuyingPercentage/100 * new_apartment_price)

    REinvestment.mortgage.display_mortgage_info()
    EQinvestment = StocksMarketInvestment(initial_fund=450000, yearly_return=StocksMarketYearlyReturn, monthly_extra=0)

    plot_compare_investment_revenue_graph_yearly(
        [REinvestment, EQinvestment],
        field="Total Revenue")


def george_alternatives_350k():
    new_apartment_price = 950000
    REinvestment = RealEstateInvestment.quick_calculation(price=new_apartment_price, down_payment=350000,
                                                          interest_rate=5.3,
                                                          mortgage_num_years=15,
                                                          appreciation_rate=RealEstateYearlyAppreciation,
                                                          monthly_rental_income=RentalMonthlyRatio * 3500,
                                                          buying_costs=TaxBuyingPercentage/100 * new_apartment_price)

    mortgage_george = Mortgage.from_dataframe(pd.read_csv('/Users/georgekour/repositories/investplanner/customers/george.csv'))
    MortgageRecycleinvestment1 = MortgageRecycleInvestment(initial_fund=350000,
                                                           mortgage=mortgage_george,
                                                           investment_yearly_return=StocksMarketYearlyReturn,
                                                           change='monthly payment',
                                                           name="Mortgage Recycle Montly change")

    MortgageRecycleinvestment2 = MortgageRecycleInvestment(initial_fund=350000,
                                                           mortgage=mortgage_george,
                                                           investment_yearly_return=StocksMarketYearlyReturn,
                                                           change='period', name="Mortgage Recycle Period change")

    EQinvestment = StocksMarketInvestment(initial_fund=350000, yearly_return=StocksMarketYearlyReturn, monthly_extra=0)

    plot_compare_investment_revenue_graph_yearly(
        [REinvestment, EQinvestment, MortgageRecycleinvestment1, MortgageRecycleinvestment2],
        field="Total Revenue")


if __name__ == '__main__':
    # mortgage = Ritta()
    # mortgage.write_csv('./customers/nariman.csv')
    #
    loaded_mortgage = Mortgage.from_dataframe(pd.read_csv('./customers/nariman.csv'))

    old = loaded_mortgage.highest_monthly_payment()
    new_mortgage = loaded_mortgage.recycle_mortgage(mortgage=loaded_mortgage, extra_payment=350000, change='period')
    new = new_mortgage.highest_monthly_payment()
    print(f'{old} {new}')

    # amortization_schedule_period = MortgageRecycleInvestment(initial_fund=350000,
    #                           mortgage=loaded_mortgage,
    #                           investment_yearly_return=constants.StocksMarketYearlyReturn,
    #                           change='period',
    #                           name="Mortgage Recycle Period change").generate_amortization_schedule(
    #     loaded_mortgage.num_of_months() // 12 + 10)







    # george_alternatives_350k()
    # alfred_alternatives_450k()
    # NarimanRecycle()

    # plot_monthly_payments_graph_yearly(mortgage.amortization_schedule)
    # plot_remaining_balance_yearly(mortgage.amortization_schedule)
    # plot_interest_principal_graph_yearly(mortgage.amortization_schedule)
    # plot_interest_principal_graph_yearly(rec_mortgage.amortization_schedule)

    x = 1
