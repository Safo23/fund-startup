import os
import requests
import streamlit as st
from datetime import datetime, timedelta
from typing import Optional
from utils.secrets import get_secret


class NewsAPIClient:
    BASE_URL = "https://newsapi.org/v2"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or get_secret("NEWSAPI_KEY")

    def _get(self, endpoint: str, params: dict) -> dict:
        if not self.api_key:
            raise ValueError("NEWSAPI_KEY is not set.")
        resp = requests.get(
            f"{self.BASE_URL}/{endpoint}",
            params={"apiKey": self.api_key, **params},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()

    @st.cache_data(ttl=600, show_spinner=False)
    def get_company_news(_self, query: str, days: int = 7, page_size: int = 20) -> list[dict]:
        from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        data = _self._get("everything", {
            "q": query,
            "from": from_date,
            "sortBy": "publishedAt",
            "language": "en",
            "pageSize": page_size,
        })
        return data.get("articles", [])

    @st.cache_data(ttl=600, show_spinner=False)
    def get_financial_headlines(_self, page_size: int = 20) -> list[dict]:
        data = _self._get("top-headlines", {
            "category": "business",
            "language": "en",
            "pageSize": page_size,
        })
        return data.get("articles", [])
