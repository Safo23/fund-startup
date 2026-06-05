import streamlit as st
import pandas as pd
from data.pipeline import DataPipeline
from components.charts import render_price_chart
from components.tables import render_metric_cards
from utils.helpers import fmt_large_number, fmt_percent, fmt_currency

st.set_page_config(page_title="Stock Analysis", page_icon="📉", layout="wide")

st.title("📉 Stock Analysis")

ticker = st.session_state.get("ticker", "AAPL")
pipeline = DataPipeline()

col1, col2, col3 = st.columns([2, 2, 2])
with col1:
    ticker = st.text_input("Ticker", value=ticker).upper().strip()
    st.session_state["ticker"] = ticker
with col2:
    period_map = {
        "1 Month": "1mo", "3 Months": "3mo", "6 Months": "6mo",
        "1 Year": "1y", "2 Years": "2y", "5 Years": "5y",
    }
    period_label = st.selectbox("Period", list(period_map.keys()), index=3)
    period = period_map[period_label]
with col3:
    interval_map = {"Daily": "1d", "Weekly": "1wk", "Monthly": "1mo"}
    interval_label = st.selectbox("Interval", list(interval_map.keys()), index=0)
    interval = interval_map[interval_label]

if not ticker:
    st.warning("Enter a ticker symbol above.")
    st.stop()

with st.spinner(f"Loading price data for **{ticker}**..."):
    try:
        df = pipeline.get_price_data(ticker, period=period, interval=interval)
        quote = pipeline.get_quote(ticker)
        overview = pipeline.get_company_overview(ticker)
    except Exception as e:
        st.error(f"Failed to fetch data: {e}")
        st.stop()

# Header
st.subheader(f"{overview.get('name', ticker)} ({ticker})")

price = quote.get("price", 0)
change = quote.get("change", 0)
change_pct = quote.get("change_pct", 0)

col_p, col_c, col_mc, col_pe = st.columns(4)
col_p.metric("Current Price", fmt_currency(price), delta=f"{change:+.2f} ({change_pct:+.2f}%)" if change else None)
col_c.metric("Market Cap", fmt_large_number(quote.get("market_cap")))
col_mc.metric("P/E Ratio", f"{quote.get('pe_ratio', 0):.2f}" if quote.get("pe_ratio") else "N/A")
col_pe.metric("EPS", fmt_currency(quote.get("eps")))

st.divider()

# Price chart
show_vol = st.checkbox("Show Volume", value=True)
render_price_chart(df, ticker, show_volume=show_vol)

# Trading stats
st.subheader("Trading Statistics")
render_metric_cards({
    "Open": fmt_currency(quote.get("open")),
    "Day High": fmt_currency(quote.get("high")),
    "Day Low": fmt_currency(quote.get("low")),
    "52W High": fmt_currency(quote.get("52w_high")),
    "52W Low": fmt_currency(quote.get("52w_low")),
    "Volume": fmt_large_number(quote.get("volume")),
    "Avg Volume": fmt_large_number(quote.get("avg_volume")),
    "Beta": f"{overview.get('beta', 'N/A')}",
})

# Analyst recommendations
st.subheader("Analyst Recommendations")
try:
    recs = pipeline.yf.get_analyst_recommendations(ticker)
    if not recs.empty:
        if "period" in recs.columns:
            recs = recs.reset_index()
        st.dataframe(recs.head(10), use_container_width=True)
    else:
        st.info("No analyst recommendations available.")
except Exception:
    st.info("No analyst recommendations available.")
