import streamlit as st
import psutil
import pandas as pd
import os
from datetime import datetime
import matplotlib.pyplot as plt
import time

LOG_COLUMNS = ["time", "uptime_hours", "cpu", "ram", "disk"]

# ---------------- CONFIG ----------------
st.set_page_config(page_title="NeuroTrack AI", layout="wide")

# ---------------- STYLE ----------------
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    </style>
""", unsafe_allow_html=True)

# ---------------- FUNCTIONS ----------------

def get_uptime():
    with open('/proc/uptime', 'r') as f:
        return float(f.readline().split()[0])

def format_uptime(seconds):
    days = int(seconds // (24 * 3600))
    hours = int((seconds % (24 * 3600)) // 3600)
    minutes = int((seconds % 3600) // 60)
    return days, hours, minutes

def get_system_stats():
    return {
        "cpu": psutil.cpu_percent(),
        "ram": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage('/').percent
    }


def ensure_log_schema(file):
    if not os.path.exists(file):
        return

    try:
        header_df = pd.read_csv(file, nrows=0)
        if list(header_df.columns) == LOG_COLUMNS:
            return
    except Exception:
        pass

    backup_name = f"usage_log_legacy_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    os.replace(file, backup_name)

def log_data(uptime, stats):
    file = "usage_log.csv"
    now = datetime.now()
    ensure_log_schema(file)

    data = {
        "time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "uptime_hours": uptime / 3600,
        "cpu": stats["cpu"],
        "ram": stats["ram"],
        "disk": stats["disk"]
    }

    df = pd.DataFrame([data])

    if os.path.exists(file):
        df.to_csv(file, mode='a', header=False, index=False)
    else:
        df.to_csv(file, index=False)

def load_data():
    if os.path.exists("usage_log.csv"):
        try:
            df = pd.read_csv("usage_log.csv")
        except Exception:
            return pd.DataFrame(columns=LOG_COLUMNS)

        for col in LOG_COLUMNS:
            if col not in df.columns:
                df[col] = 0 if col in ["cpu", "ram", "disk"] else pd.NA
        return df[LOG_COLUMNS]
    return pd.DataFrame()

def health_score(cpu, ram, disk):
    score = 100 - (cpu * 0.3 + ram * 0.4 + disk * 0.3)
    return max(0, int(score))


def estimate_next_value(series):
    clean_series = series.dropna()
    if len(clean_series) < 3:
        return clean_series.iloc[-1] if len(clean_series) > 0 else 0

    recent = clean_series.tail(8)
    trend = recent.diff().dropna().mean()
    return max(0, min(100, recent.iloc[-1] + trend))

# ---------------- SIDEBAR ----------------

st.sidebar.title("🧠 NeuroTrack AI")
page = st.sidebar.radio("Navigation", ["Dashboard", "Analytics", "AI Insights"])

# ---------------- MAIN ----------------

uptime = get_uptime()
days, hours, minutes = format_uptime(uptime)
stats = get_system_stats()

log_data(uptime, stats)
df = load_data()

# ---------------- DASHBOARD ----------------

if page == "Dashboard":
    st.title("💻 System Dashboard")

    col1, col2, col3 = st.columns(3)
    col1.metric("🕒 Days", days)
    col2.metric("⏳ Hours", hours)
    col3.metric("⏱ Minutes", minutes)

    st.info(f"System running for {days}d {hours}h {minutes}m")

    st.subheader("⚙️ Live System Stats")

    col1, col2, col3 = st.columns(3)
    col1.metric("CPU %", stats["cpu"])
    col2.metric("RAM %", stats["ram"])
    col3.metric("Disk %", stats["disk"])

    score = health_score(stats["cpu"], stats["ram"], stats["disk"])
    st.metric("🧠 System Health Score", score)

# ---------------- ANALYTICS ----------------

elif page == "Analytics":
    st.title("📊 Analytics")

    if not df.empty:
        df['time'] = pd.to_datetime(df['time'])
        recent_df = df.tail(120).copy()

        st.subheader("Snapshot")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Samples", len(recent_df))
        col2.metric("Avg CPU", f"{recent_df['cpu'].mean():.1f}%")
        col3.metric("Avg RAM", f"{recent_df['ram'].mean():.1f}%")
        col4.metric("Peak Disk", f"{recent_df['disk'].max():.1f}%")

        trend_tab, dist_tab, compare_tab = st.tabs(["Trends", "Distribution", "Compare"])

        with trend_tab:
            selected_metric = st.selectbox(
                "Metric",
                ["uptime_hours", "cpu", "ram", "disk"],
                index=1,
            )
            chart_df = recent_df[["time", selected_metric]].copy()
            chart_df["rolling_mean"] = chart_df[selected_metric].rolling(window=5, min_periods=1).mean()

            plt.figure(figsize=(10, 4))
            plt.plot(chart_df["time"], chart_df[selected_metric], label="Raw", alpha=0.5)
            plt.plot(chart_df["time"], chart_df["rolling_mean"], label="Rolling Mean", linewidth=2)
            plt.xlabel("Time")
            plt.ylabel(selected_metric.replace("_", " ").title())
            plt.legend()
            st.pyplot(plt)

        with dist_tab:
            distribution_metric = st.selectbox("Distribution Metric", ["cpu", "ram", "disk"], index=0)
            plt.figure(figsize=(8, 4))
            plt.hist(recent_df[distribution_metric], bins=12)
            plt.xlabel(f"{distribution_metric.upper()} %")
            plt.ylabel("Frequency")
            st.pyplot(plt)

        with compare_tab:
            latest = recent_df.iloc[-1]
            compare_df = pd.DataFrame(
                {
                    "Metric": ["CPU", "RAM", "Disk"],
                    "Current": [latest["cpu"], latest["ram"], latest["disk"]],
                    "Average": [recent_df["cpu"].mean(), recent_df["ram"].mean(), recent_df["disk"].mean()],
                }
            ).set_index("Metric")
            st.bar_chart(compare_df)

# ---------------- AI INSIGHTS ----------------

elif page == "AI Insights":
    st.title("🤖 AI Insights")

    if not df.empty:
        recent_df = df.tail(120).copy()
        latest = recent_df.iloc[-1]

        baseline_cpu = recent_df["cpu"].mean()
        baseline_ram = recent_df["ram"].mean()
        baseline_disk = recent_df["disk"].mean()

        cpu_next = estimate_next_value(recent_df["cpu"])
        ram_next = estimate_next_value(recent_df["ram"])
        disk_next = estimate_next_value(recent_df["disk"])

        uptime_risk = min(100, days * 10)
        resource_risk = (latest["cpu"] * 0.35) + (latest["ram"] * 0.35) + (latest["disk"] * 0.30)
        risk_score = int(min(100, (resource_risk * 0.7) + (uptime_risk * 0.3)))

        st.subheader("Risk Summary")
        col1, col2, col3 = st.columns(3)
        col1.metric("Burnout Risk", f"{risk_score}%")
        col2.metric("Predicted CPU (next cycle)", f"{cpu_next:.1f}%")
        col3.metric("Predicted RAM (next cycle)", f"{ram_next:.1f}%")

        if risk_score >= 75:
            st.error("🚨 High risk: system may degrade soon.")
        elif risk_score >= 50:
            st.warning("⚠️ Moderate risk: keep monitoring and reduce heavy tasks.")
        else:
            st.success("✅ Low risk: usage pattern is stable.")

        st.subheader("Anomaly Flags")
        flags = []
        if latest["cpu"] > baseline_cpu + recent_df["cpu"].std():
            flags.append("CPU spike above recent behavior")
        if latest["ram"] > baseline_ram + recent_df["ram"].std():
            flags.append("RAM spike above recent behavior")
        if latest["disk"] > baseline_disk + recent_df["disk"].std():
            flags.append("Disk usage jump detected")

        if flags:
            for flag in flags:
                st.warning(f"• {flag}")
        else:
            st.success("No strong anomalies detected in recent data.")

        st.subheader("AI Action Plan")
        actions = []
        if cpu_next > 80 or latest["cpu"] > 80:
            actions.append("Close browser tabs, IDE tasks, or background apps using high CPU.")
        if ram_next > 80 or latest["ram"] > 80:
            actions.append("Restart memory-heavy apps or reboot to free RAM.")
        if disk_next > 90 or latest["disk"] > 90:
            actions.append("Clean temp/download files and keep at least 10% disk free.")
        if days >= 5:
            actions.append("Planned restart recommended because uptime is above 5 days.")

        if not actions:
            actions.append("No urgent action required. Keep collecting data for stronger predictions.")

        for action in actions:
            st.write(f"- {action}")

# ---------------- AUTO REFRESH ----------------

time.sleep(5)
st.rerun()