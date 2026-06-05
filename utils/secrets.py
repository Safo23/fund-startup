import os
import streamlit as st


def get_secret(key: str) -> str:
    """Read from Streamlit secrets first, then environment variables."""
    try:
        val = st.secrets.get(key, "")
        if val:
            return val
    except Exception:
        pass
    return os.getenv(key, "")
