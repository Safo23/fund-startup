import os
import streamlit as st
from data.pipeline import DataPipeline
from components.charts import render_financial_bar_chart
from components.tables import render_financial_table, render_metric_cards
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
pipeline = DataPipeline()

col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    ticker = st.text_input("Ticker", value=ticker).upper().strip()
    st.session_state["ticker"] = ticker
with col2:
    period = st.selectbox("Period", ["annual", "quarter"], index=0)
with col3:
    limit = st.selectbox("Years / Quarters", [4, 5, 8, 10], index=1)

if not ticker:
    st.warning("Enter a ticker symbol above.")
    st.stop()

with st.spinner(f"Loading financials for **{ticker}**..."):
    try:
        stmts = pipeline.get_financial_statements(ticker, period=period, limit=limit)
        overview = pipeline.get_company_overview(ticker)
    except Exception as e:
        st.error(f"Failed to fetch data: {e}")
        st.stop()

income = stmts["income"]
balance = stmts["balance"]
cashflow = stmts["cashflow"]

if not income and not balance and not cashflow:
    st.error(
        "No financial data returned. "
        "Enter your FMP API key in the sidebar to load full statement data, "
        "or check that the ticker symbol is valid."
    )
    st.stop()

if overview.get("logo"):
    st.image(overview["logo"], width=60)

st.subheader(f"{overview.get('name', ticker)} ({ticker})")
st.caption(f"{overview.get('sector', '')} · {overview.get('industry', '')} · {overview.get('exchange', '')}")

if income:
    latest = income[0]
    render_metric_cards({
        "Revenue": fmt_large_number(latest.get("revenue")),
        "Gross Profit": fmt_large_number(latest.get("grossProfit")),
        "Operating Income": fmt_large_number(latest.get("operatingIncome")),
        "Net Income": fmt_large_number(latest.get("netIncome")),
        "EBITDA": fmt_large_number(latest.get("ebitda")),
        "EPS": f"${latest.get('eps', 0):.2f}" if latest.get("eps") else "N/A",
        "Gross Margin": fmt_percent(latest.get("grossProfitRatio", 0) * 100 if latest.get("grossProfitRatio") else None),
        "Net Margin": fmt_percent(latest.get("netIncomeRatio", 0) * 100 if latest.get("netIncomeRatio") else None),
    })

st.divider()

tab_income, tab_balance, tab_cashflow = st.tabs(["Income Statement", "Balance Sheet", "Cash Flow"])

with tab_income:
    st.subheader("Income Statement")
    render_financial_bar_chart(
        income,
        fields=["revenue", "grossProfit", "operatingIncome", "netIncome"],
        labels=["Revenue", "Gross Profit", "Operating Income", "Net Income"],
        title="Revenue & Profitability",
    )
    render_financial_table(income, statement="income")

with tab_balance:
    st.subheader("Balance Sheet")
    render_financial_bar_chart(
        balance,
        fields=["totalAssets", "totalLiabilities", "totalStockholdersEquity"],
        labels=["Total Assets", "Total Liabilities", "Shareholders Equity"],
        title="Assets vs. Liabilities",
    )
    render_financial_table(balance, statement="balance")

with tab_cashflow:
    st.subheader("Cash Flow Statement")
    render_financial_bar_chart(
        cashflow,
        fields=["operatingCashFlow", "freeCashFlow", "capitalExpenditure"],
        labels=["Operating Cash Flow", "Free Cash Flow", "CapEx"],
        title="Cash Flow",
    )
    render_financial_table(cashflow, statement="cashflow")
