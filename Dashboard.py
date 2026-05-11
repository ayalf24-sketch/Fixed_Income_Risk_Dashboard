"""
Fixed Income Portfolio Dashboard
================================
Visualizes portfolio summary, treasury yield curves (historical + current),
and scenario testing (parallel shifts, steepener / flattener, custom tenor bumps)
with live P&L recompute.

How to run
----------
    pip install -r requirements.txt
    streamlit run dashboard.py

Place these alongside the script so the dashboard finds them:
    - historical_yield_curve.png
    - current_yield_curve.png
(If missing, the dashboard offers an in-app uploader.)
"""

import ssl
import certifi
ssl._create_default_https_context = lambda: ssl.create_default_context(cafile=certifi.where())

import time
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from fredapi import Fred
import yfinance as yf

# ─────────────────────────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Fixed Income Portfolio Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

SCRIPT_DIR = Path(__file__).parent if "__file__" in globals() else Path.cwd()

# ─────────────────────────────────────────────────────────────────────────────
# Bond math (lifted from mockPortfolio.py)
# ─────────────────────────────────────────────────────────────────────────────
MATURITY_MAP = {"2Y": 2, "5Y": 5, "10Y": 10, "30Y": 30}


def bond_price(face, coupon_rate, ytm, periods):
    c = (coupon_rate / 100) * face / 2
    y = ytm / 100 / 2
    n = periods * 2
    if abs(y) < 1e-12:
        return c * n + face
    pv_coupons = c * (1 - (1 + y) ** -n) / y
    pv_face = face / (1 + y) ** n
    return pv_coupons + pv_face


def macaulay_duration(face, coupon_rate, ytm, periods):
    c = (coupon_rate / 100) * face / 2
    y = ytm / 100 / 2
    n = periods * 2
    price = bond_price(face, coupon_rate, ytm, periods)
    weighted = sum((t / 2) * (c / (1 + y) ** t) for t in range(1, n)) \
        + (n / 2) * ((c + face) / (1 + y) ** n)
    return weighted / price


def convexity(face, coupon_rate, ytm, periods):
    c = (coupon_rate / 100) * face / 2
    y = ytm / 100 / 2
    n = periods * 2
    price = bond_price(face, coupon_rate, ytm, periods)
    conv = sum((t * (t + 1)) * (c / (1 + y) ** (t + 2)) for t in range(1, n)) \
        + (n * (n + 1)) * ((c + face) / (1 + y) ** (n + 2))
    return conv / (price * 4)


def credit_spread(debt_ebitda: float, int_cov: float) -> float:
    if np.isnan(debt_ebitda) or np.isnan(int_cov):
        return 1.00
    if debt_ebitda < 1.0:   lev = 0.40
    elif debt_ebitda < 2.0: lev = 0.65
    elif debt_ebitda < 3.5: lev = 1.00
    elif debt_ebitda < 5.0: lev = 1.75
    elif debt_ebitda < 7.0: lev = 2.75
    else:                   lev = 4.50
    if int_cov > 10:  cov = -0.10
    elif int_cov > 5: cov = 0.00
    elif int_cov > 3: cov = 0.25
    elif int_cov > 1.5: cov = 0.75
    else:               cov = 1.50
    return round(lev + cov, 3)


def get_financials(ticker: str):
    try:
        tk = yf.Ticker(ticker)
        info = tk.info
        fin = tk.financials
        total_debt = info.get("totalDebt", np.nan)
        ebitda = info.get("ebitda", np.nan)
        try:
            ebit = fin.loc["EBIT"].iloc[0]
            int_exp = fin.loc["Interest Expense"].iloc[0]
            int_cov = ebit / abs(int_exp) if ebit and int_exp != 0 else np.nan
        except Exception:
            int_cov = np.nan
        de = total_debt / ebitda if total_debt and ebitda != 0 else np.nan
        return {"debt_ebitda": de, "int_cov": int_cov}
    except Exception:
        return {"debt_ebitda": np.nan, "int_cov": np.nan}


