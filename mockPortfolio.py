import ssl, certifi
ssl._create_default_https_context = lambda: ssl.create_default_context(cafile=certifi.where())
from fredapi import Fred
import yfinance as yf
import pandas as pd
import numpy as np
import seaborn as sns
import time

fred = Fred(api_key="5e0c5fb26762b84a6b8eb806511522fe")
treasury_series = {"2Y": "DGS2", "5Y": "DGS5", "10Y": "DGS10", "30Y": "DGS30"}

treasury = {
    name: fred.get_series(sid).dropna().iloc[-1]
    for name, sid in treasury_series.items()
}

#Pull company financials from yahoo finance
companies = {
    # ── Industrials (Strong) ──────────────────────────────────────────────────
    "CAT":  {"name": "Caterpillar",       "sector": "Industrials", "maturity": "10Y", "coupon": 3.80, "face": 1000},
    "HON":  {"name": "Honeywell",         "sector": "Industrials", "maturity": "10Y", "coupon": 3.35, "face": 1000},
    "LMT":  {"name": "Lockheed Martin",   "sector": "Industrials", "maturity": "10Y", "coupon": 3.55, "face": 1000},
    "RTX":  {"name": "Raytheon",          "sector": "Industrials", "maturity": "10Y", "coupon": 3.95, "face": 1000},
    "GE":   {"name": "GE Aerospace",      "sector": "Industrials", "maturity": "10Y", "coupon": 4.10, "face": 1000},
    "UPS":  {"name": "UPS",               "sector": "Industrials", "maturity": "10Y", "coupon": 3.40, "face": 1000},
    "MMM":  {"name": "3M",                "sector": "Industrials", "maturity": "10Y", "coupon": 3.70, "face": 1000},
    # ── Industrials (Distressed / Declining) ─────────────────────────────────
    "BA":   {"name": "Boeing",            "sector": "Industrials", "maturity": "10Y", "coupon": 5.71, "face": 1000},
    "ALK":  {"name": "Alaska Air",        "sector": "Industrials", "maturity": "5Y",  "coupon": 4.80, "face": 1000},
    "R":    {"name": "Ryder System",      "sector": "Industrials", "maturity": "5Y",  "coupon": 4.63, "face": 1000},
    # ── Energy (Strong) ──────────────────────────────────────────────────────
    "XOM":  {"name": "ExxonMobil",        "sector": "Energy",      "maturity": "10Y", "coupon": 3.68, "face": 1000},
    "CVX":  {"name": "Chevron",           "sector": "Energy",      "maturity": "10Y", "coupon": 3.08, "face": 1000},
    "COP":  {"name": "ConocoPhillips",    "sector": "Energy",      "maturity": "10Y", "coupon": 4.15, "face": 1000},
    "SLB":  {"name": "SLB",              "sector": "Energy",      "maturity": "5Y",  "coupon": 4.00, "face": 1000},
    "PSX":  {"name": "Phillips 66",       "sector": "Energy",      "maturity": "5Y",  "coupon": 4.65, "face": 1000},
    # ── Energy (Distressed / Leveraged) ──────────────────────────────────────
    "OXY":  {"name": "Occidental",        "sector": "Energy",      "maturity": "10Y", "coupon": 6.63, "face": 1000},
    "HAL":  {"name": "Halliburton",       "sector": "Energy",      "maturity": "10Y", "coupon": 4.85, "face": 1000},
    "AR":   {"name": "Antero Resources",  "sector": "Energy",      "maturity": "5Y",  "coupon": 7.63, "face": 1000},
    # ── Consumer Staples (Strong) ────────────────────────────────────────────
    "PG":   {"name": "Procter & Gamble",  "sector": "Cons.Staples","maturity": "10Y", "coupon": 3.00, "face": 1000},
    "KO":   {"name": "Coca-Cola",         "sector": "Cons.Staples","maturity": "10Y", "coupon": 3.45, "face": 1000},
    "PEP":  {"name": "PepsiCo",           "sector": "Cons.Staples","maturity": "10Y", "coupon": 3.50, "face": 1000},
    "CL":   {"name": "Colgate-Palmolive", "sector": "Cons.Staples","maturity": "10Y", "coupon": 3.10, "face": 1000},
    "GIS":  {"name": "General Mills",     "sector": "Cons.Staples","maturity": "5Y",  "coupon": 4.20, "face": 1000},
    # ── Consumer Staples (Struggling) ────────────────────────────────────────
    "KHC":  {"name": "Kraft Heinz",       "sector": "Cons.Staples","maturity": "10Y", "coupon": 5.00, "face": 1000},
    "WBA":  {"name": "Walgreens",         "sector": "Cons.Staples","maturity": "5Y",  "coupon": 8.13, "face": 1000},
    "MO":   {"name": "Altria",            "sector": "Cons.Staples","maturity": "10Y", "coupon": 5.80, "face": 1000},
    # ── Tech (Strong) ────────────────────────────────────────────────────────
    "MSFT": {"name": "Microsoft",         "sector": "Tech",        "maturity": "10Y", "coupon": 3.45, "face": 1000},
    "GOOGL":{"name": "Alphabet",          "sector": "Tech",        "maturity": "10Y", "coupon": 2.25, "face": 1000},
    "CSCO": {"name": "Cisco",             "sector": "Tech",        "maturity": "10Y", "coupon": 3.50, "face": 1000},
    "IBM":  {"name": "IBM",               "sector": "Tech",        "maturity": "10Y", "coupon": 4.15, "face": 1000},
    "ORCL": {"name": "Oracle",            "sector": "Tech",        "maturity": "10Y", "coupon": 4.65, "face": 1000},
    # ── Tech (Leveraged / Declining) ─────────────────────────────────────────
    "HPE":  {"name": "HP Enterprise",     "sector": "Tech",        "maturity": "5Y",  "coupon": 4.45, "face": 1000},
    "INTC": {"name": "Intel",             "sector": "Tech",        "maturity": "10Y", "coupon": 5.05, "face": 1000},
    "PARA": {"name": "Paramount",         "sector": "Tech",        "maturity": "5Y",  "coupon": 6.38, "face": 1000},
    "DISH": {"name": "DISH/EchoStar",     "sector": "Tech",        "maturity": "5Y",  "coupon": 11.75,"face": 1000},
}

