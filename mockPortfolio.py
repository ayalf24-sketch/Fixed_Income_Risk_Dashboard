import ssl, certifi
ssl._create_default_https_context = lambda: ssl.create_default_context(cafile=certifi.where())
from fredapi import Fred
import yfinance as yf
import pandas as pd
import numpy as np
import seaborn as sns
import numpy as np
import time
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors

fred = Fred(api_key="5e0c5fb26762b84a6b8eb806511522fe")
treasury_series = {"2Y": "DGS2", "5Y": "DGS5", "10Y": "DGS10", "30Y": "DGS30"}

treasury = {
    name: fred.get_series(sid).dropna().iloc[-1]
    for name, sid in treasury_series.items()
}
yields = pd.DataFrame({name: fred.get_series(sid) for name, sid in treasury_series.items()})


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
    #Interest coverage = EBIT/Interest expense        interest exp in incomestatement --> apple is empty

    try:
        ebit = fin.loc["EBIT"].iloc[0]
        intExp = fin.loc["Interest Expense"].iloc[0]            
        int_cov = (ebit / abs(intExp) if not np.isnan(ebit) and not np.isnan(intExp) and intExp != 0
    else np.nan
    )
    except Exception:
        int_cov = np.nan

    debt_Ebitda_ratio = (totalDebt / ebitda if not np.isnan(totalDebt) and not np.isnan(ebitda) and ebitda != 0
    else np.nan
    )

    return {"debt_Ebitda_ratio": debt_Ebitda_ratio, "int_coverage": int_cov}

#Credit spread = debtEbitda(direct) + Interest Coverage(inverse) (bps)
#If company has high leverage(ie High debt/equity ratio) then investors want a wider spread to account for that risk
#If company has low liquidty to account for interest payments 
#       then investors want wider spread to account for risk of missing an interest payment

def credit_spread(debt_Ebitda_ratio: float, int_coverage: float) -> float:
        #Leverage
    if debt_Ebitda_ratio < 0: lev_spread = 4.50         #negative EBITDA MEANS BURNING CASH
    elif debt_Ebitda_ratio < 1.0:  lev_spread = 0.40    #very safe, low leverage
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
 
    # If data is missing --> default 1% spread
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
        print(f"Skipping {ticker} — unreliable financials")
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
        "T":             maturity_map[meta["maturity"]],
    })
    time.sleep(0.3)
 
portfolio = pd.DataFrame(rows).set_index("Ticker")

#risk-free UST bonds
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
        "T":             maturity_map[meta["maturity"]],
    }
 
if skipped:
    print(f"\n Skipped tickers (unreliable yfinance data): {skipped}")
 
print(f"\n── Portfolio ({len(portfolio)} bonds) ───────────────────────────────────────")
print(portfolio.to_string())

#CALCULATE RISK METRICS AND VALUES

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
merged = portfolio.join(risk[["Mod. Dur"]], how="left")

print("\n── Risk Metrics ─────────────────────────────────────────────────────────")
print(risk.to_string())
 
# Quick interpretation
print("\n── Portfolio Aggregates ─────────────────────────────────────────────────")
print(f"  Total Market Value : ${risk['Price ($)'].sum():,.2f}")
print(f"  Avg Modified Dur   : {risk['Mod. Dur'].mean():.3f} years")
print(f"  Avg Convexity      : {risk['Convexity'].mean():.4f}")
print(f"  Total DV01         : ${risk['DV01 ($)'].sum():.4f}  (portfolio $ loss per +1bp)")

#VaR
#take N historical days ago
#HISTORICAL CHANGES
yields = yields.ffill().dropna(subset=["2Y", "10Y"]).loc["2000-01-01":]
monthly_changes = yields.resample("ME").last().diff().dropna()

tenor_map = {"2Y" : "2Y", "5Y": "5Y", "10Y": "10Y", "30Y": "30Y"} #maps each bond to correct yield col
mock_PnL = []
for date, row in monthly_changes.iterrows():
    month_PnL = 0
    
    for ticker, bond in portfolio.iterrows():
        y_shift = row[tenor_map[bond["Maturity"]]]
        base_p = bond_price(float(bond["Face Value"]), float(bond["Coupon (%)"]), float(bond["YTM (%)"]), float(bond["T"]))
        shocked_p = bond_price(float(bond["Face Value"]), float(bond["Coupon (%)"]), float(bond["YTM (%)"])  + y_shift, float(bond["T"]))
        month_PnL += shocked_p - base_p
    
    mock_PnL.append({"Date": date, "PnL": month_PnL})

