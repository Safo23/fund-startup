#!/usr/bin/env python3
"""
Stock Valuation Excel Generator — Palantir (PLTR)
Run `python generate_valuation.py` to regenerate.
Live data is fetched from yfinance when network allows; otherwise
the script falls back to curated static data (current as of Jun 2025).
Output: PLTR_Valuation.xlsx
"""

import warnings
warnings.filterwarnings("ignore")

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from datetime import datetime

# ── Palette ──────────────────────────────────────────────────────────────────
NAVY    = "1F3864"
BLUE    = "2E75B6"
LBLUE   = "BDD7EE"
LGRAY   = "F2F2F2"
WHITE   = "FFFFFF"
GREEN   = "375623"
LGREEN  = "E2EFDA"
RED_C   = "C00000"
LRED    = "FFE0E0"
GOLD    = "C9A227"
LGOLD   = "FFF2CC"
LORANGE = "FCE4D6"
DGRAY   = "595959"


# ── Style helpers ─────────────────────────────────────────────────────────────

def thin():
    s = Side(style="thin", color="BFBFBF")
    return Border(left=s, right=s, top=s, bottom=s)

def apply_border(ws, r1, c1, r2, c2):
    for row in ws.iter_rows(min_row=r1, min_col=c1, max_row=r2, max_col=c2):
        for cell in row:
            cell.border = thin()

def hdr(cell, text, bg=NAVY, fg=WHITE, size=10, bold=True, align="center", wrap=False):
    cell.value = text
    cell.font  = Font(bold=bold, color=fg, size=size, name="Calibri")
    cell.fill  = PatternFill("solid", fgColor=bg)
    cell.alignment = Alignment(horizontal=align, vertical="center", wrap_text=wrap)

def subhdr(cell, text, bg=BLUE, fg=WHITE, size=9):
    cell.value = text
    cell.font  = Font(bold=True, color=fg, size=size, name="Calibri")
    cell.fill  = PatternFill("solid", fgColor=bg)
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

def lbl(cell, text, bold=True, size=9, bg=LGRAY, align="left"):
    cell.value = text
    cell.font  = Font(bold=bold, size=size, name="Calibri")
    cell.fill  = PatternFill("solid", fgColor=bg)
    cell.alignment = Alignment(horizontal=align, vertical="center", wrap_text=True)

def val(cell, value, size=9, align="center", bg=WHITE, bold=False,
        num_fmt=None, color=None):
    cell.value = value
    cell.font  = Font(size=size, name="Calibri", bold=bold,
                      color=color if color else "000000")
    cell.fill  = PatternFill("solid", fgColor=bg)
    cell.alignment = Alignment(horizontal=align, vertical="center", wrap_text=True)
    if num_fmt:
        cell.number_format = num_fmt

def rbg(i):
    return WHITE if i % 2 == 0 else LGRAY

def section_title(ws, row, c1, c2, text, bg=BLUE):
    ws.merge_cells(start_row=row, start_column=c1, end_row=row, end_column=c2)
    hdr(ws.cell(row, c1), text, bg=bg, size=11)
    ws.row_dimensions[row].height = 22

def spacer(ws, row, h=5):
    ws.row_dimensions[row].height = h


# ── Live data attempt ─────────────────────────────────────────────────────────

LIVE = {}           # populated if network is reachable

def try_live_fetch():
    global LIVE
    try:
        import yfinance as yf
        import pandas as pd

        TICKERS = ["PLTR", "SNOW", "AI", "BBAI", "SAIC", "BAH", "LDOS", "VRNT", "CRM", "MSFT", "SPY"]
        print("  Attempting live yfinance fetch …", flush=True)
        for sym in TICKERS:
            try:
                t = yf.Ticker(sym)
                i = t.info
                if not i:
                    continue
                mktcap = i.get("marketCap") or 0
                debt   = i.get("totalDebt") or 0
                cash   = i.get("totalCash") or 0
                rev    = i.get("totalRevenue") or 0
                ev     = mktcap + debt - cash
                LIVE[sym] = {
                    "price":      i.get("currentPrice") or i.get("regularMarketPrice") or i.get("previousClose"),
                    "mktcap":     mktcap,
                    "ev":         ev,
                    "ev_rev":     ev / rev if rev else None,
                    "pe_ttm":     i.get("trailingPE"),
                    "pe_fwd":     i.get("forwardPE"),
                    "eps_ttm":    i.get("trailingEps"),
                    "eps_fwd":    i.get("forwardEps"),
                    "rev_growth": i.get("revenueGrowth"),
                    "gross_m":    i.get("grossMargins"),
                    "beta":       i.get("beta"),
                    "shares":     i.get("sharesOutstanding"),
                    "total_cash": cash,
                    "total_debt": debt,
                }
            except Exception:
                pass

        # Price history for PLTR
        try:
            t = yf.Ticker("PLTR")
            hist = t.history(period="3y", interval="1d")
            hist.index = pd.to_datetime(hist.index).tz_localize(None)
            hist_q = hist.resample("QE").agg(
                {"Open": "first", "High": "max", "Low": "min",
                 "Close": "last", "Volume": "mean"}
            ).dropna().tail(12)
            LIVE["PLTR_HIST"] = hist_q

            edf = t.earnings_dates
            if edf is not None and not edf.empty:
                past = edf[edf["EPS Actual"].notna()].sort_index(ascending=False).head(8)
                rows = []
                for dt, rr in past.iterrows():
                    actual = rr.get("EPS Actual")
                    est    = rr.get("EPS Estimate")
                    beat   = (actual - est) if (actual is not None and est is not None) else None
                    pct    = (beat / abs(est)) if (beat is not None and est and est != 0) else None
                    rows.append((
                        f"Q{((dt.month-1)//3)+1} {dt.year}",
                        dt.strftime("%b %d, %Y"),
                        actual, est, beat, pct,
                    ))
                LIVE["EARNINGS"] = rows

            inst = t.institutional_holders
            if inst is not None and not inst.empty:
                rows2 = []
                for _, rr in inst.head(4).iterrows():
                    sh  = rr.get("Shares", 0)
                    pct = rr.get("% Out", 0)
                    pct_s = f"{pct*100:.1f}%" if pct < 1 else f"{pct:.1f}%"
                    rows2.append((str(rr.get("Holder", "")), f"{sh/1e6:.0f}M", pct_s))
                LIVE["INST"] = rows2
        except Exception:
            pass

        print(f"  Live data fetched for: {list(LIVE.keys())}")
    except Exception as e:
        print(f"  Live fetch unavailable ({e}). Using static data.")


def g(sym, key, default=None):
    """Get live value if available, else return default."""
    return LIVE.get(sym, {}).get(key, default)


def fmt_b(n, prefix="$"):
    if n is None:
        return "N/A"
    try:
        n = float(n)
    except (TypeError, ValueError):
        return "N/A"
    if n >= 1e12:
        return f"{prefix}{n/1e12:.2f}T"
    if n >= 1e9:
        return f"{prefix}{n/1e9:.2f}B"
    if n >= 1e6:
        return f"{prefix}{n/1e6:.0f}M"
    return f"{prefix}{n:.0f}"

def fmt_x(n):
    try:
        return f"{float(n):.1f}x"
    except (TypeError, ValueError):
        return "N/A"

def fmt_pct(n):
    try:
        return f"{float(n)*100:.1f}%"
    except (TypeError, ValueError):
        return "N/A"


# ═══════════════════════════════════════════════════════════════════════════════
# SHEET 1 — COMPANY OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════════

