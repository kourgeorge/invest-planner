import copy
import numpy as np
import pandas as pd
import tabulate
from loan import Loan
from constants import *


class Mortgage:
    def __init__(self, loans):
        self.loans = loans
        self.amortization_schedule = self.generate_amortization_schedule()

    def get_mortgage_info(self):
        loan_details = []

        for i, loan in enumerate(self.loans, start=1):
            # Calculate additional information
            total_loan_amount = loan.total_payments()
            interest_per_dollar = loan.total_payments() / loan.loan_amount()

            # Append details to the list
            loan_details.append([
                loan.loan_type,
                loan.loan_amount(),
                loan.num_of_months(),
                loan.interest_rate,
                loan.cpi,
                loan.grace_period,
                loan.average_monthly_payment(),
                loan.total_interest_payments(),
                total_loan_amount,
                interest_per_dollar
            ])

        loan_details.append([
            'Total Mortgage', self.loan_amount(),
            self.num_of_months(),
            self.average_interest_rate(), '', '', self.average_monthly_payment(),
            self.total_interest_payments(), self.total_payments(),
            self.total_payments() / self.loan_amount()
        ])

        headers = ["Loan Type", "Loan Amount", "Number of Months", "Interest Rate", "CPI",
                   "Grace Period", "Avg. Monthly Payment", "Total Interest", "Total Cost", "Cost to Currency"]

        df = pd.DataFrame(loan_details, columns=headers)

        return df

    def display_mortgage_info(self):
        # Initialize a list to store the loan details
        loan_details = []

        for i, loan in enumerate(self.loans, start=1):
            # Calculate additional information
            total_loan_amount = loan.total_payments()
            interest_per_dollar = loan.total_payments() / loan.loan_amount()

            # Append details to the list
            loan_details.append([
                f'({i})',
                loan.loan_type,
                "{:,.0f}".format(loan.amount),
                f'{loan._num_of_months} ({np.round(loan._num_of_months / 12, 1)} y)',
                "{}%".format(loan.interest_rate),
                "{}%".format(loan.cpi),
                loan.grace_period,
                "{:,.0f}".format(loan.average_monthly_payment()),
                "{:,.0f}".format(loan.total_interest_payments()),
                "{:,.0f}".format(total_loan_amount),
                "{:,.2f}".format(interest_per_dollar)
            ])

        loan_details.append([
            'Total', 'Mortgage', "{:,.0f}".format(self.loan_amount()),
            f'{self.num_of_months()} ({np.round(self.num_of_months() / 12, 1)} y)',
            "{:,.2f}%".format(self.average_interest_rate()), '', '', "{:,.0f}".format(self.average_monthly_payment()),
            "{:,.0f}".format(self.total_interest_payments()), "{:,.0f}".format(self.total_payments()),
            "{:,.2f}".format(self.total_payments() / self.loan_amount())
        ])

        # Define column headers
        headers = ["Loan #", "Loan Type", "Loan Amount", "Number of Months", "Interest Rate", "CPI",
                   "Grace Period", "Avg. Monthly Payment", "Total Interest", "Total Cost", "Cost to Currency"]

        df = pd.DataFrame(loan_details, columns=headers)

        # Print the tabulated information
        print("\nMortgage Details:")
        print(tabulate.tabulate(loan_details, headers=headers, tablefmt="pretty"))

        return df

    def generate_amortization_schedule(self):
        # Determine the maximum number of months across all loans
        max_months = max(loan._num_of_months for loan in self.loans)

        amortization_schedule = []

        # Iterate for each month
        for month in range(1, max_months + 1):
            # Initialize totals for the month
            total_principal_payment = 0
            total_interest_payment = 0
            total_monthly_payment = 0
            total_remaining_balance = 0

            # Iterate through each loan
            for i, loan in enumerate(self.loans, start=1):
                if month <= loan._num_of_months:
                    total_principal_payment += loan.amortization_schedule.at[month - 1, 'Principal Payment']
                    total_interest_payment += loan.amortization_schedule.at[month - 1, 'Interest Payment']
                    total_monthly_payment += loan.amortization_schedule.at[month - 1, 'Monthly Payment']
                    total_remaining_balance += loan.amortization_schedule.at[month - 1, 'Remaining Balance']

            # Append totals to the dictionary
            amortization_schedule.append({
                'Month': month,
                'Monthly Payment': total_monthly_payment,
                'Principal Payment': total_principal_payment,
                'Interest Payment': total_interest_payment,
                'Remaining Balance': total_remaining_balance
            })

        mortgage_amortization = pd.DataFrame(amortization_schedule)

        return mortgage_amortization

    def num_of_months(self):
        return max(loan.num_of_months() for loan in self.loans if loan.loan_amount() > 0)

    def loan_amount(self):
        return sum(loan.amount for loan in self.loans)

    def monthly_payment(self, month):
        if month > 0 and month < self.num_of_months():
            return self.amortization_schedule.loc[month, 'Monthly Payment'].sum()
        else:
            return 0

    def average_monthly_payment(self):
        return np.sum([loan.average_monthly_payment() for loan in self.loans if loan.loan_amount() > 0])

    def average_interest_rate(self):
        weighted_interest_rates = [loan.amount * loan.interest_rate for loan in self.loans]
        weighted_average_interest_rate = sum(weighted_interest_rates)/ self.loan_amount()
        return weighted_average_interest_rate

    def total_interest_payments(self, month=None):
        if month is not None:
            return self.amortization_schedule.loc[:month, 'Interest Payment'].sum()
        else:
            return self.amortization_schedule['Interest Payment'].sum()

    def interest_payment(self, month):
        return 0 if month >= self.num_of_months() else self.amortization_schedule.loc[month, 'Interest Payment']

    def total_principal_payments(self, months=None):
        if months is not None and months < self.num_of_months():
            return self.amortization_schedule.loc[:months, 'Principal Payment'].sum()
        else:
            return self.amortization_schedule['Principal Payment'].sum()

    def total_payments(self, months=None):
        if months is not None:
            return self.amortization_schedule.loc[:months, 'Monthly Payment'].sum()
        else:
            return self.amortization_schedule['Monthly Payment'].sum()

    def remaining_balance(self, months):
        return self.amortization_schedule.loc[months, 'Remaining Balance'] if months < self.num_of_months() else 0

    def add_loan(self, loan):
        self.loans.append(loan)
        self.amortization_schedule = self.generate_amortization_schedule()

    @staticmethod
    def read_csv(csv_path):
        df = pd.read_csv(csv_path)
        loans = []
        for i, row in df.iterrows():  # Use df.iterrows() to iterate through rows
            cpi = 0.9 if row['cpi']=='Yes' else 0
            loan = Loan(row['amount'], row['num_of_months'], row['interest_rate'], row['loan_type'],
                        row['grace_period'], cpi)
            loans.append(loan)

        return Mortgage(loans)


    def write_csv(self, csv_path):
        # Create a list of dictionaries to store loan information
        loan_data = []
        for loan in self.loans:
            loan_data.append({
                'amount': loan.loan_amount(),
                'num_of_months': loan.num_of_months(),
                'interest_rate': loan.average_interest_rate(),
                'loan_type': loan.loan_type,
                'grace_period': loan.grace_period,
                'cpi': loan.cpi
            })

        # Create a DataFrame from the list of loan dictionaries
        df = pd.DataFrame(loan_data)

        # Write the DataFrame to a CSV file
        df.to_csv(csv_path, index=False)

    @staticmethod
    def recycle_mortgage(mortgage, extra_payment, change='payment'):

        recycled_mortgage = copy.deepcopy(mortgage)
        previous_monthly_payment = recycled_mortgage.average_monthly_payment()
        # Calculate cost per dollar for each loan

        remainder = extra_payment
        # Apply the extra payment to the principal of the most expensive loan
        while remainder > 0:
            cost_per_currency = [loan.cost_per_currency() for loan in recycled_mortgage.loans]
            loan_index = cost_per_currency.index(max(cost_per_currency))
            remainder = recycled_mortgage.loans[loan_index].apply_extra_payment(remainder, change)
            if change.lower() == 'period':
                if recycled_mortgage.average_monthly_payment() < previous_monthly_payment:
                    cost_per_currency = [loan.cost_per_currency() for loan in recycled_mortgage.loans]
                    loan_index = cost_per_currency.index(max(cost_per_currency))
                    remainder_monthly_payment = previous_monthly_payment - recycled_mortgage.average_monthly_payment()

                    target_loan = recycled_mortgage.loans[loan_index]
                    new_period = Loan.calculate_loan_period(amount=target_loan.loan_amount(),
                                                            interest_rate=target_loan.interest_rate,
                                                            monthly_payment=target_loan.average_monthly_payment() +
                                                                            remainder_monthly_payment)
                    target_loan.set_period(new_period)

        # Create a new Mortgage instance with the updated loans and amortization schedule
        recycled_mortgage.loans = [loan for loan in recycled_mortgage.loans if loan.loan_amount() > 0]
        recycled_mortgage.amortization_schedule = recycled_mortgage.generate_amortization_schedule()

        return recycled_mortgage

    @staticmethod
    def amortization_diff(mortgage_before, mortgage_after):

        max_months = max(mortgage_before.num_of_months(), mortgage_after.num_of_months())

        amortization_schedule = []

        # Iterate for each month
        for month in range(1, max_months + 1):
            # Initialize totals for the month
            total_principal_payment = 0
            total_interest_payment = 0
            total_monthly_payment = 0
            total_remaining_balance = 0

            # Iterate through each loan
            if month <= max_months:
                total_principal_payment += mortgage_before.total_principal_payments(month - 1) - \
                                           mortgage_after.total_principal_payments(month - 1)
                total_interest_payment += mortgage_before.interest_payment(month - 1) - \
                                          mortgage_after.interest_payment(month - 1)
                total_monthly_payment += mortgage_before.monthly_payment(month - 1) - \
                                         mortgage_after.monthly_payment(month - 1)
                total_remaining_balance += mortgage_before.remaining_balance(month - 1) - \
                                           mortgage_after.remaining_balance(month - 1)

            amortization_schedule.append({
                'Month': month,
                'Monthly Payment': total_monthly_payment,
                'Principal Payment': total_principal_payment,
                'Interest Payment': total_interest_payment,
                # 'Remaining Balance': total_remaining_balance
            })

        combined_amortization = pd.DataFrame(amortization_schedule)

        return combined_amortization


if __name__ == '__main__':
    loan1 = Loan(loan_type="Kalatz", amount=600000, num_of_months=22 * 12, interest_rate=5.2, grace_period=20)
    loan2 = Loan(loan_type="Kalatz", amount=300000, num_of_months=22 * 12, interest_rate=6, grace_period=0)

    mortgage = Mortgage([loan1, loan2])
    mortgage.display_mortgage_info()
    # plot_interest_principal_graph_yearly(mortgage.amortization_schedule)

    mortgage.recycle_mortgage(350000, 'period')

    mortgage.display_mortgage_info()

    x = 1
