import streamlit as st
import requests
import pandas as pd
from groq import Groq
import plotly.express as px

# --- 1. SETUP ---
st.set_page_config(page_title="SecureH AI Assessor", layout="wide")
st.title("🛡️ SecureH Automated IT Assessment")

# Ensure these match your Streamlit Cloud Secrets
CLIENT_ID = st.secrets.get("ACTION1_CLIENT_ID")
CLIENT_SECRET = st.secrets.get("ACTION1_CLIENT_SECRET")
GROQ_KEY = st.secrets.get("GROQ_TOKEN")

# --- 2. AUTHENTICATION ---
def get_action1_token():
    url = "https://app.au.action1.com/api/3.0/oauth2/token"
    payload = {"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET}
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    try:
        res = requests.post(url, data=payload, headers=headers)
        if res.status_code == 200:
            return res.json().get("access_token")
        st.error(f"Auth Failed ({res.status_code}): Check your credentials.")
    except Exception as e:
        st.error(f"Connection Error: {e}")
    return None

# --- 3. DATA FETCHING ---
@st.cache_data(ttl=600)
def fetch_endpoints(_token, org_id=None):
    # Action1 AU Region Endpoint
    # If no org_id is provided, we try the general search
    url = "https://app.au.action1.com/api/3.0/endpoints"
    if org_id:
        url = f"https://app.au.action1.com/api/3.0/endpoints/managed/{org_id}"
    
    headers = {"Authorization": f"Bearer {_token}"}
    res = requests.get(url, headers=headers)
    
    if res.status_code == 200:
        return res.json().get("items", [])
    else:
        # This is where we catch the 403 error and explain it
        st.warning(f"⚠️ Action1 returned {res.status_code}. You may need to enable 'API Access' in your Action1 console settings.")
        return []

# --- 4. MAIN LOGIC ---
token = get_action1_token()

if token:
    # We'll start by searching for ALL endpoints (useful for the 'Shivnit' search)
    raw_data = fetch_endpoints(token)
    
    if raw_data:
        df = pd.DataFrame(raw_data)
        
        # UI METRICS
        st.subheader("📊 Fleet Health Summary")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Devices", len(df))
        
        # Safely count critical updates
        crit_col = 'missing_critical_updates' if 'missing_critical_updates' in df else None
        total_crit = df[crit_col].sum() if crit_col else 0
        col2.metric("Critical Security Gaps", total_crit, delta="Risk High", delta_color="inverse")
        
        # AI REPORT GENERATOR
        st.divider()
        if st.button("Generate AI Assessment"):
            client = Groq(api_api_key=GROQ_KEY)
            prompt = f"Analyze this IT data: {df[['endpoint_name', 'os_name']].to_string()}. Write a 3-sentence risk report for SecureH clients."
            with st.spinner("Analyzing..."):
                chat = client.chat.completions.create(messages=[{"role":"user","content":prompt}], model="llama3-8b-8192")
                st.info(chat.choices[0].message.content)

        # DATA TABLE
        st.subheader("Inventory View")
        st.dataframe(df)
    else:
        st.info("No devices found. Ensure your Action1 agent is running and the API key has 'Read' permissions.")
