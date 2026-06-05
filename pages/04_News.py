import streamlit as st
from datetime import datetime
from data.news_client import NewsAPIClient
from data.pipeline import DataPipeline

st.set_page_config(page_title="News", page_icon="📰", layout="wide")

st.title("📰 Market News")

ticker = st.session_state.get("ticker", "AAPL")
pipeline = DataPipeline()
news = NewsAPIClient()

col1, col2 = st.columns([2, 1])
with col1:
    ticker = st.text_input("Ticker", value=ticker).upper().strip()
    st.session_state["ticker"] = ticker
with col2:
    days = st.selectbox("Look back", [3, 7, 14, 30], index=1, format_func=lambda x: f"Last {x} days")

if not ticker:
    st.warning("Enter a ticker symbol above.")
    st.stop()

# Resolve company name for a richer search query
try:
    overview = pipeline.get_company_overview(ticker)
    company_name = overview.get("name", ticker)
except Exception:
    company_name = ticker

query = f"{ticker} OR \"{company_name}\""

tab_company, tab_market = st.tabs([f"{ticker} News", "Market Headlines"])


def _render_articles(articles: list[dict]) -> None:
    if not articles:
        st.info("No articles found.")
        return
    for art in articles:
        if not art.get("title") or art["title"] == "[Removed]":
            continue
        with st.container():
            cols = st.columns([1, 4])
            with cols[0]:
                if art.get("urlToImage"):
                    st.image(art["urlToImage"], use_column_width=True)
                else:
                    st.markdown("📄")
            with cols[1]:
                published = art.get("publishedAt", "")
                if published:
                    try:
                        published = datetime.fromisoformat(published.replace("Z", "+00:00")).strftime("%b %d, %Y %H:%M")
                    except Exception:
                        pass
                source = art.get("source", {}).get("name", "")
                st.markdown(f"**[{art['title']}]({art.get('url', '#')})**")
                st.caption(f"{source}  ·  {published}")
                if art.get("description"):
                    st.markdown(art["description"])
            st.divider()


with tab_company:
    st.subheader(f"Latest news for {company_name} ({ticker})")
    with st.spinner("Fetching news..."):
        try:
            articles = news.get_company_news(query, days=days, page_size=20)
            _render_articles(articles)
        except ValueError:
            st.warning("No NewsAPI key configured. Add `NEWSAPI_KEY` in Streamlit secrets or your `.env` file.")
        except Exception as e:
            st.error(f"Failed to fetch news: {e}")

with tab_market:
    st.subheader("Top Business & Market Headlines")
    with st.spinner("Fetching headlines..."):
        try:
            articles = news.get_financial_headlines(page_size=20)
            _render_articles(articles)
        except ValueError:
            st.warning("No NewsAPI key configured. Add `NEWSAPI_KEY` in Streamlit secrets or your `.env` file.")
        except Exception as e:
            st.error(f"Failed to fetch headlines: {e}")