# ─────────────────────────────────────────────────────────────────────────────
# Portfolio universe (mirrors mockPortfolio.py)
# ─────────────────────────────────────────────────────────────────────────────
COMPANIES = {
    # Industrials (Strong)
    "CAT":  {"name": "Caterpillar",       "sector": "Industrials",  "maturity": "10Y", "coupon": 3.80, "face": 1000},
    "HON":  {"name": "Honeywell",         "sector": "Industrials",  "maturity": "10Y", "coupon": 3.35, "face": 1000},
    "LMT":  {"name": "Lockheed Martin",   "sector": "Industrials",  "maturity": "10Y", "coupon": 3.55, "face": 1000},
    "RTX":  {"name": "Raytheon",          "sector": "Industrials",  "maturity": "10Y", "coupon": 3.95, "face": 1000},
    "GE":   {"name": "GE Aerospace",      "sector": "Industrials",  "maturity": "10Y", "coupon": 4.10, "face": 1000},
    "UPS":  {"name": "UPS",               "sector": "Industrials",  "maturity": "10Y", "coupon": 3.40, "face": 1000},
    "MMM":  {"name": "3M",                "sector": "Industrials",  "maturity": "10Y", "coupon": 3.70, "face": 1000},
    # Industrials (Distressed)
    "BA":   {"name": "Boeing",            "sector": "Industrials",  "maturity": "10Y", "coupon": 5.71, "face": 1000},
    "ALK":  {"name": "Alaska Air",        "sector": "Industrials",  "maturity": "5Y",  "coupon": 4.80, "face": 1000},
    "R":    {"name": "Ryder System",      "sector": "Industrials",  "maturity": "5Y",  "coupon": 4.63, "face": 1000},
    # Energy (Strong)
    "XOM":  {"name": "ExxonMobil",        "sector": "Energy",       "maturity": "10Y", "coupon": 3.68, "face": 1000},
    "CVX":  {"name": "Chevron",           "sector": "Energy",       "maturity": "10Y", "coupon": 3.08, "face": 1000},
    "COP":  {"name": "ConocoPhillips",    "sector": "Energy",       "maturity": "10Y", "coupon": 4.15, "face": 1000},
    "SLB":  {"name": "SLB",               "sector": "Energy",       "maturity": "5Y",  "coupon": 4.00, "face": 1000},
    "PSX":  {"name": "Phillips 66",       "sector": "Energy",       "maturity": "5Y",  "coupon": 4.65, "face": 1000},
    # Energy (Distressed)
    "OXY":  {"name": "Occidental",        "sector": "Energy",       "maturity": "10Y", "coupon": 6.63, "face": 1000},
    "HAL":  {"name": "Halliburton",       "sector": "Energy",       "maturity": "10Y", "coupon": 4.85, "face": 1000},
    "AR":   {"name": "Antero Resources",  "sector": "Energy",       "maturity": "5Y",  "coupon": 7.63, "face": 1000},
    # Consumer Staples (Strong)
    "PG":   {"name": "Procter & Gamble",  "sector": "Cons.Staples", "maturity": "10Y", "coupon": 3.00, "face": 1000},
    "KO":   {"name": "Coca-Cola",         "sector": "Cons.Staples", "maturity": "10Y", "coupon": 3.45, "face": 1000},
    "PEP":  {"name": "PepsiCo",           "sector": "Cons.Staples", "maturity": "10Y", "coupon": 3.50, "face": 1000},
    "CL":   {"name": "Colgate-Palmolive", "sector": "Cons.Staples", "maturity": "10Y", "coupon": 3.10, "face": 1000},
    "GIS":  {"name": "General Mills",     "sector": "Cons.Staples", "maturity": "5Y",  "coupon": 4.20, "face": 1000},
    # Consumer Staples (Struggling)
    "KHC":  {"name": "Kraft Heinz",       "sector": "Cons.Staples", "maturity": "10Y", "coupon": 5.00, "face": 1000},
    "WBA":  {"name": "Walgreens",         "sector": "Cons.Staples", "maturity": "5Y",  "coupon": 8.13, "face": 1000},
    "MO":   {"name": "Altria",            "sector": "Cons.Staples", "maturity": "10Y", "coupon": 5.80, "face": 1000},
    # Tech (Strong)
    "MSFT": {"name": "Microsoft",         "sector": "Tech",         "maturity": "10Y", "coupon": 3.45, "face": 1000},
    "GOOGL":{"name": "Alphabet",          "sector": "Tech",         "maturity": "10Y", "coupon": 2.25, "face": 1000},
    "CSCO": {"name": "Cisco",             "sector": "Tech",         "maturity": "10Y", "coupon": 3.50, "face": 1000},
    "IBM":  {"name": "IBM",               "sector": "Tech",         "maturity": "10Y", "coupon": 4.15, "face": 1000},
    "ORCL": {"name": "Oracle",            "sector": "Tech",         "maturity": "10Y", "coupon": 4.65, "face": 1000},
    # Tech (Leveraged / Declining)
    "HPE":  {"name": "HP Enterprise",     "sector": "Tech",         "maturity": "5Y",  "coupon": 4.45, "face": 1000},
    "INTC": {"name": "Intel",             "sector": "Tech",         "maturity": "10Y", "coupon": 5.05, "face": 1000},
    "PARA": {"name": "Paramount",         "sector": "Tech",         "maturity": "5Y",  "coupon": 6.38, "face": 1000},
    "DISH": {"name": "DISH/EchoStar",     "sector": "Tech",         "maturity": "5Y",  "coupon": 11.75,"face": 1000},
}

