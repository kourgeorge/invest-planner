import pandas as pd
from constants import *
from loan import Loan
from mortgage import Mortgage
import numpy_financial as npf


class Investment:

    def __init__(self, initial_fund, investment_years, name):
        self.initial_fund = initial_fund
        self.investment_years = investment_years
        self.name = name

    def get_initial_investment(self):
        return self.initial_fund

    def generate_amortization_schedule(self, investment_years) -> pd.DataFrame:
        pass

    def set_investment_years(self, new_investment_years):
        self.investment_years = new_investment_years
        self.amortization_schedule = self.generate_amortization_schedule(new_investment_years)

    def total_income_payments(self, month=None):
        if month is not None:
            return self.amortization_schedule.loc[:month, 'Income'].sum()
        else:
            return self.amortization_schedule['Income'].sum()

    def total_assets(self, month=None):
        if month is not None:
            return round(self.amortization_schedule.loc[month, 'Total Assets'])
        else:
            return round(self.amortization_schedule['Total Assets'].iloc[-1])

    def total_liabilities(self, month=None):
        if month is not None:
            return round(self.amortization_schedule.loc[month, 'Total Liabilities'])
        else:
            return round(self.amortization_schedule['Total Liabilities'].iloc[-1])

    def total_expenses_payments(self, month=None):
        if month is not None:
            return self.amortization_schedule.loc[:month, 'Expenses'].sum()
        else:
            return self.amortization_schedule['Expenses'].sum()

    def total_revenue(self, month=None):
        if month is not None:
            return self.amortization_schedule.loc[month, 'Total Revenue']
        else:
            return self.amortization_schedule['Total Revenue'].iloc[-1]

    def net_worth(self, month=None):
        if month is not None:
            return self.amortization_schedule.loc[month, 'Total Assets'] - \
                   self.amortization_schedule.loc[month, 'Total Liabilities']
        else:
            return self.amortization_schedule['Total Assets'].iloc[-1] - \
                   self.amortization_schedule['Total Liabilities'].iloc[-1]

    def highest_cash_dept(self):
        """TODO: fix"""
        return (self.amortization_schedule.loc[1:, 'Income'] - self.amortization_schedule.loc[1:, 'Expenses']).min()

    def expected_tax(self):
        return self.amortization_schedule['Total Revenue'].iloc[-1] - self.amortization_schedule['Net Revenue'].iloc[-1]

    def get_investment_years(self):
        return self.investment_years

    def get_irr(self):
        pass

    @staticmethod
    def get_yearly_amortization(amortization_schedule):
        yearly_amortization = amortization_schedule.groupby(amortization_schedule.index // 12).agg({
            'Month': 'last',
            'Total Assets': 'last',
            'Total Liabilities': 'last',
            'Income': 'sum',
            'Expenses': 'sum',
            'Monthly Extra': 'sum',
            'Total Revenue': 'last',
            'Net Revenue': 'last',
        }).astype({'Month': int, 'Total Assets': int, 'Expenses': int, 'Total Revenue': int,
                   'Net Revenue': int, 'Income': int})

        return yearly_amortization