PnL_df = pd.DataFrame(mock_PnL).set_index("Date").sort_values("PnL")
VaR95 = np.percentile(PnL_df["PnL"], 5) #worst 5% of month losses
CVaR_95 = PnL_df[PnL_df["PnL"] <= VaR95]["PnL"].mean()  #avg VaR lost in bottom 5%

print(f"1-Month Historical VaR  (95%): ${VaR95:,.2f}")
print(f"1-Month CVaR/Expected Shortfall: ${CVaR_95:,.2f}")



# ─────────────────────────────────────────────────────────────────────────────
# MACRO VIEW: Rates stay steady/higher, spreads widen, energy outperforms due to war
# Weights: 40% Duration + 40% Credit Resilience + 20% Sector Tailwind
# Score: 1-10 worst to best per factor. Higher = better BUY under my assumption
# ─────────────────────────────────────────────────────────────────────────────

WEIGHTS = {"duration": 0.40, "credit": 0.40, "sector": 0.20}

# ── Sector tailwind scores (manual, based on macro view) ─────────────────────
# Energy wins (surging prices improve credit), Government neutral,
# HY Tech/Consumer punished (spread widening + rate risk)
SECTOR_SCORES = {
    "Energy":      9,   # revenues rise with oil — credit improves
    "Government":  6,   # safe but long-duration USTs get hurt
    "Industrials": 5,   # mixed — defense ok, distressed names (BA) punished
    "Cons.Staples":4,   # defensive but leveraged names (WBA, KHC) at risk
    "Tech":        3,   # HY tech gets double-hit: rates up + spreads wide
}

def duration_score(mod_dur: float) -> float:
    """
    Lower duration = better under rising/steady rates.
    Score 10 at ModDur ~1 (very short), score 1 at ModDur ~16 (very long).
    Linear interpolation clamped to [1, 10].
    """
    score = 10 - (mod_dur - 1) * (9 / 15)
    return round(float(np.clip(score, 1, 10)), 2)


def credit_score(debt_ebitda: float, int_coverage: float) -> float:
    """
    Higher resilience = better under spread widening environment.
    Two sub-components averaged:
      - Low Debt/EBITDA → high score
      - High interest coverage → high score
    """
    # Debt/EBITDA sub-score (lower leverage = higher score)
    if   debt_ebitda < 0:   de_score = 1.0   # negative EBITDA = distressed
    elif debt_ebitda < 1.0:  de_score = 10.0
    elif debt_ebitda < 2.0:  de_score = 8.5
    elif debt_ebitda < 3.5:  de_score = 7.0
    elif debt_ebitda < 5.0:  de_score = 5.0
    elif debt_ebitda < 7.0:  de_score = 3.0
    else:                     de_score = 1.5

    # Interest coverage sub-score (higher coverage = higher score)
    if   int_coverage > 10:  cov_score = 10.0
    elif int_coverage > 5:   cov_score = 8.0
    elif int_coverage > 3:   cov_score = 6.0
    elif int_coverage > 1.5: cov_score = 3.5
    else:                     cov_score = 1.5

    return round((de_score + cov_score) / 2, 2)


def composite_score(mod_dur, debt_ebitda, int_coverage, sector):
    d = duration_score(mod_dur)
    c = credit_score(debt_ebitda, int_coverage)
    s = SECTOR_SCORES.get(sector, 5)
    score = (WEIGHTS["duration"] * d +
             WEIGHTS["credit"]   * c +
             WEIGHTS["sector"]   * s)
    return round(score, 2), round(d, 2), round(c, 2), float(s)

def credit_rating(score: float) -> str:
        if   score > 8.0: return "AAA"
        elif score > 7.0: return "AA"
        elif score > 6.0: return "BBB"
        elif score > 5.0: return "B"
        else:             return "CCC"