def getFinancials(ticker: str):     #get values from yfincance to compute credit spreads
    tk = yf.Ticker(ticker)
    info = tk.info      
    fin = tk.financials         #income statement
    totalDebt = info.get("totalDebt", np.nan)       #totaldebt in balance sheet
    ebitda = info.get("ebitda",    np.nan)          #in inc statement
    #Intrest coverage = EBIT/Intrest expense        interest exp in incomestatement --> apple is empty

    try:
        ebit = fin.loc["EBIT"].iloc[0]
        intExp = fin.loc["Interest Expense"].iloc[0]            
        int_cov   = ebit / abs(intExp) if ebit and intExp != 0 else np.nan
    except Exception:
        int_cov = np.nan

    debt_Ebitda_ratio = totalDebt/ebitda if totalDebt and ebitda != 0 else np.nan 
    
    return {"debt_Ebitda_ratio": debt_Ebitda_ratio, "int_coverage": int_cov}

#Credit spread = debtEbitda(direct) + Interest Coverage(inverse) (bps)
#If company has high leverage(ie High debt/equity ratio) then investors want a wider spread to account for that risk
#If company has low liquidty to account for interest payments 
#       then investors want wider spread to account for risk of missing an interest payment

def credit_spread(debt_Ebitda_ratio: float, int_coverage: float) -> float:
        #Leverage
    if   debt_Ebitda_ratio < 1.0:  lev_spread = 0.40    #very safe, low leverage
    elif debt_Ebitda_ratio < 2.0:  lev_spread = 0.65
    elif debt_Ebitda_ratio < 3.5:  lev_spread = 1.00
    elif debt_Ebitda_ratio < 5.0:  lev_spread = 1.75
    elif debt_Ebitda_ratio < 7.0:  lev_spread = 2.75
    else:                     lev_spread = 4.50   # distressed / HY
 
    # Liquidity/Coverage
    if   int_coverage > 10:  cov_spread = -0.10   # High liquidity, very safe, tighten
    elif int_coverage > 5:   cov_spread =  0.00
    elif int_coverage > 3:   cov_spread =  0.25
    elif int_coverage > 1.5: cov_spread =  0.75
    else:                     cov_spread =  1.50   # near distress
 
    # If data is missing, fall back to a default 1% spread
    if np.isnan(debt_Ebitda_ratio) or np.isnan(int_coverage):
        return 1.00
 
    return round(lev_spread + cov_spread, 3)


