import matplotlib.pyplot as plt
import pandas as pd

from loan import Loan
from mortgage import Mortgage
from investments import RealEstateInvestment, Investment

plt.switch_backend('TkAgg')


def format_with_commas(value):
    return "{:,.0f}".format(value)


def plot_interest_principal_graph(amortization_schedule):
    plt.figure(figsize=(12, 6))

    plt.bar(amortization_schedule.index, amortization_schedule[f'Principal Payment'],
            label=f'Principal Payment')
    plt.bar(amortization_schedule.index, amortization_schedule[f'Interest Payment'],
            bottom=amortization_schedule['Principal Payment'],
            label='Interest Payment')

    plt.title('Total Principal Paid and Total Paid Interest Over Time')
    plt.xlabel('Month')
    plt.ylabel('Payment Amount (Currency)')
    plt.legend()
    plt.show()


def plot_interest_principal_graph_yearly(amortization_schedule):
    # Group amortization data by year and sum the values for each year
    yearly_amortization = Loan.get_yearly_amortization(amortization_schedule)

    plt.figure(figsize=(12, 6))

    # Plot yearly principal payments
    plt.bar(yearly_amortization.index, yearly_amortization['Principal Payment'],
            label='Yearly Principal Payment')

    # Plot yearly interest payments on top of principal payments
    plt.bar(yearly_amortization.index, yearly_amortization['Interest Payment'],
            bottom=yearly_amortization['Principal Payment'],
            label='Yearly Interest Payment')

    plt.title('Total Principal Paid and Total Paid Interest Over Time (Yearly)')
    plt.xlabel('Year')
    plt.ylabel('Payment Amount (Currency)')
    plt.legend()
    plt.show()


def plot_remaining_balance_yearly(amortization_schedule):
    yearly_amortization = Loan.get_yearly_amortization(amortization_schedule)

    plt.figure(figsize=(12, 6))
    plt.plot(yearly_amortization.index + 1, yearly_amortization['Remaining Balance'], label='Remaining Balance')

    # Add vertical grid lines for each year
    for year in yearly_amortization.index + 1:
        plt.axvline(x=year, color='gray', linestyle='--', alpha=0.7)

    plt.ticklabel_format(style='plain', axis='y')

    plt.title('Remaining Balance')
    plt.xlabel('Year')
    plt.ylabel('Monthly Payment Amount (Currency)')
    plt.legend()
    plt.grid(True)
    plt.show()


def plot_monthly_payments_graph_yearly(amortization_schedule):
    yearly_amortization = Loan.get_yearly_amortization(amortization_schedule)

    plt.figure(figsize=(12, 6))
    plt.bar(yearly_amortization.index+1, yearly_amortization['Monthly Payment'], label='Monthly Payment')

    plt.title('Monthly Payment')
    plt.xlabel('Year')
    plt.ylabel('Monthly Payment Amount (Currency)')
    plt.legend()
    plt.grid(True)
    plt.show()


def plot_investment_revenue_graph_yearly(amortization_schedule):
    yearly_amortization = RealEstateInvestment.get_yearly_amortization(amortization_schedule)

    plt.figure(figsize=(12, 6))
    plt.plot(yearly_amortization.index + 1, yearly_amortization['Total Revenue'], label='Total Revenue')

    # Add vertical grid lines for each year
    for year in yearly_amortization.index + 1:
        plt.axvline(x=year, color='gray', linestyle='--', alpha=0.7)

    plt.title('Total Revenue')
    plt.xlabel('Year')
    plt.ylabel('Total Revenue Amount (Currency)')
    plt.legend()
    plt.grid(True)
    plt.show()


def plot_compare_investment_revenue_graph_yearly(investments, field='Net Revenue'):
    plt.figure(figsize=(12, 6))

    for i, investment in enumerate(investments):
        amortization_schedule = investment.generate_amortization_schedule(30)
        yearly_amortization = Investment.get_yearly_amortization(amortization_schedule)
        plt.plot(yearly_amortization.index + 1, yearly_amortization[field],
                 label=f'{investment.name}')

        # Add vertical grid lines for each year
        for year in yearly_amortization.index + 1:
            plt.axvline(x=year, color='gray', linestyle='--', alpha=0.7)

    plt.title(f'{field} Across Investments')
    plt.xlabel('Year')
    plt.ylabel(f'{field} Amount (Currency)')
    plt.legend()
    plt.grid(True)
    plt.show()


def plot_investments_interest_principal_graph_yearly(amortization_schedule):
    initial_fund = amortization_schedule['Total Assets'][0]
    yearly_amortization = Investment.get_yearly_amortization(amortization_schedule)

    plt.figure(figsize=(12, 6))

    plt.bar(yearly_amortization.index+1, initial_fund, label='Initial Fund')

    # Plot yearly principal payments
    plt.bar(yearly_amortization.index+1, yearly_amortization['Monthly Extra'],
            bottom=initial_fund,
            label='Monthly Extra')

    plt.bar(yearly_amortization.index+1, yearly_amortization['Monthly Income'],
            bottom=initial_fund+yearly_amortization['Monthly Extra'],
            label='Interest')

    # Plot yearly interest payments on top of principal payments
    plt.bar(yearly_amortization.index, - yearly_amortization['Total Expenses'],
            bottom=0,
            label='Total Expenses')

    plt.title('Investment Over Time (Yearly)')
    plt.xlabel('Year')
    plt.ylabel('Payment Amount (Currency)')
    plt.legend()
    plt.show()


def print_amortization_schedule_yearly(amortization_schedule):
    # Format the DataFrame with commas for thousands separators

    if 'Total Revenue' in amortization_schedule.columns:
        yearly_amortization = Investment.get_yearly_amortization(amortization_schedule)
    else:
        yearly_amortization = Loan.get_yearly_amortization(amortization_schedule)

    formatted_amortization = yearly_amortization.apply(
        lambda x: x.apply(format_with_commas))

    pd.set_option('display.max_columns', None)  # Display all columns
    pd.set_option('display.expand_frame_repr', False)  # Do not wrap DataFrame across pages

    # Print the DataFrame
    print(formatted_amortization.to_string(index=False))


def print_amortization_schedule(amortization_schedule):
    # Round numbers to 2 decimal points
    amortization_schedule = amortization_schedule.round(2)
    pd.set_option('display.max_columns', None)  # Display all columns
    pd.set_option('display.expand_frame_repr', False)  # Do not wrap DataFrame across pages

    # Print the DataFrame
    print(amortization_schedule.to_string(index=False))