scores = []
for ticker, bond in merged.iterrows():
    de  = bond["Debt/EBITDA"]
    cov = bond["Int. Coverage"]

    # Handle non-numeric values (N/A strings from UST rows)
    try:
        de  = float(de)
        cov = float(cov)
    except (ValueError, TypeError):
        de  = 0.0
        cov = 999.0

    comp, d_sc, c_sc, s_sc = composite_score(float(bond["Mod. Dur"]), de, cov, bond["Sector"])
    

    scores.append({
        "Ticker":           ticker,
        "Name":             bond["Name"],
        "Sector":           bond["Sector"],
        "Maturity":         bond["Maturity"],
        "Mod. Dur":         bond["Mod. Dur"],
        "Duration Score":   d_sc,
        "Credit Score":     c_sc,
        "Sector Score":     s_sc,
        "Composite Score":  comp,
        "Rating":          credit_rating(comp),  #personal credit rating
        "Verdict":         "BUY" if comp >= 7.0 else "HOLD" if comp >= 5.0 else "AVOID",
    })

scores_df = pd.DataFrame(scores).set_index("Ticker").sort_values("Composite Score", ascending=False)



print("═" * 75)
print(f"{'MACRO SCORING — Rates Steady/Higher | Spreads Widen | Energy Wins':^75}")
print("═" * 75)
print(scores_df[[
    "Name","Sector","Maturity","Duration Score",
    "Credit Score","Sector Score","Composite Score","Rating","Verdict"]].to_string())

print("\n── TOP 5 BUYS ───────────────────────────────────────────────────────────")
print(scores_df[scores_df["Verdict"] == "BUY"][["Name","Sector","Composite Score", "Rating"]].head(5).to_string())

print("\n── TOP 5 AVOIDS ─────────────────────────────────────────────────────────")
print(scores_df[scores_df["Verdict"] == "AVOID"][["Name","Sector","Composite Score", "Rating"]].tail(5).to_string())



# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────





# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
###GRAPHING
scores_df = scores_df.join(risk[["Convexity"]], how="left")
scores_df = scores_df.join(portfolio[["Debt/EBITDA", "Int. Coverage"]], how="left", rsuffix="_p")
 
# Force numeric
for col in ["Debt/EBITDA", "Int. Coverage", "Mod. Dur", "Convexity"]:
    scores_df[col] = pd.to_numeric(scores_df[col], errors="coerce")
 
# Drop UST bonds from corp charts (no leverage data)
corp = scores_df[scores_df["Sector"] != "Government"].copy()
 
# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
sns.set_theme(style="darkgrid")
 
SECTOR_COLORS = {
    "Industrials":  "#2563eb",
    "Energy":       "#dc2626",
    "Cons.Staples": "#16a34a",
    "Tech":         "#9333ea",
    "Government":   "#6b7280",
}
 
RATING_COLORS = {
    "AAA": "#15803d",
    "AA":  "#65a30d",
    "BBB": "#ca8a04",
    "B":   "#ea580c",
    "CCC": "#dc2626",
}
 
# FIGURE 1 — Horizontal Bar: Debt/EBITDA + Interest Coverage side by side
# ═════════════════════════════════════════════════════════════════════════════
fig1, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 11))
fig1.suptitle("Portfolio Credit Quality — Leverage & Interest Coverage",
              fontsize=14, fontweight="bold")
 
# Sort by Debt/EBITDA descending (worst at top)
de_sorted  = corp["Debt/EBITDA"].clip(-5, 20).sort_values(ascending=True)
cov_sorted = corp.loc[de_sorted.index, "Int. Coverage"].clip(0, 40)
 
colors_de  = [SECTOR_COLORS.get(corp.loc[t, "Sector"], "gray") for t in de_sorted.index]
colors_cov = ["#dc2626" if v < 3 else "#ca8a04" if v < 6 else "#16a34a"
              for v in cov_sorted]
 
# Left: Debt/EBITDA
ax1.barh(de_sorted.index, de_sorted.values, color=colors_de, edgecolor="none", height=0.6)
ax1.axvline(0,   color="white",  linewidth=0.8, linestyle="--", alpha=0.5)
ax1.axvline(3.5, color="#ca8a04", linewidth=1.0, linestyle="--", alpha=0.6,
            label="3.5x threshold")
ax1.set_xlabel("Debt / EBITDA  (clipped at 20x)", fontsize=10)
ax1.set_title("Leverage (Debt/EBITDA)", fontweight="bold")
ax1.legend(fontsize=8)
 
# Sector color legend
sector_patches = [mpatches.Patch(color=c, label=s) for s, c in SECTOR_COLORS.items()]
ax1.legend(handles=sector_patches, fontsize=8, title="Sector",
           title_fontsize=8, loc="lower right")
 