#Make portfolio df
maturity_map = {"2Y": 2, "5Y": 5, "10Y": 10, "30Y": 30}
skipped      = []
rows         = []
 
for ticker, meta in companies.items():
    print(f"  Fetching {meta['name']} ({ticker}) …")
    fins = getFinancials(ticker)
    spd  = credit_spread(fins["debt_Ebitda_ratio"], fins["int_coverage"])
 
    if np.isnan(spd):
        print(f"    ⚠️  Skipping {ticker} — unreliable financials")
        skipped.append(ticker)
        continue
 
    tsy = treasury[meta["maturity"]]
    ytm = round(tsy + spd, 4)
    rows.append({
        "Ticker":        ticker,
        "Name":          meta["name"],
        "Sector":        meta["sector"],
        "Maturity":      meta["maturity"],
        "Coupon (%)":    meta["coupon"],
        "Face Value":    meta["face"],
        "Treasury (%)":  round(tsy, 3),
        "Debt/EBITDA":   round(fins["debt_Ebitda_ratio"], 2),
        "Int. Coverage": round(fins["int_coverage"], 2),
        "Spread (%)":    spd,
        "YTM (%)":       ytm,
    })
    time.sleep(0.3)
 
portfolio = pd.DataFrame(rows).set_index("Ticker")
 
# ── Add risk-free UST bonds ───────────────────────────────────────────────────
for maturity, ytm in treasury.items():
    portfolio.loc[f"UST_{maturity}"] = {
        "Name":          f"US Treasury {maturity}",
        "Sector":        "Government",
        "Maturity":      maturity,
        "Coupon (%)":    round(ytm, 2),
        "Face Value":    1000,
        "Treasury (%)":  round(ytm, 2),
        "Debt/EBITDA":   0.0,
        "Int. Coverage": 999.0,
        "Spread (%)":    0.00,
        "YTM (%)":       round(ytm, 2),
    }
 
if skipped:
    print(f"\n⚠️  Skipped tickers (unreliable yfinance data): {skipped}")
 
print(f"\n── Portfolio ({len(portfolio)} bonds) ───────────────────────────────────────")
print(portfolio.to_string())




#include US Treasury bonds in portfolio
#CALCULATE RISK METRICS AND VALUES
#create dashboard STEP4
#could add more advanced portfolio -->add more companies

def bond_price(face, coupon_rate, ytm, periods):
    """Standard bond price: PV of coupons + PV of face. Semi-annual."""
    c = (coupon_rate / 100) * face / 2   # semi-annual coupon payment
    y = ytm / 100 / 2                    # semi-annual yield
    n = periods * 2                      # total semi-annual periods
 
    pv_coupons = c * (1 - (1 + y) ** -n) / y
    pv_face = face / (1 + y) ** n
    return pv_coupons + pv_face
 
 
