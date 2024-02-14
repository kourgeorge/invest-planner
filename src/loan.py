import numpy as np
import pandas as pd
import numpy_financial as npf

from constants import CPI


class Loan:
    def __init__(self, amount, num_of_months, interest_rate, loan_type='Shpitzer', grace_period=0, cpi=CPI):
        assert grace_period < num_of_months
        self.loan_type = loan_type
        self.amount = amount
        self._num_of_months = num_of_months
        self.interest_rate = interest_rate
        self.grace_period = grace_period
        self.cpi = cpi

        self.amortization_schedule = self.generate_amortization_schedule()

    def display_loan_info(self):
        print("Loan Type: {}".format(self.loan_type))
        print("Loan Amount: {:,.2f}".format(self.amount))
        print("Number of Months: {}".format(self._num_of_months))
        print("Interest Rate: {}%".format(self.interest_rate))
        print("Grace Period: {} months".format(self.grace_period))

    def generate_amortization_schedule(self):
        r = (self.interest_rate / 12) / 100
        monthly_cpi = 1 + (self.cpi / 12) / 100
        remaining_balance = self.amount
        amortization_schedule = []

        for month in range(1, self.grace_period + 1):
            remaining_balance = remaining_balance * monthly_cpi
            # During grace period, only interest payments, no principal reduction
            interest_payment = remaining_balance * r
            principal_payment = 0
            remaining_balance -= principal_payment

            amortization_schedule.append({
                'Month': month,
                'Monthly Payment': 0,  # Monthly payment is 0 during grace period
                'Principal Payment': principal_payment,
                'Interest Payment': interest_payment,
                'Remaining Balance': remaining_balance
            })

        n = self._num_of_months - self.grace_period

        for month in range(self.grace_period + 1, n + self.grace_period + 1):
            remaining_balance = remaining_balance * monthly_cpi
            monthly_payment = -npf.pmt(r, self._num_of_months - month + 1, remaining_balance)
            interest_payment = remaining_balance * r
            principal_payment = monthly_payment - interest_payment
            remaining_balance -= principal_payment

            amortization_schedule.append({
                'Month': month,
                'Monthly Payment': monthly_payment,
                'Principal Payment': principal_payment,
                'Interest Payment': interest_payment,
                'Remaining Balance': remaining_balance
            })

        return pd.DataFrame(amortization_schedule)

    def loan_amount(self):
        return self.amount

    def num_of_months(self):
        return self._num_of_months

    def average_interest_rate(self):
        return self.interest_rate

    def set_period(self, num_of_months):
        assert num_of_months >= 0
        self._num_of_months = num_of_months
        self.amortization_schedule = self.generate_amortization_schedule()

    def set_amount(self, amount):
        self.amount = amount
        self.amortization_schedule = self.generate_amortization_schedule()

    def monthly_payment(self, month):
        if month < 0 or month > self.num_of_months():
            return 0
        else:
            return self.amortization_schedule.at[month, 'Monthly Payment']

    def average_monthly_payment(self):
        return self.amortization_schedule['Monthly Payment'].mean()

    def highest_monthly_payment(self):
        return np.max(self.amortization_schedule["Monthly Payment"])

    def total_interest_payments(self, months=None):
        if months is not None:
            return self.amortization_schedule.loc[:months, 'Interest Payment'].sum()
        else:
            return self.amortization_schedule['Interest Payment'].sum()

    def total_payments(self, months=None):
        if months is not None:
            return self.amortization_schedule.loc[:months, 'Monthly Payment'].sum()
        else:
            return self.amortization_schedule['Monthly Payment'].sum()

    def remaining_balance(self, months):
        return self.amortization_schedule.loc[months, 'Remaining Balance'] if months < self.num_of_months() else 0

    def cost_per_currency(self):
        if self.loan_amount() > 0:
            return self.total_payments() / self.loan_amount()
        return 0

    def apply_extra_payment(self, extra_payment, change='payment'):
        # consume the maximum extra payment and return the remainder
        if extra_payment < 0:
            raise ValueError("Extra payment should be non-negative.")
        previous_amount = self.loan_amount()
        previous_monthly_payment = self.monthly_payment(0)
        # if the extra payment is larger than the loan, return the remainder of the extra payment
        if extra_payment >= self.loan_amount():
            self.amount = 0
            self.amortization_schedule = self.generate_amortization_schedule()
            return extra_payment - previous_amount
        else:
            new_loan_amount = self.loan_amount() - extra_payment
            self.set_amount(new_loan_amount)
            if change.lower() == 'period':
                new_period = Loan.calculate_loan_period(self.loan_amount(), self.interest_rate,
                                                        monthly_payment=previous_monthly_payment)
                self.set_period(new_period)

            return 0

    @staticmethod
    def calculate_loan_period(amount, interest_rate, monthly_payment):
        """
        loan_period: The number of periods (months) required to repay the loan.
        """

        # Convert annual interest rate to monthly interest rate
        monthly_interest_rate = (interest_rate / 100) / 12

        # Calculate the number of payment periods using the formula
        n = -np.log(1 - (amount * monthly_interest_rate) / monthly_payment) / np.log(1 + monthly_interest_rate)

        # Round up to the nearest whole number since the number of months must be an integer
        n = np.ceil(n)

        return int(n)

    @staticmethod
    def get_yearly_amortization(amortization_schedule):
        yearly_amortization = amortization_schedule.groupby(amortization_schedule.index // 12).agg({
            'Month': 'last',
            'Principal Payment': 'sum',
            'Interest Payment': 'sum',
            'Monthly Payment': 'mean',
            'Remaining Balance': 'last'  # Take the last value for Remaining Balance
        }).astype({'Month': int, 'Principal Payment': int, 'Interest Payment': int, 'Monthly Payment': int,
                   'Remaining Balance': int})

        return yearly_amortization

# if __name__ == '__main__':
#     loan = Loan(loan_type="Mortgage", amount=300000, num_of_months=360, interest_rate=4.5, grace_period=0)
#     print_amortization_schedule(loan.amortization_schedule)
#     plot_interest_principal_graph_yearly(loan.amortization_schedule)
#
#     period = Loan.calculate_loan_period(amount=300000, interest_rate=4.5, monthly_payment=3143)
#     x = 1
