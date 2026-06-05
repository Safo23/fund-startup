import pandas as pd
from typing import Optional
from .fmp_client import FMPClient
from .yfinance_client import YFinanceClient

# Each entry: (list of possible yfinance field names to try in order, FMP-style key)
_INCOME_CANDIDATES = [
    (["Total Revenue", "Revenue"], "revenue"),
    (["Cost Of Revenue", "Cost of Revenue"], "costOfRevenue"),
    (["Gross Profit"], "grossProfit"),
    (["Research And Development", "Research And Development Expenses"], "researchAndDevelopmentExpenses"),
    (["Selling General And Administrative", "Selling General Administrative", "General And Administrative Expense"], "sellingGeneralAndAdministrativeExpenses"),
    (["Operating Expense", "Total Operating Expenses", "Operating Expenses"], "operatingExpenses"),
    (["Operating Income", "Total Operating Income As Reported", "EBIT"], "operatingIncome"),
    (["EBITDA", "Normalized EBITDA"], "ebitda"),
    (["Interest Expense", "Interest Expense Non Operating"], "interestExpense"),
    (["Interest Income", "Interest Income Non Operating"], "interestIncome"),
    (["Total Other Income Expense Net", "Other Income Expense", "Non Operating Income"], "totalOtherIncomeExpensesNet"),
    (["Pretax Income", "Income Before Tax"], "incomeBeforeTax"),
    (["Tax Provision", "Income Tax Expense"], "incomeTaxExpense"),
    (["Net Income", "Net Income Common Stockholders", "Net Income Continuous Operations"], "netIncome"),
    (["Basic EPS", "Basic Earnings Per Share"], "eps"),
    (["Diluted EPS", "Diluted Earnings Per Share"], "epsdiluted"),
    (["Basic Average Shares", "Ordinary Shares Number"], "weightedAverageShsOut"),
    (["Diluted Average Shares"], "weightedAverageShsOutDil"),
    (["Depreciation And Amortization", "Reconciled Depreciation"], "depreciationAndAmortization"),
]

_BALANCE_CANDIDATES = [
    (["Total Assets"], "totalAssets"),
    (["Current Assets", "Total Current Assets"], "totalCurrentAssets"),
    (["Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments"], "cashAndCashEquivalents"),
    (["Other Short Term Investments", "Available For Sale Securities"], "shortTermInvestments"),
    (["Accounts Receivable", "Net Receivables", "Receivables"], "netReceivables"),
    (["Inventory"], "inventory"),
    (["Other Current Assets"], "otherCurrentAssets"),
    (["Total Non Current Assets", "Net PPE"], "totalNonCurrentAssets"),
    (["Net PPE", "Gross PPE"], "propertyPlantEquipmentNet"),
    (["Goodwill"], "goodwill"),
    (["Goodwill And Other Intangible Assets", "Other Intangible Assets"], "intangibleAssets"),
    (["Long Term Equity Investment", "Investments And Advances"], "longTermInvestments"),
    (["Total Liabilities Net Minority Interest", "Total Liabilities"], "totalLiabilities"),
    (["Current Liabilities", "Total Current Liabilities"], "totalCurrentLiabilities"),
    (["Accounts Payable"], "accountPayables"),
    (["Current Debt", "Current Debt And Capital Lease Obligation"], "shortTermDebt"),
    (["Other Current Liabilities"], "otherCurrentLiabilities"),
    (["Long Term Debt", "Long Term Debt And Capital Lease Obligation"], "longTermDebt"),
    (["Other Non Current Liabilities"], "otherNonCurrentLiabilities"),
    (["Stockholders Equity", "Total Equity Gross Minority Interest", "Common Stock Equity"], "totalStockholdersEquity"),
    (["Retained Earnings"], "retainedEarnings"),
    (["Common Stock"], "commonStock"),
]