def macaulay_duration(face, coupon_rate, ytm, periods):
    """Weighted average time to receive cash flows (in years)."""
    c = (coupon_rate / 100) * face / 2
    y = ytm / 100 / 2
    n = periods * 2
 
    price = bond_price(face, coupon_rate, ytm, periods)
    weighted_t = sum((t / 2) * (c / (1 + y) ** t) for t in range(1, n)) + (n / 2) * ((c + face) / (1 + y) ** n)
 
    return weighted_t / price
 
 
def convexity(face, coupon_rate, ytm, periods):
    """
    Convexity measures how duration changes as yields change.
    Second-order price sensitivity — always positive for plain bonds.
    """
    c = (coupon_rate / 100) * face / 2
    y = ytm / 100 / 2
    n = periods * 2
 
    price = bond_price(face, coupon_rate, ytm, periods)
    conv  = sum(
        (t * (t + 1)) * (c / (1 + y) ** (t + 2)) for t in range(1, n)
    ) + (n * (n + 1)) * ((c + face) / (1 + y) ** (n + 2))
 
    return conv / (price * 4)   # divide by 4 to annualise semi-annual
 
 
def krd(face, coupon_rate, ytm, periods, key_tenors=(2, 5, 10, 30), bump=0.01):
    """
    Key Rate Duration: price sensitivity to a 1bp bump at each key tenor.
    Approximated by bumping the yield at each tenor and computing dP.
    For a single bond, only the KRD for the matched tenor is non-zero;
    this gives you the framework to extend to a full curve later.
    """
    base_price = bond_price(face, coupon_rate, ytm, periods)
    krds = {}
    for tenor in key_tenors:
        # Only apply bump if this tenor is close to the bond's maturity
        if abs(tenor - periods) <= 2.5:
            bumped_ytm = ytm + bump
            bumped_price = bond_price(face, coupon_rate, bumped_ytm, periods)
            krds[f"KRD_{tenor}Y"] = round((bumped_price - base_price) / base_price * 100, 4)
        else:
            krds[f"KRD_{tenor}Y"] = 0.0
    return krds
 
 
# Map maturity label → years
maturity_map = {"2Y": 2, "5Y": 5, "10Y": 10, "30Y": 30}
 
risk_rows = []
for ticker, row in portfolio.iterrows():
    T      = maturity_map[row["Maturity"]]
    face   = row["Face Value"]
    coupon = row["Coupon (%)"]
    ytm    = row["YTM (%)"]
 
    price  = bond_price(face, coupon, ytm, T)
    mac_d  = macaulay_duration(face, coupon, ytm, T)
    mod_d  = mac_d / (1 + ytm / 100 / 2)           # Modified Duration
    conv   = convexity(face, coupon, ytm, T)
    dv01   = -mod_d * price * 0.0001                # $ change per 1bp move
    krds   = krd(face, coupon, ytm, T)
 
    risk_rows.append({
        "Ticker":       ticker,
        "Name":         row["Name"],
        "Price ($)":    round(price, 2),
        "Mac. Dur":     round(mac_d, 3),
        "Mod. Dur":     round(mod_d, 3),
        "Convexity":    round(conv, 4),
        "DV01 ($)":     round(dv01, 4),
        **krds
    })
 
risk = pd.DataFrame(risk_rows).set_index("Ticker")
 
print("\n── Risk Metrics ─────────────────────────────────────────────────────────")
print(risk.to_string())
 
# ── Quick interpretation ──────────────────────────────────────────────────────
print("\n── Portfolio Aggregates ─────────────────────────────────────────────────")
print(f"  Total Market Value : ${risk['Price ($)'].sum():,.2f}")
print(f"  Avg Modified Dur   : {risk['Mod. Dur'].mean():.3f} years")
print(f"  Avg Convexity      : {risk['Convexity'].mean():.4f}")
print(f"  Total DV01         : ${risk['DV01 ($)'].sum():.4f}  (portfolio $ loss per +1bp)")




