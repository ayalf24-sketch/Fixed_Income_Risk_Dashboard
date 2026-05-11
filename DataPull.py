import ssl
import certifi
ssl._create_default_https_context = lambda: ssl.create_default_context(cafile=certifi.where())

from fredapi import Fred
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
import seaborn as sns


API_KEY = "5e0c5fb26762b84a6b8eb806511522fe"
fred = Fred(api_key=API_KEY)
 
series = {
    "1Y":           "DGS1",     #1YR TREASURY YIELD...etc
    "2Y":           "DGS2",
    "5Y":           "DGS5",
    "10Y":          "DGS10",
    "30Y":          "DGS30",    
    "FedFunds":     "DFF",  #daily effective fedfunds rate
    "SOFR":         "SOFR", #NaN before 2018
    "CPI":          "CPIAUCSL", #monthly values
    "Unemployment": "UNRATE"    #monthly values
}

# Pull each series and collect into a dict
raw = {}
for name, series_id in series.items():
    raw[name] = fred.get_series(series_id)
 
# Combine into a single DataFrame
df = pd.DataFrame(raw)
df.index.name = "Date"

# Forward-fill gaps (weekends, holidays, monthly series like CPI/Unemployment)
df = df.ffill()
 
# Drop rows where ALL values are NaN (e.g. before any series existed)
df = df.dropna(how="all")
 
# Trim to where we have at least the core yield data
df = df.dropna(subset=["2Y", "10Y"])


print(df.tail(10))

 
sns.set_theme(style="darkgrid")

latest = df[["2Y", "5Y", "10Y", "30Y"]].dropna().iloc[-1]

maturities = [2, 5, 10, 30]
yields = latest.values

plt.figure(figsize=(10, 6))

sns.lineplot(x=maturities, y=yields, marker="o", linewidth=2, color="red")

plt.title("Current Treasury Yield Curve", fontsize=14, fontweight="bold")
plt.xlabel("Maturity (Years)")
plt.ylabel("Yield (%)")

plt.xticks(maturities)
for x, y in zip(maturities, yields):
    plt.text(
        x, y,
        f"{y:.2f}%",          # format to 2 decimals
        ha="center",
        va="bottom",
        fontsize=10
    )
plt.grid(True)

plt.show()



