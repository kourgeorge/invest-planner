import pandas as pd
from constants import *
from loan import Loan
from mortgage import Mortgage


class Investment:
    @staticmethod
    def get_yearly_amortization(amortization_schedule):
        yearly_amortization = amortization_schedule.groupby(amortization_schedule.index // 12).agg({
            'Month': 'last',
            'Total Assets': 'last',
            'Monthly Extra': 'sum',
            'Monthly Income': 'sum',
            'Total Expenses': 'last',
            'Total Revenue': 'last',
            'Net Revenue': 'last',
        }).astype({'Month': int, 'Total Assets': int, 'Total Expenses': int, 'Total Revenue': int,
                   'Net Revenue': int, 'Monthly Income': int})

        return yearly_amortization

    def generate_amortization_schedule(self, investment_num_years):
        pass


class StocksMarketInvestment(Investment):
    def __init__(self, initial_fund, yearly_return=StocksMarketYearlyReturn, yearly_fee_percent=StocksMarketFeesPercentage,
                 gain_tax=TaxGainPercentage, monthly_extra=0,
                 name='Stock Market'):
        self.name = name
        self.initial_fund = initial_fund
        self.yearly_return = yearly_return
        self.gain_tax = gain_tax
        self.yearly_fee_percent = yearly_fee_percent
        self.monthly_extra = monthly_extra

    def generate_amortization_schedule(self, investment_num_years):
        amortization_schedule = []
        current_asset_price = self.initial_fund
        monthly_return = (1 + self.yearly_return / 100) ** (1 / 12) - 1

        monthly_fee_percent = (1 + self.yearly_fee_percent / 100) ** (1 / 12) - 1
        investment_num_months = int(investment_num_years * 12)

        total_expenses = 0
        for month in range(1, investment_num_months + 1):
            previous_asset_price = current_asset_price
            current_asset_price = previous_asset_price * (1 + monthly_return) + self.monthly_extra
            interest = previous_asset_price * monthly_return
            monthly_expenses = monthly_fee_percent * current_asset_price
            total_expenses += monthly_expenses
            current_asset_price -= monthly_expenses
            total_revenue = current_asset_price - self.initial_fund - month * self.monthly_extra
            net_revenue = total_revenue if total_revenue <= 0 else (1 - (self.gain_tax / 100)) * total_revenue
            amortization_schedule.append({
                'Month': month,
                'Monthly Extra': self.monthly_extra,
                'Monthly Income': interest,
                'Total Assets': current_asset_price,
                'Total Expenses': total_expenses,
                'Total Revenue': total_revenue,
                'Net Revenue': net_revenue
            })

        return pd.DataFrame(amortization_schedule)


