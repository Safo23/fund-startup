# Fund Startup — Stock Analysis Platform

## Project Overview

A Streamlit-based stock analysis platform that aggregates data from **Financial Modeling Prep (FMP)** and **yfinance** to provide financial statements, price charts, and key metrics for publicly traded companies.

## Project Structure

```
fund-startup/
├── app.py                          # Streamlit entry point (home page + global sidebar)
├── pages/
│   ├── 01_Financial_Statements.py  # Income, balance sheet, cash flow + charts
│   ├── 02_Stock_Analysis.py        # Price history, candlestick chart, analyst ratings
│   └── 03_Key_Metrics.py           # Valuation, profitability, growth, liquidity ratios
├── data/
│   ├── __init__.py
│   ├── fmp_client.py               # FMP REST API wrapper (cached with st.cache_data)
│   ├── yfinance_client.py          # yfinance wrapper (cached with st.cache_data)
│   └── pipeline.py                 # Orchestrates both sources; FMP-first, yfinance fallback
├── components/
│   ├── __init__.py
│   ├── charts.py                   # Plotly chart components (price, bar, gauge)
│   └── tables.py                   # Dataframe formatters and metric card renderer
├── utils/
│   ├── __init__.py
│   └── helpers.py                  # Number/percent/currency formatters, safe_get
├── .streamlit/
│   └── config.toml                 # Dark theme + server config
├── requirements.txt
├── .env.example
└── CLAUDE.md
```

## Running the App

```bash
# Install dependencies
pip install -r requirements.txt

# Set your FMP API key (or paste it in the sidebar at runtime)
cp .env.example .env
# Edit .env: FMP_API_KEY=your_key_here

# Launch
streamlit run app.py
```

The app runs at `http://localhost:8501` by default.

## Data Sources

### Financial Modeling Prep (FMP)
- Base URL: `https://financialmodelingprep.com/api/v3`
- Used for: income statements, balance sheets, cash flows, key metrics, ratios, quotes, company profiles
- Requires a free or paid API key from [financialmodelingprep.com](https://financialmodelingprep.com)
- Client: `data/fmp_client.py` — `FMPClient`

### yfinance
- Used for: OHLCV price history, company info, analyst recommendations, earnings dates, options
- No API key required
- Client: `data/yfinance_client.py` — `YFinanceClient`

### Data Pipeline (`data/pipeline.py`)
`DataPipeline` is the single interface pages use. It tries FMP first and silently falls back to yfinance when FMP fails or is unconfigured. Key methods:

| Method | Returns |
|--------|---------|
| `get_company_overview(ticker)` | Merged company profile dict |
| `get_financial_statements(ticker, period, limit)` | `{income, balance, cashflow}` lists |
| `get_key_metrics(ticker, period, limit)` | `{metrics, ratios}` lists |
| `get_price_data(ticker, period, interval)` | OHLCV `pd.DataFrame` |
| `get_quote(ticker)` | Live price snapshot dict |

## Caching Strategy

All API calls use `@st.cache_data` with appropriate TTLs:
- Live quotes: **5 minutes** (TTL 300s)
- Price history: **5 minutes**
- Financial statements / metrics: **1 hour** (TTL 3600s)

## Pages

### Financial Statements (`pages/01_Financial_Statements.py`)
- Controls: ticker, annual/quarterly period, number of periods
- Snapshot metric cards from latest period
- Three tabs: Income Statement, Balance Sheet, Cash Flow
- Each tab has a grouped bar chart + formatted dataframe table

### Stock Analysis (`pages/02_Stock_Analysis.py`)
- Controls: ticker, date range (1M–5Y), interval (daily/weekly/monthly)
- Live quote metrics: price, change, market cap, P/E, EPS
- Candlestick chart with optional volume overlay
- Trading statistics card grid
- Analyst recommendations table

### Key Metrics (`pages/03_Key_Metrics.py`)
- Gauge charts for P/E, P/B, P/S, Debt/Equity
- Four tabs: Valuation, Profitability, Growth, Liquidity
- Trend line charts + summary metric cards per tab

## Components

### `components/charts.py`
- `render_price_chart(df, ticker, show_volume)` — candlestick + volume bar chart
- `render_financial_bar_chart(data, fields, labels, title)` — grouped bar chart from FMP dicts
- `render_ratio_gauges(ratios)` — row of gauge indicators

### `components/tables.py`
- `render_financial_table(data, statement)` — formats FMP list into a readable dataframe
- `render_metric_cards(metrics, cols)` — renders `st.metric` cards in a grid

### `utils/helpers.py`
- `fmt_large_number(value)` — formats to K/M/B/T suffix
- `fmt_percent(value)` — formats as `"12.34%"`
- `fmt_currency(value, currency)` — formats with currency symbol
- `safe_get(data, *keys, default)` — nested dict lookup without KeyError

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `FMP_API_KEY` | Optional* | Financial Modeling Prep API key. Can also be entered in the sidebar at runtime. Without it, the app falls back to yfinance. |

*yfinance-only mode works without any API key.

## Development Notes

- All pages share the ticker stored in `st.session_state["ticker"]` set via the home page sidebar.
- The `DataPipeline` is instantiated fresh per page render; caching lives inside the individual client methods.
- Plotly uses `template="plotly_dark"` to match the dark Streamlit theme.
- To add a new page: create `pages/NN_Name.py` — Streamlit auto-discovers it.
- To add a new data field to a financial table: edit the row-map dicts in `components/tables.py`.
