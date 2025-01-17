import numpy as np
import pandas as pd
import numpy_financial as npf
from constants import CPI
from finance_utils import CPIVAR,PrimeInterestVAR
from enum import Enum


class LoanType(Enum):
    FIXED = 'Kvoa'
    VARIABLE = 'Mishtana'
    PRIME = 'Prime'


class Loan:
    def __init__(self, amount, num_of_months, interest_rate, loan_type=LoanType, grace_period=0, cpi=CPI):
        # assert grace_period < num_of_months
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
        remaining_balance = self.loan_amount()
        amortization_schedule = []

        if self._num_of_months == 0:
            amortization_schedule = {
                'Month': 1,
                'Monthly Payment': 0,  # Monthly payment is 0 during grace period
                'Principal Payment': 0,
                'Interest Payment': 0,
                'Inflation Payment':0,
                'Remaining Balance': 0
            }
            return pd.DataFrame([amortization_schedule])

        for month in range(1, self.grace_period + 1):
            remaining_balance = remaining_balance #* monthly_cpi
            inflation_part = 0 #remaining_balance * (1 - 1 / monthly_cpi)
            interest_payment = 0 # remaining_balance * r
            remaining_balance = remaining_balance + interest_payment

            amortization_schedule.append({
                'Month': month,
                'Monthly Payment': 0,  # Monthly payment is 0 during grace period
                'Principal Payment': 0,
                'Inflation Payment': inflation_part,
                'Interest Payment': interest_payment,
                'Remaining Balance': remaining_balance
            })

        n = self._num_of_months - self.grace_period

        for month in range(self.grace_period + 1, n + self.grace_period + 1):
            remaining_balance = remaining_balance * monthly_cpi
            monthly_payment = -npf.pmt(r, self.num_of_months() - month + 1, remaining_balance)
            inflation_part = remaining_balance * (1 - 1 / monthly_cpi)
            interest_payment = remaining_balance * r
            principal_payment = monthly_payment - interest_payment
            remaining_balance -= principal_payment

            amortization_schedule.append({
                'Month': month,
                'Monthly Payment': monthly_payment,
                'Principal Payment': principal_payment,
                'Inflation Payment': inflation_part,
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

    def get_volatility(self):
        vii = 0 if self.loan_type == LoanType.FIXED.name else PrimeInterestVAR.value_at_risk(self.num_of_months())
        vicpi = 0 if self.cpi == 0 else CPIVAR.value_at_risk(self.num_of_months())
        return (vii+vicpi)*100

    def set_period(self, num_of_months):
        assert num_of_months >= 0
        self._num_of_months = num_of_months
        self.amortization_schedule = self.generate_amortization_schedule()

    def set_amount(self, amount):
        self.amount = amount
        if amount == 0:
            self.set_period(0)
        self.amortization_schedule = self.generate_amortization_schedule()

    def get_irr(self):
        return npf.irr([-self.loan_amount()]+self.amortization_schedule['Monthly Payment'].tolist())*12*100

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
            self.set_amount(0)
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

    def change_first_payment(self, monthly_payment_amount):
        new_period = Loan.calculate_loan_period(self.loan_amount(), self.interest_rate,
                                                self.monthly_payment(0) + monthly_payment_amount)
        self.set_period(new_period)
        self.amortization_schedule = self.generate_amortization_schedule()

    def is_empty(self):
        return True if len(self.loans) < 1 else False

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
    def min_monthly_increase(loan):
        "Return the monthly amount payment increase that will change the period."
        r = (loan.interest_rate / 12) / 100
        monthly_payment = -npf.pmt(r, loan.num_of_months()-1, loan.loan_amount())
        return monthly_payment

    @staticmethod
    def get_yearly_amortization(amortization_schedule):
        yearly_amortization = amortization_schedule.groupby(amortization_schedule.index // 12).agg({
            'Month': 'last',
            'Monthly Payment': 'sum',
            'Principal Payment': 'sum',
            'Inflation Payment': 'sum',
            'Interest Payment': 'sum',
            'Remaining Balance': 'last'  # Take the last value for Remaining Balance
        }).astype({'Month': int, 'Principal Payment': int, 'Inflation Payment':int, 'Interest Payment': int, 'Monthly Payment': int,
                   'Remaining Balance': int})
        return yearly_amortization