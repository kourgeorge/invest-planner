import numpy as np
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import investpy
from scipy.optimize import fmin
from numpy import random as rn
import scipy.stats as si
import seaborn as sns
import calendar
from datetime import date
import datetime

plt.switch_backend('TkAgg')

def get_monthly_inflation(start_date, end_date, symbol='^CPIAUCNS'):
    """
    Fetch monthly inflation rates using the yfinance library.

    Parameters:
    - start_date: Start date in the format 'YYYY-MM-DD'
    - end_date: End date in the format 'YYYY-MM-DD'
    - symbol: Ticker symbol for the inflation index (default is CPI)

    Returns:
    - DataFrame with Date and Inflation columns
    """
    data = yf.download(symbol, start=start_date, end=end_date)
    data['Inflation'] = data['Close'].pct_change() * 100  # Calculate monthly inflation
    return data[['Inflation']].dropna()


def get_monthly_inflation_israel(start_date, end_date, country='Israel', index_name='CPI'):
    """
    Fetch monthly inflation rates for a specific country using the investpy library.

    Parameters:
    - start_date: Start date in the format 'YYYY-MM-DD'
    - end_date: End date in the format 'YYYY-MM-DD'
    - country: Name of the country (default is 'Israel')
    - index_name: Name of the inflation index (default is 'CPI')

    Returns:
    - DataFrame with Date and Inflation columns
    """
    # inflation_data = investpy.economic_calendar.get_calendar_data(country=country, event='Inflation Rate', from_date=start_date, to_date=end_date)
    res = investpy.economic_calendar(countries=[country], from_date=start_date, to_date=end_date)
    inflation_data = res
    inflation_data['Date'] = pd.to_datetime(inflation_data['Date'])
    inflation_data = inflation_data.set_index('Date')[['Actual']]
    inflation_data.columns = ['Inflation']
    return inflation_data


def plot_inflation(data):
    """
    Plot the monthly inflation rates.

    Parameters:
    - data: DataFrame with Date and Inflation columns
    """
    plt.figure(figsize=(10, 6))
    plt.plot(data.index, data['Inflation'], label='Monthly Inflation Rate', marker='o')
    plt.title('Monthly Inflation Rates in the Last 10 Years')
    plt.xlabel('Date')
    plt.ylabel('Inflation Rate (%)')
    plt.legend()
    plt.grid(True)
    plt.show()




df = pd.read_csv('data/CPI.csv')
df_copy = df.copy()  # Create a copy of the DataFrame
df_cpi = df_copy.tail(50).reset_index()
df_cpi['CPIi'] = df_cpi['CPIi']  - df_cpi.at[len(df_cpi)-13, 'CPIi']+101.983


def ImpliedBrownianMotion(c):

    df_cpi["delta_CPI"] = 0.00
    df_cpi["ui"] = 0.00
    df_cpi["vi"] = 0.00
    df_cpi["wi"] = 0.00
    df_cpi["PDFi"] = 0.00
    df_cpi["ln(PDFi)"] = 0.00

    for i in range(len(df_cpi) - 1):
        df_cpi.at[i, "delta_CPI"] = df_cpi.at[i + 1, "CPIi"] - df_cpi.at[i, "CPIi"]
        df_cpi.at[i, "ui"] = c[0] * df_cpi.at[i, "CPIi"]
        df_cpi.at[i, "vi"] = df_cpi.at[i, "delta_CPI"] - df_cpi.at[i, "ui"]
        df_cpi.at[i, "wi"] = c[1] * df_cpi.at[i, "CPIi"]
        df_cpi.at[i, "PDFi"] = si.norm.pdf(df_cpi.at[i, "vi"], 0, df_cpi.at[i, "wi"])
        df_cpi.at[i, "ln(PDFi)"] = np.log(df_cpi.at[i, "PDFi"])

    f1 = df_cpi["ln(PDFi)"].sum()
    val = -f1

    print("[μ, σ]=", c, ", Object Function Value:", val)
    return val

def RAND():
    d = rn.uniform(0, 1, 1)[0]
    return (d)

def NORMSINV(x):
    x = si.norm.ppf(x)
    return (x)

def CPI_prediction():
    c = fmin(ImpliedBrownianMotion, [0.015, 0.001])
    mu = c[0]
    sigma = c[1]
    print("μ =", "{:.4%}".format(mu), ", σ =", "{:.4%}".format(sigma))

    mu = mu*12
    sigma = sigma*np.sqrt(12)
    CPI0 = df_cpi.at[len(df_cpi)-1, 'CPIi']
    T = 1
    M = 50000

    I = CPI0 * np.ones(M)
    d = {'CPI0': I}
    df = pd.DataFrame(data=d)

    df["RAND"] = 0.00
    for i in range(0, len(df["CPI0"])):
        df["RAND"][i] = RAND()

    df["NORMSINV"] = 0.00
    for i in range(0, int(0.5 * len(df["CPI0"]))):
        df["NORMSINV"][i] = NORMSINV(df["RAND"][i])
    for i in range(int(0.5 * len(df["CPI0"])), len(df["CPI0"])):
        df["NORMSINV"][i] = -df["NORMSINV"][i - 250]

    df["CPIT"] = 0.00
    for i in range(0, len(df["CPI0"])):
        df["CPIT"][i] = df["CPI0"][i] * (1 + mu * T + sigma * df["NORMSINV"][i] * np.sqrt(T))

    df["Inflation"] = df["CPIT"] / df["CPI0"] - 1

    V = df["Inflation"]
    Simulations = 10
    curr_date = date.today()
    today = date.today()
    now = datetime.datetime.now()

    plt.figure(figsize = (4,4))
    sns.set(font_scale = 1.2)
    ax = sns.histplot(data=V,bins=10,color="red")
    ax.set_xlabel("Default Probability",fontsize=14)
    ax.set_ylabel("Frequency",fontsize=14)
    ax.set_xlim(np.min(V),np.max(V))
    print("\033[1m Probability Density Function for Inflation Forecast for 2024 (Sim#1)")
    print("\033[0m ====================================================================")
    print("\033[1m Performed By:","\033[0mRoi Polanitzer")
    print("\033[1m Date:","\033[0m",calendar.day_name[curr_date.weekday()],",",today.strftime("%B %d, %Y"),",",now.strftime("%H:%M:%S AM"))

    print("The Israel inflation rate forecast for 2024 is {:.2%} with a standard error of sample mean of {:.3%}".format(np.mean(V),np.std(V)/np.sqrt(M)))

    plt.show()

if __name__ == "__main__":
    CPI_prediction()

    # Set the start and end dates
    date_format = '%Y-%m-%d'
    date_format = '%d/%m/%Y'
    end_date = pd.Timestamp.now().strftime(date_format)
    start_date = (pd.Timestamp.now() - pd.DateOffset(years=10)).strftime(date_format)

    # Fetch and display monthly inflation rates
    inflation_data = get_monthly_inflation_israel(start_date, end_date)
    print(inflation_data)

    # Plot the data
    plot_inflation(inflation_data)
