import pandas as pd
from typing import Optional
from .fmp_client import FMPClient
from .yfinance_client import YFinanceClient


class DataPipeline:
    """Orchestrates data fetching from FMP and yfinance, merging into unified structures."""

    def __init__(self, fmp_api_key: Optional[str] = None):
        self.fmp = FMPClient(api_key=fmp_api_key)
        self.yf = YFinanceClient()

    def get_company_overview(self, ticker: str) -> dict:
        profile = {}
        yf_info = {}
        try:
            profile = self.fmp.get_company_profile(ticker)
        except Exception:
            pass
        try:
            yf_info = self.yf.get_info(ticker)
        except Exception:
            pass

        # Prefer FMP data, fall back to yfinance
        return {
            "name": profile.get("companyName") or yf_info.get("longName", ticker),
            "sector": profile.get("sector") or yf_info.get("sector", "N/A"),
            "industry": profile.get("industry") or yf_info.get("industry", "N/A"),
            "description": profile.get("description") or yf_info.get("longBusinessSummary", ""),
            "website": profile.get("website") or yf_info.get("website", ""),
            "market_cap": profile.get("mktCap") or yf_info.get("marketCap", 0),
            "employees": profile.get("fullTimeEmployees") or yf_info.get("fullTimeEmployees", 0),
            "exchange": profile.get("exchangeShortName") or yf_info.get("exchange", ""),
            "country": profile.get("country") or yf_info.get("country", ""),
            "currency": profile.get("currency") or yf_info.get("currency", "USD"),
            "logo": profile.get("image", ""),
        }

    def get_financial_statements(self, ticker: str, period: str = "annual", limit: int = 5) -> dict:
        income, balance, cashflow = [], [], []
        try:
            income = self.fmp.get_income_statement(ticker, period=period, limit=limit)
        except Exception:
            pass
        try:
            balance = self.fmp.get_balance_sheet(ticker, period=period, limit=limit)
        except Exception:
            pass
        try:
            cashflow = self.fmp.get_cash_flow(ticker, period=period, limit=limit)
        except Exception:
            pass
        return {"income": income, "balance": balance, "cashflow": cashflow}

    def get_key_metrics(self, ticker: str, period: str = "annual", limit: int = 5) -> dict:
        metrics, ratios = [], []
        try:
            metrics = self.fmp.get_key_metrics(ticker, period=period, limit=limit)
        except Exception:
            pass
        try:
            ratios = self.fmp.get_ratios(ticker, period=period, limit=limit)
        except Exception:
            pass
        return {"metrics": metrics, "ratios": ratios}

    def get_price_data(self, ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        return self.yf.get_price_history(ticker, period=period, interval=interval)

    def get_quote(self, ticker: str) -> dict:
        fmp_quote, yf_info = {}, {}
        try:
            fmp_quote = self.fmp.get_quote(ticker)
        except Exception:
            pass
        try:
            yf_info = self.yf.get_info(ticker)
        except Exception:
            pass

        price = fmp_quote.get("price") or yf_info.get("currentPrice", 0)
        change = fmp_quote.get("change") or yf_info.get("regularMarketChange", 0)
        change_pct = fmp_quote.get("changesPercentage") or yf_info.get("regularMarketChangePercent", 0)

        return {
            "price": price,
            "change": change,
            "change_pct": change_pct,
            "open": fmp_quote.get("open") or yf_info.get("open", 0),
            "high": fmp_quote.get("dayHigh") or yf_info.get("dayHigh", 0),
            "low": fmp_quote.get("dayLow") or yf_info.get("dayLow", 0),
            "volume": fmp_quote.get("volume") or yf_info.get("volume", 0),
            "avg_volume": fmp_quote.get("avgVolume") or yf_info.get("averageVolume", 0),
            "52w_high": fmp_quote.get("yearHigh") or yf_info.get("fiftyTwoWeekHigh", 0),
            "52w_low": fmp_quote.get("yearLow") or yf_info.get("fiftyTwoWeekLow", 0),
            "pe_ratio": fmp_quote.get("pe") or yf_info.get("trailingPE", 0),
            "eps": fmp_quote.get("eps") or yf_info.get("trailingEps", 0),
            "market_cap": fmp_quote.get("marketCap") or yf_info.get("marketCap", 0),
        }
