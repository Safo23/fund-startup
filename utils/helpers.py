from typing import Any


def fmt_large_number(value: float | int | None, decimals: int = 2) -> str:
    if value is None:
        return "N/A"
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "N/A"
    abs_val = abs(value)
    sign = "-" if value < 0 else ""
    if abs_val >= 1e12:
        return f"{sign}{abs_val / 1e12:.{decimals}f}T"
    if abs_val >= 1e9:
        return f"{sign}{abs_val / 1e9:.{decimals}f}B"
    if abs_val >= 1e6:
        return f"{sign}{abs_val / 1e6:.{decimals}f}M"
    if abs_val >= 1e3:
        return f"{sign}{abs_val / 1e3:.{decimals}f}K"
    return f"{sign}{abs_val:.{decimals}f}"


def fmt_percent(value: float | None, decimals: int = 2) -> str:
    if value is None:
        return "N/A"
    try:
        return f"{float(value):.{decimals}f}%"
    except (TypeError, ValueError):
        return "N/A"


def fmt_currency(value: float | None, currency: str = "USD", decimals: int = 2) -> str:
    if value is None:
        return "N/A"
    symbols = {"USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥"}
    symbol = symbols.get(currency, currency + " ")
    try:
        return f"{symbol}{float(value):,.{decimals}f}"
    except (TypeError, ValueError):
        return "N/A"


def safe_get(data: dict, *keys: str, default: Any = None) -> Any:
    current = data
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key, default)
    return current
