import streamlit as st
import time
import pandas as pd
import os
from datetime import datetime
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import numpy as np

# ---------- Functions ----------

def get_uptime():
    with open('/proc/uptime', 'r') as f:
        return float(f.readline().split()[0])

def format_uptime(seconds):
    days = int(seconds // (24 * 3600))
    hours = int((seconds % (24 * 3600)) // 3600)
    minutes = int((seconds % 3600) // 60)
    return days, hours, minutes

def log_data(uptime):
    file = "usage_log.csv"
    now = datetime.now()

    data = {
        "time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "uptime_hours": uptime / 3600
    }

    df = pd.DataFrame([data])

    if os.path.exists(file):
        df.to_csv(file, mode='a', header=False, index=False)
    else:
        df.to_csv(file, index=False)

def load_data():
    if os.path.exists("usage_log.csv"):
        return pd.read_csv("usage_log.csv")
    return pd.DataFrame()


def get_ai_recommendation(df, days):
    if df.empty:
        return "✅ System usage is optimal.", "success"

    if len(df) > 5:
        working_df = df.copy()
        working_df['time'] = pd.to_datetime(working_df['time'])
        working_df['time_num'] = (working_df['time'] - working_df['time'].min()).dt.total_seconds()

        X = working_df[['time_num']]
        y = working_df['uptime_hours']

        model = LinearRegression()
        model.fit(X, y)

        future_time = pd.DataFrame({'time_num': [working_df['time_num'].max() + 3600]})
        prediction = model.predict(future_time)[0]

        if prediction > 120:
            return "🔄 AI suggests restarting your system soon.", "warning"
        if prediction > y.mean() + y.std():
            return "⚡ AI suggests monitoring system usage closely.", "warning"
        return "✅ AI predicts normal system usage.", "success"

    if days >= 5:
        return "🔄 You should restart your system for better performance.", "warning"
    if days >= 2:
        return "⚡ Moderate usage detected. Monitor performance.", "info"
    return "✅ System usage is optimal.", "success"

# ---------- UI ----------

st.set_page_config(page_title="AI Laptop Tracker", layout="wide")
st.title("🤖 AI Laptop Usage Dashboard")

uptime = get_uptime()
days, hours, minutes = format_uptime(uptime)

log_data(uptime)

# ---------- Metrics ----------
col1, col2, col3 = st.columns(3)
col1.metric("Days", days)
col2.metric("Hours", hours)
col3.metric("Minutes", minutes)

st.info(f"Running for: {days}d {hours}h {minutes}m")

# ---------- Load Data ----------
df = load_data()

# ---------- Graph ----------
st.subheader("📊 Uptime Trend")

if not df.empty:
    df['time'] = pd.to_datetime(df['time'])

    plt.figure()
    plt.plot(df['time'], df['uptime_hours'])
    plt.xlabel("Time")
    plt.ylabel("Uptime (Hours)")
    plt.title("Usage Over Time")
    st.pyplot(plt)

# ---------- AI Prediction ----------
st.subheader("🧠 AI Prediction")

if not df.empty and len(df) > 5:
    df['time_num'] = (df['time'] - df['time'].min()).dt.total_seconds()

    X = df[['time_num']]
    y = df['uptime_hours']

    model = LinearRegression()
    model.fit(X, y)

    # Predict next 1 hour
    future_time = pd.DataFrame({'time_num': [df['time_num'].max() + 3600]})
    prediction = model.predict(future_time)[0]

    st.success(f"📈 Predicted uptime in 1 hour: {prediction:.2f} hours")

    # Restart suggestion
    if prediction > 120:
        st.warning("⚠️ AI Suggestion: Restart your system soon!")

# ---------- Anomaly Detection ----------
st.subheader("🚨 Anomaly Detection")

if not df.empty:
    mean = df['uptime_hours'].mean()
    std = df['uptime_hours'].std()

    latest = df['uptime_hours'].iloc[-1]

    if abs(latest - mean) > 2 * std:
        st.error("🚨 Unusual system usage detected!")
    else:
        st.success("✅ Usage looks normal")

# ---------- Recommendation ----------
st.subheader("💡 AI Recommendation")

recommendation_text, recommendation_level = get_ai_recommendation(df, days)

if recommendation_level == "warning":
    st.warning(recommendation_text)
elif recommendation_level == "info":
    st.info(recommendation_text)
else:
    st.success(recommendation_text)

# ---------- Auto Refresh ----------
time.sleep(5)
st.rerun()