FRED_SERIES = {"2Y": "DGS2", "5Y": "DGS5", "10Y": "DGS10", "30Y": "DGS30"}
FRED_API_KEY = "5e0c5fb26762b84a6b8eb806511522fe"


# ─────────────────────────────────────────────────────────────────────────────
# Data loaders (cached)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=24 * 3600, show_spinner=False)
def fetch_treasury():
    fred = Fred(api_key=FRED_API_KEY)
    return {name: float(fred.get_series(sid).dropna().iloc[-1])
            for name, sid in FRED_SERIES.items()}


@st.cache_data(ttl=24 * 3600, show_spinner=False)
def build_portfolio():
    treasury = fetch_treasury()
    rows = []
    bar = st.progress(0.0, text="Pulling company financials from Yahoo Finance…")
    items = list(COMPANIES.items())
    for i, (ticker, meta) in enumerate(items):
        bar.progress((i + 1) / len(items), text=f"{i+1}/{len(items)}  {ticker}")
        fins = get_financials(ticker)
        spd = credit_spread(fins["debt_ebitda"], fins["int_cov"])
        tsy = treasury[meta["maturity"]]
        ytm = round(tsy + spd, 4)
        rows.append({
            "Ticker": ticker, "Name": meta["name"], "Sector": meta["sector"],
            "Maturity": meta["maturity"], "Coupon (%)": meta["coupon"],
            "Face Value": meta["face"], "Treasury (%)": round(tsy, 3),
            "Debt/EBITDA": round(fins["debt_ebitda"], 2) if not np.isnan(fins["debt_ebitda"]) else np.nan,
            "Int. Coverage": round(fins["int_cov"], 2) if not np.isnan(fins["int_cov"]) else np.nan,
            "Spread (%)": spd, "YTM (%)": ytm,
        })
        time.sleep(0.15)
    bar.empty()
    df = pd.DataFrame(rows).set_index("Ticker")

    # Add risk-free US Treasury bonds
    for mat, ytm in treasury.items():
        df.loc[f"UST_{mat}"] = {
            "Name": f"US Treasury {mat}", "Sector": "Government", "Maturity": mat,
            "Coupon (%)": round(ytm, 2), "Face Value": 1000, "Treasury (%)": round(ytm, 2),
            "Debt/EBITDA": 0.0, "Int. Coverage": 999.0, "Spread (%)": 0.00, "YTM (%)": round(ytm, 2),
        }
    return df, treasury


def compute_risk(portfolio: pd.DataFrame) -> pd.DataFrame:
    out = []
    for tk, row in portfolio.iterrows():
        T = MATURITY_MAP[row["Maturity"]]
        face, cpn, ytm = row["Face Value"], row["Coupon (%)"], row["YTM (%)"]
        price = bond_price(face, cpn, ytm, T)
        mac = macaulay_duration(face, cpn, ytm, T)
        mod = mac / (1 + ytm / 100 / 2)
        cvx = convexity(face, cpn, ytm, T)
        dv01 = -mod * price * 0.0001
        out.append({
            "Ticker": tk, "Name": row["Name"], "Sector": row["Sector"], "Maturity": row["Maturity"],
            "Price ($)": price, "Mac. Dur": mac, "Mod. Dur": mod,
            "Convexity": cvx, "DV01 ($)": dv01,
        })
    return pd.DataFrame(out).set_index("Ticker")