# Static snapshots (Jun 2025)
STATIC = {
    "PLTR": {
        "price":     120.0,
        "mktcap":    2.60e11,
        "total_cash":5.8e9,
        "total_debt":0,
        "ev":        2.54e11,
        "ev_rev":    28.0,
        "pe_ttm":    600.0,
        "pe_fwd":    200.0,
        "eps_ttm":   0.20,
        "eps_fwd":   0.52,
        "rev_growth":0.36,
        "gross_m":   0.81,
        "beta":      2.50,
        "shares":    2.16e9,
    },
    "SNOW": {
        "price":     160.0, "mktcap":5.4e10, "pe_ttm":None, "pe_fwd":170.0,
        "eps_ttm":-1.80, "eps_fwd":0.93, "rev_growth":0.26, "gross_m":0.67,
        "ev_rev":13.0, "beta":1.80,
    },
    "AI": {
        "price":  33.0, "mktcap":4.0e9, "pe_ttm":None, "pe_fwd":None,
        "eps_ttm":-0.90, "eps_fwd":-0.35, "rev_growth":0.25, "gross_m":0.60,
        "ev_rev":5.0, "beta":2.20,
    },
    "BBAI": {
        "price":  4.5, "mktcap":1.0e9, "pe_ttm":None, "pe_fwd":None,
        "eps_ttm":-0.40, "eps_fwd":-0.10, "rev_growth":0.15, "gross_m":0.22,
        "ev_rev":3.0, "beta":2.50,
    },
    "SAIC": {
        "price":  118.0, "mktcap":5.0e9, "pe_ttm":14.0, "pe_fwd":12.0,
        "eps_ttm":8.0, "eps_fwd":9.5, "rev_growth":0.04, "gross_m":0.11,
        "ev_rev":0.35, "beta":0.70,
    },
    "BAH": {
        "price":  148.0, "mktcap":1.9e10, "pe_ttm":20.0, "pe_fwd":18.0,
        "eps_ttm":7.2, "eps_fwd":8.2, "rev_growth":0.13, "gross_m":0.26,
        "ev_rev":1.5, "beta":0.80,
    },
    "LDOS": {
        "price":  168.0, "mktcap":2.3e10, "pe_ttm":18.0, "pe_fwd":15.0,
        "eps_ttm":9.0, "eps_fwd":11.0, "rev_growth":0.07, "gross_m":0.16,
        "ev_rev":0.90, "beta":0.75,
    },
    "VRNT": {
        "price":  24.0, "mktcap":1.5e9, "pe_ttm":None, "pe_fwd":10.0,
        "eps_ttm":-0.50, "eps_fwd":2.4, "rev_growth":0.06, "gross_m":0.66,
        "ev_rev":2.0, "beta":0.90,
    },
    "CRM": {
        "price":  285.0, "mktcap":2.7e11, "pe_ttm":43.0, "pe_fwd":28.0,
        "eps_ttm":6.6, "eps_fwd":10.2, "rev_growth":0.09, "gross_m":0.77,
        "ev_rev":6.5, "beta":1.40,
    },
    "MSFT": {
        "price":  465.0, "mktcap":3.5e12, "pe_ttm":34.0, "pe_fwd":29.0,
        "eps_ttm":13.6, "eps_fwd":16.0, "rev_growth":0.15, "gross_m":0.69,
        "ev_rev":12.0, "beta":0.90,
    },
    "SPY": {
        "pe_ttm": 25.0, "pe_fwd": 22.0,
    },
}

COMP_NAMES = {
    "PLTR": "Palantir Technologies",
    "SNOW": "Snowflake",
    "AI":   "C3.ai",
    "BBAI": "BigBear.ai",
    "SAIC": "Sci. Applications Intl.",
    "BAH":  "Booz Allen Hamilton",
    "LDOS": "Leidos Holdings",
    "VRNT": "Verint Systems",
    "CRM":  "Salesforce",
    "MSFT": "Microsoft",
}


def gv(sym, key):
    """Live data if available, else static snapshot."""
    live_val = g(sym, key)
    if live_val is not None:
        return live_val
    return STATIC.get(sym, {}).get(key)


