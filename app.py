# ============================================================
# ValuEngine - Monte Carlo DCF Valuation Model
# Built by Pavas Kaushal
# MBA Finance | TMT Strategy Consultant
# Powered by live financial data via yfinance
# ============================================================

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy import stats
import yfinance as yf

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="ValuEngine | Monte Carlo DCF",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
    <style>
    .main { background-color: #0f1117; }
    .kpi-card {
        background-color: #1e2130;
        border-radius: 10px;
        padding: 20px;
        border-left: 4px solid #00b4d8;
    }
    .kpi-value {
        font-size: 28px;
        font-weight: bold;
        color: #00b4d8;
    }
    .kpi-label {
        font-size: 14px;
        color: #8b8fa8;
        margin-bottom: 8px;
    }
    .section-header {
        font-size: 20px;
        font-weight: bold;
        color: #ffffff;
        padding: 10px 0;
        border-bottom: 2px solid #00b4d8;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================
# FETCH LIVE DATA FROM YAHOO FINANCE
# ============================================================

@st.cache_data(ttl=3600)
def fetch_company_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        financials = stock.financials

        current_price = info.get("currentPrice", 0)
        shares = info.get("sharesOutstanding", 0) / 1e6

        if financials is not None and not financials.empty:
            if "Total Revenue" in financials.index:
                revenue = financials.loc["Total Revenue"].iloc[0] / 1e6
            else:
                revenue = info.get("totalRevenue", 0) / 1e6
        else:
            revenue = info.get("totalRevenue", 0) / 1e6

        if financials is not None and not financials.empty:
            if "EBIT" in financials.index:
                ebit = financials.loc["EBIT"].iloc[0] / 1e6
            else:
                ebit = info.get("ebit", 0) / 1e6
        else:
            ebit = info.get("ebit", 0) / 1e6

        ebit_margin = (ebit / revenue * 100) if revenue > 0 else 15.0
        total_debt = info.get("totalDebt", 0) / 1e6
        cash = info.get("totalCash", 0) / 1e6
        net_debt = total_debt - cash
        market_cap = info.get("marketCap", 0) / 1e6
        company_name = info.get("longName", ticker)

        # Auto detect currency
        currency = info.get("currency", "USD")
        if currency == "INR":
            currency_symbol = "\u20b9"
            unit_label = "Millions (INR)"
        elif currency == "GBP":
            currency_symbol = "\u00a3"
            unit_label = "Millions (GBP)"
        elif currency == "EUR":
            currency_symbol = "\u20ac"
            unit_label = "Millions (EUR)"
        else:
            currency_symbol = "$"
            unit_label = "Millions (USD)"

        return {
            "current_price": current_price,
            "shares": shares,
            "revenue": revenue,
            "ebit_margin": max(1, min(50, ebit_margin)),
            "net_debt": net_debt,
            "market_cap": market_cap,
            "company_name": company_name,
            "currency": currency,
            "currency_symbol": currency_symbol,
            "unit_label": unit_label,
            "success": True
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# ============================================================
# DASHBOARD HEADER
# ============================================================

st.markdown("""
    <div style='text-align: center; padding: 20px 0;'>
        <h1 style='color: #00b4d8; font-size: 42px; font-weight: bold;'>
            📈 ValuEngine
        </h1>
        <p style='color: #8b8fa8; font-size: 18px;'>
            Stochastic DCF Valuation & Monte Carlo Risk Simulation
        </p>
        <p style='color: #8b8fa8; font-size: 14px;'>
            Private Equity | Investment Banking | TMT Sector
        </p>
        <p style='color: #ffffff; font-size: 15px; margin-top: 10px;'>
            Built by <span style='color: #00b4d8; font-weight: bold;'>
            Pavas Kaushal</span> · MBA Finance · TMT Strategy
        </p>
    </div>
""", unsafe_allow_html=True)

st.divider()

# ============================================================
# SIDEBAR — COMPANY SELECTION
# ============================================================

st.sidebar.markdown("## ⚙️ Model Assumptions")
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 Company Selection")

ticker_input = st.sidebar.text_input(
    "Enter Ticker Symbol",
    value="RELIANCE.NS",
    help="NSE: RELIANCE.NS, TCS.NS | US: AAPL, MSFT | UK: HSBA.L"
)

load_button = st.sidebar.button("🔄 Load Live Data")

# ============================================================
# LOAD DATA INTO SESSION STATE
# ============================================================

if "company_data" not in st.session_state:
    st.session_state.company_data = fetch_company_data("RELIANCE.NS")

if load_button:
    with st.spinner("Fetching live data..."):
        st.session_state.company_data = fetch_company_data(ticker_input)

# Assign data BEFORE using it
data = st.session_state.company_data

if not data["success"]:
    st.warning("Live data fetch failed. Loading Reliance Industries demo data.")
    data = {
        "current_price": 1352.0,
        "shares": 6766.0,
        "revenue": 975000.0,
        "ebit_margin": 15.0,
        "net_debt": 100000.0,
        "market_cap": 1800000.0,
        "company_name": "Reliance Industries Limited",
        "currency": "INR",
        "currency_symbol": "\u20b9",
        "unit_label": "Millions (INR)",
        "success": True
    }

currency_symbol = data.get("currency_symbol", "$")
unit_label = data.get("unit_label", "Millions")

st.sidebar.success("✅ " + data["company_name"])

# ============================================================
# SIDEBAR — MODEL INPUTS
# ============================================================

st.sidebar.markdown("### 🏢 Company Profile")

current_share_price = st.sidebar.number_input(
    "Current Share Price (" + currency_symbol + ")",
    value=float(round(data["current_price"], 2)),
    step=1.0
)

shares_outstanding = st.sidebar.number_input(
    "Shares Outstanding (Millions)",
    value=float(round(data["shares"], 2)),
    step=1.0
)

net_debt = st.sidebar.number_input(
    "Net Debt (" + currency_symbol + " Millions)",
    value=float(round(data["net_debt"], 2)),
    step=100.0
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Financial Assumptions")

base_revenue = st.sidebar.number_input(
    "Base Revenue (" + currency_symbol + " Millions)",
    value=float(round(data["revenue"], 2)),
    step=1000.0
)

ebit_margin = st.sidebar.slider(
    "EBIT Margin %", 1, 50,
    value=int(round(data["ebit_margin"]))
)

tax_rate = st.sidebar.slider("Tax Rate %", 1, 40, 25)
da_pct = st.sidebar.slider("D&A as % of Revenue", 1, 20, 5)
capex_pct = st.sidebar.slider("CapEx as % of Revenue", 1, 30, 10)
nwc_pct = st.sidebar.slider("Change in NWC as % of Revenue", 1, 10, 2)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎲 Monte Carlo Parameters")

st.sidebar.markdown("**Revenue Growth Rate**")
rev_growth_mean = st.sidebar.slider("Mean Growth %", 1, 30, 12)
rev_growth_std = st.sidebar.slider("Std Dev %", 1, 15, 4)

st.sidebar.markdown("**WACC**")
wacc_low = st.sidebar.slider("WACC Low %", 1, 15, 9)
wacc_mid = st.sidebar.slider("WACC Mid %", 1, 20, 12)
wacc_high = st.sidebar.slider("WACC High %", 1, 25, 16)

st.sidebar.markdown("**Terminal Growth Rate**")
tgr_mean = st.sidebar.slider("Terminal Growth Mean %", 1, 10, 5)
tgr_std = st.sidebar.slider("Terminal Growth Std Dev %", 1, 5, 1)

num_simulations = st.sidebar.selectbox(
    "Simulations",
    options=[1000, 5000, 10000],
    index=2
)

st.sidebar.markdown("---")
st.sidebar.markdown("""
    <p style='color: #8b8fa8; font-size: 11px; text-align: center;'>
        Data: Yahoo Finance · Live prices<br>
        ValuEngine © 2024 · Pavas Kaushal
    </p>
""", unsafe_allow_html=True)

# ============================================================
# COMPANY SNAPSHOT
# ============================================================

st.markdown("<div class='section-header'>🏢 Company Snapshot</div>",
    unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(
        "<div class='kpi-card'>"
        "<div class='kpi-label'>Company</div>"
        "<div class='kpi-value' style='font-size:18px;'>"
        + data["company_name"] + "</div>"
        "<div style='color: #8b8fa8; font-size: 12px;'>" + ticker_input + "</div>"
        "</div>",
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        "<div class='kpi-card'>"
        "<div class='kpi-label'>Live Share Price</div>"
        "<div class='kpi-value'>"
        + currency_symbol + f"{data['current_price']:,.2f}" + "</div>"
        "<div style='color: #8b8fa8; font-size: 12px;'>Live · Yahoo Finance</div>"
        "</div>",
        unsafe_allow_html=True
    )

with col3:
    st.markdown(
        "<div class='kpi-card'>"
        "<div class='kpi-label'>Market Cap</div>"
        "<div class='kpi-value'>"
        + currency_symbol + f"{data['market_cap']:,.0f}M" + "</div>"
        "<div style='color: #8b8fa8; font-size: 12px;'>Live Market Data</div>"
        "</div>",
        unsafe_allow_html=True
    )

with col4:
    st.markdown(
        "<div class='kpi-card'>"
        "<div class='kpi-label'>Base Revenue</div>"
        "<div class='kpi-value'>"
        + currency_symbol + f"{base_revenue:,.0f}M" + "</div>"
        "<div style='color: #8b8fa8; font-size: 12px;'>Latest Annual</div>"
        "</div>",
        unsafe_allow_html=True
    )

st.markdown("<br>", unsafe_allow_html=True)

# ============================================================
# MONTE CARLO ENGINE
# ============================================================

def run_monte_carlo(
    base_revenue, ebit_margin, tax_rate, da_pct,
    capex_pct, nwc_pct, rev_growth_mean, rev_growth_std,
    wacc_low, wacc_mid, wacc_high, tgr_mean, tgr_std,
    shares_outstanding, net_debt, num_simulations
):
    ebit_margin = ebit_margin / 100
    tax_rate = tax_rate / 100
    da_pct = da_pct / 100
    capex_pct = capex_pct / 100
    nwc_pct = nwc_pct / 100
    rev_growth_mean = rev_growth_mean / 100
    rev_growth_std = rev_growth_std / 100
    wacc_low = wacc_low / 100
    wacc_mid = wacc_mid / 100
    wacc_high = wacc_high / 100
    tgr_mean = tgr_mean / 100
    tgr_std = tgr_std / 100

    enterprise_values = np.zeros(num_simulations)
    share_prices = np.zeros(num_simulations)

    for i in range(num_simulations):
        rev_growth = np.random.normal(rev_growth_mean, rev_growth_std)
        wacc = np.random.triangular(wacc_low, wacc_mid, wacc_high)
        tgr = np.random.normal(tgr_mean, tgr_std)
        tgr = min(tgr, wacc - 0.01)

        fcff = []
        revenue = base_revenue

        for year in range(1, 6):
            revenue = revenue * (1 + rev_growth)
            ebit = revenue * ebit_margin
            nopat = ebit * (1 - tax_rate)
            da = revenue * da_pct
            capex = revenue * capex_pct
            nwc = revenue * nwc_pct
            free_cash_flow = nopat + da - capex - nwc
            fcff.append(free_cash_flow)

        terminal_value = (fcff[-1] * (1 + tgr)) / (wacc - tgr)
        pv_fcff = sum([fcff[t] / (1 + wacc) ** (t + 1) for t in range(5)])
        pv_terminal = terminal_value / (1 + wacc) ** 5
        ev = pv_fcff + pv_terminal
        equity_value = ev - net_debt
        share_price = equity_value / shares_outstanding

        enterprise_values[i] = ev
        share_prices[i] = share_price

    return enterprise_values, share_prices

# RUN SIMULATION
with st.spinner(f"Running {num_simulations:,} Monte Carlo simulations..."):
    ev_results, sp_results = run_monte_carlo(
        base_revenue, ebit_margin, tax_rate, da_pct,
        capex_pct, nwc_pct, rev_growth_mean, rev_growth_std,
        wacc_low, wacc_mid, wacc_high, tgr_mean, tgr_std,
        shares_outstanding, net_debt, num_simulations
    )

st.success(f"✅ {num_simulations:,} simulations completed on live {data['company_name']} data!")
st.markdown("<br>", unsafe_allow_html=True)

# ============================================================
# VALUATION SUMMARY
# ============================================================

st.markdown("<div class='section-header'>📊 Valuation Summary</div>",
    unsafe_allow_html=True)

p25_price = np.percentile(sp_results, 25)
p50_price = np.percentile(sp_results, 50)
p75_price = np.percentile(sp_results, 75)
p50_ev = np.percentile(ev_results, 50)
std_price = np.std(sp_results)
prob_undervalued = np.mean(sp_results > current_share_price) * 100
upside = ((p50_price - current_share_price) / current_share_price) * 100

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(
        "<div class='kpi-card'>"
        "<div class='kpi-label'>Median Share Price</div>"
        "<div class='kpi-value'>"
        + currency_symbol + f"{p50_price:,.2f}" + "</div>"
        "<div style='color: #8b8fa8; font-size: 12px;'>50th Percentile</div>"
        "</div>",
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        "<div class='kpi-card'>"
        "<div class='kpi-label'>Median EV</div>"
        "<div class='kpi-value'>"
        + currency_symbol + f"{p50_ev:,.0f}M" + "</div>"
        "<div style='color: #8b8fa8; font-size: 12px;'>Enterprise Value</div>"
        "</div>",
        unsafe_allow_html=True
    )

with col3:
    color = "#00d4aa" if prob_undervalued > 50 else "#ff6b6b"
    label = "Undervalued" if prob_undervalued > 50 else "Overvalued"
    st.markdown(
        "<div class='kpi-card'>"
        "<div class='kpi-label'>Probability Undervalued</div>"
        "<div class='kpi-value' style='color:" + color + ";'>"
        + f"{prob_undervalued:.1f}%" + "</div>"
        "<div style='color:" + color + "; font-size: 12px;'>" + label + "</div>"
        "</div>",
        unsafe_allow_html=True
    )

with col4:
    color2 = "#00d4aa" if upside > 0 else "#ff6b6b"
    st.markdown(
        "<div class='kpi-card'>"
        "<div class='kpi-label'>Median Upside / Downside</div>"
        "<div class='kpi-value' style='color:" + color2 + ";'>"
        + f"{upside:+.1f}%" + "</div>"
        "<div style='color: #8b8fa8; font-size: 12px;'>vs Live Price "
        + currency_symbol + f"{current_share_price:,.2f}" + "</div>"
        "</div>",
        unsafe_allow_html=True
    )

st.markdown("<br>", unsafe_allow_html=True)

# ============================================================
# MONTE CARLO DISTRIBUTION CHART
# ============================================================

st.markdown("<div class='section-header'>🎲 Monte Carlo Distribution</div>",
    unsafe_allow_html=True)

fig_mc = go.Figure()

fig_mc.add_trace(go.Histogram(
    x=sp_results,
    nbinsx=100,
    name="Simulated Prices",
    marker_color="#00b4d8",
    opacity=0.7,
    histnorm="probability density"
))

x_range = np.linspace(sp_results.min(), sp_results.max(), 300)
kde = stats.gaussian_kde(sp_results)
fig_mc.add_trace(go.Scatter(
    x=x_range,
    y=kde(x_range),
    mode="lines",
    name="Distribution Curve",
    line=dict(color="#ffffff", width=2)
))

fig_mc.add_vline(
    x=p25_price, line_dash="dash", line_color="#ff6b6b", line_width=2,
    annotation_text="P25: " + currency_symbol + f"{p25_price:,.2f}",
    annotation_font_color="#ff6b6b",
    annotation_position="top right"
)
fig_mc.add_vline(
    x=p50_price, line_dash="dash", line_color="#00d4aa", line_width=2,
    annotation_text="Median: " + currency_symbol + f"{p50_price:,.2f}",
    annotation_font_color="#00d4aa",
    annotation_position="top right"
)
fig_mc.add_vline(
    x=p75_price, line_dash="dash", line_color="#1e88e5", line_width=2,
    annotation_text="P75: " + currency_symbol + f"{p75_price:,.2f}",
    annotation_font_color="#1e88e5",
    annotation_position="top right"
)
fig_mc.add_vline(
    x=current_share_price, line_dash="solid",
    line_color="#ffd700", line_width=3,
    annotation_text="Live: " + currency_symbol + f"{current_share_price:,.2f}",
    annotation_font_color="#ffd700",
    annotation_position="top left"
)

fig_mc.update_layout(
    title=data["company_name"] + " — Share Price Distribution (" + f"{num_simulations:,}" + " Simulations)",
    xaxis_title="Implied Share Price (" + currency_symbol + ")",
    yaxis_title="Probability Density",
    plot_bgcolor="#1e2130",
    paper_bgcolor="#1e2130",
    font=dict(color="#ffffff"),
    legend=dict(bgcolor="#1e2130", bordercolor="#00b4d8"),
    xaxis=dict(gridcolor="#2d3148"),
    yaxis=dict(gridcolor="#2d3148"),
    height=500
)

st.plotly_chart(fig_mc, use_container_width=True)

st.markdown("""
    <div style='background-color: #1e2130; border-radius: 10px;
    padding: 15px; border-left: 4px solid #00b4d8; margin-bottom: 20px;'>
        <p style='color: #ffffff; font-size: 14px; margin: 0;'>
            <span style='color: #00b4d8; font-weight: bold;'>
            How to read this chart:</span>
            Each bar represents the frequency of a simulated share price.
            The <span style='color: #ffd700;'>gold line</span> shows the
            live trading price. When the distribution sits
            <b>to the right</b> of the gold line, the majority of scenarios
            suggest the stock is
            <span style='color: #00d4aa;'>undervalued</span>.
        </p>
    </div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ============================================================
# 5 YEAR DCF PROJECTION TABLE
# ============================================================

st.markdown("<div class='section-header'>📋 5-Year DCF Projection</div>",
    unsafe_allow_html=True)

wacc_base = wacc_mid / 100
tgr_base = tgr_mean / 100
growth_base = rev_growth_mean / 100
ebit_base = ebit_margin / 100
tax_base = tax_rate / 100
da_base = da_pct / 100
capex_base = capex_pct / 100
nwc_base = nwc_pct / 100

projection_data = []
revenue = base_revenue

for year in range(1, 6):
    revenue = revenue * (1 + growth_base)
    ebit = revenue * ebit_base
    nopat = ebit * (1 - tax_base)
    da = revenue * da_base
    capex = revenue * capex_base
    nwc = revenue * nwc_base
    fcff = nopat + da - capex - nwc
    pv_factor = 1 / (1 + wacc_base) ** year
    pv_fcff = fcff * pv_factor

    projection_data.append({
        "Year": f"Year {year}",
        "Revenue (M)": f"{revenue:,.0f}",
        "EBIT (M)": f"{ebit:,.0f}",
        "NOPAT (M)": f"{nopat:,.0f}",
        "D&A (M)": f"{da:,.0f}",
        "CapEx (M)": f"{capex:,.0f}",
        "ΔNWC (M)": f"{nwc:,.0f}",
        "FCFF (M)": f"{fcff:,.0f}",
        "PV Factor": f"{pv_factor:.4f}",
        "PV FCFF (M)": f"{pv_fcff:,.0f}"
    })

df_projection = pd.DataFrame(projection_data)
st.dataframe(df_projection, use_container_width=True, hide_index=True)

last_fcff_val = float(projection_data[-1]["FCFF (M)"].replace(",", ""))
tv = (last_fcff_val * (1 + tgr_base)) / (wacc_base - tgr_base)
pv_tv = tv / (1 + wacc_base) ** 5
pv_fcffs = sum([float(row["PV FCFF (M)"].replace(",", "")) for row in projection_data])
base_ev = pv_fcffs + pv_tv
base_equity = base_ev - net_debt
base_price = base_equity / shares_outstanding

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        "<div class='kpi-card'>"
        "<div class='kpi-label'>Terminal Value</div>"
        "<div class='kpi-value'>"
        + currency_symbol + f"{tv:,.0f}M" + "</div>"
        "<div style='color: #8b8fa8; font-size: 12px;'>Gordon Growth Model</div>"
        "</div>",
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        "<div class='kpi-card'>"
        "<div class='kpi-label'>PV of Terminal Value</div>"
        "<div class='kpi-value'>"
        + currency_symbol + f"{pv_tv:,.0f}M" + "</div>"
        "<div style='color: #8b8fa8; font-size: 12px;'>Discounted to Today</div>"
        "</div>",
        unsafe_allow_html=True
    )

with col3:
    st.markdown(
        "<div class='kpi-card'>"
        "<div class='kpi-label'>Base Case Share Price</div>"
        "<div class='kpi-value'>"
        + currency_symbol + f"{base_price:,.2f}" + "</div>"
        "<div style='color: #8b8fa8; font-size: 12px;'>Deterministic DCF</div>"
        "</div>",
        unsafe_allow_html=True
    )

st.markdown("<br>", unsafe_allow_html=True)

# ============================================================
# SCENARIO ANALYSIS
# ============================================================

st.markdown("<div class='section-header'>📉 Scenario Analysis</div>",
    unsafe_allow_html=True)

scenarios = {
    "Bear (P10)": np.percentile(sp_results, 10),
    "Conservative (P25)": np.percentile(sp_results, 25),
    "Base (P50)": np.percentile(sp_results, 50),
    "Optimistic (P75)": np.percentile(sp_results, 75),
    "Bull (P90)": np.percentile(sp_results, 90),
}

scenario_names = list(scenarios.keys())
scenario_prices = list(scenarios.values())
scenario_upsides = [
    ((p - current_share_price) / current_share_price) * 100
    for p in scenario_prices
]
scenario_colors = ["#ff6b6b" if u < 0 else "#00d4aa" for u in scenario_upsides]

col1, col2 = st.columns(2)

with col1:
    fig_scenario = go.Figure(go.Bar(
        x=scenario_names,
        y=scenario_prices,
        marker_color=scenario_colors,
        text=[currency_symbol + f"{p:,.2f}" for p in scenario_prices],
        textposition="outside"
    ))
    fig_scenario.add_hline(
        y=current_share_price,
        line_dash="dash",
        line_color="#ffd700",
        line_width=2,
        annotation_text="Live: " + currency_symbol + f"{current_share_price:,.2f}",
        annotation_font_color="#ffd700"
    )
    fig_scenario.update_layout(
        title="Implied Share Price by Scenario",
        plot_bgcolor="#1e2130",
        paper_bgcolor="#1e2130",
        font=dict(color="#ffffff"),
        xaxis=dict(gridcolor="#2d3148"),
        yaxis=dict(gridcolor="#2d3148", tickprefix=currency_symbol)
    )
    st.plotly_chart(fig_scenario, use_container_width=True)

with col2:
    fig_upside = go.Figure(go.Bar(
        x=scenario_names,
        y=scenario_upsides,
        marker_color=scenario_colors,
        text=[f"{u:+.1f}%" for u in scenario_upsides],
        textposition="outside"
    ))
    fig_upside.add_hline(y=0, line_color="#ffffff", line_width=1)
    fig_upside.update_layout(
        title="Upside / Downside vs Live Price",
        plot_bgcolor="#1e2130",
        paper_bgcolor="#1e2130",
        font=dict(color="#ffffff"),
        xaxis=dict(gridcolor="#2d3148"),
        yaxis=dict(gridcolor="#2d3148", ticksuffix="%")
    )
    st.plotly_chart(fig_upside, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ============================================================
# RISK METRICS
# ============================================================

st.markdown("<div class='section-header'>⚠️ Risk Metrics</div>",
    unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(
        "<div class='kpi-card'>"
        "<div class='kpi-label'>Value at Risk (P5)</div>"
        "<div class='kpi-value' style='color:#ff6b6b;'>"
        + currency_symbol + f"{np.percentile(sp_results, 5):,.2f}" + "</div>"
        "<div style='color: #8b8fa8; font-size: 12px;'>Worst 5% of scenarios</div>"
        "</div>",
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        "<div class='kpi-card'>"
        "<div class='kpi-label'>Standard Deviation</div>"
        "<div class='kpi-value'>"
        + currency_symbol + f"{std_price:,.2f}" + "</div>"
        "<div style='color: #8b8fa8; font-size: 12px;'>Price volatility range</div>"
        "</div>",
        unsafe_allow_html=True
    )

with col3:
    st.markdown(
        "<div class='kpi-card'>"
        "<div class='kpi-label'>Bull Case (P90)</div>"
        "<div class='kpi-value' style='color:#00d4aa;'>"
        + currency_symbol + f"{np.percentile(sp_results, 90):,.2f}" + "</div>"
        "<div style='color: #8b8fa8; font-size: 12px;'>Best 10% of scenarios</div>"
        "</div>",
        unsafe_allow_html=True
    )

with col4:
    prob_loss = np.mean(sp_results < current_share_price) * 100
    st.markdown(
        "<div class='kpi-card'>"
        "<div class='kpi-label'>Probability of Loss</div>"
        "<div class='kpi-value' style='color:#ff6b6b;'>"
        + f"{prob_loss:.1f}%" + "</div>"
        "<div style='color: #8b8fa8; font-size: 12px;'>Below live price</div>"
        "</div>",
        unsafe_allow_html=True
    )

st.markdown("<br>", unsafe_allow_html=True)

# ============================================================
# FOOTER
# ============================================================

st.divider()
st.markdown("""
    <div style='text-align: center; color: #8b8fa8;
    font-size: 13px; padding: 20px;'>
        ValuEngine | Stochastic DCF & Monte Carlo Risk Simulation<br>
        Built by Pavas Kaushal · MBA Finance · TMT Strategy Consultant<br>
        Built with Python · NumPy · yfinance · Streamlit · Plotly<br>
        Live data: Yahoo Finance · For educational purposes only
    </div>
""", unsafe_allow_html=True)