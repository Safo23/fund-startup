import pandas as pd
import streamlit as st
from utils.helpers import fmt_large_number, fmt_percent, fmt_currency


_INCOME_ROWS = {
    "revenue": "Revenue",
    "costOfRevenue": "Cost of Revenue",
    "grossProfit": "Gross Profit",
    "operatingExpenses": "Operating Expenses",
    "operatingIncome": "Operating Income",
    "ebitda": "EBITDA",
    "netIncome": "Net Income",
    "eps": "EPS",
    "epsdiluted": "EPS Diluted",
}

_BALANCE_ROWS = {
    "totalAssets": "Total Assets",
    "totalCurrentAssets": "Current Assets",
    "cashAndCashEquivalents": "Cash & Equivalents",
    "totalLiabilities": "Total Liabilities",
    "totalCurrentLiabilities": "Current Liabilities",
    "longTermDebt": "Long-Term Debt",
    "totalStockholdersEquity": "Shareholders Equity",
}

_CASHFLOW_ROWS = {
    "operatingCashFlow": "Operating Cash Flow",
    "capitalExpenditure": "CapEx",
    "freeCashFlow": "Free Cash Flow",
    "dividendsPaid": "Dividends Paid",
    "netCashUsedForInvestingActivities": "Investing Activities",
    "netCashUsedProvidedByFinancingActivities": "Financing Activities",
}


def _build_stmt_df(data: list[dict], row_map: dict) -> pd.DataFrame:
    if not data:
        return pd.DataFrame()
    periods = [d.get("date", "N/A") for d in data]
    rows = {}
    for field, label in row_map.items():
        row = []
        for d in data:
            val = d.get(field)
            if field in ("eps", "epsdiluted"):
                row.append(f"${val:.2f}" if val is not None else "N/A")
            else:
                row.append(fmt_large_number(val))
        rows[label] = row
    return pd.DataFrame(rows, index=periods).T


def render_financial_table(data: list[dict], statement: str = "income") -> None:
    row_maps = {
        "income": _INCOME_ROWS,
        "balance": _BALANCE_ROWS,
        "cashflow": _CASHFLOW_ROWS,
    }
    row_map = row_maps.get(statement, _INCOME_ROWS)
    df = _build_stmt_df(data, row_map)
    if df.empty:
        st.info("No data to display. Check your API key or ticker symbol.")
        return
    st.dataframe(df, use_container_width=True)


def render_metric_cards(metrics: dict[str, str | float | None], cols: int = 4) -> None:
    items = list(metrics.items())
    for i in range(0, len(items), cols):
        row = items[i : i + cols]
        columns = st.columns(cols)
        for col, (label, value) in zip(columns, row):
            col.metric(label=label, value=value if value is not None else "N/A")