_CASHFLOW_CANDIDATES = [
    (["Operating Cash Flow", "Cash Flow From Continuing Operating Activities"], "operatingCashFlow"),
    (["Net Income", "Net Income From Continuing Operations"], "netIncome"),
    (["Depreciation And Amortization", "Depreciation Amortization Depletion"], "depreciationAndAmortization"),
    (["Stock Based Compensation"], "stockBasedCompensation"),
    (["Change In Working Capital", "Changes In Account Receivables"], "changeInWorkingCapital"),
    (["Accounts Receivable", "Change In Receivables"], "accountsReceivables"),
    (["Inventory", "Change In Inventory"], "inventory"),
    (["Accounts Payable", "Change In Payable"], "accountsPayables"),
    (["Capital Expenditure", "Capital Expenditures", "Purchase Of PPE"], "capitalExpenditure"),
    (["Free Cash Flow"], "freeCashFlow"),
    (["Purchase Of Investment", "Purchase Of Business"], "acquisitionsNet"),
    (["Sale Of Investment", "Proceeds From Sale Of Investment"], "salesMaturitiesOfInvestments"),
    (["Investing Cash Flow", "Cash Flow From Continuing Investing Activities"], "netCashUsedForInvestingActivities"),
    (["Common Stock Repurchased", "Repurchase Of Capital Stock"], "commonStockRepurchased"),
    (["Common Stock Issued", "Proceeds From Issuance Of Common Stock"], "commonStockIssued"),
    (["Common Stock Dividend Paid", "Cash Dividends Paid", "Payment Of Dividends"], "dividendsPaid"),
    (["Long Term Debt Issuance", "Proceeds From Debt"], "debtRepayment"),
    (["Financing Cash Flow", "Cash Flow From Continuing Financing Activities"], "netCashUsedProvidedByFinancingActivities"),
    (["End Cash Position", "Changes In Cash"], "netChangeInCash"),
]


def _yf_df_to_fmp(df: pd.DataFrame, field_candidates: list, limit: int) -> list[dict]:
    """Convert yfinance financial DataFrame to FMP-style list of dicts."""
    if df is None or df.empty:
        return []
    result = []
    for col in list(df.columns)[:limit]:
        try:
            date_str = col.date().isoformat()
        except Exception:
            date_str = str(col)[:10]
        row: dict = {"date": date_str}
        for candidates, fmp_key in field_candidates:
            val = None
            for name in candidates:
                if name in df.index:
                    raw = df.loc[name, col]
                    val = None if pd.isna(raw) else float(raw)
                    break
            row[fmp_key] = val
        result.append(row)
    return result


class DataPipeline:
    """Orchestrates FMP (paid) and yfinance (free fallback) into unified structures."""

    def __init__(self, fmp_api_key: Optional[str] = None):
        self.fmp = FMPClient(api_key=fmp_api_key)
        self.yf = YFinanceClient()

    def get_company_overview(self, ticker: str) -> dict:
        profile, yf_info = {}, {}
        try:
            profile = self.fmp.get_company_profile(ticker)
        except Exception:
            pass
        try:
            yf_info = self.yf.get_info(ticker)
        except Exception:
            pass
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
        quarterly = period == "quarter"
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

        if not income:
            try:
                df = self.yf.get_income_stmt(ticker, quarterly=quarterly)
                income = _yf_df_to_fmp(df, _INCOME_CANDIDATES, limit)
            except Exception:
                pass
        if not balance:
            try:
                df = self.yf.get_balance_sheet(ticker, quarterly=quarterly)
                balance = _yf_df_to_fmp(df, _BALANCE_CANDIDATES, limit)
            except Exception:
                pass
        if not cashflow:
            try:
                df = self.yf.get_cash_flow(ticker, quarterly=quarterly)
                cashflow = _yf_df_to_fmp(df, _CASHFLOW_CANDIDATES, limit)
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

        if not metrics and not ratios:
            try:
                info = self.yf.get_info(ticker)
                snap = {
                    "date": pd.Timestamp.now().date().isoformat(),
                    "priceEarningsRatio": info.get("trailingPE"),
                    "priceToBookRatio": info.get("priceToBook"),
                    "priceToSalesRatio": info.get("priceToSalesTrailing12Months"),
                    "debtEquityRatio": info.get("debtToEquity"),
                    "returnOnEquity": info.get("returnOnEquity"),
                    "returnOnAssets": info.get("returnOnAssets"),
                    "currentRatio": info.get("currentRatio"),
                    "quickRatio": info.get("quickRatio"),
                    "grossProfitMargin": info.get("grossMargins"),
                    "netProfitMargin": info.get("profitMargins"),
                    "operatingProfitMargin": info.get("operatingMargins"),
                    "enterpriseValueMultiple": info.get("enterpriseToEbitda"),
                    "marketCap": info.get("marketCap"),
                    "enterpriseValue": info.get("enterpriseValue"),
                    "evToEbitda": info.get("enterpriseToEbitda"),
                    "evToSales": info.get("enterpriseToRevenue"),
                    "revenuePerShare": info.get("revenuePerShare"),
                    "netIncomePerShare": info.get("trailingEps"),
                    "freeCashFlowPerShare": info.get("freeCashflow"),
                    "bookValuePerShare": info.get("bookValue"),
                }
                ratios = [snap]
                metrics = [snap]
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
