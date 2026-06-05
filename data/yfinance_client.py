import yfinance as yf
import pandas as pd
import streamlit as st
from typing import Optional


class YFinanceClient:

    @st.cache_data(ttl=300, show_spinner=False)
    def get_price_history(_self, ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        t = yf.Ticker(ticker)
        df = t.history(period=period, interval=interval, auto_adjust=True)
        df.index = pd.to_datetime(df.index).tz_localize(None)
        return df

    @st.cache_data(ttl=3600, show_spinner=False)
    def get_info(_self, ticker: str) -> dict:
        return yf.Ticker(ticker).info or {}

    @st.cache_data(ttl=3600, show_spinner=False)
    def get_income_stmt(_self, ticker: str, quarterly: bool = False) -> pd.DataFrame:
        t = yf.Ticker(ticker)
        return t.quarterly_income_stmt if quarterly else t.income_stmt

    @st.cache_data(ttl=3600, show_spinner=False)
    def get_balance_sheet(_self, ticker: str, quarterly: bool = False) -> pd.DataFrame:
        t = yf.Ticker(ticker)
        return t.quarterly_balance_sheet if quarterly else t.balance_sheet

    @st.cache_data(ttl=3600, show_spinner=False)
    def get_cash_flow(_self, ticker: str, quarterly: bool = False) -> pd.DataFrame:
        t = yf.Ticker(ticker)
        return t.quarterly_cashflow if quarterly else t.cashflow

    @st.cache_data(ttl=300, show_spinner=False)
    def get_options_expiries(_self, ticker: str) -> tuple:
        return yf.Ticker(ticker).options

    @st.cache_data(ttl=300, show_spinner=False)
    def get_option_chain(_self, ticker: str, expiry: str):
        return yf.Ticker(ticker).option_chain(expiry)

    @st.cache_data(ttl=3600, show_spinner=False)
    def get_analyst_recommendations(_self, ticker: str) -> pd.DataFrame:
        return yf.Ticker(ticker).recommendations or pd.DataFrame()

    @st.cache_data(ttl=3600, show_spinner=False)
    def get_earnings_dates(_self, ticker: str) -> pd.DataFrame:
        return yf.Ticker(ticker).earnings_dates or pd.DataFrame()