def build_overview(wb):
    ws = wb.create_sheet("1. Overview")
    ws.sheet_view.showGridLines = False

    for col, w in zip("ABCDEFGH", [2, 22, 30, 22, 30, 22, 22, 2]):
        ws.column_dimensions[col].width = w

    r = 1

    # Banner
    ws.merge_cells(f"B{r}:G{r}")
    hdr(ws.cell(r, 2),
        "PALANTIR TECHNOLOGIES INC (PLTR) — COMPANY OVERVIEW",
        bg=NAVY, size=13)
    ws.row_dimensions[r].height = 32
    r += 1

    ws.merge_cells(f"B{r}:G{r}")
    src = "LIVE via yfinance" if LIVE.get("PLTR") else "STATIC (Jun 2025)"
    sub = ws.cell(r, 2)
    sub.value = (
        f"Last refreshed: {datetime.now().strftime('%B %d, %Y  %H:%M')}  |  "
        f"Data source: {src}"
    )
    sub.font  = Font(italic=True, size=8, color=DGRAY, name="Calibri")
    sub.alignment = Alignment(horizontal="right", vertical="center")
    ws.row_dimensions[r].height = 14
    r += 1
    spacer(ws, r); r += 1

    # ── Company Profile ───────────────────────────────────────────────────────
    section_title(ws, r, 2, 7, "COMPANY PROFILE"); r += 1

    profile_rows = [
        ("Ticker",          "PLTR",                               "Exchange",         "NYSE"),
        ("Full Name",       "Palantir Technologies Inc.",         "IPO Date",         "September 30, 2020"),
        ("CEO",             "Alexander C. Karp",                  "Founded",          "2003"),
        ("Headquarters",    "Denver, CO  (formerly Palo Alto)",   "Employees",        "~3,600 (FY24)"),
        ("Sector",          "Technology",                         "Industry",         "Software — Infrastructure / AI"),
        ("Website",         "palantir.com",                       "Fiscal Year End",  "December 31"),
    ]

    for label1, v1, label2, v2 in profile_rows:
        ws.row_dimensions[r].height = 18
        lbl(ws.cell(r, 2), label1)
        val(ws.cell(r, 3), v1, align="left", bg=WHITE)
        lbl(ws.cell(r, 4), label2)
        val(ws.cell(r, 5), v2, align="left", bg=WHITE)
        ws.merge_cells(start_row=r, start_column=6, end_row=r, end_column=7)
        r += 1

    ws.row_dimensions[r].height = 18
    lbl(ws.cell(r, 2), "Business")
    ws.merge_cells(start_row=r, start_column=3, end_row=r+2, end_column=7)
    c = ws.cell(r, 3)
    c.value = (
        "Palantir builds AI-powered decision-intelligence platforms for government and enterprise clients. "
        "Its three core products — Gotham (government ops & targeting), Foundry (enterprise data fabric), "
        "and Apollo (continuous deployment on classified / air-gapped infrastructure) — are increasingly "
        "unified by AIP (AI Platform, launched 2023), which orchestrates large language models within "
        "secure, auditable workflows. Revenue splits ~65% Government / ~35% Commercial. "
        "Palantir achieved its first full year of GAAP profitability in FY2024 and has no debt."
    )
    c.font  = Font(size=9, name="Calibri")
    c.fill  = PatternFill("solid", fgColor=WHITE)
    c.alignment = Alignment(wrap_text=True, vertical="top", horizontal="left")
    apply_border(ws, r-len(profile_rows), 2, r+2, 7)
    r += 3
    spacer(ws, r); r += 1

    # ── Products & Divisions ──────────────────────────────────────────────────
    section_title(ws, r, 2, 7, "PRODUCTS & DIVISIONS"); r += 1

    for c_i, h in enumerate(
        ["Division", "Platform / Product", "Customer Type", "Key Capability", "Est. % Revenue (FY24)"], 2
    ):
        subhdr(ws.cell(r, c_i), h)
    ws.row_dimensions[r].height = 18
    dh = r; r += 1

    divisions = [
        ("Government – US",    "Gotham + AIP",         "DoD, NGA, NSA, USAF, Army",     "Mission ops, AI-assisted targeting, C2, logistics",     "~38%"),
        ("Government – Intl.", "Gotham / MetaConst.",  "NATO allies, UK MoD, JSDF",     "Battlefield awareness, satellite analytics, NATO cloud", "~14%"),
        ("Commercial – US",    "Foundry + AIP",        "Fortune 500, healthcare, energy","Data integration, LLM orchestration, AIP Bootcamps",    "~35%"),
        ("Commercial – Intl.", "Foundry + Apollo",     "European / APAC enterprises",   "Supply chain, manufacturing, automotive analytics",      "~13%"),
        ("Apollo (cross-cut)", "Apollo",               "Gov + Commercial",              "Continuous deployment on classified / edge infra",       "Platform infra"),
    ]

    for i, rd in enumerate(divisions):
        bg = rbg(i)
        ws.row_dimensions[r].height = 18
        for c_i, v in enumerate(rd, 2):
            cell = ws.cell(r, c_i)
            cell.value = v
            cell.font  = Font(size=9, name="Calibri")
            cell.fill  = PatternFill("solid", fgColor=bg)
            cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
        r += 1

    apply_border(ws, dh, 2, r-1, 6)
    spacer(ws, r); r += 1

    # ── Share Structure ───────────────────────────────────────────────────────
    section_title(ws, r, 2, 7, "SHARE STRUCTURE"); r += 1

    for c_i, h in enumerate(
        ["Class", "Voting Rights", "Who Holds It", "Transferable?", "Key Notes"], 2
    ):
        subhdr(ws.cell(r, c_i), h)
    ws.row_dimensions[r].height = 18
    sh_hdr = r; r += 1

    share_classes = [
        ("Class A", "1 vote / share",
         "Public investors (NYSE)",
         "Yes",
         "Primary publicly-traded share. Eligible for index inclusion (S&P 500 since Sep 2023)."),
        ("Class B", "10 votes / share",
         "Founders & early employees",
         "Yes → converts to Class A on transfer",
         "Founders retain voting control through concentrated Class B ownership."),
        ("Class F", "Variable — dynamically adjusts to keep founder bloc at ≤49.999% of total votes",
         "Karp, Thiel, Cohen (three co-founders only)",
         "No — non-transferable",
         "Unique anti-dilution mechanism. Prevents founders from losing control as shares are issued. "
         "Expires Sep 2034 or when founders' combined holding falls below 100M shares."),
    ]

    for i, rd in enumerate(share_classes):
        bg = rbg(i)
        ws.row_dimensions[r].height = 24
        for c_i, v in enumerate(rd, 2):
            cell = ws.cell(r, c_i)
            cell.value = v
            cell.font  = Font(size=9, name="Calibri")
            cell.fill  = PatternFill("solid", fgColor=bg)
            cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
        r += 1

    apply_border(ws, sh_hdr, 2, r-1, 6)
    spacer(ws, r); r += 1

    # ── Ownership ─────────────────────────────────────────────────────────────
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=4)
    hdr(ws.cell(r, 2), "MANAGEMENT & INSIDER OWNERSHIP", bg=BLUE, size=10)
    ws.merge_cells(start_row=r, start_column=5, end_row=r, end_column=7)
    hdr(ws.cell(r, 5), "MAJOR INSTITUTIONAL HOLDERS", bg=BLUE, size=10)
    ws.row_dimensions[r].height = 22
    r += 1

    for c_i, h in enumerate(["Name / Role", "Shares (est.)", "% Outstanding"], 2):
        subhdr(ws.cell(r, c_i), h)
    for c_i, h in enumerate(["Institution", "Shares (est.)", "% Outstanding"], 5):
        subhdr(ws.cell(r, c_i), h)
    ws.row_dimensions[r].height = 18
    own_hdr = r; r += 1

    insider_rows = [
        ("Alexander Karp (CEO)",         "~270M",  "~12%"),
        ("Peter Thiel (Co-founder)",     "~675M",  "~30%"),
        ("Stephen Cohen (Co-founder)",   "~120M",  "~5%"),
        ("Total Insider / Founder",      "~1,065M","~47%"),
    ]

    inst_rows = LIVE.get("INST") or [
        ("Vanguard Group",    "~1,150M", "~8.1%"),
        ("BlackRock",         "~870M",   "~6.1%"),
        ("State Street",      "~480M",   "~3.4%"),
        ("Capital Research",  "~290M",   "~2.0%"),
    ]

    for i, (ins, inst) in enumerate(zip(insider_rows, inst_rows)):
        bg = rbg(i)
        is_total = (i == len(insider_rows) - 1)
        fill_bg  = LBLUE if is_total else bg
        ws.row_dimensions[r].height = 18
        for c_i, v in enumerate(ins, 2):
            cell = ws.cell(r, c_i)
            cell.value = v
            cell.font  = Font(size=9, name="Calibri", bold=is_total)
            cell.fill  = PatternFill("solid", fgColor=fill_bg)
            cell.alignment = Alignment(
                horizontal="left" if c_i == 2 else "center", vertical="center"
            )
        for c_i, v in enumerate(inst, 5):
            cell = ws.cell(r, c_i)
            cell.value = v
            cell.font  = Font(size=9, name="Calibri")
            cell.fill  = PatternFill("solid", fgColor=bg)
            cell.alignment = Alignment(
                horizontal="left" if c_i == 5 else "center", vertical="center"
            )
        r += 1

    apply_border(ws, own_hdr, 2, r-1, 7)
    spacer(ws, r); r += 1

    # ── Key Metrics ───────────────────────────────────────────────────────────
    section_title(ws, r, 2, 7, "KEY METRICS — CURRENT & STREET CONSENSUS ESTIMATES"); r += 1

    for c_i, h in enumerate(
        ["Metric", "Current / LTM", "FY2024A", "FY2025E (Cons.)", "FY2026E (Cons.)", "Notes"], 2
    ):
        subhdr(ws.cell(r, c_i), h)
    ws.row_dimensions[r].height = 18
    met_hdr = r; r += 1

    price_f  = gv("PLTR", "price")     or 120.0
    mktcap   = gv("PLTR", "mktcap")    or 2.60e11
    cash     = gv("PLTR", "total_cash")or 5.8e9
    debt     = gv("PLTR", "total_debt")or 0
    ev       = mktcap + (debt or 0) - (cash or 0)
    eps_ttm  = gv("PLTR", "eps_ttm")   or 0.20
    eps_fwd  = gv("PLTR", "eps_fwd")   or 0.52
    pe_ttm   = gv("PLTR", "pe_ttm")
    pe_fwd   = gv("PLTR", "pe_fwd")
    shares   = gv("PLTR", "shares")    or 2.16e9
    rev_ttm  = 3.50e9  # FY24 annualized / TTM est.

    metrics = [
        ("Stock Price",               f"${price_f:.2f}",  "—",         "—",         "—",       "As of last market close"),
        ("Market Cap",                fmt_b(mktcap),       "—",         "—",         "—",       ""),
        ("Enterprise Value (EV)",     fmt_b(ev),           "—",         "—",         "—",       "EV = Mkt Cap + Debt − Cash; PLTR is net-cash so EV < Mkt Cap"),
        ("Revenue",                   fmt_b(rev_ttm),      "$2.87B",    "$3.75B+",   "$4.69B",  "Company guided ≥$3.75B for FY25"),
        ("Revenue Growth YoY",        "—",                 "+29%",      "+31%",      "+25%",    ""),
        ("Adj. Operating Income",     "—",                 "$1.09B",    "$1.45B",    "$1.85B",  "Company-defined; ~38% margin FY24; excludes SBC"),
        ("Adj. EBITDA Margin",        "—",                 "~38%",      "~39%",      "~40%",    ""),
        ("EPS (GAAP, diluted)",       f"${eps_ttm:.3f}",  "$0.06",     "$0.14",     "$0.24",   "First full profitable GAAP year: FY2024"),
        ("EPS (Adj., diluted)",       f"${eps_fwd:.3f}",  "$0.41",     "$0.52",     "$0.71",   "Primary Street metric; excludes SBC"),
        ("P/E (GAAP, TTM)",           fmt_x(pe_ttm),       "—",         "—",         "—",       "Very high — GAAP EPS is tiny vs. stock price"),
        ("P/E (Adj., NTM)",           fmt_x(pe_fwd),       "~85x",      "~230x",     "~170x",   "AI premium; elevated vs. any historical comp"),
        ("EV / Revenue (NTM)",        "—",                 "—",         "~28x",      "~22x",    ""),
        ("EV / EBITDA (NTM)",         "—",                 "—",         "~70x",      "~55x",    "Key relative valuation metric"),
        ("Diluted Shares Outstanding",f"{shares/1e9:.2f}B","~2.16B",   "~2.20B",    "~2.25B",  "SBC adds ~3-4% dilution per year"),
        ("Free Cash Flow (Adj.)",     "—",                 "$1.15B",    "$1.40B",    "$1.75B",  "Adj. FCF margin ~40%; near-zero CapEx"),
        ("Net Cash",                  fmt_b(cash - debt),  "~$5.2B",    "—",         "—",       "Debt-free; growing cash balance"),
        ("Consensus Rating",          "—",                 "—",         "~Hold/Buy", "—",       "Wide dispersion; bulls on AI, bears on valuation"),
        ("Consensus Price Target",    "—",                 "—",         "~$95–110",  "—",       "Street median; PLTR often trades above consensus PT"),
    ]

    for i, row_data in enumerate(metrics):
        bg = rbg(i)
        ws.row_dimensions[r].height = 17
        for c_i, v in enumerate(row_data, 2):
            cell = ws.cell(r, c_i)
            cell.value = v
            cell.font  = Font(size=9, name="Calibri", bold=(c_i == 2))
            cell.fill  = PatternFill("solid", fgColor=bg)
            cell.alignment = Alignment(
                horizontal="left" if c_i in (2, 7) else "center",
                vertical="center", wrap_text=True
            )
        r += 1

    apply_border(ws, met_hdr, 2, r-1, 7)
    spacer(ws, r); r += 1

    # ── Earnings vs Consensus ─────────────────────────────────────────────────
    section_title(ws, r, 2, 7, "HISTORICAL EARNINGS vs. CONSENSUS  (Adj. EPS per diluted share)"); r += 1

    for c_i, h in enumerate(
        ["Quarter", "Report Date", "Adj. EPS Actual", "Adj. EPS Estimate", "Beat / Miss ($)", "Beat / Miss (%)"], 2
    ):
        subhdr(ws.cell(r, c_i), h)
    ws.row_dimensions[r].height = 18
    earn_hdr = r; r += 1

    earnings_hist = LIVE.get("EARNINGS") or [
        ("Q1 2025", "May 5, 2025",    0.13, 0.12,  0.01,  0.083),
        ("Q4 2024", "Feb 3, 2025",    0.14, 0.11,  0.03,  0.273),
        ("Q3 2024", "Nov 4, 2024",    0.10, 0.09,  0.01,  0.111),
        ("Q2 2024", "Aug 5, 2024",    0.09, 0.08,  0.01,  0.125),
        ("Q1 2024", "May 6, 2024",    0.08, 0.08,  0.00,  0.000),
        ("Q4 2023", "Feb 5, 2024",    0.08, 0.07,  0.01,  0.143),
        ("Q3 2023", "Nov 2, 2023",    0.07, 0.06,  0.01,  0.167),
        ("Q2 2023", "Aug 7, 2023",    0.05, 0.05,  0.00,  0.000),
    ]

    for i, (qtr, rdate, actual, est, beat, pct) in enumerate(earnings_hist):
        bg = rbg(i)
        ws.row_dimensions[r].height = 17
        ws.cell(r, 2).value = qtr
        ws.cell(r, 3).value = rdate
        ws.cell(r, 4).value = actual
        ws.cell(r, 4).number_format = '$0.000'
        ws.cell(r, 5).value = est
        ws.cell(r, 5).number_format = '$0.000'
        ws.cell(r, 6).value = beat
        ws.cell(r, 6).number_format = '$0.000'
        ws.cell(r, 7).value = pct
        ws.cell(r, 7).number_format = '0.0%'

        beat_bg    = LGREEN if (beat is not None and beat >= 0) else LRED
        beat_col   = GREEN  if (beat is not None and beat >= 0) else RED_C

        for c_i in range(2, 8):
            cell = ws.cell(r, c_i)
            cell.font = Font(
                size=9, name="Calibri",
                bold=(c_i in (6, 7)),
                color=beat_col if c_i in (6, 7) and beat is not None else "000000",
            )
            cell.fill = PatternFill(
                "solid",
                fgColor=beat_bg if c_i in (6, 7) and beat is not None else bg,
            )
            cell.alignment = Alignment(
                horizontal="left" if c_i == 2 else "center", vertical="center"
            )
        r += 1

    apply_border(ws, earn_hdr, 2, r-1, 7)
    spacer(ws, r); r += 1

    # ── Historical Price ──────────────────────────────────────────────────────
    section_title(ws, r, 2, 7, "HISTORICAL STOCK PRICE — QUARTERLY"); r += 1

    for c_i, h in enumerate(
        ["Quarter", "Period End", "Open", "High", "Low", "Close", "Avg. Daily Vol (M)"], 2
    ):
        subhdr(ws.cell(r, c_i), h)
    ws.row_dimensions[r].height = 18
    price_hdr = r; r += 1

    hist_q = LIVE.get("PLTR_HIST")

    if hist_q is not None and not hist_q.empty:
        for i, (dt, rr) in enumerate(hist_q.iterrows()):
            bg = rbg(i)
            ws.row_dimensions[r].height = 17
            ws.cell(r, 2).value = f"Q{((dt.month-1)//3)+1} {dt.year}"
            ws.cell(r, 3).value = dt.strftime("%b %d, %Y")
            ws.cell(r, 4).value = round(float(rr["Open"]),  2)
            ws.cell(r, 5).value = round(float(rr["High"]),  2)
            ws.cell(r, 6).value = round(float(rr["Low"]),   2)
            ws.cell(r, 7).value = round(float(rr["Close"]), 2)
            ws.cell(r, 8).value = round(float(rr["Volume"]) / 1e6, 1)
            for c_i in range(2, 9):
                cell = ws.cell(r, c_i)
                cell.font  = Font(size=9, name="Calibri")
                cell.fill  = PatternFill("solid", fgColor=bg)
                cell.alignment = Alignment(
                    horizontal="left" if c_i == 2 else "center", vertical="center"
                )
                if 4 <= c_i <= 7:
                    cell.number_format = "$0.00"
            r += 1
    else:
        # Static quarterly price history (PLTR, curated)
        static_price = [
            ("Q3 2022", "Sep 30, 2022",   8.18,  10.20,  5.86,  8.18,  42.1),
            ("Q4 2022", "Dec 31, 2022",   8.20,  9.75,   5.92,  7.10,  38.5),
            ("Q1 2023", "Mar 31, 2023",   7.08,  9.85,   6.41,  8.20,  45.2),
            ("Q2 2023", "Jun 30, 2023",   8.22,  19.20,  7.94,  16.22, 65.8),
            ("Q3 2023", "Sep 30, 2023",   16.30, 21.05, 13.58,  15.49, 58.4),
            ("Q4 2023", "Dec 31, 2023",   15.55, 23.10, 14.42,  22.36, 61.0),
            ("Q1 2024", "Mar 31, 2024",   22.38, 27.50, 19.60,  24.56, 72.3),
            ("Q2 2024", "Jun 30, 2024",   24.60, 30.25, 20.00,  27.62, 68.7),
            ("Q3 2024", "Sep 30, 2024",   27.65, 38.20, 25.10,  37.44, 95.2),
            ("Q4 2024", "Dec 31, 2024",   37.50, 84.80, 36.60,  78.54, 148.6),
            ("Q1 2025", "Mar 31, 2025",   78.60, 125.00,68.40,  89.62, 162.3),
            ("Q2 2025", "Jun 13, 2025",   90.00, 135.00,82.00,  120.00,175.0),
        ]
        for i, (qtr, end, o, h, lo, cl, vol) in enumerate(static_price):
            bg = rbg(i)
            ws.row_dimensions[r].height = 17
            ws.cell(r, 2).value = qtr
            ws.cell(r, 3).value = end
            ws.cell(r, 4).value = o
            ws.cell(r, 5).value = h
            ws.cell(r, 6).value = lo
            ws.cell(r, 7).value = cl
            ws.cell(r, 8).value = vol
            for c_i in range(2, 9):
                cell = ws.cell(r, c_i)
                cell.font  = Font(size=9, name="Calibri")
                cell.fill  = PatternFill("solid", fgColor=bg)
                cell.alignment = Alignment(
                    horizontal="left" if c_i == 2 else "center", vertical="center"
                )
                if 4 <= c_i <= 7:
                    cell.number_format = "$0.00"
            r += 1

    apply_border(ws, price_hdr, 2, r-1, 8)
    return ws


