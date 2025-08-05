import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from dotenv import load_dotenv
import os
#
load_dotenv()
sheet_url = os.getenv("GOOGLE_SHEET_URL")
st.set_page_config(layout="wide")
st.title("📊 Production Dashboard (Multi-Month View)")

# Load from Google Drive
@st.cache_data
def load_all_months():
    xls = pd.ExcelFile(sheet_url)
    data = {}
    for sheet in xls.sheet_names:
        df = xls.parse(sheet)
        df.dropna(how='all', inplace=True)
        df.dropna(axis=1, how='all', inplace=True)
        
        # Clean column names
        df.columns = df.columns.str.strip().str.upper()
        
        # DEBUG: Print columns to verify
        print(f"Columns in sheet '{sheet}': {df.columns.tolist()}")
        
        # Convert DATE column to datetime
        if 'DATE' in df.columns:
            df["DATE"] = pd.to_datetime(df["DATE"], errors='coerce')
        else:
            st.error(f"'DATE' column not found in sheet {sheet}. Check Excel structure.")
        
        data[sheet.strip()] = df
    return data


all_data = load_all_months()

# Month selector
month = st.selectbox("Select Month", sorted(all_data.keys()))
df = all_data[month]

# Today's data
today = pd.Timestamp(datetime.now().date())
df_today = df[df["DATE"] == today]

st.header(f"📅 Summary for {month}")

# Today's summary
if not df_today.empty:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Day Pick", df_today["DAY PICK"].sum())
    col2.metric("Day MTR", df_today["DAY MTR"].sum())
    col3.metric("Night Pick", df_today["NIGHT PICK"].sum())
    col4.metric("Night MTR", df_today["NIGHT MTR"].sum())
else:
    st.warning("No data for today in this month.")

# Daily Chart
st.subheader("📊 Daily Production")
fig, ax = plt.subplots()
df.plot(x="DATE", y=["DAY MTR", "NIGHT MTR"], ax=ax, marker="o", figsize=(10, 4))
plt.xticks(rotation=45)
st.pyplot(fig)

# Machine Summary
st.subheader("⚙️ M NO-wise Production")
df["TOTAL PICK"] = df["DAY PICK"] + df["NIGHT PICK"]
df["TOTAL MTR"] = df["DAY MTR"] + df["NIGHT MTR"]
machine_summary = df.groupby("M NO")[["DAY PICK", "NIGHT PICK", "DAY MTR", "NIGHT MTR", "TOTAL PICK", "TOTAL MTR"]].sum()
st.dataframe(machine_summary)

# Insights
st.subheader("🔍 Insights")
best_day = df.loc[df["TOTAL MTR"].idxmax()]
worst_day = df.loc[df["TOTAL MTR"].idxmin()]
st.markdown(f"📈 Best Day: {best_day['DATE'].date()} - {best_day['TOTAL MTR']} MTR")
st.markdown(f"📉 Worst Day: {worst_day['DATE'].date()} - {worst_day['TOTAL MTR']} MTR")

# Machine average performance
machine_avg = df.groupby("M NO")["TOTAL MTR"].mean()
top_machine = machine_avg.idxmax()
st.markdown(f"🏭 Top Machine: {top_machine} with Avg {machine_avg.max():.2f} MTR")

# Efficiency ratio
df["EFFICIENCY"] = df["TOTAL PICK"] / df["TOTAL MTR"]
st.markdown(f"⚙️ Avg Efficiency (Pick/MTR): {df['EFFICIENCY'].mean():.2f}")
