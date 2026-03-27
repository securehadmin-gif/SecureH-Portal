import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# --- 1. CONFIGURATION ---
# Replace these with your actual credentials or use st.secrets["KEY"] in Streamlit Cloud
CLIENT_ID = "api-key-42129c27-66f0-4af0-ab7e-eec58245e89aa9ee04d8-c021-7000-9100-463e86ad7d4f@action1.com"
CLIENT_SECRET = "41f772f5a1e40b609a5f4baf14a8b6b6"
BASE_URL = "https://app.au.action1.com/api/3.0"

# --- 2. API & AUTHENTICATION ---
@st.cache_data(ttl=3500)
def get_access_token():
    """Handshake with Action1 to get a fresh OAuth2 Token"""
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
        st.error(f"Authentication Error: {e}")
        return None

def fetch_data(endpoint, token):
    headers = {'Authorization': f'Bearer {token}'}
    try:
        # We use fields=* to get everything, but some clusters 
        # also require the 'include' parameter for patch details
        url = f"{BASE_URL}/{endpoint}?fields=*&include=updates,vulnerabilities"
            
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        items = response.json().get('items', [])
        
        # DEBUG: This will show you the exact keys Action1 is sending in your Streamlit logs
        if items:
            print(f"DEBUG: Keys received from Action1: {items[0].keys()}")
            
        return items
    except Exception as e:
        st.sidebar.error(f"API Fetch Error: {e}")
        return []

# --- INSIDE YOUR MAIN APP LOGIC (Data Cleaning Section) ---
if not df.empty:
    # Action1 sometimes nests data or uses 'critical_vulnerabilities'
    # Let's check for EVERY possible name for critical updates
    crit_options = [
        'missing_critical_updates', 
        'critical_updates_count', 
        'vulnerabilities_critical_count',
        'missing_security_updates'
    ]
    
    actual_crit_col = next((c for c in crit_options if c in df.columns), None)
    
    if actual_crit_col:
        df['critical'] = pd.to_numeric(df[actual_crit_col], errors='coerce').fillna(0).astype(int)
    else:
        # If we still can't find it, let's look for a generic 'updates' list 
        # and count them manually (Last resort)
        df['critical'] = 0 
        st.warning("Could not find 'Critical' field. Showing total updates instead.")

    # ... rest of the code ...

# --- 3. UI LAYOUT & STYLING ---
st.set_page_config(page_title="SecureH | IT Audit Portal", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { 
        background-color: #ffffff; 
        padding: 20px; 
        border-radius: 12px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); 
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ SecureH: Automated IT Assessment")
st.caption("Professional Security Audit Portal | Powered by Action1")

# --- 4. MAIN APP LOGIC ---
token = get_access_token()

if token:
    with st.sidebar:
        st.header("Client Management")
        org_items = fetch_data("organizations", token)
        
        if org_items:
            org_map = {o['name']: o['id'] for o in org_items}
            selected_org_name = st.selectbox("Select Client", list(org_map.keys()))
            selected_org_id = org_map[selected_org_name]
        else:
            st.error("No organizations found.")
            st.stop()

    # 1. FETCH DATA (Using the 'Deep Scan' path)
    endpoint_path = f"endpoints/managed/{selected_org_id}"
    data_items = fetch_data(endpoint_path, token)
    
    # 2. CREATE THE DATAFRAME (This fixes the NameError)
    df = pd.DataFrame(data_items)

    if not df.empty:
        # --- THE "REAL DATA" SCANNER ---
        # We look for ANY column that might contain your "4" missing updates
        possible_cols = [
            'missing_critical_updates', 'critical_updates_count', 
            'vulnerabilities_critical_count', 'missing_updates', 
            'updates_count', 'missing_security_updates'
        ]
        
        # We force these to numbers so we can sum them up
        for col in df.columns:
            if col in possible_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

        # Identify the best 'Critical' column found
        crit_col = next((c for c in ['missing_critical_updates', 'critical_updates_count'] if c in df.columns), None)
        total_col = next((c for c in ['missing_updates', 'updates_count'] if c in df.columns), None)

        # --- EXECUTIVE SUMMARY ---
        st.header(f"Executive Report: {selected_org_name}")
        m1, m2, m3 = st.columns(3)
        
        val_crit = df[crit_col].sum() if crit_col else 0
        val_total = df[total_col].sum() if total_col else 0
        
        m1.metric("Total Assets", len(df))
        m2.metric("Critical Security Risks", int(val_crit), delta="Action Required" if val_crit > 0 else None, delta_color="inverse")
        m3.metric("Total Missing Patches", int(val_total))

        # --- DEBUG VIEW (Temporary) ---
        # If your report still says 0, look at this table to see the REAL column names
        with st.expander("🔍 Technician Data Check (See Raw API Fields)"):
            st.write("Current Columns found in Action1:", df.columns.tolist())
            st.dataframe(df.head(5))

        # --- AUDIT TABLE ---
        st.divider()
        st.subheader("📋 Security Audit Detail")
        
        # Dynamic OS Column
        os_c = next((c for c in ['os_name', 'os_version'] if c in df.columns), 'name')
        
        # Build the viewable report
        report_df = df[['name', os_c]].copy()
        report_df['Critical Risks'] = df[crit_col] if crit_col else 0
        report_df['Total Patches'] = df[total_col] if total_col else 0
        
        st.dataframe(report_df, use_container_width=True)

    else:
        st.warning(f"No devices found for {selected_org_name}.")
else:
    st.error("Auth failed. Please check Client ID/Secret.")
st.sidebar.divider()
st.sidebar.caption(f"✅ Secure Connection: Active")
st.sidebar.caption(f"📡 Source: Action1 Cloud API (AU Cluster)")
st.sidebar.caption(f"🕒 Last Sync: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}")