# Right: Interest Coverage
ax2.barh(cov_sorted.index, cov_sorted.values, color=colors_cov, edgecolor="none", height=0.6)
ax2.axvline(3, color="#ca8a04", linewidth=1.0, linestyle="--", alpha=0.6,
            label="3x min threshold")
ax2.axvline(6, color="#16a34a", linewidth=1.0, linestyle="--", alpha=0.6,
            label="6x healthy threshold")
ax2.set_xlabel("Interest Coverage (clipped at 40x)", fontsize=10)
ax2.set_title("Interest Coverage", fontweight="bold")
 
cov_patches = [
    mpatches.Patch(color="#dc2626", label="< 3x  Danger"),
    mpatches.Patch(color="#ca8a04", label="3–6x  Watch"),
    mpatches.Patch(color="#16a34a", label="> 6x  Healthy"),
]
ax2.legend(handles=cov_patches, fontsize=8, title="Coverage Zone",title_fontsize=8, loc="lower right")
 
plt.tight_layout()
plt.savefig("graph1_leverage_coverage.png", dpi=150, bbox_inches="tight")
plt.show()
 
 
# ═════════════════════════════════════════════════════════════════════════════
# FIGURE 2 — Heatmap: all scoring components + rating + verdict
# ═════════════════════════════════════════════════════════════════════════════
# Build heatmap data — numeric columns only
heatmap_cols = ["Duration Score", "Credit Score", "Sector Score", "Composite Score"]
hmap_data = corp[heatmap_cols].copy().round(2)
 
# Sort by composite score descending
hmap_data = hmap_data.sort_values("Composite Score", ascending=False)
 
# Add rating and verdict as text annotations per row
ratings  = scores_df.loc[hmap_data.index, "Rating"]
verdicts = scores_df.loc[hmap_data.index, "Verdict"]
row_labels = [
    f"{ticker}  [{ratings[ticker]}  {verdicts[ticker]}]"
    for ticker in hmap_data.index
]
 
fig_d, ax = plt.subplots(figsize=(16, 16))
 
cmap = mcolors.LinearSegmentedColormap.from_list(
    "rg", ["#dc2626", "#ca8a04", "#15803d"]
)
 
sns.heatmap(
    hmap_data,
    ax=ax,
    cmap=cmap,
    vmin=1, vmax=10,
    annot=True, fmt=".2f",
    annot_kws={"size": 8},
    linewidths=0.4,
    linecolor="#1e1e2e",
    yticklabels=row_labels,
    cbar_kws={"label": "Score (1=worst → 10=best)", "shrink": 0.4}
)
 
# Color the row tick labels by verdict
verdict_colors = {"BUY": "#15803d", "HOLD": "#ca8a04", "AVOID": "#dc2626"}
for tick, ticker in zip(ax.get_yticklabels(), hmap_data.index):
    v = verdicts[ticker]
    tick.set_color(verdict_colors.get(v, "white"))
    tick.set_fontsize(8.5)
 
ax.set_xticklabels(
    ["Duration\nScore", "Credit\nScore", "Sector\nScore", "Composite\nScore"],
    fontsize=10, rotation=0
)
ax.set_title("Full Scoring Heatmap\n"
             "Best Bonds under the assumption that rates will steady/hike ",
             fontsize=13, fontweight="bold", pad=15)
 
# Legend for verdict colors
verdict_patches = [
    mpatches.Patch(color="#15803d", label="BUY"),
    mpatches.Patch(color="#ca8a04", label="HOLD"),
    mpatches.Patch(color="#dc2626", label="AVOID"),
]
ax.legend(handles=verdict_patches, fontsize=9, title="Verdict",
          title_fontsize=9, loc="lower right",
          bbox_to_anchor=(1.18, 0), framealpha=0.3)
 
plt.tight_layout()
plt.savefig("graphD_heatmap.png", dpi=150, bbox_inches="tight")
plt.show()


# ═════════════════════════════════════════════════════════════════════════════
#FIGURE 3
MATURITY_MAP = {"2Y": 2, "5Y": 5, "10Y": 10, "30Y": 30}

pf = pd.DataFrame(rows).set_index("Ticker")
pf = pf.join(risk[["Price ($)", "Mod. Dur", "Convexity", "DV01 ($)"]], how="left")
fig1, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 11), sharex=False)
fig1.suptitle("Portfolio Risk Profile — DV01 & Convexity vs Yield",
              fontsize=14, fontweight="bold")
 
