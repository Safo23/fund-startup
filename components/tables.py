import pandas as pd
import streamlit as st
from utils.helpers import fmt_large_number, fmt_percent, fmt_currency


_INCOME_ROWS = {
    "revenue": "Revenue",
    "costOfRevenue": "Cost of Revenue",
    "grossProfit": "Gross Profit",
    "researchAndDevelopmentExpenses": "R&D Expenses",
    "sellingGeneralAndAdministrativeExpenses": "SG&A Expenses",
    "operatingExpenses": "Operating Expenses",
    "operatingIncome": "Operating Income",
    "ebitda": "EBITDA",
    "depreciationAndAmortization": "D&A",
    "interestExpense": "Interest Expense",
    "interestIncome": "Interest Income",
    "totalOtherIncomeExpensesNet": "Other Income / Expense",
    "incomeBeforeTax": "Income Before Tax",
    "incomeTaxExpense": "Income Tax",
    "netIncome": "Net Income",
    "eps": "EPS (Basic)",
    "epsdiluted": "EPS (Diluted)",
    "weightedAverageShsOut": "Shares Outstanding",
    "weightedAverageShsOutDil": "Shares Outstanding (Diluted)",
}

_BALANCE_ROWS = {
    "totalAssets": "Total Assets",
    "totalCurrentAssets": "Current Assets",
    "cashAndCashEquivalents": "Cash & Equivalents",
    "shortTermInvestments": "Short-Term Investments",
    "netReceivables": "Accounts Receivable",
    "inventory": "Inventory",
    "otherCurrentAssets": "Other Current Assets",
    "propertyPlantEquipmentNet": "Property, Plant & Equipment",
    "goodwill": "Goodwill",
    "intangibleAssets": "Intangible Assets",
    "longTermInvestments": "Long-Term Investments",
    "totalNonCurrentAssets": "Total Non-Current Assets",
    "totalLiabilities": "Total Liabilities",
    "totalCurrentLiabilities": "Current Liabilities",
    "accountPayables": "Accounts Payable",
    "shortTermDebt": "Short-Term Debt",
    "otherCurrentLiabilities": "Other Current Liabilities",
    "longTermDebt": "Long-Term Debt",
    "otherNonCurrentLiabilities": "Other Non-Current Liabilities",
    "totalStockholdersEquity": "Shareholders Equity",
    "retainedEarnings": "Retained Earnings",
    "commonStock": "Common Stock",
}

_CASHFLOW_ROWS = {
    "operatingCashFlow": "Operating Cash Flow",
    "netIncome": "Net Income",
    "depreciationAndAmortization": "D&A",
    "stockBasedCompensation": "Stock-Based Compensation",
    "changeInWorkingCapital": "Change in Working Capital",
    "capitalExpenditure": "Capital Expenditure (CapEx)",
    "freeCashFlow": "Free Cash Flow",
    "acquisitionsNet": "Acquisitions",
    "salesMaturitiesOfInvestments": "Sale of Investments",
    "netCashUsedForInvestingActivities": "Investing Cash Flow",
    "commonStockRepurchased": "Share Buybacks",
    "commonStockIssued": "Stock Issued",
    "dividendsPaid": "Dividends Paid",
    "debtRepayment": "Debt Issuance / Repayment",
    "netCashUsedProvidedByFinancingActivities": "Financing Cash Flow",
    "netChangeInCash": "Net Change in Cash",
}


def _fmt_val(field: str, val) -> str:
    if val is None:
        return "—"
    if field in ("eps", "epsdiluted"):
        return f"${float(val):.2f}"
    if field in ("weightedAverageShsOut", "weightedAverageShsOutDil"):
        return fmt_large_number(val)
    return fmt_large_number(val)


def _build_stmt_df(data: list[dict], row_map: dict) -> pd.DataFrame:
    if not data:
        return pd.DataFrame()
    periods = [d.get("date", "N/A") for d in data]
    rows = {}
    for field, label in row_map.items():
        row = [_fmt_val(field, d.get(field)) for d in data]
        # Skip rows that are all dashes (field not available)
        if any(v != "—" for v in row):
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
    st.dataframe(df, use_container_width=True, height=min(50 + len(df) * 35, 600))


def render_metric_cards(metrics: dict[str, str | float | None], cols: int = 4) -> None:
    items = list(metrics.items())
    for i in range(0, len(items), cols):
        row = items[i : i + cols]
        columns = st.columns(cols)
        for col, (label, value) in zip(columns, row):
            col.metric(label=label, value=value if value is not None else "N/A")
