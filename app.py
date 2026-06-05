import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def _secret(key: str) -> str:
    """Read from Streamlit secrets first, fall back to env vars."""
    try:
        return st.secrets.get(key, "") or os.getenv(key, "")
    except Exception:
        return os.getenv(key, "")


st.set_page_config(
    page_title="Fund Startup — Stock Analysis",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject API keys from secrets/env so all pages can access them
if _secret("FMP_API_KEY"):
    os.environ["FMP_API_KEY"] = _secret("FMP_API_KEY")
if _secret("NEWSAPI_KEY"):
    os.environ["NEWSAPI_KEY"] = _secret("NEWSAPI_KEY")

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
        "FMP API Key",
        value=os.getenv("FMP_API_KEY", ""),
        type="password",
        help="Get a free key at financialmodelingprep.com",
    )
    if fmp_key:
        os.environ["FMP_API_KEY"] = fmp_key

    news_key = st.text_input(
        "NewsAPI Key",
        value=os.getenv("NEWSAPI_KEY", ""),
        type="password",
        help="Get a free key at newsapi.org",
    )
    if news_key:
        os.environ["NEWSAPI_KEY"] = news_key

    st.divider()
    st.caption("Navigate using the sidebar pages above.")

st.title("Welcome to Fund Startup")
st.markdown(
    """
    A stock analysis platform powered by **Financial Modeling Prep**, **yfinance**, and **NewsAPI**.

    ### Getting Started
    1. Enter a ticker symbol in the sidebar (e.g. `AAPL`).
    2. Navigate to a page:

    | Page | Description |
    |------|-------------|
    | **Financial Statements** | Income, balance sheet & cash flow with charts |
    | **Stock Analysis** | Price history, technicals & analyst ratings |
    | **Key Metrics** | Valuation ratios, profitability & growth |
    | **News** | Company news & market headlines |
    """
)

col1, col2, col3, col4 = st.columns(4)
col1.info("📊 **Financial Statements**\nAnnual & quarterly financials")
col2.info("📉 **Stock Analysis**\nPrice charts & technicals")
col3.info("🔢 **Key Metrics**\nValuation & profitability ratios")
col4.info("📰 **News**\nCompany & market headlines")
