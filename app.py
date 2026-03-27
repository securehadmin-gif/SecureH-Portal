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
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_headers=True)

st.title("🛡️ SecureH Automated IT Audit")
st.caption("Real-time security insights powered by Action1 API")

# --- 4. MAIN EXECUTION ---
token = get_access_token()

if token:
    # Sidebar - Organization Selection
    with st.sidebar:
        st.header("Settings")
        orgs = fetch_action1_data("organizations", token)
        
        if orgs:
            org_map = {o['name']: o['id'] for o in orgs}
            selected_org_name = st.selectbox("Select Client / Organization", list(org_map.keys()))
            selected_org_id = org_map[selected_org_name]
        else:
            st.error("No organizations found.")
            st.stop()

    # Fetch Endpoints for selected Org
    # Using fields=* to get patching and vulnerability data
    endpoints_raw = fetch_action1_data(f"endpoints/managed/{selected_org_id}?fields=*", token)
    df = pd.DataFrame(endpoints_raw)

    if not df.empty:
        # --- HEADER METRICS ---
        st.header(f"Executive Summary: {selected_org_name}")
        m1, m2, m3, m4 = st.columns(4)
        
        total_endpoints = len(df)
        # Check if 'missing_critical_updates' exists, else default to 0
        crit_patches = df['missing_critical_updates'].sum() if 'missing_critical_updates' in df.columns else 0
        vulnerabilities = df['vulnerabilities_count'].sum() if 'vulnerabilities_count' in df.columns else "N/A"
        
        m1.metric("Total Assets", total_endpoints)
        m2.metric("Critical Patches", crit_patches, delta="Action Required", delta_color="inverse")
        m3.metric("Security Risks", vulnerabilities)
        m4.metric("Global Compliance", "84%") # Example static metric

        # --- VISUALIZATION SECTION ---
        st.divider()
        c1, c2 = st.columns(2)

        with c1:
            st.subheader("OS Distribution")
            # Safety Check for Column Name
            os_col = next((c for c in ['os_name', 'os_family', 'operating_system'] if c in df.columns), None)
            if os_col:
                fig_os = px.pie(df, names=os_col, hole=0.5, color_discrete_sequence=px.colors.qualitative.Bold)
                st.plotly_chart(fig_os, use_container_width=True)
            else:
                st.info("OS Data unavailable.")

        with c2:
            st.subheader("Missing Updates per Endpoint")
            if 'name' in df.columns and 'missing_updates' in df.columns:
                fig_bar = px.bar(df.sort_values('missing_updates', ascending=False).head(10), 
                                 x='name', y='missing_updates', color='missing_updates',
                                 color_continuous_scale='Reds')
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("Patch data unavailable for bar chart.")

        # --- DATA TABLE ---
        st.divider()
        st.subheader("📋 Detailed Endpoint Audit List")
        
        # Select only the columns we want to show, if they exist
        display_cols = [c for c in ['name', 'os_name', 'ip_address', 'last_seen', 'missing_critical_updates'] if c in df.columns]
        st.dataframe(df[display_cols], use_container_width=True)
        
        # --- EXPORT SECTION ---
        st.sidebar.divider()
        if st.sidebar.button("Generate Audit PDF (Coming Soon)"):
            st.sidebar.info("PDF Generation feature is being integrated.")

    else:
        st.warning(f"No active devices found for {selected_org_name}.")

else:
    st.error("Authentication Failed. Please check your Action1 API Credentials.")