class RealEstateInvestment(Investment):
    def __init__(self, price, initial_fund, mortgage: Mortgage, appreciation_rate,
                 monthly_rental_income=0, buying_costs=0, selling_tax=TaxGainPercentage, name='New Real Estate'):
        self.name = name
        self.price = price
        self.initial_fund = initial_fund
        self.appreciation_rate = appreciation_rate
        self.mortgage: Mortgage = mortgage
        self.monthly_rental_income = monthly_rental_income
        self.buying_costs = buying_costs
        self.selling_tax = selling_tax

    def generate_amortization_schedule(self, investment_num_years):

        amortization_schedule = []
        total_rent_income = 0
        current_asset_price = self.price
        monthly_appreciation_rate = (1 + self.appreciation_rate / 100) ** (1 / 12) - 1
        investment_num_months = int(investment_num_years * 12)

        for month in range(1, investment_num_months + 1):
            previous_asset_value = current_asset_price
            current_asset_price = current_asset_price * (1 + monthly_appreciation_rate)
            monthly_rental_income = self.monthly_rental_income
            total_rent_income += monthly_rental_income
            total_expenses = self.buying_costs + self.mortgage.total_payments(month) + \
                             self.mortgage.remaining_balance(month)
            total_income = current_asset_price + total_rent_income
            total_revenue = total_income - total_expenses - self.initial_fund
            net_revenue = total_revenue if total_revenue <= 0 else (1 - (self.selling_tax / 100)) * total_revenue

            monthly_interest = self.mortgage.amortization_schedule.loc[
                month, "Interest Payment"] if month < self.mortgage.num_of_months() else 0
            amortization_schedule.append({
                'Month': month,
                'Monthly Extra': self.mortgage.total_payments(0) - self.monthly_rental_income,
                'Monthly Income': monthly_rental_income + (
                        current_asset_price - previous_asset_value) - monthly_interest,
                'Total Assets': total_income,
                'Total Expenses': total_expenses,
                'Total Revenue': total_revenue,
                'Net Revenue': net_revenue
            })

        return pd.DataFrame(amortization_schedule)

    def get_investment_info(self, investment_num_years):
        investment_num_month = int(investment_num_years * 12)

        # Calculate current property value after appreciation
        current_property_value = self.price * (1 + self.appreciation_rate / 100) ** investment_num_years

        total_rental_income = self.monthly_rental_income * investment_num_month

        remaining_balance = self.mortgage.remaining_balance(investment_num_month)
        total_payments = self.mortgage.total_payments(investment_num_month)

        # Calculate total revenue (rental income + property appreciation - mortgage payments after mortgage period)
        total_revenue = current_property_value - self.initial_fund + total_rental_income - total_payments - remaining_balance - self.buying_costs

        # Store information in a dictionary
        return {
            "property_price": self.price,
            "buying_costs": self.buying_costs,
            "down_payment": self.initial_fund,
            "mortgage_amount": self.mortgage.loan_amount(),
            "mortgage_years": self.mortgage.num_of_months() // 12,
            "monthly_mortgage_payment": self.mortgage.total_payments() / self.mortgage.num_of_months(),
            "total_interest_payments": self.mortgage.total_interest_payments(investment_num_month),
            "total_mortgage_payments": self.mortgage.total_payments(investment_num_month),
            "remaining_mortgage_balance": remaining_balance,
            "current_property_value": current_property_value,
            "monthly_rental_income": self.monthly_rental_income,
            "total_rental_income": total_rental_income,
            "investment_years": investment_num_years,
            "total_revenue": total_revenue,
            "net_revenue": total_revenue if total_revenue <= 0 else (1 - (self.selling_tax / 100)) * total_revenue
        }

    def print_real_estate_information(self, investment_num_years):
        # Print detailed summary
        print("Detailed Summary:")
        for key, value in self.get_investment_info(investment_num_years).items():
            print("{}: {:,.0f}".format(key.replace("_", " ").title(), value))

    @staticmethod
    def get_yearly_amortization(amortization_schedule):
        yearly_amortization = amortization_schedule.groupby(amortization_schedule.index // 12).agg({
            'Month': 'last',
            'Total Assets': 'last',
            'Total Expenses': 'last',
            'Total Revenue': 'last',
            'Net Revenue': 'last',
        }).astype({'Month': int, 'Total Assets': int, 'Total Expenses': int, 'Total Revenue': int,
                   'Net Revenue': int})

        return yearly_amortization

    @staticmethod
    def quick_calculation(price, down_payment, interest_rate, appreciation_rate,
                          mortgage_num_years, monthly_rental_income,
                          buying_costs=0):
        loan = Loan(amount=price - down_payment, interest_rate=interest_rate,
                    num_of_months=mortgage_num_years * 12)
        investment = RealEstateInvestment(price=price, initial_fund=down_payment, mortgage=Mortgage([loan]),
                                          appreciation_rate=appreciation_rate,
                                          monthly_rental_income=monthly_rental_income, buying_costs=buying_costs)

        return investment


class MortgageRecycleInvestment(Investment):
    def __init__(self, initial_fund, mortgage: Mortgage, investment_yearly_return=StocksMarketYearlyReturn,
                 stocks_yearly_fee_percent=StocksMarketFeesPercentage, name='Mortgage Recycle',
                 gain_tax=TaxGainPercentage, change='payment'):
        self.name = name
        self.initial_fund = initial_fund
        self.old_mortgage = mortgage
        self.change = change
        self.recycled_mortgage = Mortgage.recycle_mortgage(self.old_mortgage, extra_payment=self.initial_fund,
                                                           change=change)

        self.investment_yearly_return = investment_yearly_return
        self.yearly_fee_percent = stocks_yearly_fee_percent
        self.gain_tax = gain_tax

    def get_recycled_mortgage(self):
        return self.recycled_mortgage

    def generate_amortization_schedule(self, investment_num_years):
        diff_amortization_schedule = Mortgage.amortization_diff(self.old_mortgage, self.recycled_mortgage)

        current_asset_price = 0
        amortization_schedule = []
        monthly_return = (1 + self.investment_yearly_return / 100) ** (1 / 12) - 1
        monthly_fee_percent = (1 + self.yearly_fee_percent / 100) ** (1 / 12) - 1
        investment_num_months = int(investment_num_years * 12)

        diff_mortgage_length = len(diff_amortization_schedule)
        total_expenses = 0
        total_savings = 0
        for month in range(1, investment_num_months + 1):
            previous_asset_price = current_asset_price
            monthly_saving = 0 if month > diff_mortgage_length else diff_amortization_schedule.at[
                month - 1, 'Interest Payment']
            current_asset_price = previous_asset_price * (1 + monthly_return) + monthly_saving
            total_savings += monthly_saving
            investment_interest = previous_asset_price * monthly_return
            monthly_expenses = monthly_fee_percent * current_asset_price
            total_expenses += monthly_expenses
            current_asset_price -= monthly_expenses
            total_revenue = current_asset_price
            net_revenue = total_revenue if total_revenue <= 0 else (1 - (self.gain_tax / 100)) * total_revenue
            amortization_schedule.append({
                'Month': month,
                'Monthly Extra': monthly_saving,
                'Monthly Income': investment_interest,
                'Total Assets': current_asset_price,
                'Total Expenses': total_expenses,
                'Total Revenue': total_revenue,
                'Net Revenue': net_revenue
            })
        return pd.DataFrame(amortization_schedule)