# ─────────────────────────────────────────────────────────────────────────────
# Scenario engine
# ─────────────────────────────────────────────────────────────────────────────
def apply_scenario(portfolio: pd.DataFrame, parallel_bp: float,
                   slope_bp: float, custom_bumps: dict):
    """
    parallel_bp   : parallel shift, applied to every tenor
    slope_bp      : steepener-style tilt, anchored at 5Y
                    +slope ⇒ steepener (long-end up, short-end down)
                    -slope ⇒ flattener
    custom_bumps  : extra per-tenor bps {2Y, 5Y, 10Y, 30Y}
    Returns (DataFrame of bond-level results, dict of tenor shifts in bps)
    """
    # Anchored at 5Y; coefficients chosen so |coef| = 1 at the wings
    slope_coef = {"2Y": -1.0, "5Y": -0.33, "10Y": 0.33, "30Y": 1.0}
    shifts_bp = {
        t: parallel_bp + slope_coef[t] * slope_bp + custom_bumps.get(t, 0)
        for t in ["2Y", "5Y", "10Y", "30Y"]
    }

    rows = []
    for tk, row in portfolio.iterrows():
        mat = row["Maturity"]
        T = MATURITY_MAP[mat]
        face, cpn = row["Face Value"], row["Coupon (%)"]
        old_ytm = row["YTM (%)"]
        new_ytm = old_ytm + shifts_bp[mat] / 100  # bps → %
        p0 = bond_price(face, cpn, old_ytm, T)
        p1 = bond_price(face, cpn, new_ytm, T)
        pnl = p1 - p0
        rows.append({
            "Ticker": tk, "Name": row["Name"], "Sector": row["Sector"],
            "Maturity": mat, "Coupon (%)": cpn,
            "Old YTM (%)": old_ytm, "Shock (bps)": shifts_bp[mat],
            "New YTM (%)": new_ytm,
            "Base Price ($)": p0, "New Price ($)": p1,
            "P&L ($)": pnl, "P&L (%)": pnl / p0 * 100,
        })
    return pd.DataFrame(rows).set_index("Ticker"), shifts_bp


# ─────────────────────────────────────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────────────────────────────────────
st.title("📊 Fixed Income Portfolio Dashboard")
st.caption("Treasury exposure, scenario testing, and live P&L across the curve.")

# Load data
try:
    portfolio, treasury = build_portfolio()
    risk = compute_risk(portfolio)
except Exception as exc:
    st.error(f"Failed to load portfolio data: {exc}")
    st.stop()

# ── Sidebar: scenario controls ──────────────────────────────────────────────
st.sidebar.header("🎛️ Scenario Controls")

preset = st.sidebar.radio(
    "Preset Scenario",
    [
        "Custom",
        "+25 bps parallel",
        "+100 bps parallel",
        "Bear Steepener (long ↑)",
        "Bull Flattener (long ↓)",
    ],
    index=0,
)

if preset == "+25 bps parallel":
    p_def, s_def = 25, 0
elif preset == "+100 bps parallel":
    p_def, s_def = 100, 0
elif preset == "Bear Steepener (long ↑)":
    p_def, s_def = 25, 50
elif preset == "Bull Flattener (long ↓)":
    p_def, s_def = -25, -50
else:
    p_def, s_def = 0, 0

parallel = st.sidebar.slider(
    "Parallel shift (bps)", min_value=-300, max_value=300, value=p_def, step=5,
    help="Shifts every point on the curve by the same amount.",
)
slope = st.sidebar.slider(
    "Steepener / Flattener (bps)", min_value=-150, max_value=150, value=s_def, step=5,
    help="Positive ⇒ steepener (30Y +X, 2Y −X). Negative ⇒ flattener.",
)

with st.sidebar.expander("Custom tenor bumps (on top of above)"):
    custom_bumps = {
        "2Y":  st.slider("Extra 2Y (bps)",  -200, 200, 0, step=5),
        "5Y":  st.slider("Extra 5Y (bps)",  -200, 200, 0, step=5),
        "10Y": st.slider("Extra 10Y (bps)", -200, 200, 0, step=5),
        "30Y": st.slider("Extra 30Y (bps)", -200, 200, 0, step=5),
    }

st.sidebar.divider()
if st.sidebar.button("🔄 Refresh market data"):
    fetch_treasury.clear()
    build_portfolio.clear()
    st.rerun()