# ── Top: DV01 vs YTM ─────────────────────────────────────────────────────────
for sector, grp in pf.groupby("Sector"):
    ax1.scatter(
        grp["YTM (%)"], grp["DV01 ($)"].abs(),
        color=SECTOR_COLORS.get(sector, "gray"),
        s=60, alpha=0.70, edgecolors="white", linewidths=0.4,
        label=sector, zorder=3
    )
    for ticker, row in grp.iterrows():
        ax1.annotate(
            ticker,
            (row["YTM (%)"], abs(row["DV01 ($)"])),
            fontsize=7, color="black",
            xytext=(5, 4), textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.1", fc="white", alpha=0.35, lw=0),
            zorder=4
        )
 
ax1.set_xlabel("YTM (%)", fontsize=10)
ax1.set_ylabel("DV01 — Absolute ($)", fontsize=10)
ax1.set_title("DV01 vs Yield  |  Higher yield + high DV01 = most exposed under rate hikes",
              fontsize=10)
sector_patches = [mpatches.Patch(color=c, label=s) for s, c in SECTOR_COLORS.items()]
ax1.legend(handles=sector_patches, fontsize=8, title="Sector",
           title_fontsize=8, loc="upper right", framealpha=0.3)
 
# ── Bottom: Convexity vs YTM ──────────────────────────────────────────────────
for sector, grp in pf.groupby("Sector"):
    ax2.scatter(
        grp["YTM (%)"], grp["Convexity"],
        color=SECTOR_COLORS.get(sector, "gray"),
        s=60, alpha=0.70, edgecolors="white", linewidths=0.4,
        label=sector, zorder=3
    )
    for ticker, row in grp.iterrows():
        ax2.annotate(
            ticker,
            (row["YTM (%)"], row["Convexity"]),
            fontsize=7, color="black",
            xytext=(5, 4), textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.1", fc="white", alpha=0.35, lw=0),
            zorder=4
        )
 
ax2.set_xlabel("YTM (%)", fontsize=10)
ax2.set_ylabel("Convexity", fontsize=10)
ax2.set_title("Convexity vs Yield  |  Higher convexity = price gains accelerate if rates fall",
              fontsize=10)
ax2.legend(handles=sector_patches, fontsize=8, title="Sector",
           title_fontsize=8, loc="upper right", framealpha=0.3)
 
plt.tight_layout()
plt.savefig("graph_dv01_convexity_vs_yield.png", dpi=150, bbox_inches="tight")
plt.show()
 
 
# ═════════════════════════════════════════════════════════════════════════════
# FIGURE 4 — Portfolio Summary Heatmap + Aggregates panel
# ═════════════════════════════════════════════════════════════════════════════
 
# ═════════════════════════════════════════════════════════════════════════════
 
# ── Aggregate metrics (hardcoded reference values) ───────────────────────────
total_mv    = 36452.32
avg_md      = 6.994
avg_conv    = 66.3186
total_dv01  = -25.0984
var_95      = -1014.85
cvar_95     = -1314.39
 
# ── Heatmap data — numeric columns only ──────────────────────────────────────
hmap_cols = ["Coupon (%)", "Treasury (%)", "Spread (%)", "YTM (%)",
             "Debt/EBITDA", "Int. Coverage", "Mod. Dur", "Convexity"]
 
hmap_data  = pf[hmap_cols].copy()
hmap_data  = hmap_data.sort_values("YTM (%)", ascending=False)
 
# Normalise each column 0→1 for coloring (so different scales compare fairly)
hmap_norm  = hmap_data.apply(lambda col: (col - col.min()) / (col.max() - col.min() + 1e-9))
 
# Row labels: Ticker | Sector | Maturity
row_labels = [
    f"{ticker}  |  {pf.loc[ticker,'Sector']:<12}  |  {pf.loc[ticker,'Maturity']}"
    for ticker in hmap_data.index
]
 
# ── Build figure with heatmap + aggregate text panel ─────────────────────────
fig2 = plt.figure(figsize=(16, 20))
gs   = fig2.add_gridspec(1, 2, width_ratios=[3.2, 1], wspace=0.05)
 
ax_heat = fig2.add_subplot(gs[0])
ax_info = fig2.add_subplot(gs[1])
 
cmap = mcolors.LinearSegmentedColormap.from_list("rg", ["#dc2626", "#ca8a04", "#15803d"])
 
