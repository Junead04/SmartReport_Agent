# ─────────────────────────────────────────────
# SmartReport Agent — Configuration
# Reads from Streamlit Secrets on Cloud
# Falls back to hardcoded values for local run
# ─────────────────────────────────────────────

try:
    import streamlit as st
    GROQ_API_KEY       = st.secrets["GROQ_API_KEY"]
    GMAIL_ADDRESS      = st.secrets["GMAIL_ADDRESS"]
    GMAIL_APP_PASSWORD = st.secrets["GMAIL_APP_PASSWORD"]
except Exception:
    # ── LOCAL VALUES — fill these for running locally ──
    GROQ_API_KEY       = "gsk_your_groq_api_key_here"
    GMAIL_ADDRESS      = "your@gmail.com"
    GMAIL_APP_PASSWORD = "xxxx xxxx xxxx xxxx"

DEFAULT_RECIPIENTS = ["recipient@gmail.com"]
GROQ_MODEL         = "llama-3.1-8b-instant"

