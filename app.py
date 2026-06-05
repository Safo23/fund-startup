import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Fund Startup — Stock Analysis",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Sidebar: global ticker input + API key
with st.sidebar:
    st.title("📈 Fund Startup")
    st.caption("Stock Analysis Platform")
    st.divider()

    ticker = st.text_input(
        "Ticker Symbol",
        value=st.session_state.get("ticker", "AAPL"),
        placeholder="e.g. AAPL, MSFT, TSLA",
        key="ticker_input",
    ).upper().strip()

    if ticker:
        st.session_state["ticker"] = ticker

    st.divider()
    fmp_key = st.text_input(
        "FMP API Key (optional)",
        value=os.getenv("FMP_API_KEY", ""),
        type="password",
        help="Get a free key at financialmodelingprep.com",
    )
    if fmp_key:
        os.environ["FMP_API_KEY"] = fmp_key

    st.divider()
    st.caption("Navigate using the sidebar pages above.")

# Home / landing page
st.title("Welcome to Fund Startup")
st.markdown(
    """
    A lightweight stock analysis platform powered by **Financial Modeling Prep** and **yfinance**.

    ### Getting Started
    1. Enter a ticker symbol in the sidebar (e.g. `AAPL`).
    2. Optionally paste your **FMP API Key** for richer financial data.
    3. Navigate to a page using the sidebar:

    | Page | Description |
    |------|-------------|
    | **Financial Statements** | Income, balance sheet & cash flow with charts |
    | **Stock Analysis** | Price history, technicals & analyst ratings |
    | **Key Metrics** | Valuation ratios, profitability & growth metrics |

    > **Note:** Without an FMP API key, the app falls back to yfinance data where possible.
    """
)

col1, col2, col3 = st.columns(3)
col1.info("📊 **Financial Statements**\nAnnual & quarterly financials")
col2.info("📉 **Stock Analysis**\nPrice charts & technicals")
col3.info("🔢 **Key Metrics**\nValuation & profitability ratios")
