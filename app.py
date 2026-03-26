import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from groq import Groq

# --- 1. SETTINGS & AUTH ---
st.set_page_config(page_title="SecureH Executive Portal", layout="wide")

def get_token():
    try:
        url = "https://app.au.action1.com/api/3.0/oauth2/token"
        res = requests.post(url, data={
            "client_id": st.secrets["ACTION1_CLIENT_ID"],
            "client_secret": st.secrets["ACTION1_CLIENT_SECRET"]
        }, headers={"Content-Type": "application/x-www-form-urlencoded"})
        return res.json().get("access_token")
    except:
        return None

# --- 2. DATA FETCHING (REAL VS MOCK) ---
def get_data(token):
    if token:
        headers = {"Authorization": f"Bearer {token}"}
        # Try to get real endpoints
        res = requests.get("https://app.au.action1.com/api/3.0/endpoints", headers=headers)
        if res.status_code == 200:
            items = res.json().get("items", [])
            if items:
                df = pd.DataFrame(items)
                # Rename columns to match our fancy dashboard needs
                df = df.rename(columns={'endpoint_name': 'Device', 'os_name': 'OS', 'missing_critical_updates': 'Critical'})
                df['Warning'] = 2 # Placeholder for non-critical
                df['Source'] = "LIVE DATA"
                return df
    
    # MOCK DATA if API fails or is empty
    st.sidebar.warning("⚠️ Using Assessment Simulation Mode (API Restricted)")
    mock_data = [
        {"Device": "SH-RECEPTION-01", "OS": "Windows 10", "Critical": 5, "Warning": 8, "Source": "SIMULATED"},
        {"Device": "SH-SERVER-PROD", "OS": "Win Server 2022", "Critical": 12, "Warning": 15, "Source": "SIMULATED"},
        {"Device": "Shivnit-PC (Demo)", "OS": "Windows 11", "Critical": 1, "Warning": 4, "Source": "SIMULATED"},
    ]
    return pd.DataFrame(mock_data)

# --- 3. BUILD THE DASHBOARD ---
st.title("🛡️ SecureH Managed IT Assessment")
token = get_token()
df = get_data(token)

# METRICS
c1, c2, c3 = st.columns(3)
total_crit = df['Critical'].sum()
c1.metric("Fleet Risk Level", "HIGH" if total_crit > 10 else "MODERATE")
c2.metric("Critical Gaps", total_crit)
c3.metric("Assessment Status", df['Source'].iloc[0])

# CHARTS
st.subheader("🚀 Vulnerability Distribution")
fig = px.bar(df, x="Device", y="Critical", color="Critical", 
             color_continuous_scale="Reds", title="Missing Security Patches per Device")
st.plotly_chart(fig, use_container_width=True)

# AI REPORT
st.divider()
if st.button("Generate AI Executive Analysis"):
    client = Groq(api_key=st.secrets["GROQ_TOKEN"])
    prompt = f"Analyze these IT risks for a business owner. Data: {df.to_string()}. Be professional and urgent."
    with st.spinner("AI is auditing network..."):
        completion = client.chat.completions.create(messages=[{"role":"user","content":prompt}], model="llama3-8b-8192")
        st.success(completion.choices[0].message.content)

# DATA TABLE (Removed the styling to prevent the Matplotlib error)
st.subheader("🔍 Deep-Dive Inventory")
st.dataframe(df, use_container_width=True)
