import numpy as np
import pandas as pd
from scipy.stats import norm


banks_monthly_data = pd.read_csv('data/israel_banks_monthly.csv')


class CPIVAR:
    base = None

    @staticmethod
    def value_at_risk(holding_period):
        if CPIVAR.base is None:
            df = pd.read_csv('data/CPI_israel.csv')
            cpi_series = df['CPIi']
            CPIVAR.base = calculate_var(cpi_series, confidence_level=0.95)

        return CPIVAR.base * np.sqrt(holding_period/12)


class PrimeInterestVAR:
    base = None

    @staticmethod
    def value_at_risk(holding_period):
        if PrimeInterestVAR.base is None:
            df = pd.read_csv('data/prime_interest_israel.csv')
            prime_series = df['Prime']
            PrimeInterestVAR.base = calculate_var(prime_series, confidence_level=0.95)
        return PrimeInterestVAR.base * np.sqrt(holding_period/12)


def calculate_var(sequence, confidence_level=0.95):
    """
    The VaR value,represents the potential loss or increase in the cost of the loan due to changes  in inflation.
    For example, if you calculate a one-year VaR at a 95% confidence level, it might indicate the potential increase
    in the loan cost that you would expect to see with a 5% probability, assuming the inflation rate follows a normal distribution.
    """

    # Calculate daily returns
    returns = sequence.pct_change().dropna()

    # Calculate mean and standard deviation of returns
    mean_return = returns.mean()
    std_dev = returns.std()

    # Calculate Z-Score based on the confidence level
    z_score = norm.ppf(confidence_level)

    # Calculate VaR
    var = mean_return + z_score * std_dev

    return var