class StocksMarketInvestment(Investment):
    def __init__(self, initial_fund, investment_years, yearly_return=StocksMarketYearlyReturn,
                 yearly_fee_percent=StocksMarketFeesPercentage, gain_tax=TaxGainPercentage, monthly_extra=0,
                 name='Stock Market'):
        super().__init__(initial_fund=initial_fund, investment_years=investment_years, name=name)
        self.yearly_return = yearly_return
        self.gain_tax = gain_tax
        self.yearly_fee_percent = yearly_fee_percent
        self.monthly_extra = monthly_extra
        self.amortization_schedule = self.generate_amortization_schedule(investment_years)

    def generate_amortization_schedule(self, investment_years):
        amortization_schedule = []
        current_asset_price = self.initial_fund
        monthly_return = (1 + self.yearly_return / 100) ** (1 / 12) - 1
        monthly_fee_percent = (1 + self.yearly_fee_percent / 100) ** (1 / 12) - 1
        investment_num_months = int(investment_years * 12)

        for month in range(1, investment_num_months + 1):
            previous_asset_price = current_asset_price
            current_asset_price = previous_asset_price * (1 + monthly_return) + self.monthly_extra
            interest = previous_asset_price * monthly_return
            monthly_expenses = monthly_fee_percent * current_asset_price + self.monthly_extra
            current_asset_price -= monthly_fee_percent * current_asset_price
            total_revenue = current_asset_price - self.initial_fund - month * self.monthly_extra
            taxes = self.gain_tax / 100 * total_revenue
            net_revenue = total_revenue if total_revenue <= 0 else total_revenue-taxes
            amortization_schedule.append({
                'Month': month,
                'Monthly Extra':self.monthly_extra,
                'Income': 0,
                'Expenses': monthly_expenses,
                'Total Assets': current_asset_price,
                'Total Liabilities': 0,
                'Total Revenue': total_revenue,
                'Net Revenue': net_revenue
            })

        return pd.DataFrame(amortization_schedule)

    def get_irr(self):
        annual_amortization = Investment.get_yearly_amortization(self.amortization_schedule)
        taxes = self.amortization_schedule['Net Revenue'].iloc[-1] - self.amortization_schedule['Total Revenue'].iloc[-1]
        cashflow = [-self.initial_fund] + [0]*len(annual_amortization) + [self.total_assets() - taxes]
        return npf.irr(cashflow) * 100


