import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import os
import sys
import time
import base64

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.anomaly_detector import (
    analyze_sales_anomalies, analyze_operations_anomalies,
    compute_kpis, detect_anomalies_zscore
)
from agents.report_generator import (
    generate_sales_report, generate_operations_report,
    generate_forecast_narrative, generate_email_summary
)
from utils.email_sender import send_report_email
from utils.report_exporter import export_report_txt, export_report_html
from config import GROQ_API_KEY, GMAIL_ADDRESS, GMAIL_APP_PASSWORD, DEFAULT_RECIPIENTS


def get_bg_image_css() -> str:
    """Load background image as base64 for CSS injection."""
    img_path = os.path.join(os.path.dirname(__file__), "assets", "background.png")
    if not os.path.exists(img_path):
        return ""
    with open(img_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    ext = img_path.split(".")[-1].lower()
    mime = "image/jpeg" if ext in ["jpg", "jpeg"] else "image/png"
    return f"data:{mime};base64,{encoded}"

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="SmartReport Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# LOAD BACKGROUND IMAGE AS BASE64
# ─────────────────────────────────────────────
def get_base64_image(image_path: str) -> str:
    """Convert local image to base64 string for CSS embedding."""
    try:
        with open(image_path, "rb") as f:
            data = base64.b64encode(f.read()).decode("utf-8")
        ext = os.path.splitext(image_path)[1].lstrip(".")
        ext = "jpeg" if ext.lower() == "jpg" else ext.lower()
        return f"data:image/{ext};base64,{data}"
    except FileNotFoundError:
        return ""

bg_image_path = os.path.join(os.path.dirname(__file__), "assets", "background.png")
bg_base64 = get_base64_image(bg_image_path)
bg_css = f"url('{bg_base64}')" if bg_base64 else "none"
# ─────────────────────────────────────────────
# CUSTOM CSS — Gold & White Enterprise Theme
# ─────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {{ font-family: 'DM Sans', sans-serif; }}
#MainMenu, footer, header {{ visibility: hidden; }}
.block-container {{ padding-top: 1rem; padding-bottom: 2rem; }}

/* Background — warm white + optional image */
.stApp {{
    background-color: #fdf8ef;
    background-image: {bg_css};
    background-size: cover;
    background-position: center right;
    background-attachment: fixed;
    color: #2a1f05;
}}

/* Overlay to keep readability */
.stApp::before {{
    content: '';
    position: fixed;
    inset: 0;
    background: rgba(253, 248, 239, 0.91);
    pointer-events: none;
    z-index: 0;
}}

/* Sidebar — clean warm white */
section[data-testid="stSidebar"] {{
    background: #ffffff !important;
    border-right: 1px solid #e8d8a0 !important;
}}
section[data-testid="stSidebar"] * {{ color: #4a3810 !important; }}
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stTextInput label,
section[data-testid="stSidebar"] .stTextArea label {{
    color: #8a7030 !important; font-size: 11px !important;
    text-transform: uppercase; letter-spacing: 1px;
}}

/* Header banner */
.header-banner {{
    background: #ffffff;
    border: 1px solid #d4a830;
    border-radius: 12px;
    padding: 26px 36px;
    margin-bottom: 24px;
    position: relative;
    overflow: hidden;
    box-shadow: 0 2px 12px rgba(180,140,30,0.10);
}}
.header-banner::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 4px;
    background: linear-gradient(90deg, #B8892A, #D4AA50, #C9A030, #8a6010);
}}
.header-title {{
    font-family: 'DM Serif Display', serif;
    font-size: 28px;
    color: #1a1208;
    margin: 0;
    letter-spacing: 0.5px;
}}
.header-sub {{
    color: #8a7030;
    font-size: 13px;
    margin-top: 6px;
    letter-spacing: 1px;
    text-transform: uppercase;
}}
.header-badge {{
    display: inline-block;
    background: #f0fae8;
    color: #3B6D11;
    border: 1px solid #97C45955;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 11px;
    margin-top: 10px;
    letter-spacing: 1px;
}}

/* KPI Cards */
.kpi-card {{
    background: #ffffff;
    border: 1px solid #e8d8a0;
    border-top: 3px solid #C9A030;
    border-radius: 10px;
    padding: 18px 20px;
    transition: border-color 0.2s, box-shadow 0.2s;
}}
.kpi-card:hover {{
    border-color: #B8892A;
    box-shadow: 0 4px 14px rgba(180,140,30,0.12);
}}
.kpi-label {{
    font-size: 10px;
    color: #8a7030;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 8px;
}}
.kpi-value {{
    font-size: 26px;
    font-weight: 600;
    color: #1a1208;
    line-height: 1;
}}
.kpi-delta {{ font-size: 11px; margin-top: 6px; }}
.kpi-delta.up {{ color: #3B6D11; }}
.kpi-delta.down {{ color: #A32D2D; }}

/* Anomaly cards */
.anomaly-card {{
    border-radius: 8px;
    padding: 14px 18px;
    margin-bottom: 10px;
}}
.anomaly-card.HIGH {{ border-left: 4px solid #E24B4A; background: #fff5f5; border: 1px solid #F7C1C1; border-left: 4px solid #E24B4A; }}
.anomaly-card.MEDIUM {{ border-left: 4px solid #BA7517; background: #fffbf0; border: 1px solid #FAC775; border-left: 4px solid #BA7517; }}
.anomaly-card .sev-badge {{
    font-size: 10px; font-weight: 600; letter-spacing: 1px;
    padding: 2px 8px; border-radius: 4px;
    display: inline-block; margin-bottom: 6px;
}}
.anomaly-card.HIGH .sev-badge {{ background: #F7C1C1; color: #791F1F; }}
.anomaly-card.MEDIUM .sev-badge {{ background: #FAC775; color: #633806; }}
.anomaly-card .anom-type {{ font-size: 13px; font-weight: 600; color: #1a1208; }}
.anomaly-card .anom-detail {{ font-size: 12px; color: #6a5020; margin-top: 4px; }}
.anomaly-card .anom-date {{ font-size: 11px; color: #8a7030; margin-top: 4px; }}

/* Section headers */
.section-header {{
    font-family: 'DM Serif Display', serif;
    font-size: 18px;
    color: #1a1208;
    margin: 24px 0 14px;
    padding-bottom: 8px;
    border-bottom: 1px solid #e8d8a0;
}}

/* Report box */
.report-box {{
    background: #ffffff;
    border: 1px solid #e8d8a0;
    border-radius: 10px;
    padding: 24px;
    font-size: 14px;
    line-height: 1.8;
    color: #2a1f05;
    white-space: pre-line;
    max-height: 500px;
    overflow-y: auto;
}}

/* Status pills */
.status-pill {{
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.5px;
}}
.status-ok  {{ background: #EAF3DE; color: #3B6D11; border: 1px solid #97C45966; }}
.status-warn {{ background: #FFF8E6; color: #854F0B; border: 1px solid #EF9F2766; }}
.status-crit {{ background: #FCEBEB; color: #A32D2D; border: 1px solid #F0959566; }}

/* Buttons — gold */
.stButton > button {{
    background: #B8892A !important;
    color: #ffffff !important;
    border: 1px solid #a07820 !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important;
    letter-spacing: 0.5px !important;
    transition: all 0.2s !important;
}}
.stButton > button:hover {{
    background: #9a7020 !important;
    color: #ffffff !important;
    box-shadow: 0 4px 12px rgba(180,140,30,0.25) !important;
}}

/* Inputs */
.stTextInput input, .stTextArea textarea, .stSelectbox select {{
    background: #ffffff !important;
    color: #2a1f05 !important;
    border: 1px solid #d4c080 !important;
    border-radius: 8px !important;
}}

hr {{ border-color: #e8d8a0 !important; }}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {{
    background: #fff8e8;
    border-radius: 8px;
    padding: 4px;
    gap: 4px;
    border: 1px solid #e8d8a0;
}}
.stTabs [data-baseweb="tab"] {{
    background: transparent !important;
    color: #8a7030 !important;
    border-radius: 6px !important;
    font-size: 13px !important;
}}
.stTabs [aria-selected="true"] {{
    background: #B8892A !important;
    color: #ffffff !important;
}}

.streamlit-expanderHeader {{
    background: #ffffff !important;
    border: 1px solid #e8d8a0 !important;
    border-radius: 8px !important;
    color: #2a1f05 !important;
}}

.stAlert {{
    background: #fffdf5 !important;
    border: 1px solid #e8d8a0 !important;
    border-radius: 8px !important;
}}

.stFileUploader {{
    background: #ffffff !important;
    border: 2px dashed #d4c080 !important;
    border-radius: 10px !important;
}}

.stRadio > div {{ color: #2a1f05 !important; }}
.stCheckbox > label {{ color: #2a1f05 !important; }}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
for key in ['report_text', 'anomaly_result', 'kpis', 'df', 'report_type', 'forecast_text', 'email_summary']:
    if key not in st.session_state:
        st.session_state[key] = None


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:16px 0 8px">
        <div style="display:flex;align-items:center;gap:10px">
            <div style="width:34px;height:34px;background:#B8892A;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:18px">📊</div>
            <div>
                <div style="font-size:17px;font-weight:600;color:#1a1208;letter-spacing:0.3px">SmartReport</div>
                <div style="font-size:10px;color:#8a7030;text-transform:uppercase;letter-spacing:2px;margin-top:1px">Agent v1.0</div>
            </div>
        </div>
    </div>
    <hr style="border-color:#e8d8a0;margin:10px 0 14px">
    """, unsafe_allow_html=True)

    st.markdown("**📂 Data Source**")
    data_source = st.radio("", ["Use Sample Data", "Upload CSV"], label_visibility="collapsed")

    report_type = st.selectbox("**📋 Report Type**", ["Sales Intelligence", "Operations KPIs"])

    st.markdown("---")
    st.markdown("**🎛️ Detection Settings**")
    zscore_threshold = st.slider("Z-Score Sensitivity", 1.0, 3.0, 1.8, 0.1,
                                  help="Lower = more sensitive anomaly detection")
    auto_forecast = st.checkbox("Enable AI Forecast", value=True, help="Generate 7-day forward forecast")
    auto_email_summary = st.checkbox("Generate Email Summary", value=True)

    st.markdown("---")
    st.markdown("**📧 Email Alerts**")
    enable_email = st.checkbox("Send Report via Email")
    if enable_email:
        recipient_emails = st.text_area("Recipients (one per line)",
                                         value="\n".join(DEFAULT_RECIPIENTS),
                                         placeholder="boss@company.com\nteam@company.com")

    st.markdown("---")
    st.markdown("""
    <div style="font-size:10px;color:#8a7030;text-align:center;line-height:1.8;padding:8px 0">
    SmartReport Agent<br>
    Built for Sash.AI Portfolio<br>
    <span style="color:#B8892A;font-weight:500">Groq LLM + Statistical AI</span>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div class="header-banner">
    <div style="display:flex;justify-content:space-between;align-items:flex-start">
        <div>
            <h1 class="header-title">📊 SmartReport Agent</h1>
            <p class="header-sub">Enterprise Intelligence · Anomaly Detection · AI Narratives</p>
            <span class="header-badge">🟢 AGENT ONLINE</span>
        </div>
        <div style="text-align:right">
            <div style="font-size:11px;color:#8a7030;text-transform:uppercase;letter-spacing:1px">Last Run</div>
            <div style="font-size:14px;color:#B8892A;font-weight:500;margin-top:4px">""" + datetime.now().strftime('%b %d, %Y · %H:%M') + """</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────
df = None
data_dir = os.path.join(os.path.dirname(__file__), "data")

if data_source == "Use Sample Data":
    if report_type == "Sales Intelligence":
        sample_path = os.path.join(data_dir, "sales_data.csv")
        if os.path.exists(sample_path):
            df = pd.read_csv(sample_path)
            st.info(f"📁 Loaded sample sales data — {len(df)} records across {df['date'].nunique()} days")
        else:
            st.error("Sample data file not found. Please upload a CSV.")
    else:
        sample_path = os.path.join(data_dir, "operations_data.csv")
        if os.path.exists(sample_path):
            df = pd.read_csv(sample_path)
            st.info(f"📁 Loaded sample operations data — {len(df)} records")
        else:
            st.error("Sample data file not found. Please upload a CSV.")
else:
    uploaded = st.file_uploader(
        "Upload your CSV file",
        type=['csv'],
        help="Sales CSV: date, region, product, revenue, units_sold, target, returns, cost\nOps CSV: date, department, metric, value, threshold, status"
    )
    if uploaded:
        df = pd.read_csv(uploaded)
        st.success(f"✅ Uploaded: {uploaded.name} — {len(df)} records")
    else:
        st.markdown("""
        <div style="background:#111124;border:2px dashed #2a2a5a;border-radius:10px;padding:30px;text-align:center;color:#4444aa">
            <div style="font-size:32px">📤</div>
            <div style="font-size:14px;margin-top:8px">Upload a CSV to begin</div>
            <div style="font-size:11px;margin-top:4px;color:#3333aa">or switch to Sample Data in the sidebar</div>
        </div>
        """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# MAIN ANALYSIS
# ─────────────────────────────────────────────
if df is not None:
    # Quick data preview
    with st.expander("🔍 Data Preview", expanded=False):
        col1, col2 = st.columns([2, 1])
        with col1:
            st.dataframe(df.head(10), use_container_width=True)
        with col2:
            st.markdown("**Dataset Info**")
            info_df = pd.DataFrame({
                'Metric': ['Rows', 'Columns', 'Date Range', 'Null Values'],
                'Value': [
                    str(len(df)),
                    str(len(df.columns)),
                    f"{df['date'].min()} → {df['date'].max()}" if 'date' in df.columns else 'N/A',
                    str(df.isnull().sum().sum())
                ]
            })
            st.dataframe(info_df, hide_index=True, use_container_width=True)

    st.markdown("---")

    # ── RUN BUTTON ──
    col_run, col_clear = st.columns([2, 1])
    with col_run:
        run_analysis = st.button("🚀 Run SmartReport Analysis", use_container_width=True)
    with col_clear:
        if st.button("🗑️ Clear Results", use_container_width=True):
            for key in ['report_text', 'anomaly_result', 'kpis', 'forecast_text', 'email_summary']:
                st.session_state[key] = None
            st.rerun()

    if run_analysis:
        if not GROQ_API_KEY or GROQ_API_KEY == "gsk_your_groq_api_key_here":
            st.warning("⚠️ Groq API key not set in config.py — running in offline mode with rule-based analysis.")

        with st.spinner("🔍 Detecting anomalies..."):
            time.sleep(0.5)
            if report_type == "Sales Intelligence":
                anomaly_result = analyze_sales_anomalies(df)
                kpis = compute_kpis(df, "sales")
            else:
                anomaly_result = analyze_operations_anomalies(df)
                kpis = compute_kpis(df, "operations")

        with st.spinner("🤖 Generating AI report narrative..."):
            date_range = ""
            if 'date' in df.columns:
                date_range = f"{df['date'].min()} to {df['date'].max()}"
            if report_type == "Sales Intelligence":
                report_text = generate_sales_report(kpis, anomaly_result, GROQ_API_KEY, date_range)
            else:
                report_text = generate_operations_report(kpis, anomaly_result, GROQ_API_KEY)

        forecast_text = None
        if auto_forecast and GROQ_API_KEY:
            with st.spinner("📈 Generating AI forecast..."):
                df_summary = {
                    "kpis": kpis,
                    "total_anomalies": anomaly_result['total_anomalies'],
                    "high_severity": anomaly_result['high_severity'],
                    "insights": anomaly_result['insights'][:3]
                }
                forecast_text = generate_forecast_narrative(df_summary, GROQ_API_KEY)

        email_summary = None
        if auto_email_summary and GROQ_API_KEY:
            with st.spinner("✉️ Generating email summary..."):
                email_summary = generate_email_summary(
                    report_text, anomaly_result['total_anomalies'],
                    anomaly_result['high_severity'], GROQ_API_KEY
                )

        st.session_state['report_text'] = report_text
        st.session_state['anomaly_result'] = anomaly_result
        st.session_state['kpis'] = kpis
        st.session_state['df'] = df
        st.session_state['report_type'] = report_type
        st.session_state['forecast_text'] = forecast_text
        st.session_state['email_summary'] = email_summary
        st.success("✅ Analysis complete!")

    # ─────────────────────────────────────────
    # RESULTS DISPLAY
    # ─────────────────────────────────────────
    if st.session_state['report_text'] is not None:
        anomaly_result = st.session_state['anomaly_result']
        kpis = st.session_state['kpis']
        report_text = st.session_state['report_text']
        df_stored = st.session_state['df']

        # ── STATUS BAR ──
        high_count = anomaly_result['high_severity']
        if high_count == 0:
            status_html = '<span class="status-pill status-ok">✅ SYSTEM HEALTHY</span>'
        elif high_count <= 2:
            status_html = '<span class="status-pill status-warn">⚠️ MONITORING REQUIRED</span>'
        else:
            status_html = '<span class="status-pill status-crit">🔴 CRITICAL ATTENTION NEEDED</span>'

        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:16px;margin:16px 0">
            {status_html}
            <span style="font-size:12px;color:#8a7030">{anomaly_result['total_anomalies']} anomalies · {high_count} critical · {anomaly_result['medium_severity']} warnings</span>
        </div>
        """, unsafe_allow_html=True)

        # ── KPI CARDS ──
        st.markdown('<div class="section-header">📌 Key Performance Indicators</div>', unsafe_allow_html=True)
        kpi_items = list(kpis.items())
        cols = st.columns(min(len(kpi_items), 4))
        for i, (key, val) in enumerate(kpi_items):
            with cols[i % 4]:
                label = key.replace('_', ' ').title()
                if isinstance(val, float):
                    if any(x in key for x in ['rate', 'margin', 'achievement']):
                        formatted = f"{val:.1f}%"
                    else:
                        formatted = f"₹{val:,.0f}"
                elif isinstance(val, int) and val > 1000:
                    formatted = f"{val:,}"
                else:
                    formatted = str(val) if not isinstance(val, float) else f"{val:.2f}"
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-label">{label}</div>
                    <div class="kpi-value">{formatted}</div>
                </div>
                """, unsafe_allow_html=True)
        # ── TABS ──
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Charts", "🚨 Anomalies", "🤖 AI Report", "📈 Forecast & Export"])

        # ── TAB 1: CHARTS ──
        with tab1:
            if 'revenue' in df_stored.columns:
                df_plot = df_stored.copy()
                df_plot['date'] = pd.to_datetime(df_plot['date'])
                df_plot = df_plot.sort_values('date')

                # Revenue over time with anomaly overlay
                anomaly_flags = detect_anomalies_zscore(df_plot['revenue'], threshold=1.8)
                df_plot['is_anomaly'] = anomaly_flags

                fig = make_subplots(rows=2, cols=2,
                    subplot_titles=('Revenue Trend & Anomalies', 'Revenue by Region',
                                    'Product Performance', 'Target vs Actual'),
                    specs=[[{"colspan": 2}, None], [{}, {}]])
                fig.update_layout(
                    paper_bgcolor='#fdf8ef', plot_bgcolor='#ffffff',
                    font=dict(color='#8a7030', size=11),
                    height=500, showlegend=True,
                    legend=dict(bgcolor='#ffffff', bordercolor='#e8d8a0', borderwidth=1)
                )

                # Revenue line
                fig.add_trace(go.Scatter(
                    x=df_plot['date'], y=df_plot['revenue'],
                    mode='lines', name='Revenue',
                    line=dict(color='#B8892A', width=2),
                    fill='tozeroy', fillcolor='rgba(184,137,42,0.07)'
                ), row=1, col=1)

                # Anomaly markers
                anomaly_df = df_plot[df_plot['is_anomaly']]
                if len(anomaly_df) > 0:
                    fig.add_trace(go.Scatter(
                        x=anomaly_df['date'], y=anomaly_df['revenue'],
                        mode='markers', name='Anomaly',
                        marker=dict(color='#E24B4A', size=10, symbol='x',
                                    line=dict(color='#E24B4A', width=2))
                    ), row=1, col=1)

                # Target line
                if 'target' in df_plot.columns:
                    fig.add_trace(go.Scatter(
                        x=df_plot['date'], y=df_plot['target'],
                        mode='lines', name='Target',
                        line=dict(color='#9E9E9E', width=1, dash='dash')
                    ), row=1, col=1)

                # Region bar
                region_rev = df_plot.groupby('region')['revenue'].sum().reset_index()
                fig.add_trace(go.Bar(
                    x=region_rev['region'], y=region_rev['revenue'],
                    marker_color='#C9A030', name='Region Revenue', showlegend=False
                ), row=2, col=1)

                # Product bar
                if 'product' in df_plot.columns:
                    prod_rev = df_plot.groupby('product')['revenue'].sum().reset_index()
                    fig.add_trace(go.Bar(
                        x=prod_rev['product'], y=prod_rev['revenue'],
                        marker_color=['#B8892A', '#D4AA60', '#EF9F27'][:len(prod_rev)],
                        name='Product Revenue', showlegend=False
                    ), row=2, col=2)

                for row in [1, 2]:
                    for col in [1, 2]:
                        try:
                            fig.update_xaxes(gridcolor='#e8d8a055', row=row, col=col)
                            fig.update_yaxes(gridcolor='#e8d8a055', row=row, col=col)
                        except:
                            pass

                st.plotly_chart(fig, use_container_width=True)

            elif 'value' in df_stored.columns:
                df_plot = df_stored.copy()
                df_plot['date'] = pd.to_datetime(df_plot['date'])
                fig = px.line(df_plot, x='date', y='value', color='metric', facet_col='department',
                              template='plotly_white',
                              color_discrete_sequence=['#B8892A','#C9A030','#D4AA60','#EF9F27'])
                fig.update_layout(paper_bgcolor='#fdf8ef', plot_bgcolor='#ffffff', height=400)
                st.plotly_chart(fig, use_container_width=True)

        # ── TAB 2: ANOMALIES ──
        with tab2:
            if anomaly_result['anomalies']:
                st.markdown(f'<div class="section-header">🚨 {anomaly_result["total_anomalies"]} Anomalies Detected</div>', unsafe_allow_html=True)
                for a in anomaly_result['anomalies']:
                    sev = a['severity']
                    st.markdown(f"""
                    <div class="anomaly-card {sev}">
                        <span class="sev-badge">{sev}</span>
                        <div class="anom-type">{a['type']}</div>
                        <div class="anom-detail">{a['detail']}</div>
                        <div class="anom-date">📅 {a['date']}</div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown('<div class="section-header">💡 Data Insights</div>', unsafe_allow_html=True)
                for insight in anomaly_result['insights']:
                    st.markdown(f'<div style="color:#6a5020;font-size:13px;padding:6px 0;border-bottom:1px solid #e8d8a0">{insight}</div>', unsafe_allow_html=True)
            else:
                st.success("✅ No anomalies detected in this dataset.")

        # ── TAB 3: AI REPORT ──
        with tab3:
            st.markdown('<div class="section-header">🤖 AI-Generated Intelligence Report</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="report-box">{report_text}</div>', unsafe_allow_html=True)

            if st.session_state.get('email_summary'):
                st.markdown('<div class="section-header">✉️ Email Alert Summary</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="report-box" style="max-height:200px">{st.session_state["email_summary"]}</div>', unsafe_allow_html=True)

        # ── TAB 4: FORECAST & EXPORT ──
        with tab4:
            if st.session_state.get('forecast_text'):
                st.markdown('<div class="section-header">📈 AI 7-Day Forecast</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="report-box">{st.session_state["forecast_text"]}</div>', unsafe_allow_html=True)
            elif not GROQ_API_KEY or GROQ_API_KEY == "gsk_your_groq_api_key_here":
                st.info("💡 Add your Groq API key in config.py to enable AI-powered forecasting.")

            st.markdown('<div class="section-header">📥 Export Report</div>', unsafe_allow_html=True)
            col_e1, col_e2 = st.columns(2)

            with col_e1:
                if st.button("📄 Export as TXT Report", use_container_width=True):
                    reports_dir = os.path.join(os.path.dirname(__file__), "reports")
                    path = export_report_txt(report_text, kpis, anomaly_result,
                                              st.session_state['report_type'], reports_dir)
                    with open(path, 'r', encoding='utf-8') as f:
                        st.download_button("⬇️ Download TXT", f.read(), file_name=os.path.basename(path),
                                           mime='text/plain', use_container_width=True)

            with col_e2:
                if st.button("🌐 Export as HTML Report", use_container_width=True):
                    reports_dir = os.path.join(os.path.dirname(__file__), "reports")
                    path = export_report_html(report_text, kpis, anomaly_result,
                                              st.session_state['report_type'], reports_dir)
                    with open(path, 'r', encoding='utf-8') as f:
                        st.download_button("⬇️ Download HTML", f.read(), file_name=os.path.basename(path),
                                           mime='text/html', use_container_width=True)

            # Email send
            if enable_email and st.session_state.get('report_text'):
                st.markdown('<div class="section-header">📧 Send Email Alert</div>', unsafe_allow_html=True)
                if st.button("📤 Send Report Email Now", use_container_width=True):
                    recipients = [r.strip() for r in recipient_emails.strip().split('\n') if r.strip()]
                    if recipients:
                        with st.spinner("Sending..."):
                            result = send_report_email(
                                GMAIL_ADDRESS, GMAIL_APP_PASSWORD, recipients,
                                f"SmartReport Alert — {anomaly_result['total_anomalies']} Anomalies Detected",
                                report_text
                            )
                        if result['success']:
                            st.success(f"✅ {result['message']}")
                        else:
                            st.error(f"❌ {result['message']}")
                    else:
                        st.warning("Please add at least one recipient email.")

else:
    # Welcome screen
    st.markdown("""
    <div style="text-align:center;padding:60px 20px;color:#3333aa">
        <div style="font-size:64px;margin-bottom:16px">📊</div>
        <div style="font-family:'DM Serif Display',serif;font-size:24px;color:#1a1208;margin-bottom:12px">
            Ready to Analyse
        </div>
        <div style="font-size:14px;color:#6a5020;max-width:400px;margin:auto;line-height:1.8">
            Select a data source and report type in the sidebar,<br>
            then click <strong style="color:#B8892A">Run SmartReport Analysis</strong> to begin.
        </div>
        <div style="margin-top:32px;display:flex;gap:20px;justify-content:center;flex-wrap:wrap">
            <div style="background:#ffffff;border:1px solid #e8d8a0;border-top:3px solid #B8892A;border-radius:10px;padding:16px 24px;text-align:left;width:180px">
                <div style="font-size:24px">🔍</div>
                <div style="font-size:12px;color:#1a1208;margin-top:8px;font-weight:600">Anomaly Detection</div>
                <div style="font-size:11px;color:#8a7030;margin-top:4px">Z-Score + IQR statistical methods</div>
            </div>
            <div style="background:#ffffff;border:1px solid #e8d8a0;border-top:3px solid #C9A030;border-radius:10px;padding:16px 24px;text-align:left;width:180px">
                <div style="font-size:24px">🤖</div>
                <div style="font-size:12px;color:#1a1208;margin-top:8px;font-weight:600">AI Narratives</div>
                <div style="font-size:11px;color:#8a7030;margin-top:4px">Groq LLM executive reports</div>
            </div>
            <div style="background:#ffffff;border:1px solid #e8d8a0;border-top:3px solid #D4AA60;border-radius:10px;padding:16px 24px;text-align:left;width:180px">
                <div style="font-size:24px">📈</div>
                <div style="font-size:12px;color:#1a1208;margin-top:8px;font-weight:600">AI Forecast</div>
                <div style="font-size:11px;color:#8a7030;margin-top:4px">7-day forward intelligence</div>
            </div>
            <div style="background:#ffffff;border:1px solid #e8d8a0;border-top:3px solid #EF9F27;border-radius:10px;padding:16px 24px;text-align:left;width:180px">
                <div style="font-size:24px">📧</div>
                <div style="font-size:12px;color:#1a1208;margin-top:8px;font-weight:600">Email Alerts</div>
                <div style="font-size:11px;color:#8a7030;margin-top:4px">Auto-deliver to stakeholders</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