# ═══════════════════════════════════════════════════════════════════════════════
# SHEET 2 — COMPS
# ═══════════════════════════════════════════════════════════════════════════════

def build_comps(wb):
    ws = wb.create_sheet("2. Comps")
    ws.sheet_view.showGridLines = False

    col_widths = [2, 8, 24, 10, 13, 10, 10, 11, 11, 11, 10, 10, 10, 2]
    for i, w in enumerate(col_widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

    r = 1

    ws.merge_cells(f"B{r}:M{r}")
    hdr(ws.cell(r, 2), "COMPARABLE COMPANIES ANALYSIS — PALANTIR (PLTR)", bg=NAVY, size=13)
    ws.row_dimensions[r].height = 32
    r += 1

    ws.merge_cells(f"B{r}:M{r}")
    src = "LIVE via yfinance" if LIVE.get("PLTR") else "STATIC (Jun 2025)"
    ts = ws.cell(r, 2)
    ts.value = (
        f"Last refreshed: {datetime.now().strftime('%B %d, %Y  %H:%M')}  |  "
        f"Data source: {src}  |  "
        "Yellow row = PLTR (subject company)"
    )
    ts.font  = Font(italic=True, size=8, color=DGRAY, name="Calibri")
    ts.alignment = Alignment(horizontal="right", vertical="center")
    ws.row_dimensions[r].height = 14
    r += 1
    spacer(ws, r); r += 1

    # ── Market Reference ──────────────────────────────────────────────────────
    section_title(ws, r, 2, 13, "MARKET REFERENCE  —  S&P 500 / Nasdaq-100"); r += 1

    spy_pe_ttm = gv("SPY", "pe_ttm") or 25.0
    spy_pe_fwd = gv("SPY", "pe_fwd") or 22.0
    pltr_pe_fwd = gv("PLTR", "pe_fwd") or 200.0

    for c_i, h in enumerate(["Metric", "Value", "Comment"], 2):
        subhdr(ws.cell(r, c_i), h)
    ws.merge_cells(start_row=r, start_column=4, end_row=r, end_column=13)
    subhdr(ws.cell(r, 4), "Comment")
    ws.row_dimensions[r].height = 18
    mkt_hdr = r; r += 1

    def prem(a, b):
        try:
            p = (float(a) / float(b) - 1) * 100
            return f"{'+' if p>=0 else ''}{p:.0f}% {'premium' if p>=0 else 'discount'}"
        except (TypeError, ValueError):
            return "N/A"

    mkt_rows = [
        ("S&P 500 P/E (TTM est.)",
            fmt_x(spy_pe_ttm), "Broad market benchmark"),
        ("Nasdaq-100 P/E (est.)",
            "~32x", "Tech-heavy; most PLTR peers live here"),
        ("PLTR GAAP P/E (TTM) vs. S&P 500",
            prem(gv("PLTR","pe_ttm"), spy_pe_ttm),
            "PLTR GAAP P/E massively elevated vs. market; reflects AI growth premium"),
        ("PLTR Adj. P/E (Fwd) vs. S&P 500 Fwd P/E",
            prem(pltr_pe_fwd, spy_pe_fwd),
            "Even on adj. basis, PLTR commands a very large premium"),
    ]

    for i, (m, v, note) in enumerate(mkt_rows):
        bg = rbg(i)
        ws.row_dimensions[r].height = 17
        lbl(ws.cell(r, 2), m, bg=bg)
        val(ws.cell(r, 3), v, bg=bg)
        ws.merge_cells(start_row=r, start_column=4, end_row=r, end_column=13)
        val(ws.cell(r, 4), note, bg=bg, align="left")
        r += 1

    apply_border(ws, mkt_hdr, 2, r-1, 13)
    spacer(ws, r); r += 1

    # ── Peer Table ────────────────────────────────────────────────────────────
    section_title(ws, r, 2, 13, "PEER COMPARISON TABLE"); r += 1

    comp_headers = [
        "Ticker", "Company", "Price", "Mkt Cap", "P/E (TTM)", "P/E (Fwd NTM)",
        "EV/Rev (TTM)", "Rev Growth", "Gross Margin", "EPS (TTM)", "EPS (Fwd)", "Beta",
    ]
    for c_i, h in enumerate(comp_headers, 2):
        subhdr(ws.cell(r, c_i), h)
    ws.row_dimensions[r].height = 18
    comp_hdr = r; r += 1

    for i, (sym, name) in enumerate(COMP_NAMES.items()):
        is_pltr = sym == "PLTR"
        bg  = LGOLD if is_pltr else rbg(i)
        bld = is_pltr
        ws.row_dimensions[r].height = 17

        price_v   = gv(sym, "price")
        mktcap_v  = gv(sym, "mktcap")
        pe_ttm_v  = gv(sym, "pe_ttm")
        pe_fwd_v  = gv(sym, "pe_fwd")
        ev_rev_v  = gv(sym, "ev_rev")
        rg_v      = gv(sym, "rev_growth")
        gm_v      = gv(sym, "gross_m")
        eps_ttm_v = gv(sym, "eps_ttm")
        eps_fwd_v = gv(sym, "eps_fwd")
        beta_v    = gv(sym, "beta")

        row_vals = [
            sym,
            name,
            f"${float(price_v):.2f}"    if price_v   is not None else "N/A",
            fmt_b(mktcap_v),
            fmt_x(pe_ttm_v),
            fmt_x(pe_fwd_v),
            fmt_x(ev_rev_v),
            fmt_pct(rg_v),
            fmt_pct(gm_v),
            f"${float(eps_ttm_v):.3f}"  if eps_ttm_v is not None else "N/A",
            f"${float(eps_fwd_v):.3f}"  if eps_fwd_v is not None else "N/A",
            f"{float(beta_v):.2f}"      if beta_v    is not None else "N/A",
        ]

        for c_i, v in enumerate(row_vals, 2):
            cell = ws.cell(r, c_i)
            cell.value = v
            cell.font  = Font(size=9, name="Calibri", bold=bld)
            cell.fill  = PatternFill("solid", fgColor=bg)
            cell.alignment = Alignment(
                horizontal="left" if c_i in (2, 3) else "center", vertical="center"
            )
        r += 1

    apply_border(ws, comp_hdr, 2, r-1, 13)
    spacer(ws, r); r += 1

    # ── Relative Valuation Summary ────────────────────────────────────────────
    section_title(ws, r, 2, 13, "PALANTIR — RELATIVE VALUATION SUMMARY"); r += 1

    for c_i, h in enumerate(["Metric", "PLTR", "Peer Median*", "Premium / Discount", "Interpretation"], 2):
        subhdr(ws.cell(r, c_i), h)
    ws.merge_cells(start_row=r, start_column=6, end_row=r, end_column=13)
    subhdr(ws.cell(r, 6), "Interpretation")
    ws.row_dimensions[r].height = 18
    rel_hdr = r; r += 1

    # Compute medians from non-PLTR peers
    def med(key):
        vals = [v for s in COMP_NAMES if s != "PLTR"
                for v in [gv(s, key)] if v is not None]
        if not vals:
            return None
        vals.sort()
        return vals[len(vals)//2]

    med_pe_fwd = med("pe_fwd")
    med_ev_rev = med("ev_rev")
    med_rg     = med("rev_growth")

    pltr_pe_f = gv("PLTR", "pe_fwd")
    pltr_evr  = gv("PLTR", "ev_rev")
    pltr_rg   = gv("PLTR", "rev_growth")

    rel_rows = [
        ("P/E Fwd (NTM)",
            fmt_x(pltr_pe_f), fmt_x(med_pe_fwd),
            prem(pltr_pe_f, med_pe_fwd),
            "Large premium to peers; requires sustained 30%+ revenue growth and margin expansion to justify"),
        ("EV / Revenue (TTM)",
            fmt_x(pltr_evr), fmt_x(med_ev_rev),
            prem(pltr_evr, med_ev_rev),
            "Premium reflects AI platform uniqueness and high-quality recurring gov contract revenue"),
        ("Revenue Growth (YoY)",
            fmt_pct(pltr_rg), fmt_pct(med_rg),
            prem(pltr_rg, med_rg) if pltr_rg and med_rg else "N/A",
            "PLTR grows materially faster than peers; growth re-acceleration is the key bull case"),
        ("PLTR Fwd P/E vs. S&P 500",
            fmt_x(pltr_pe_f), fmt_x(spy_pe_fwd),
            prem(pltr_pe_f, spy_pe_fwd),
            "Extreme premium vs. broad market; entirely 'story stock' / growth pricing"),
    ]

    for i, (m, pv, peerv, prem_s, interp) in enumerate(rel_rows):
        bg = rbg(i)
        ws.row_dimensions[r].height = 22
        lbl(ws.cell(r, 2), m, bg=bg)
        val(ws.cell(r, 3), pv, bg=LGOLD, bold=True)
        val(ws.cell(r, 4), peerv, bg=bg)
        val(ws.cell(r, 5), prem_s,
            bg=LORANGE if "premium" in str(prem_s) else LGREEN, bold=True)
        ws.merge_cells(start_row=r, start_column=6, end_row=r, end_column=13)
        val(ws.cell(r, 6), interp, bg=bg, align="left")
        r += 1

    apply_border(ws, rel_hdr, 2, r-1, 13)

    ws.row_dimensions[r].height = 14
    ws.cell(r, 2).value = "* Peer median excludes PLTR. Peers: SNOW, AI, BBAI, SAIC, BAH, LDOS, VRNT, CRM, MSFT."
    ws.cell(r, 2).font  = Font(size=7, italic=True, color=DGRAY, name="Calibri")
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=13)
    r += 1
    spacer(ws, r); r += 1

    # ── Historical P/E Context ────────────────────────────────────────────────
    section_title(ws, r, 2, 13, "PALANTIR — HISTORICAL P/E CONTEXT (Annual)"); r += 1

    for c_i, h in enumerate(
        ["Year", "Adj. EPS", "Avg. Stock Price", "Implied P/E (Adj.)", "Notes"], 2
    ):
        subhdr(ws.cell(r, c_i), h)
    ws.merge_cells(start_row=r, start_column=6, end_row=r, end_column=13)
    subhdr(ws.cell(r, 6), "Notes")
    ws.row_dimensions[r].height = 18
    hist_hdr = r; r += 1

    hist_pe = [
        ("FY2020", "$-0.47 (GAAP)", "~$9",   "N/M",   "IPO year (Sep 2020); heavy GAAP losses; avg price from partial year"),
        ("FY2021", "$-0.37 (GAAP)", "~$22",   "N/M",   "Massive SBC-driven losses; peak hype cycle then sell-off"),
        ("FY2022", "$-0.06 (GAAP)", "~$9",   "N/M",   "Adj. EPS barely positive; GAAP still negative; macro sell-off"),
        ("FY2023", "$0.25 (adj.)",  "~$16",  "~64x",  "First full adj. profitable year; stock re-rated"),
        ("FY2024", "$0.41 (adj.)",  "~$35",  "~85x",  "First GAAP profitable year; AIP momentum; massive re-rating to year-end"),
        ("FY2025E","$0.52 (adj.)",  "~$120", "~230x", "AI premium in full effect; stock up 3x YTD Q2 2025"),
        ("FY2026E","$0.71 (adj.)",  "Varies","~170x", "At $120 stock price"),
    ]

    for i, (yr, eps_s, price_s, pe_s, note) in enumerate(hist_pe):
        bg = LGOLD if "2025" in yr or "2026" in yr else rbg(i)
        ws.row_dimensions[r].height = 17
        for c_i, v in enumerate([yr, eps_s, price_s, pe_s], 2):
            cell = ws.cell(r, c_i)
            cell.value = v
            cell.font  = Font(size=9, name="Calibri")
            cell.fill  = PatternFill("solid", fgColor=bg)
            cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.merge_cells(start_row=r, start_column=6, end_row=r, end_column=13)
        val(ws.cell(r, 6), note, bg=bg, align="left")
        r += 1

    apply_border(ws, hist_hdr, 2, r-1, 13)
    return ws


# ═══════════════════════════════════════════════════════════════════════════════
# SHEET 3 — CRITICAL FACTORS
# ═══════════════════════════════════════════════════════════════════════════════

def build_critical_factors(wb):
    ws = wb.create_sheet("3. Critical Factors")
    ws.sheet_view.showGridLines = False

    col_widths = [2, 4, 22, 34, 14, 14, 11, 12, 28, 28, 18, 2]
    for i, w in enumerate(col_widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

    r = 1

    ws.merge_cells(f"B{r}:K{r}")
    hdr(ws.cell(r, 2),
        "CRITICAL FACTORS — PALANTIR (PLTR)  |  Each factor must materially move EPS ≥5% vs. consensus",
        bg=NAVY, size=12)
    ws.row_dimensions[r].height = 32
    r += 1

    ws.merge_cells(f"B{r}:K{r}")
    ws.row_dimensions[r].height = 30
    c = ws.cell(r, 2)
    c.value = (
        f"Last updated: {datetime.now().strftime('%B %d, %Y')}  |  "
        "A factor qualifies when it: (1) is likely to move EPS ≥5% in either direction, "
        "(2) is likely to deviate materially from consensus during the investment horizon, "
        "(3) can be researched and forecast with work, and (4) is something the consensus is poor at spotting."
    )
    c.font  = Font(size=8, italic=True, color=DGRAY, name="Calibri")
    c.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    r += 1
    spacer(ws, r); r += 1

    for c_i, h in enumerate(
        ["#", "Factor Name", "Description & Thesis",
         "Est. EPS Impact", "Direction", "Horizon",
         "Probability", "Current Consensus View", "Our / Contrarian View",
         "Metrics to Track", "Status"], 2
    ):
        subhdr(ws.cell(r, c_i), h)
    ws.row_dimensions[r].height = 22
    r += 1

    DIR_BG = {
        "UPSIDE":                    LGREEN,
        "UPSIDE (high conviction)":  LGREEN,
        "UPSIDE (if achieved)":      LGREEN,
        "DOWNSIDE RISK":             LRED,
        "STRUCTURAL DOWNSIDE":       LRED,
        "TWO-SIDED":                 LGOLD,
    }

    factors = [
        {
            "n": 1,
            "name": "US Commercial AIP Adoption & Bootcamp Conversion",
            "desc": (
                "AIP Bootcamps (intensive 5-day pilots) have become PLTR's primary go-to-market engine. "
                "Conversion rate from bootcamp to paying contract, deal size, and whether enterprise customers "
                "expand (NRR) are the primary levers for US Commercial revenue — consensus' most sensitive line item. "
                "If conversion accelerates even modestly vs. the 30-35% YoY growth consensus models, "
                "this is the single biggest upside driver."
            ),
            "eps_impact": "+10% to +20%",
            "direction": "UPSIDE (high conviction)",
            "horizon": "0–12 months",
            "prob": "55% above cons.",
            "consensus": "~30% YoY US Commercial growth; ~$600M for FY25",
            "our_view": (
                "Enterprise AI budget re-acceleration in 2025 is well documented. PLTR uniquely wins "
                "in secure / on-prem deployments (regulated industries, defense contractors). "
                "We see path to $720-750M US Commercial revenue in FY25, ~15-20% above consensus."
            ),
            "track": "US Commercial revenue YoY % (quarterly); # new customers; ACV per deal; NRR",
            "status": "ACTIVE — High Priority",
        },
        {
            "n": 2,
            "name": "US Government Budget Risk / DOGE",
            "desc": (
                "The DOGE initiative is reviewing federal contracts and cutting spending. PLTR derives ~38% "
                "of revenue from US Government. Any contract cancellation or delay (particularly in DHS, HHS "
                "or non-core DoD segments) is a meaningful downside risk. Offsetting: PLTR itself is reportedly "
                "the platform underlying DOGE's data operations — making it a potential winner of DOGE-related "
                "contract expansions in efficiency tools."
            ),
            "eps_impact": "-5% to -15% (downside) or +5% (DOGE partner upside)",
            "direction": "TWO-SIDED",
            "horizon": "6–18 months",
            "prob": "30% risk of cut; 25% DOGE upside",
            "consensus": "Models US Gov growing ~15% YoY; minimal DOGE haircut applied",
            "our_view": (
                "Consensus is too complacent. We apply a 10% probability-weighted haircut to US Gov "
                "revenue for FY25E, partially offset by DOGE-partnership upside. Net: slight negative vs. "
                "Street. NDAA language and DoD supplemental budget are key data points."
            ),
            "track": "US Gov revenue YoY; DoD & DHS budget news; DOGE press releases; contract awards",
            "status": "HIGH PRIORITY — Risk Watch",
        },
        {
            "n": 3,
            "name": "SBC Dilution vs. GAAP EPS Trajectory",
            "desc": (
                "PLTR's SBC runs at $600M+/yr (~20% of revenue), suppressing GAAP EPS and adding ~3-4% "
                "diluted share count annually. Consensus focuses on adj. EPS (excl. SBC). If SBC does not "
                "decline as a % of revenue, the GAAP-to-adj. gap persists, making GAAP P/E structurally very "
                "high and limiting investor universe. Conversely, faster-than-expected SBC decline could "
                "trigger a GAAP re-rating."
            ),
            "eps_impact": "-5% to -10% GAAP EPS drag annually if SBC stays elevated",
            "direction": "DOWNSIDE RISK",
            "horizon": "12–24 months",
            "prob": "40% SBC stays ≥18% of revenue",
            "consensus": "Models SBC declining to ~15% of revenue by FY26; GAAP EPS reaching $0.24",
            "our_view": (
                "PLTR culture is deeply equity-driven. We model SBC at ~18% of revenue through FY26, "
                "slightly above consensus. This puts GAAP EPS ~5-8% below Street's $0.24 FY26E. "
                "Key test: whether Karp's new employment agreement in 2024 triggers new SBC cliff."
            ),
            "track": "SBC per quarter ($); diluted share count growth rate; SBC as % of revenue; option grants",
            "status": "MONITORING",
        },
        {
            "n": 4,
            "name": "Margin Expansion & Operating Leverage",
            "desc": (
                "Adj. operating margin expanded from ~20% (FY22) to ~38% (FY24). The key question: "
                "can it reach 42-45% by FY26 as revenue scales? Bootcamp-model acquisition is low-cost "
                "(few salespeople needed). If S&M efficiency continues improving, margins beat consensus "
                "by 200-300bps, which at PLTR's growth rate compounds materially into EPS upside."
            ),
            "eps_impact": "+8% to +15% on adj. EPS if margins reach 42%+",
            "direction": "UPSIDE (high conviction)",
            "horizon": "12–24 months",
            "prob": "60% margins beat consensus",
            "consensus": "Models ~39% adj. operating margin for FY25, ~40% FY26",
            "our_view": (
                "This is our highest-conviction upside factor. Bootcamp model is inherently high-margin. "
                "Once on-platform, churn is near-zero (high switching cost). Revenue-per-employee at PLTR "
                "is extremely high and rising. We target 42-44% adj. operating margin by Q4 2026."
            ),
            "track": "Adj. operating margin per quarter; S&M % of revenue; R&D % of revenue; revenue / employee",
            "status": "HIGH CONVICTION — Upside",
        },
        {
            "n": 5,
            "name": "NATO / Allied Government AI Contracts",
            "desc": (
                "European rearmament and the Ukraine conflict are driving record defense tech spending. "
                "PLTR has existing NATO deployments (UK MoD, JSDF, NATO Allied Command). "
                "New multi-year sovereign defense AI contracts in NATO countries could add $200-400M to "
                "the backlog, not in consensus. The UK DSTL, German Bundeswehr, and Australian ADF "
                "are all evaluating large AI-for-defense contracts."
            ),
            "eps_impact": "+5% to +10%",
            "direction": "UPSIDE (if achieved)",
            "horizon": "6–18 months",
            "prob": "40% probability of material new win",
            "consensus": "Models modest intl gov growth ~12% YoY; no large new contract assumed",
            "our_view": (
                "Geopolitical tailwinds are structural, not cyclical. PLTR is one of few companies "
                "with classified-grade AI at NATO scale. If a major UK or German national defense "
                "AI contract is announced, we see 5-8% EPS upside vs. Street. Biggest catalyst."
            ),
            "track": "Intl Gov revenue; UK DSTL / German Bundeswehr procurement news; NATO AI initiatives",
            "status": "ACTIVE — Monitoring",
        },
        {
            "n": 6,
            "name": "International Commercial Segment Breakout",
            "desc": (
                "PLTR's intl commercial has underperformed vs. US for years. Management restructured "
                "the European go-to-market in 2023-24. If international commercial accelerates to 20%+ "
                "YoY (from ~10% currently), this would represent a material positive surprise since "
                "consensus doesn't model it. UAE/Middle East commercial, Japanese manufacturing, and "
                "European healthcare are specific sub-segments to watch."
            ),
            "eps_impact": "+5% to +8% on adj. EPS",
            "direction": "UPSIDE (if achieved)",
            "horizon": "12–24 months",
            "prob": "25% probability of breakout",
            "consensus": "Models intl commercial growth of ~8-12% YoY; remains the 'weak' segment",
            "our_view": (
                "Low-probability, high-upside scenario. European manufacturing digitization + "
                "sovereign AI initiatives could surprise. We watch UAE expansion and Japanese auto "
                "sector contracts closely. This is a call option on intl recovery, not a base case."
            ),
            "track": "Intl Commercial revenue YoY; new intl commercial customers; contract press releases",
            "status": "LOW PRIORITY — Watching",
        },
        {
            "n": 7,
            "name": "Hyperscaler Competition (AWS / Azure / GCP)",
            "desc": (
                "Microsoft Azure AI, AWS Bedrock, and Google Vertex AI are aggressively building "
                "enterprise AI platforms that increasingly overlap with Foundry/AIP for commercial clients. "
                "If hyperscalers commoditize data-platform capabilities, PLTR's commercial pricing power "
                "could erode. Government segment is more protected (accreditation, FedRAMP, classified)."
            ),
            "eps_impact": "-10% to -20% over 3-5 years if commercial displacement accelerates",
            "direction": "STRUCTURAL DOWNSIDE",
            "horizon": "18–36 months",
            "prob": "25% risk in 2-year horizon",
            "consensus": "Largely ignores hyperscaler risk; models stable or growing PLTR commercial wins",
            "our_view": (
                "Short-term: PLTR's ontological data model and gov accreditation are real moats. "
                "Medium-term: hyperscaler commoditization will hit PLTR's commercial segment first. "
                "We rate this as a watch-list structural risk, not an immediate EPS factor, "
                "but it would compress the terminal P/E in a DCF scenario."
            ),
            "track": "PLTR NRR; commercial customer churn; Azure AI / AWS Bedrock enterprise case studies",
            "status": "WATCH — Structural Risk",
        },
    ]

    for factor in factors:
        dir_bg = DIR_BG.get(factor["direction"], LGRAY)
        ws.row_dimensions[r].height = 88

        cells = {
            2:  (str(factor["n"]), WHITE, NAVY, True),
            3:  (factor["name"],   "000000", LBLUE, True),
            4:  (factor["desc"],   "000000", WHITE, False),
            5:  (factor["eps_impact"], "000000", dir_bg, True),
            6:  (factor["direction"],  "000000", dir_bg, True),
            7:  (factor["horizon"],    "000000", LGRAY, False),
            8:  (factor["prob"],       "000000", LGRAY, False),
            9:  (factor["consensus"],  "000000", WHITE, False),
            10: (factor["our_view"],   "000000", LGOLD, False),
            11: (factor["track"],      "000000", WHITE, False),
            12: (factor["status"],     "000000", LGRAY, True),
        }

        for c_i, (text, fg, bg, bold) in cells.items():
            cell = ws.cell(r, c_i)
            cell.value = text
            cell.font  = Font(size=8, name="Calibri", bold=bold, color=fg)
            cell.fill  = PatternFill("solid", fgColor=bg)
            cell.alignment = Alignment(
                horizontal="center" if c_i in (2, 5, 6, 7, 8, 12) else "left",
                vertical="top", wrap_text=True
            )

        apply_border(ws, r, 2, r, 12)
        r += 1

    spacer(ws, r); r += 1
    ws.merge_cells(f"B{r}:K{r}")
    leg = ws.cell(r, 2)
    leg.value = (
        "COLOR LEGEND:  Green background = Upside factor  |  Red = Downside risk  |  "
        "Gold = Two-sided / uncertain  |  "
        "Probability = subjective analyst estimate.  Data source: public filings, earnings calls, sell-side research."
    )
    leg.font  = Font(size=7, italic=True, color=DGRAY, name="Calibri")
    leg.alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[r].height = 14

    return ws


# ═══════════════════════════════════════════════════════════════════════════════
# SHEET 4 — VALUATION METHOD
# ═══════════════════════════════════════════════════════════════════════════════

def build_valuation_method(wb):
    ws = wb.create_sheet("4. Valuation Method")
    ws.sheet_view.showGridLines = False

    for i, w in enumerate([2, 20, 38, 18, 38, 18, 22, 2], 1):
        ws.column_dimensions[get_column_letter(i)].width = w

    r = 1

    ws.merge_cells(f"B{r}:G{r}")
    hdr(ws.cell(r, 2),
        "VALUATION METHOD SELECTION — PALANTIR (PLTR)  |  Based on AnalystSolutions Flowchart",
        bg=NAVY, size=12)
    ws.row_dimensions[r].height = 32
    r += 1

    ws.merge_cells(f"B{r}:G{r}")
    ts = ws.cell(r, 2)
    ts.value = (
        "We evaluate both relative and absolute return contexts per the flowchart. "
        "Decision path shown below → selected methods summarized at bottom."
    )
    ts.font  = Font(italic=True, size=9, color=DGRAY, name="Calibri")
    ts.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[r].height = 18
    r += 1
    spacer(ws, r); r += 1

    def flow_row(ws, r, step, question, answer, reasoning,
                 is_result=False, answer_color=None):
        bg = LGOLD if is_result else (LGREEN if "YES" in answer else LRED if "NO" == answer.strip() else LGRAY)
        ws.row_dimensions[r].height = 45

        c = ws.cell(r, 2)
        c.value = step
        c.font  = Font(size=9, bold=True, name="Calibri",
                       color=WHITE if is_result else "000000")
        c.fill  = PatternFill("solid", fgColor=NAVY if is_result else LBLUE)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        c = ws.cell(r, 3)
        c.value = question
        c.font  = Font(size=9, name="Calibri", bold=is_result)
        c.fill  = PatternFill("solid", fgColor=bg)
        c.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)

        c = ws.cell(r, 4)
        c.value = answer
        ac = answer_color or (GREEN if ("YES" in answer or "✓" in answer) else
                              RED_C if answer.strip() == "→ NO" else NAVY)
        c.font  = Font(size=9, bold=True, name="Calibri", color=ac)
        c.fill  = PatternFill("solid", fgColor=bg)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        ws.merge_cells(start_row=r, start_column=5, end_row=r, end_column=7)
        c = ws.cell(r, 5)
        c.value = reasoning
        c.font  = Font(size=8, name="Calibri", italic=(not is_result))
        c.fill  = PatternFill("solid", fgColor=bg)
        c.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)

        apply_border(ws, r, 2, r, 7)
        return r + 1

    # ── RELATIVE PATH ─────────────────────────────────────────────────────────
    section_title(ws, r, 2, 7, "PATH A — RELATIVE RETURN EVALUATION"); r += 1

    r = flow_row(ws, r, "Q1",
        "Are you evaluated for generating relative or absolute returns?",
        "→ RELATIVE",
        "We assess PLTR's risk-adjusted return vs. peers and vs. a market benchmark (S&P 500 / Nasdaq-100).",
        answer_color=NAVY)
    r = flow_row(ws, r, "Q2",
        "Do the company's peers have similar growth, betas, and capital structures?",
        "→ PARTIALLY",
        "No single peer matches PLTR's government + commercial AI mix, its Class F voting structure, and "
        "its ~2.5 beta. We expand the peer set across sectors (gov IT, SaaS, AI) to find partial comparables.")
    r = flow_row(ws, r, "Q3",
        "Does the company pay a dividend on a consistent basis?",
        "→ NO",
        "Palantir pays no dividend and has never declared one. Dividend yield is not applicable.")
    r = flow_row(ws, r, "Q4",
        "Is the company likely to generate positive EBITDA during the forecast period?",
        "→ YES",
        "PLTR generated ~$1.1B adj. EBITDA in FY24 (~38% margin). Consensus models ~$1.45B in FY25E. "
        "Positive and growing EBITDA — EV/EBITDA is a valid relative metric.")
    r = flow_row(ws, r, "RESULT A",
        "Primary Relative Valuation Metric",
        "✓ EV/EBITDA",
        "Use NTM EV/EBITDA vs. software/gov IT peers. Fair-value range: 60-80x. "
        "Secondary cross-check: EV/Revenue (NTM) and Adj. P/E.",
        is_result=True)

    spacer(ws, r, 8); r += 1

    # ── ABSOLUTE PATH ─────────────────────────────────────────────────────────
    section_title(ws, r, 2, 7, "PATH B — ABSOLUTE RETURN EVALUATION"); r += 1

    r = flow_row(ws, r, "Q1",
        "Are you evaluated for generating relative or absolute returns?",
        "→ ABSOLUTE",
        "We also need to size the position and assess intrinsic value — what should we pay for PLTR?",
        answer_color=NAVY)
    r = flow_row(ws, r, "Q2",
        "Can company assets & debt be reliably valued using public market pricing "
        "(e.g. financial, resource companies)?",
        "→ NO",
        "PLTR is a pure software / IP company. Cash on the balance sheet is easily valued ($5.8B net cash) "
        "but the operating business value comes from future earnings, not assets. P/Book is meaningless.")
    r = flow_row(ws, r, "Q3",
        "Is the company likely to generate positive after-tax earnings during the forecast period?",
        "→ YES",
        "PLTR achieved GAAP net income profitability for the first time in FY2024. EPS is growing. "
        "Earnings-based absolute valuation methods are now applicable.")
    r = flow_row(ws, r, "Q4",
        "Can the company's EPS growth rate be accurately forecast over multiple periods?",
        "→ PARTIALLY YES",
        "EPS growth is forecastable 1-2 years out with reasonable confidence (contract visibility, "
        "bootcamp pipeline). 3+ year forecasts carry high uncertainty. We proceed on both sub-paths.")
    r = flow_row(ws, r, "Q4a",
        "Can capital expenditures AND the payout ratio be accurately forecast for multiple future periods?",
        "→ YES",
        "CapEx is minimal (<2% of revenue; software company). Payout ratio = 0% (no dividends). "
        "FCF closely tracks adj. net income. DCF is applicable and is the primary absolute method.")
    r = flow_row(ws, r, "RESULT B1",
        "Primary Absolute Valuation Metric",
        "✓ DCF",
        "10-year DCF with terminal value. Key: 27% rev CAGR yrs 1-5 / 17% yrs 6-10 / 3% terminal / 11% WACC. "
        "Base case: ~$85-105 intrinsic value. See DCF assumptions table below.",
        is_result=True)
    r = flow_row(ws, r, "Q4b",
        "Can the company's 'maintenance' capital expenditures be accurately forecast?",
        "→ YES",
        "Software company. Maintenance CapEx is minimal and predictable. FCF ≈ NOPAT for PLTR.")
    r = flow_row(ws, r, "RESULT B2",
        "Alternative Absolute Cross-Check",
        "✓ P/FCF",
        "FCF yield approach as sanity check. At $120 stock price: FCF yield ~0.8%. "
        "vs. 10yr Treasury ~4.5% — implies enormous growth premium is priced in.",
        is_result=True)

    spacer(ws, r, 8); r += 1

    # ── Conclusion ────────────────────────────────────────────────────────────
    section_title(ws, r, 2, 7, "CONCLUSION — SELECTED METHODS FOR PALANTIR (PLTR)", bg=NAVY); r += 1

    for c_i, h in enumerate(["Applicability", "Method", "Rationale"], 2):
        subhdr(ws.cell(r, c_i), h)
    ws.merge_cells(start_row=r, start_column=4, end_row=r, end_column=7)
    subhdr(ws.cell(r, 4), "Rationale")
    ws.row_dimensions[r].height = 18
    conc_hdr = r; r += 1

    methods = [
        ("✓ PRIMARY (Relative)",   "EV/EBITDA",       LGREEN,
            "NTM basis vs. gov-IT and software peers. "
            "Bull / base / bear range: 90x / 70x / 45x on $1.45B NTM EBITDA → $130B / $102B / $65B EV → "
            "~$150 / ~$118 / ~$75 per share (after adding net cash ~$6B, dividing by ~2.2B shares)."),
        ("✓ PRIMARY (Absolute)",   "DCF",             LGREEN,
            "10-year FCF model. Base case: $85-105 intrinsic value. "
            "High sensitivity to terminal growth (3%) and WACC (11%). "
            "See assumptions table below."),
        ("✓ CROSS-CHECK",          "Adj. P/E (NTM)",  LGOLD,
            "Use adj. (ex-SBC) NTM P/E vs. high-growth peers. "
            "PLTR at ~230x NTM; top software comps at 40-60x → implies meaningful overvaluation "
            "unless you assign much higher growth or a structural AI-platform premium."),
        ("✓ CROSS-CHECK",          "P/FCF",           LGOLD,
            "FCF yield: ~0.8% at $120 price vs. risk-free ~4.5%. "
            "Premium is entirely predicated on sustained 25%+ growth for 10+ years. "
            "Useful bear-case anchor."),
        ("✗ NOT APPLICABLE",       "Dividend Yield",  LRED,
            "PLTR pays no dividend. Dividend yield analysis not applicable."),
        ("✗ NOT APPLICABLE",       "Price / Book",    LRED,
            "Software / IP company. Book value (mostly cash) does not reflect intangible platform value."),
        ("✗ SECONDARY ONLY",       "EV / Revenue",    LGOLD,
            "EV/Revenue is more appropriate for pre-profitability companies. "
            "PLTR is now EBITDA-positive, so EV/EBITDA is preferred. "
            "EV/Rev used only as a quick growth-vs-valuation sanity check."),
    ]

    for i, (appl, method, bg, rationale) in enumerate(methods):
        ws.row_dimensions[r].height = 28
        val(ws.cell(r, 2), appl,   bg=bg, bold=True, align="center")
        val(ws.cell(r, 3), method, bg=bg, bold=True, size=10)
        ws.merge_cells(start_row=r, start_column=4, end_row=r, end_column=7)
        val(ws.cell(r, 4), rationale, bg=bg, align="left")
        apply_border(ws, r, 2, r, 7)
        r += 1

    spacer(ws, r, 8); r += 1

    # ── DCF Assumptions ───────────────────────────────────────────────────────
    section_title(ws, r, 2, 7, "DCF KEY ASSUMPTIONS  (Edit gold cells to build your own model)"); r += 1

    for c_i, h in enumerate(["Parameter", "Base Case", "Bull Case", "Bear Case", "Notes"], 2):
        subhdr(ws.cell(r, c_i), h)
    ws.merge_cells(start_row=r, start_column=6, end_row=r, end_column=7)
    subhdr(ws.cell(r, 6), "Notes")
    ws.row_dimensions[r].height = 18
    dcf_hdr = r; r += 1

    dcf_params = [
        ("Revenue CAGR, Years 1-5",    "27%",   "35%",   "19%",   "Anchored to management guidance + bootcamp pipeline"),
        ("Revenue CAGR, Years 6-10",   "17%",   "23%",   "11%",   "Normalization as TAM matures"),
        ("Terminal Revenue Growth",     "3.0%",  "4.0%",  "2.0%",  "Conservative; slightly above long-run nominal GDP"),
        ("EBITDA Margin at Maturity",   "42%",   "48%",   "35%",   "Adj. operating margin at scale (ex-SBC)"),
        ("CapEx as % of Revenue",       "1.5%",  "1.0%",  "2.5%",  "Software; near-zero maintenance CapEx"),
        ("Effective Tax Rate",          "21%",   "18%",   "24%",   "US statutory; partially offset by R&D credits"),
        ("WACC",                        "11.0%", "9.5%",  "13.0%", "Beta ~2.5; equity risk premium ~5%; Rf ~4.5%"),
        ("Annual Share Dilution (SBC)", "3.5%",  "2.5%",  "5.0%",  "Key sensitivity; reduces per-share value"),
        ("Net Cash (added to EV)",      "$5.8B", "$5.8B", "$5.8B", "Current net cash position; debt-free"),
        ("Shares Outstanding",          "2.20B", "2.18B", "2.25B", "Diluted; including future SBC grants"),
        ("─────────────────────",       "──────","──────","──────", ""),
        ("Implied Equity Value",        "~$240B","~$360B","~$130B","EV + net cash"),
        ("Implied Fair Value / Share",  "~$109", "~$165", "~$58",  "Equity Value / Diluted Shares"),
        ("Upside / (Downside) at $120", "~-9%",  "~+38%", "~-52%", "vs. current $120 stock price"),
    ]

    for i, row_data in enumerate(dcf_params):
        is_output = any(x in row_data[0] for x in ("Implied", "Upside"))
        is_sep    = "─" in row_data[0]
        bg_row    = LBLUE if is_output else LGRAY if is_sep else rbg(i)
        ws.row_dimensions[r].height = 18

        lbl(ws.cell(r, 2), row_data[0], bg=LGRAY, bold=is_output)

        for c_i, v in enumerate(row_data[1:4], 3):
            cell = ws.cell(r, c_i)
            cell.value = v
            cell.font  = Font(size=9, name="Calibri", bold=is_output)
            cell.fill  = PatternFill("solid", fgColor=LGOLD if not is_output and not is_sep else bg_row)
            cell.alignment = Alignment(horizontal="center", vertical="center")

        ws.merge_cells(start_row=r, start_column=6, end_row=r, end_column=7)
        val(ws.cell(r, 6), row_data[4], bg=rbg(i), align="left", size=8)
        apply_border(ws, r, 2, r, 7)
        r += 1

    return ws


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    out_path = "/home/user/fund-startup/PLTR_Valuation.xlsx"

    print("Palantir Valuation Generator")
    print("─" * 40)

    try_live_fetch()

    wb = openpyxl.Workbook()
    del wb[wb.sheetnames[0]]   # remove default Sheet

    print("Building Sheet 1: Overview …")
    build_overview(wb)

    print("Building Sheet 2: Comps …")
    build_comps(wb)

    print("Building Sheet 3: Critical Factors …")
    build_critical_factors(wb)

    print("Building Sheet 4: Valuation Method …")
    build_valuation_method(wb)

    wb.save(out_path)
    print(f"\n✓ Saved → {out_path}")
    mode = "LIVE" if LIVE.get("PLTR") else "STATIC (Jun 2025)"
    print(f"  Data mode : {mode}")
    print("  To refresh: python generate_valuation.py")


if __name__ == "__main__":
    main()
