import os
import requests
from typing import Optional
import streamlit as st
from utils.secrets import get_secret


class FMPClient:
    BASE_URL = "https://financialmodelingprep.com/api/v3"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or get_secret("FMP_API_KEY")

    def _get(self, endpoint: str, params: dict = None) -> dict | list:
        if not self.api_key:
            raise ValueError("FMP_API_KEY is not set. Add it to your .env file.")
        url = f"{self.BASE_URL}/{endpoint}"
        query = {"apikey": self.api_key, **(params or {})}
        resp = requests.get(url, params=query, timeout=15)
        resp.raise_for_status()
        return resp.json()

    @st.cache_data(ttl=3600, show_spinner=False)
    def get_income_statement(_self, ticker: str, period: str = "annual", limit: int = 5) -> list[dict]:
        return _self._get(f"income-statement/{ticker}", {"period": period, "limit": limit})

    @st.cache_data(ttl=3600, show_spinner=False)
    def get_balance_sheet(_self, ticker: str, period: str = "annual", limit: int = 5) -> list[dict]:
        return _self._get(f"balance-sheet-statement/{ticker}", {"period": period, "limit": limit})

    @st.cache_data(ttl=3600, show_spinner=False)
    def get_cash_flow(_self, ticker: str, period: str = "annual", limit: int = 5) -> list[dict]:
        return _self._get(f"cash-flow-statement/{ticker}", {"period": period, "limit": limit})

    @st.cache_data(ttl=3600, show_spinner=False)
    def get_key_metrics(_self, ticker: str, period: str = "annual", limit: int = 5) -> list[dict]:
        return _self._get(f"key-metrics/{ticker}", {"period": period, "limit": limit})

    @st.cache_data(ttl=3600, show_spinner=False)
    def get_ratios(_self, ticker: str, period: str = "annual", limit: int = 5) -> list[dict]:
        return _self._get(f"ratios/{ticker}", {"period": period, "limit": limit})

    @st.cache_data(ttl=300, show_spinner=False)
    def get_quote(_self, ticker: str) -> dict:
        result = _self._get(f"quote/{ticker}")
        return result[0] if result else {}

    @st.cache_data(ttl=3600, show_spinner=False)
    def get_company_profile(_self, ticker: str) -> dict:
        result = _self._get(f"profile/{ticker}")
        return result[0] if result else {}

    @st.cache_data(ttl=3600, show_spinner=False)
    def search_ticker(_self, query: str, limit: int = 10) -> list[dict]:
        return _self._get("search", {"query": query, "limit": limit})