# ── Compute scenario ────────────────────────────────────────────────────────
scenario, tenor_shifts = apply_scenario(portfolio, parallel, slope, custom_bumps)

# ── KPI bar ─────────────────────────────────────────────────────────────────
mv_base = scenario["Base Price ($)"].sum()
mv_new = scenario["New Price ($)"].sum()
pnl_total = mv_new - mv_base
pnl_pct = pnl_total / mv_base * 100
avg_mod_dur = risk["Mod. Dur"].mean()
port_dv01 = risk["DV01 ($)"].sum()

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Base Market Value", f"${mv_base:,.0f}")
k2.metric("Scenario MV", f"${mv_new:,.0f}", delta=f"${pnl_total:,.0f}")
k3.metric("Total P&L", f"${pnl_total:,.0f}", delta=f"{pnl_pct:+.2f}%")
k4.metric("Avg Mod. Duration", f"{avg_mod_dur:.2f} yrs")
k5.metric("Portfolio DV01", f"${port_dv01:,.2f}", help="$ change per +1bp parallel move")

# ── Tabs ────────────────────────────────────────────────────────────────────
tab_curve, tab_pnl, tab_port, tab_shock = st.tabs(
    ["📈 Yield Curves", "🎯 Scenario P&L", "📋 Portfolio & Risk", "🔍 Curve Detail"]
)

# Tab 1 — Yield curve images
with tab_curve:
    st.subheader("Yield Curve Charts")
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("**Historical Yield Curve (2010 – Present)**")
        hist_local = SCRIPT_DIR / "historical_yield_curve.png"
        if hist_local.exists():
            st.image(str(hist_local), use_container_width=True)
        else:
            up = st.file_uploader("Upload historical chart PNG", type=["png", "jpg", "jpeg"], key="hist_up")
            if up:
                st.image(up, use_container_width=True)
            else:
                st.info("Place `historical_yield_curve.png` next to this script, or upload it above.")

    with c2:
        st.markdown("**Current Treasury Yield Curve**")
        curr_local = SCRIPT_DIR / "current_yield_curve.png"
        if curr_local.exists():
            st.image(str(curr_local), use_container_width=True)
        else:
            up = st.file_uploader("Upload current chart PNG", type=["png", "jpg", "jpeg"], key="curr_up")
            if up:
                st.image(up, use_container_width=True)
            else:
                st.info("Place `current_yield_curve.png` next to this script, or upload it above.")

    st.divider()
    st.markdown("**Live Curve (FRED) — Base vs Scenario**")
    curve_df = pd.DataFrame({
        "Tenor": ["2Y", "5Y", "10Y", "30Y"],
        "Base":  [treasury[t] for t in ["2Y", "5Y", "10Y", "30Y"]],
        "Scenario": [treasury[t] + tenor_shifts[t] / 100 for t in ["2Y", "5Y", "10Y", "30Y"]],
    })
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=curve_df["Tenor"], y=curve_df["Base"],
                             name="Base", mode="lines+markers", line=dict(width=3)))
    fig.add_trace(go.Scatter(x=curve_df["Tenor"], y=curve_df["Scenario"],
                             name="Scenario", mode="lines+markers",
                             line=dict(width=3, dash="dash")))
    fig.update_layout(xaxis_title="Tenor", yaxis_title="Yield (%)", height=380,
                      legend=dict(orientation="h"))
    st.plotly_chart(fig, use_container_width=True)

