import os
import pandas as pd
import streamlit as st
import yfinance as yf
import plotly.express as px
from data.pipeline import DataPipeline
from components.tables import render_metric_cards
from utils.helpers import fmt_large_number, fmt_percent
from utils.secrets import get_secret

st.set_page_config(page_title="Financial Statements", page_icon="📊", layout="wide")

with st.sidebar:
    st.title("📈 Fund Startup")
    st.divider()
    ticker_side = st.text_input(
        "Ticker Symbol",
        value=st.session_state.get("ticker", "AAPL"),
        key="ticker_side_fs",
    ).upper().strip()
    if ticker_side:
        st.session_state["ticker"] = ticker_side
    st.divider()
    fmp_override = st.text_input(
        "FMP API Key",
        value=get_secret("FMP_API_KEY"),
        type="password",
        help="financialmodelingprep.com",
    )
    if fmp_override:
        os.environ["FMP_API_KEY"] = fmp_override

st.title("📊 Financial Statements")

ticker = st.session_state.get("ticker", "AAPL")

col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    ticker = st.text_input("Ticker", value=ticker).upper().strip()
    st.session_state["ticker"] = ticker
with col2:
    period = st.selectbox("Period", ["Annual", "Quarterly"], index=0)
with col3:
    limit = st.selectbox("Periods", [4, 5, 8, 10], index=1)

if not ticker:
    st.warning("Enter a ticker symbol above.")
    st.stop()

quarterly = period == "Quarterly"


def _fmt_df(df: pd.DataFrame, lim: int) -> pd.DataFrame:
    """Format a yfinance financial DataFrame for display."""
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.iloc[:, :lim].copy()
    # Format column headers as clean dates
    df.columns = [str(c)[:10] if not isinstance(c, str) else c for c in df.columns]
    # Format numbers
    def _fmt(v):
        if pd.isna(v):
            return "—"
        try:
            return fmt_large_number(float(v))
        except Exception:
            return str(v)
    return df.applymap(_fmt)


def _bar_chart(df_raw: pd.DataFrame, rows: list[str], title: str, lim: int):
    if df_raw is None or df_raw.empty:
        return
    available = [r for r in rows if r in df_raw.index]
    if not available:
        return
    sub = df_raw.loc[available, df_raw.columns[:lim]]
    records = []
    for row_name in available:
        for col in sub.columns:
            val = sub.loc[row_name, col]
            if not pd.isna(val):
                records.append({"Period": str(col)[:10], "Value": float(val), "Metric": row_name})
    if not records:
        return
    fig = px.bar(pd.DataFrame(records), x="Period", y="Value", color="Metric",
                 barmode="group", title=title, template="plotly_dark",
                 height=400)
    fig.update_layout(yaxis_tickformat=".2s", margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig, use_container_width=True)


with st.spinner(f"Loading financials for **{ticker}**..."):
    t = yf.Ticker(ticker)
    income_raw = t.quarterly_income_stmt if quarterly else t.income_stmt
    balance_raw = t.quarterly_balance_sheet if quarterly else t.balance_sheet
    cashflow_raw = t.quarterly_cashflow if quarterly else t.cashflow
    try:
        info = t.info or {}
    except Exception:
        info = {}

# Company header
name = info.get("longName", ticker)
st.subheader(f"{name} ({ticker})")
st.caption(f"{info.get('sector','')}{' · ' + info.get('industry','') if info.get('industry') else ''}")

# Snapshot cards from info
render_metric_cards({
    "Market Cap": fmt_large_number(info.get("marketCap")),
    "Revenue (TTM)": fmt_large_number(info.get("totalRevenue")),
    "Net Income (TTM)": fmt_large_number(info.get("netIncomeToCommon")),
    "EPS (TTM)": f"${info.get('trailingEps', 0):.2f}" if info.get("trailingEps") else "N/A",
    "Gross Margin": fmt_percent((info.get("grossMargins") or 0) * 100),
    "Net Margin": fmt_percent((info.get("profitMargins") or 0) * 100),
    "Operating Margin": fmt_percent((info.get("operatingMargins") or 0) * 100),
    "ROE": fmt_percent((info.get("returnOnEquity") or 0) * 100),
})

st.divider()

tab_income, tab_balance, tab_cashflow = st.tabs(["Income Statement", "Balance Sheet", "Cash Flow"])

with tab_income:
    if income_raw is None or income_raw.empty:
        st.info("No income statement data available for this ticker.")
    else:
        _bar_chart(income_raw,
                   ["Total Revenue", "Gross Profit", "Operating Income", "Net Income"],
                   "Revenue & Profitability", limit)
        st.dataframe(_fmt_df(income_raw, limit), use_container_width=True,
                     height=min(50 + len(income_raw) * 35, 700))

with tab_balance:
    if balance_raw is None or balance_raw.empty:
        st.info("No balance sheet data available for this ticker.")
    else:
        _bar_chart(balance_raw,
                   ["Total Assets", "Total Liabilities Net Minority Interest", "Stockholders Equity"],
                   "Assets vs Liabilities", limit)
        st.dataframe(_fmt_df(balance_raw, limit), use_container_width=True,
                     height=min(50 + len(balance_raw) * 35, 700))

with tab_cashflow:
    if cashflow_raw is None or cashflow_raw.empty:
        st.info("No cash flow data available for this ticker.")
    else:
        _bar_chart(cashflow_raw,
                   ["Operating Cash Flow", "Free Cash Flow", "Capital Expenditure"],
                   "Cash Flow", limit)
        st.dataframe(_fmt_df(cashflow_raw, limit), use_container_width=True,
                     height=min(50 + len(cashflow_raw) * 35, 700))
