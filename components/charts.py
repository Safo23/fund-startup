import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import streamlit as st
from utils.helpers import fmt_large_number


def render_price_chart(df: pd.DataFrame, ticker: str, show_volume: bool = True) -> None:
    if df.empty:
        st.warning("No price data available.")
        return

    fig = go.Figure()

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"],
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        name=ticker,
        increasing_line_color="#26a69a",
        decreasing_line_color="#ef5350",
    ))

    if show_volume and "Volume" in df.columns:
        colors = ["#26a69a" if c >= o else "#ef5350"
                  for c, o in zip(df["Close"], df["Open"])]
        fig.add_trace(go.Bar(
            x=df.index,
            y=df["Volume"],
            name="Volume",
            marker_color=colors,
            opacity=0.4,
            yaxis="y2",
        ))
        fig.update_layout(
            yaxis2=dict(overlaying="y", side="right", showgrid=False, title="Volume"),
        )

    fig.update_layout(
        title=f"{ticker} Price History",
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        height=500,
        margin=dict(l=0, r=0, t=40, b=0),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_financial_bar_chart(
    data: list[dict],
    fields: list[str],
    labels: list[str],
    title: str,
    period_key: str = "date",
) -> None:
    if not data:
        st.warning(f"No data available for {title}.")
        return

    periods = [d.get(period_key, "N/A") for d in data][::-1]
    fig = go.Figure()

    colors = px.colors.qualitative.Plotly
    for i, (field, label) in enumerate(zip(fields, labels)):
        values = [d.get(field, 0) or 0 for d in data][::-1]
        fig.add_trace(go.Bar(
            x=periods,
            y=values,
            name=label,
            marker_color=colors[i % len(colors)],
        ))

    fig.update_layout(
        title=title,
        barmode="group",
        template="plotly_dark",
        height=400,
        yaxis=dict(tickformat=".2s"),
        margin=dict(l=0, r=0, t=40, b=0),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_ratio_gauges(ratios: dict[str, tuple[float, float, float]]) -> None:
    """Render a row of gauge charts. ratios = {label: (value, min, max)}."""
    cols = st.columns(len(ratios))
    for col, (label, (value, min_val, max_val)) in zip(cols, ratios.items()):
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=value,
            title={"text": label, "font": {"size": 14}},
            gauge={
                "axis": {"range": [min_val, max_val]},
                "bar": {"color": "#1f77b4"},
                "bgcolor": "white",
                "steps": [
                    {"range": [min_val, max_val * 0.33], "color": "#ef5350"},
                    {"range": [max_val * 0.33, max_val * 0.66], "color": "#ffa726"},
                    {"range": [max_val * 0.66, max_val], "color": "#26a69a"},
                ],
            },
        ))
        fig.update_layout(
            height=220,
            margin=dict(l=10, r=10, t=40, b=10),
            template="plotly_dark",
        )
        col.plotly_chart(fig, use_container_width=True)
