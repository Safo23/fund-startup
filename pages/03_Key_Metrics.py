import streamlit as st
import pandas as pd
import plotly.express as px
from data.pipeline import DataPipeline
from components.charts import render_ratio_gauges
from components.tables import render_metric_cards
from utils.helpers import fmt_large_number, fmt_percent

st.set_page_config(page_title="Key Metrics", page_icon="🔢", layout="wide")

st.title("🔢 Key Metrics & Ratios")

ticker = st.session_state.get("ticker", "AAPL")
pipeline = DataPipeline()

col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    ticker = st.text_input("Ticker", value=ticker).upper().strip()
    st.session_state["ticker"] = ticker
with col2:
    period = st.selectbox("Period", ["annual", "quarter"], index=0)
with col3:
    limit = st.selectbox("Periods", [4, 5, 8], index=1)

if not ticker:
    st.warning("Enter a ticker symbol above.")
    st.stop()

with st.spinner(f"Loading metrics for **{ticker}**..."):
    try:
        key_data = pipeline.get_key_metrics(ticker, period=period, limit=limit)
        overview = pipeline.get_company_overview(ticker)
    except Exception as e:
        st.error(f"Failed to fetch data: {e}")
        st.stop()

metrics = key_data.get("metrics", [])
ratios = key_data.get("ratios", [])

st.subheader(f"{overview.get('name', ticker)} ({ticker})")
st.caption(f"{overview.get('sector', '')} · {overview.get('industry', '')}")
st.divider()

# Gauge charts for latest valuation ratios
if ratios:
    latest_r = ratios[0]
    pe = latest_r.get("priceEarningsRatio") or 0
    pb = latest_r.get("priceToBookRatio") or 0
    ps = latest_r.get("priceToSalesRatio") or 0
    de = latest_r.get("debtEquityRatio") or 0

    st.subheader("Valuation Snapshot")
    render_ratio_gauges({
        "P/E Ratio": (pe, 0, 60),
        "P/B Ratio": (pb, 0, 20),
        "P/S Ratio": (ps, 0, 20),
        "Debt/Equity": (de, 0, 5),
    })

st.divider()

# Tabs: Valuation, Profitability, Growth, Liquidity
tab_val, tab_prof, tab_grow, tab_liq = st.tabs(["Valuation", "Profitability", "Growth", "Liquidity"])

def _trend_chart(data: list[dict], fields: list[str], labels: list[str], title: str) -> None:
    if not data:
        st.info("No data available.")
        return
    rows = []
    for d in data[::-1]:
        date = d.get("date", "N/A")
        for field, label in zip(fields, labels):
            val = d.get(field)
            if val is not None:
                rows.append({"Date": date, "Value": val, "Metric": label})
    if not rows:
        st.info("No data available.")
        return
    df = pd.DataFrame(rows)
    fig = px.line(df, x="Date", y="Value", color="Metric", title=title, template="plotly_dark")
    fig.update_layout(height=350, margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig, use_container_width=True)

with tab_val:
    _trend_chart(
        ratios,
        ["priceEarningsRatio", "priceToBookRatio", "priceToSalesRatio", "enterpriseValueMultiple"],
        ["P/E", "P/B", "P/S", "EV/EBITDA"],
        "Valuation Ratios Over Time",
    )
    if metrics:
        latest_m = metrics[0]
        render_metric_cards({
            "Market Cap": fmt_large_number(latest_m.get("marketCap")),
            "Enterprise Value": fmt_large_number(latest_m.get("enterpriseValue")),
            "EV/EBITDA": f"{latest_m.get('evToEbitda', 0):.2f}" if latest_m.get("evToEbitda") else "N/A",
            "EV/Revenue": f"{latest_m.get('evToSales', 0):.2f}" if latest_m.get("evToSales") else "N/A",
        })

with tab_prof:
    _trend_chart(
        ratios,
        ["returnOnEquity", "returnOnAssets", "netProfitMargin", "grossProfitMargin"],
        ["ROE", "ROA", "Net Margin", "Gross Margin"],
        "Profitability Ratios Over Time",
    )
    if ratios:
        latest_r = ratios[0]
        render_metric_cards({
            "ROE": fmt_percent((latest_r.get("returnOnEquity") or 0) * 100),
            "ROA": fmt_percent((latest_r.get("returnOnAssets") or 0) * 100),
            "Net Margin": fmt_percent((latest_r.get("netProfitMargin") or 0) * 100),
            "Gross Margin": fmt_percent((latest_r.get("grossProfitMargin") or 0) * 100),
            "Operating Margin": fmt_percent((latest_r.get("operatingProfitMargin") or 0) * 100),
            "EBITDA Margin": fmt_percent((latest_r.get("ebitdaPerShare") or 0)),
        })

with tab_grow:
    _trend_chart(
        metrics,
        ["revenuePerShare", "netIncomePerShare", "freeCashFlowPerShare"],
        ["Revenue/Share", "EPS", "FCF/Share"],
        "Per Share Metrics Over Time",
    )
    if metrics:
        latest_m = metrics[0]
        render_metric_cards({
            "Revenue / Share": fmt_large_number(latest_m.get("revenuePerShare")),
            "EPS": f"${latest_m.get('netIncomePerShare', 0):.2f}" if latest_m.get("netIncomePerShare") else "N/A",
            "FCF / Share": f"${latest_m.get('freeCashFlowPerShare', 0):.2f}" if latest_m.get("freeCashFlowPerShare") else "N/A",
            "Book Value / Share": f"${latest_m.get('bookValuePerShare', 0):.2f}" if latest_m.get("bookValuePerShare") else "N/A",
        })

with tab_liq:
    _trend_chart(
        ratios,
        ["currentRatio", "quickRatio", "cashRatio", "debtEquityRatio"],
        ["Current Ratio", "Quick Ratio", "Cash Ratio", "Debt/Equity"],
        "Liquidity & Leverage Over Time",
    )
    if ratios:
        latest_r = ratios[0]
        render_metric_cards({
            "Current Ratio": f"{latest_r.get('currentRatio', 0):.2f}" if latest_r.get("currentRatio") else "N/A",
            "Quick Ratio": f"{latest_r.get('quickRatio', 0):.2f}" if latest_r.get("quickRatio") else "N/A",
            "Cash Ratio": f"{latest_r.get('cashRatio', 0):.2f}" if latest_r.get("cashRatio") else "N/A",
            "Debt/Equity": f"{latest_r.get('debtEquityRatio', 0):.2f}" if latest_r.get("debtEquityRatio") else "N/A",
            "Interest Coverage": f"{latest_r.get('interestCoverageRatio', 0):.2f}" if latest_r.get("interestCoverageRatio") else "N/A",
        })
