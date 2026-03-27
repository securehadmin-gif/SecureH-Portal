import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# --- 1. CONFIGURATION ---
# In production, use st.secrets for these!
CLIENT_ID = "api-key-42129c27-66f0-4af0-ab7e-eec58245e89aa9ee04d8-c021-7000-9100-463e86ad7d4f@action1.com"
CLIENT_SECRET = "41f772f5a1e40b609a5f4baf14a8b6b6"
BASE_URL = "https://app.au.action1.com/api/3.0"

# --- 2. API LOGIC ---
@st.cache_data(ttl=3500) # Cache token for 1 hour
def get_access_token():
    auth_url = f"{BASE_URL}/oauth2/token"
    payload = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'client_credentials'
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    try:
        response = requests.post(auth_url, data=payload, headers=headers)
        response.raise_for_status()
        return response.json().get('access_token')
    except Exception as e:
        st.error(f"Auth Error: {e}")
        return None

def fetch_action1_data(endpoint, token):
    headers = {'Authorization': f'Bearer {token}'}
    try:
        response = requests.get(f"{BASE_URL}/{endpoint}", headers=headers)
        response.raise_for_status()
        return response.json().get('items', [])
    except Exception as e:
        st.sidebar.error(f"Data Fetch Error: {e}")
        return []

# --- 3. STREAMLIT UI SETUP ---
st.set_page_config(page_title="SecureH | IT Audit Portal", layout="wide", page_icon="🛡️")

# Custom CSS for "Fancy" look
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { 
        background-color: #ffffff; 
        padding: 15px; 
        border-radius: 10px; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); 
    }
    </style>
    """, unsafe_allow_html=True) # Changed from unsafe_allow_headers to unsafe_allow_html

# --- 4. MAIN EXECUTION ---
token = get_access_token()

if token:
    with st.sidebar:
        st.header("Settings")
        orgs = fetch_action1_data("organizations", token)
        
        if orgs:
            org_map = {o['name']: o['id'] for o in orgs}
            selected_org_name = st.selectbox("Select Client", list(org_map.keys()))
            selected_org_id = org_map[selected_org_name]
        else:
            st.error("No organizations found.")
            st.stop()

    # Fetch Endpoints
    endpoints_raw = fetch_action1_data(f"endpoints/managed/{selected_org_id}?fields=*", token)
    df = pd.DataFrame(endpoints_raw)

    if not df.empty:
        # --- DATA CLEANING (The Fix for TypeErrors) ---
        # 1. Force numeric columns to be numbers, replace 'None' with 0
        numeric_cols = ['missing_updates', 'missing_critical_updates', 'vulnerabilities_count']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            else:
                df[col] = 0 # Create it if it doesn't exist to prevent crashes

        # 2. Find the OS column dynamically
        os_col = next((c for c in ['os_name', 'os_family', 'operating_system', 'os_version'] if c in df.columns), None)
        
        # 3. Ensure 'name' exists for the bar chart
        if 'name' not in df.columns:
            df['name'] = "Unknown Device"

        # --- HEADER METRICS ---
        st.header(f"Executive Summary: {selected_org_name}")
        m1, m2, m3, m4 = st.columns(4)
        
        m1.metric("Total Assets", len(df))
        m2.metric("Critical Patches", int(df['missing_critical_updates'].sum()), delta="Action Required", delta_color="inverse")
        m3.metric("Security Risks", int(df['vulnerabilities_count'].sum()))
        m4.metric("Risk Level", "High" if df['vulnerabilities_count'].sum() > 0 else "Low")

        # --- VISUALIZATION SECTION ---
        st.divider()
        c1, c2 = st.columns(2)

        with c1:
            st.subheader("OS Distribution")
            if os_col:
                # Clean OS names to ensure they are strings
                df[os_col] = df[os_col].astype(str).replace('None', 'Unknown')
                fig_os = px.pie(df, names=os_col, hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig_os, use_container_width=True)
            else:
                st.info("No OS data found in API response.")

        with c2:
            st.subheader("Top 10 Vulnerable Endpoints")
            # We sort by missing updates for the bar chart
            top_10 = df.nlargest(10, 'missing_updates')
            if not top_10.empty and top_10['missing_updates'].sum() > 0:
                fig_bar = px.bar(top_10, 
                                 x='name', y='missing_updates', 
                                 color='missing_updates',
                                 labels={'missing_updates': 'Unpatched Items'},
                                 color_continuous_scale='Reds')
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("All devices are up to date! No bars to show.")

        # --- DATA TABLE ---
        st.divider()
        st.subheader("📋 Detailed Endpoint Audit List")
        display_cols = [c for c in ['name', os_col, 'ip_address', 'last_seen', 'missing_updates'] if c and c in df.columns]
        st.dataframe(df[display_cols], use_container_width=True)

    else:
        st.warning(f"No active devices found for {selected_org_name}.")
else:
    st.error("Authentication Failed. Please check your Action1 API Credentials.")
