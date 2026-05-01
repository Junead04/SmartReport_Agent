import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple


def detect_anomalies_zscore(series: pd.Series, threshold: float = 2.0) -> pd.Series:
    """Detect anomalies using Z-score method."""
    if len(series) < 3:
        return pd.Series([False] * len(series), index=series.index)
    mean = series.mean()
    std = series.std()
    if std == 0:
        return pd.Series([False] * len(series), index=series.index)
    z_scores = np.abs((series - mean) / std)
    return z_scores > threshold


def detect_anomalies_iqr(series: pd.Series, multiplier: float = 1.5) -> pd.Series:
    """Detect anomalies using IQR method."""
    if len(series) < 4:
        return pd.Series([False] * len(series), index=series.index)
    Q1 = series.quantile(0.25)
    Q3 = series.quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - multiplier * IQR
    upper = Q3 + multiplier * IQR
    return (series < lower) | (series > upper)


def detect_threshold_breach(df: pd.DataFrame) -> pd.DataFrame:
    """Detect rows where value breaches threshold."""
    if 'value' in df.columns and 'threshold' in df.columns:
        df = df.copy()
        df['threshold_breach'] = df['value'] > df['threshold']
    return df


def analyze_sales_anomalies(df: pd.DataFrame) -> Dict:
    """Full anomaly analysis on sales data."""
    anomalies = []
    insights = []

    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')

    # Revenue anomalies
    revenue_anomalies = detect_anomalies_zscore(df['revenue'], threshold=1.8)
    anomaly_dates = df[revenue_anomalies]
    for _, row in anomaly_dates.iterrows():
        direction = "spike" if row['revenue'] > df['revenue'].mean() else "drop"
        anomalies.append({
            "type": "Revenue Anomaly",
            "severity": "HIGH" if abs(row['revenue'] - df['revenue'].mean()) > df['revenue'].std() * 2.5 else "MEDIUM",
            "date": row['date'].strftime('%Y-%m-%d'),
            "detail": f"Revenue {direction} detected: ₹{row['revenue']:,.0f} vs avg ₹{df['revenue'].mean():,.0f}",
            "region": row.get('region', 'N/A'),
            "product": row.get('product', 'N/A')
        })

    # Target miss detection
    if 'target' in df.columns:
        df['target_gap'] = df['revenue'] - df['target']
        df['target_miss'] = df['target_gap'] < 0
        missed = df[df['target_miss']]
        if len(missed) > 0:
            miss_rate = len(missed) / len(df) * 100
            insights.append(f"Target miss rate: {miss_rate:.1f}% ({len(missed)} of {len(df)} days)")

    # Returns spike
    if 'returns' in df.columns:
        return_anomalies = detect_anomalies_zscore(df['returns'], threshold=2.0)
        for _, row in df[return_anomalies].iterrows():
            anomalies.append({
                "type": "Returns Spike",
                "severity": "MEDIUM",
                "date": row['date'].strftime('%Y-%m-%d'),
                "detail": f"Unusual returns: {row['returns']} units on {row['date'].strftime('%Y-%m-%d')}",
                "region": row.get('region', 'N/A'),
                "product": row.get('product', 'N/A')
            })

    # Top performer
    best_day = df.loc[df['revenue'].idxmax()]
    worst_day = df.loc[df['revenue'].idxmin()]
    insights.append(f"Best day: {best_day['date'].strftime('%b %d')} — ₹{best_day['revenue']:,.0f} ({best_day['region']})")
    insights.append(f"Worst day: {worst_day['date'].strftime('%b %d')} — ₹{worst_day['revenue']:,.0f} ({worst_day['region']})")

    # Region breakdown
    region_revenue = df.groupby('region')['revenue'].sum()
    top_region = region_revenue.idxmax()
    insights.append(f"Top region: {top_region} with ₹{region_revenue[top_region]:,.0f} total revenue")

    # Trend
    if len(df) > 5:
        first_half = df.head(len(df)//2)['revenue'].mean()
        second_half = df.tail(len(df)//2)['revenue'].mean()
        trend_pct = ((second_half - first_half) / first_half) * 100
        trend_dir = "📈 upward" if trend_pct > 0 else "📉 downward"
        insights.append(f"Revenue trend: {trend_dir} ({trend_pct:+.1f}% period-over-period)")

    return {
        "anomalies": anomalies,
        "insights": insights,
        "total_anomalies": len(anomalies),
        "high_severity": len([a for a in anomalies if a['severity'] == 'HIGH']),
        "medium_severity": len([a for a in anomalies if a['severity'] == 'MEDIUM'])
    }


def analyze_operations_anomalies(df: pd.DataFrame) -> Dict:
    """Full anomaly analysis on operations/KPI data."""
    anomalies = []
    insights = []

    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])

    # Status-based anomalies from data
    if 'status' in df.columns:
        status_anomalies = df[df['status'] == 'anomaly']
        for _, row in status_anomalies.iterrows():
            anomalies.append({
                "type": f"KPI Breach — {row['metric']}",
                "severity": "HIGH" if row['value'] > row['threshold'] * 1.5 else "MEDIUM",
                "date": row['date'].strftime('%Y-%m-%d'),
                "detail": f"{row['department']}: {row['metric']} = {row['value']} (threshold: {row['threshold']})",
                "department": row['department']
            })

    # Department anomaly rate
    if 'department' in df.columns and 'status' in df.columns:
        dept_stats = df.groupby('department').apply(
            lambda x: (x['status'] == 'anomaly').sum() / len(x) * 100
        )
        for dept, rate in dept_stats.items():
            if rate > 30:
                insights.append(f"⚠️ {dept} has high anomaly rate: {rate:.1f}%")
            else:
                insights.append(f"✅ {dept} performing well: {100-rate:.1f}% compliance rate")

    return {
        "anomalies": anomalies,
        "insights": insights,
        "total_anomalies": len(anomalies),
        "high_severity": len([a for a in anomalies if a['severity'] == 'HIGH']),
        "medium_severity": len([a for a in anomalies if a['severity'] == 'MEDIUM'])
    }


def compute_kpis(df: pd.DataFrame, data_type: str = "sales") -> Dict:
    """Compute summary KPIs from data."""
    kpis = {}
    if data_type == "sales":
        kpis['total_revenue'] = df['revenue'].sum()
        kpis['avg_daily_revenue'] = df['revenue'].mean()
        kpis['total_units'] = df['units_sold'].sum()
        kpis['avg_order_value'] = df['revenue'].sum() / df['units_sold'].sum()
        if 'target' in df.columns:
            kpis['target_achievement'] = (df['revenue'].sum() / df['target'].sum()) * 100
        if 'returns' in df.columns:
            kpis['return_rate'] = (df['returns'].sum() / df['units_sold'].sum()) * 100
        if 'cost' in df.columns:
            kpis['gross_margin'] = ((df['revenue'].sum() - df['cost'].sum()) / df['revenue'].sum()) * 100
    elif data_type == "operations":
        if 'status' in df.columns:
            kpis['total_checks'] = len(df)
            kpis['anomaly_count'] = (df['status'] == 'anomaly').sum()
            kpis['compliance_rate'] = ((df['status'] == 'normal').sum() / len(df)) * 100
    return kpis