sns.heatmap(
    hmap_norm,
    ax=ax_heat,
    cmap=cmap,
    vmin=0, vmax=1,
    annot=hmap_data.round(2),   # show actual values, color by normalised
    fmt=".2f",
    annot_kws={"size": 7.5},
    linewidths=0.35,
    linecolor="#1e1e2e",
    yticklabels=row_labels,
    cbar_kws={"label": "Relative scale (green=high, red=low)", "shrink": 0.3}
)
 
ax_heat.set_xticklabels(
    ["Coupon\n(%)", "Treasury\n(%)", "Spread\n(%)", "YTM\n(%)",
     "Debt/\nEBITDA", "Int.\nCoverage", "Mod.\nDur", "Convexity"],
    fontsize=9, rotation=0, color="white"
)
ax_heat.tick_params(axis="y", labelsize=8, colors="white")
ax_heat.tick_params(axis="x", colors="white")
# Make the colorbar label/ticks readable on the dark background too
cbar = ax_heat.collections[0].colorbar
if cbar is not None:
    cbar.ax.yaxis.label.set_color("white")
    cbar.ax.tick_params(colors="white")
ax_heat.set_title("Full Portfolio — Bond Characteristics\n(sorted by YTM descending)",
                  fontsize=12, fontweight="bold", pad=12, color="white")
 
# ── Right panel: portfolio aggregates ────────────────────────────────────────
ax_info.axis("off")
 
agg_lines = [
    ("PORTFOLIO AGGREGATES", None, 14, "bold", "#ffffff"),
    ("", None, 9, "normal", "#ffffff"),
    ("Total Bonds",          f"{len(pf)}",                   10, "normal", "#d1d5db"),
    ("Total Market Value",   f"${total_mv:,.2f}",            10, "bold",   "#60a5fa"),
    ("Avg Modified Dur",     f"{avg_md:.3f} yrs",            10, "normal", "#d1d5db"),
    ("Avg Convexity",        f"{avg_conv:.2f}",              10, "normal", "#d1d5db"),
    ("Total DV01",           f"${total_dv01:.4f}",           10, "normal", "#d1d5db"),
    ("", None, 9, "normal", "#ffffff"),
    ("VAR & TAIL RISK", None, 12, "bold", "#ffffff"),
    ("", None, 9, "normal", "#ffffff"),
    ("1M VaR  (95%)",        f"${var_95:,.2f}",              10, "bold",   "#f87171"),
    ("1M CVaR (95%)",        f"${cvar_95:,.2f}",             10, "bold",   "#fca5a5"),
    ("", None, 9, "normal", "#ffffff"),
    ("SCENARIO P&L", None, 12, "bold", "#ffffff"),
    ("", None, 9, "normal", "#ffffff"),
]
 
# Add scenario P&L for key shocks
shifts = [("Fed +25bps", 0.25), ("Fed +50bps", 0.50),
          ("Fed +100bps", 1.00), ("Fed -50bps", -0.50)]
for label, dy in shifts:
    pl = sum(
        bond_price(r["Face Value"], r["Coupon (%)"], r["YTM (%)"] + dy,
                   MATURITY_MAP[r["Maturity"]])
        - bond_price(r["Face Value"], r["Coupon (%)"], r["YTM (%)"],
                     MATURITY_MAP[r["Maturity"]])
        for _, r in pf.iterrows()
    )
    color = "#f87171" if pl < 0 else "#86efac"
    agg_lines.append((label, f"${pl:,.2f}", 10, "normal", color))
 
y_pos = 0.98
for item in agg_lines:
    label, value, size, weight, color = item
    if value is None:
        ax_info.text(0.05, y_pos, label, transform=ax_info.transAxes,
                     fontsize=size, fontweight=weight, color=color, va="top")
    else:
        ax_info.text(0.05, y_pos, label, transform=ax_info.transAxes,
                     fontsize=size, color="#9ca3af", va="top")
        ax_info.text(0.95, y_pos, value, transform=ax_info.transAxes,
                     fontsize=size, fontweight=weight, color=color, va="top", ha="right")
    y_pos -= 0.032
 
ax_info.set_facecolor("#111827")
fig2.patch.set_facecolor("#111827")
ax_heat.set_facecolor("#111827")
 
fig2.suptitle("Portfolio Summary Dashboard", fontsize=15,
              fontweight="bold", color="white", y=1.005)
 
plt.savefig("graph_portfolio_summary.png", dpi=150, bbox_inches="tight",
            facecolor="#111827")
plt.show()