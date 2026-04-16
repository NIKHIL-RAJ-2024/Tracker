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

        st.subheader("Uptime Trend")
        plt.figure()
        plt.plot(df['time'], df['uptime_hours'])
        plt.xlabel("Time")
        plt.ylabel("Uptime (Hours)")
        st.pyplot(plt)

        st.subheader("CPU Usage Trend")
        plt.figure()
        plt.plot(df['time'], df['cpu'])
        plt.xlabel("Time")
        plt.ylabel("CPU %")
        st.pyplot(plt)

# ---------------- AI INSIGHTS ----------------

elif page == "AI Insights":
    st.title("🤖 AI Insights")

    if not df.empty:
        avg_cpu = df['cpu'].mean()
        avg_ram = df['ram'].mean()

        st.write(f"📊 Avg CPU Usage: {avg_cpu:.2f}%")
        st.write(f"📊 Avg RAM Usage: {avg_ram:.2f}%")

        if avg_cpu > 70:
            st.warning("⚠️ High CPU usage trend detected")

        if avg_ram > 70:
            st.warning("⚠️ High RAM usage trend detected")

        if days >= 5:
            st.error("🚨 System running too long! Restart recommended")

        st.subheader("💡 Recommendations")

        if stats["cpu"] > 80:
            st.write("Close heavy apps to reduce CPU load")
        if stats["ram"] > 80:
            st.write("Restart system to free memory")
        if stats["disk"] > 90:
            st.write("Free disk space immediately")

# ---------------- AUTO REFRESH ----------------

time.sleep(5)
st.rerun()