# 📊 SmartReport Agent
### Enterprise AI-Powered Business Intelligence & Anomaly Detection

> Built for Sash.AI portfolio — mirrors their **Smart Reporting Agent** product  
> Stack: Python · Pandas · Groq LLM · Plotly · Streamlit

---

## 🚀 What This Project Does

SmartReport Agent autonomously:
- **Monitors** business data (sales, operations KPIs) in real-time
- **Detects anomalies** using Z-Score + IQR statistical methods
- **Generates AI narratives** via Groq LLM (executive-level reports)
- **Sends email alerts** to stakeholders via Gmail SMTP
- **Exports reports** as styled HTML or TXT files

### ➕ Bonus Features (beyond Sash.AI spec)
1. **AI 7-Day Forecast** — forward-looking business intelligence narrative
2. **Email Summary Generator** — auto-compresses report into email-ready alert

---

## 📁 Project Structure

```
smart_report_agent/
├── app.py                      ← Main Streamlit application
├── requirements.txt            ← Python dependencies
├── .env.example                ← Environment variables template
├── data/
│   ├── sales_data.csv          ← Sample sales dataset (30 days)
│   └── operations_data.csv     ← Sample operations/KPI dataset
├── agents/
│   ├── anomaly_detector.py     ← Statistical anomaly detection engine
│   └── report_generator.py     ← Groq LLM report generation
├── utils/
│   ├── email_sender.py         ← Gmail SMTP email delivery
│   └── report_exporter.py      ← HTML + TXT report export
└── reports/                    ← Auto-created, stores exported reports
```

---

## 🛠️ Tools & Technologies

| Tool | Purpose | Cost |
|------|---------|------|
| Python 3.10+ | Core language | Free |
| Streamlit | Dashboard UI | Free |
| Pandas + NumPy | Data processing & anomaly detection | Free |
| Plotly | Interactive charts | Free |
| Groq API | LLM report generation (llama3-8b) | Free tier |
| Gmail SMTP | Email alert delivery | Free |

**Total cost: $0**

---

## ⚙️ Step-by-Step Setup Guide

### Step 1 — Clone / Download the project
```bash
# If using git
git clone <your-repo-url>
cd smart_report_agent

# Or just download and unzip the folder
```

### Step 2 — Create a virtual environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac / Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — Get your FREE Groq API key
1. Go to **https://console.groq.com**
2. Sign up (free, no credit card needed)
3. Click **API Keys → Create API Key**
4. Copy the key (starts with `gsk_...`)

### Step 5 — (Optional) Set up Gmail for email alerts
1. Go to **https://myaccount.google.com/apppasswords**
2. Select App: **Mail**, Device: **Other** → name it "SmartReport"
3. Copy the 16-character app password
4. Use this password in the app (NOT your regular Gmail password)

> ⚠️ You need 2FA enabled on your Google account for App Passwords

### Step 6 — Run the application
```bash
streamlit run app.py
```

The app opens at **http://localhost:8501**

---

Streamlit live app:https://smartreport-agent.streamlit.app/

## 🎯 How to Use

1. **Enter Groq API Key** in the sidebar (or leave blank for offline mode)
2. **Select Data Source**: Use sample data or upload your own CSV
3. **Choose Report Type**: Sales Intelligence or Operations KPIs
4. **Adjust Detection Sensitivity** with the Z-Score slider
5. **Click "Run SmartReport Analysis"**
6. View results across 4 tabs:
   - 📊 **Charts** — revenue trends, anomaly markers, regional breakdown
   - 🚨 **Anomalies** — severity-graded incident cards
   - 🤖 **AI Report** — LLM-generated executive narrative
   - 📈 **Forecast & Export** — 7-day forecast + download options

---

## 📊 CSV Format for Your Own Data

### Sales Data
```
date,region,product,revenue,units_sold,target,returns,cost
2024-01-01,North,Product A,45200,320,42000,12,28000
```

### Operations/KPI Data
```
date,department,metric,value,threshold,status
2024-01-01,Engineering,Bug Resolution Rate,87.5,85,normal
```

---

## 🧠 How Anomaly Detection Works

1. **Z-Score Method**: Flags values more than N standard deviations from mean
   - Threshold configurable via sidebar slider (default: 1.8)
2. **IQR Method**: Flags values outside Q1-1.5×IQR and Q3+1.5×IQR range
3. **Threshold Breach**: Direct comparison against user-defined thresholds (ops data)

---

## 🔮 Future Enhancements 
- Connect to live databases (PostgreSQL, BigQuery)
- Add APScheduler for automated hourly/daily runs
- Slack/Teams webhook integration
- Multi-dataset comparison across time periods
- Fine-tuned domain-specific LLM for finance reports

---