class RealEstateInvestment(Investment):
    def __init__(self, price, initial_fund, mortgage: Mortgage, appreciation_rate, housing_index, investment_years,
                 construction_period=0, monthly_rental_income=0, buying_costs=0, selling_tax=TaxGainPercentage,
                 name='Real Estate'):
        super().__init__(initial_fund=initial_fund, investment_years=investment_years, name=name)

        self.price = price
        self.construction_period = construction_period
        self.appreciation_rate = appreciation_rate
        self.housing_index = housing_index
        self.mortgage: Mortgage = mortgage
        self.monthly_rental_income = monthly_rental_income
        self.buying_costs = buying_costs
        self.selling_tax = selling_tax

        self.amortization_schedule = self.generate_amortization_schedule(investment_years)

    def get_initial_investment(self):
        return self.initial_fund + self.buying_costs

    def generate_amortization_schedule(self, investment_years):
        amortization_schedule = []
        total_rent_income = 0
        current_asset_price = self.price
        monthly_appreciation_rate = (1 + self.appreciation_rate / 100) ** (1 / 12) - 1
        monthly_housing_index = (1 + self.housing_index / 100) ** (1 / 12) - 1
        investment_num_months = int(investment_years * 12)

        for month in range(1, investment_num_months + 1):
            previous_asset_value = current_asset_price
            current_asset_price = current_asset_price * (1 + monthly_appreciation_rate)
            monthly_rental_income = 0 if month < self.construction_period * 12 else self.monthly_rental_income * (
                        1 + monthly_housing_index * month)
            total_rent_income += monthly_rental_income
            expenses = self.mortgage.monthly_payment(month)
            total_expenses = self.mortgage.total_payments(month) + self.initial_fund + self.buying_costs
            total_liabilities = self.mortgage.remaining_balance(month)
            total_revenue = current_asset_price - total_liabilities + total_rent_income - total_expenses
            net_revenue = total_revenue if total_revenue <= 0 else (1 - (self.selling_tax / 100)) * total_revenue
            amortization_schedule.append({
                'Month': month,
                'Income': monthly_rental_income,
                'Expenses': expenses,
                'Monthly Extra': expenses,
                'Total Assets': current_asset_price,
                'Total Liabilities': total_liabilities,
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

    def expected_tax(self, month=None):
        return self.amortization_schedule['Total Revenue'].iloc[-1] - self.amortization_schedule['Net Revenue'].iloc[
            -1] + self.buying_costs

    def get_irr(self):
        annual_amortization = Investment.get_yearly_amortization(self.amortization_schedule)
        cashflow = [-self.buying_costs - self.initial_fund]+list(
            annual_amortization['Income'] - annual_amortization['Expenses']) + [
                           self.net_worth()]
        return npf.irr(cashflow) * 100

    @staticmethod
    def quick_calculation(price, down_payment, interest_rate, appreciation_rate, investment_years,
                          mortgage_num_years, housing_index, monthly_rental_income, name, building_period=0, grace=0,
                          buying_costs=0, ):
        loan = Loan(amount=price - down_payment, interest_rate=interest_rate,
                    num_of_months=mortgage_num_years * 12, grace_period=grace*12)
        investment = RealEstateInvestment(price=price, initial_fund=down_payment,
                                          mortgage=Mortgage([loan]),
                                          investment_years=investment_years,
                                          housing_index=housing_index,
                                          appreciation_rate=appreciation_rate,
                                          construction_period=building_period,
                                          monthly_rental_income=monthly_rental_income,
                                          buying_costs=buying_costs,
                                          name=name)

        return investment


class MortgageRecycleInvestment(Investment):
    def __init__(self, initial_fund, mortgage: Mortgage, investment_years,
                 investment_yearly_return=StocksMarketYearlyReturn,
                 stocks_yearly_fee_percent=StocksMarketFeesPercentage, name='Mortgage Recycle',
                 gain_tax=TaxGainPercentage, change='payment'):
        super().__init__(initial_fund=initial_fund, investment_years=investment_years, name=name)

        self.old_mortgage = mortgage
        self.change = change
        self.recycled_mortgage = Mortgage.recycle_mortgage(self.old_mortgage, extra_payment=self.initial_fund, change=change)
        self.investment_yearly_return = investment_yearly_return
        self.yearly_fee_percent = stocks_yearly_fee_percent
        self.gain_tax = gain_tax

        self.amortization_schedule = self.generate_amortization_schedule(investment_years)

    def get_recycled_mortgage(self):
        return self.recycled_mortgage

    def generate_amortization_schedule(self, investment_years):
        diff_amortization_schedule = Mortgage.amortization_diff(self.old_mortgage, self.recycled_mortgage)

        current_asset_price = 0
        amortization_schedule = []
        monthly_return = (1 + self.investment_yearly_return / 100) ** (1 / 12) - 1
        monthly_fee_percent = (1 + self.yearly_fee_percent / 100) ** (1 / 12) - 1
        investment_num_months = int(investment_years * 12)

        diff_mortgage_length = len(diff_amortization_schedule)
        for month in range(1, investment_num_months + 1):
            previous_asset_price = current_asset_price
            monthly_mortgage_saving = 0 if month > diff_mortgage_length else diff_amortization_schedule.at[
                month - 1, 'Interest Payment'] + diff_amortization_schedule.at[month - 1, 'Inflation Payment']
            current_asset_price = previous_asset_price * (1 + monthly_return) + monthly_mortgage_saving
            investment_interest = previous_asset_price * monthly_return
            monthly_expenses = monthly_fee_percent * current_asset_price
            current_asset_price -= monthly_expenses
            total_revenue = current_asset_price
            net_revenue = total_revenue if total_revenue <= 0 else (1 - (self.gain_tax / 100)) * total_revenue
            amortization_schedule.append({
                'Month': month,
                'Monthly Extra': monthly_mortgage_saving,
                'Income':  monthly_mortgage_saving + investment_interest,
                'Expenses': monthly_expenses,
                'Total Assets': current_asset_price,
                'Total Liabilities': 0,
                'Total Revenue': total_revenue,
                'Net Revenue': net_revenue
            })
        return pd.DataFrame(amortization_schedule)

    def get_irr(self):
        return npf.irr([-self.initial_fund] +
            list(
                self.amortization_schedule['Income'] - self.amortization_schedule['Expenses']) + [self.initial_fund]) * 12 * 100
