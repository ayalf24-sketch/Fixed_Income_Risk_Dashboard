import ssl, certifi
ssl._create_default_https_context = lambda: ssl.create_default_context(cafile=certifi.where())
 
from fredapi import Fred
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns

fred = Fred(api_key="5e0c5fb26762b84a6b8eb806511522fe")
 
series = {"2Y": "DGS2", "5Y": "DGS5", "10Y": "DGS10", "30Y": "DGS30"}
df = pd.DataFrame({name: fred.get_series(sid) for name, sid in series.items()})
df = df.ffill().dropna(subset=["2Y", "10Y"]).loc["2010-01-01":]

#Yield Spreads
df["2Y10Y"] = df["10Y"] - df["2Y"]
df["2Y30Y"] = df["30Y"] - df["2Y"]
df["10Y30Y"] = df["30Y"] - df["10Y"]

sns.set_theme(style="darkgrid", palette="tab10")
fig, axes = plt.subplots(4, 1, figsize=(12, 12))
fig.suptitle("Treasury Yield Curve Analysis (2010–Present)", fontsize=14, fontweight="bold")

#Yield History
ax = axes[0]
for col in ["2Y", "5Y", "10Y", "30Y"]:
    ax.plot(df.index, df[col], label=col, linewidth=1.2)
ax.set_title("Treasury Yields")
ax.set_ylabel("Yield (%)")
ax.legend(ncol=4)

#2Y–10Y spread
ax = axes[1]
ax.plot(df.index, df["2Y10Y"], color="crimson", linewidth=1.2, label="2Y–10Y")
ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
ax.fill_between(df.index, df["2Y10Y"], 0, where=(df["2Y10Y"] < 0), color="red", alpha=0.2, label="Inverted")
ax.set_title("2Y–10Y Spread")
ax.set_ylabel("Spread (%)")
ax.legend()

#2Y–30Y spread
ax = axes[2]
ax.plot(df.index, df["2Y30Y"], color="steelblue", linewidth=1.2, label="2Y–30Y")
ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
ax.fill_between(df.index, df["2Y30Y"], 0, where=(df["2Y30Y"] < 0), color="red", alpha=0.2, label="Inverted")
ax.set_title("2Y–30Y Spread")
ax.set_ylabel("Spread (%)")
ax.legend()
 

#10-30Y spread
ax = axes[3]
ax.plot(df.index, df["10Y30Y"], color="steelblue", linewidth=1.2, label="10Y–30Y")
ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
ax.fill_between(df.index, df["10Y30Y"], 0, where=(df["10Y30Y"] < 0), color="red", alpha=0.2, label="Inverted")
ax.set_title("10–30Y Spread")
ax.set_ylabel("Spread (%)")
ax.legend()

for ax in axes:
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
 
plt.tight_layout()
plt.show()
 
print(f"\n2Y–10Y latest: {df['2Y10Y'].iloc[-1]:.2f}%")
print(f"2Y–30Y latest: {df['2Y30Y'].iloc[-1]:.2f}%")
print(f"10Y–30Y latest: {df['10Y30Y'].iloc[-1]:.2f}%")