# Tab 2 — Scenario P&L
with tab_pnl:
    st.subheader("P&L Impact (Scenario − Base)")

    pnl_sorted = scenario.sort_values("P&L ($)")
    fig = px.bar(
        pnl_sorted.reset_index(),
        x="Ticker", y="P&L ($)", color="Sector",
        hover_data=["Name", "Maturity", "P&L (%)", "Shock (bps)"],
        title="P&L by Bond",
    )
    fig.update_layout(height=480, xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        sec = scenario.groupby("Sector")["P&L ($)"].sum().reset_index().sort_values("P&L ($)")
        f2 = px.bar(sec, x="Sector", y="P&L ($)", color="P&L ($)",
                    color_continuous_scale="RdYlGn", title="P&L by Sector")
        f2.update_layout(height=380, coloraxis_showscale=False)
        st.plotly_chart(f2, use_container_width=True)
    with c2:
        mat = scenario.groupby("Maturity")["P&L ($)"].sum() \
                      .reindex(["2Y", "5Y", "10Y", "30Y"]).reset_index()
        f3 = px.bar(mat, x="Maturity", y="P&L ($)", color="P&L ($)",
                    color_continuous_scale="RdYlGn", title="P&L by Maturity Bucket")
        f3.update_layout(height=380, coloraxis_showscale=False)
        st.plotly_chart(f3, use_container_width=True)

    st.subheader("Bond-Level Detail")
    show_cols = ["Name", "Sector", "Maturity", "Coupon (%)", "Old YTM (%)",
                 "Shock (bps)", "New YTM (%)", "Base Price ($)", "New Price ($)",
                 "P&L ($)", "P&L (%)"]
    st.dataframe(
        scenario[show_cols].style.format({
            "Coupon (%)":     "{:.2f}",
            "Old YTM (%)":    "{:.3f}",
            "New YTM (%)":    "{:.3f}",
            "Shock (bps)":    "{:+.0f}",
            "Base Price ($)": "${:,.2f}",
            "New Price ($)":  "${:,.2f}",
            "P&L ($)":        "${:+,.2f}",
            "P&L (%)":        "{:+.3f}%",
        }).background_gradient(subset=["P&L ($)"], cmap="RdYlGn"),
        use_container_width=True, height=480,
    )

# Tab 3 — Portfolio & Risk
with tab_port:
    st.subheader("🏦 Portfolio")
    st.dataframe(portfolio, use_container_width=True, height=460)

    st.subheader("Risk Metrics")
    st.dataframe(
        risk.style.format({
            "Price ($)": "${:,.2f}",
            "Mac. Dur":  "{:.3f}",
            "Mod. Dur":  "{:.3f}",
            "Convexity": "{:.4f}",
            "DV01 ($)":  "${:.4f}",
        }),
        use_container_width=True, height=400,
    )

    c1, c2 = st.columns(2)
    with c1:
        sec_alloc = risk.assign(MV=risk["Price ($)"]) \
                        .groupby("Sector")["MV"].sum().reset_index()
        f = px.pie(sec_alloc, values="MV", names="Sector",
                   title="Sector Allocation by Market Value", hole=0.4)
        st.plotly_chart(f, use_container_width=True)
    with c2:
        mat_alloc = risk.assign(MV=risk["Price ($)"]) \
                        .groupby("Maturity")["MV"].sum() \
                        .reindex(["2Y", "5Y", "10Y", "30Y"]).reset_index()
        f = px.pie(mat_alloc, values="MV", names="Maturity",
                   title="Maturity Allocation by Market Value", hole=0.4)
        st.plotly_chart(f, use_container_width=True)

# Tab 4 — Curve detail
with tab_shock:
    st.subheader("Per-Tenor Shocks Applied")
    rows = [
        {"Tenor": t,
         "Base Yield (%)": treasury[t],
         "Shock (bps)": tenor_shifts[t],
         "New Yield (%)": treasury[t] + tenor_shifts[t] / 100}
        for t in ["2Y", "5Y", "10Y", "30Y"]
    ]
    shock_df = pd.DataFrame(rows)
    st.dataframe(
        shock_df.style.format({
            "Base Yield (%)": "{:.3f}",
            "Shock (bps)":    "{:+.0f}",
            "New Yield (%)":  "{:.3f}",
        }),
        use_container_width=True,
    )

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=shock_df["Tenor"], y=shock_df["Base Yield (%)"],
                             name="Base Curve", mode="lines+markers",
                             marker=dict(size=12), line=dict(width=3)))
    fig.add_trace(go.Scatter(x=shock_df["Tenor"], y=shock_df["New Yield (%)"],
                             name="Scenario Curve", mode="lines+markers",
                             marker=dict(size=12, symbol="diamond"),
                             line=dict(width=3, dash="dash")))
    fig.update_layout(title="Yield Curve: Base vs Scenario",
                      xaxis_title="Tenor", yaxis_title="Yield (%)", height=480)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        "**Scenario summary**  •  "
        f"Parallel: **{parallel:+d} bps**  •  "
        f"Slope (steep/flat): **{slope:+d} bps**  •  "
        f"Total P&L: **${pnl_total:+,.0f} ({pnl_pct:+.2f}%)**"
    )

st.caption("Built with Streamlit  •  Data: FRED + Yahoo Finance  •  Bond math from mockPortfolio.py")