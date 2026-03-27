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
    """Generic function to fetch items from any Action1 endpoint"""
    headers = {'Authorization': f'Bearer {token}'}
    try:
        # We append ?fields=* to ensure we get OS, Reboot, and Patch details
        url = f"{BASE_URL}/{endpoint}"
        if "?" not in url:
            url += "?fields=*"
        else:
            url += "&fields=*"
            
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json().get('items', [])
    except Exception as e:
        st.sidebar.error(f"API Fetch Error: {e}")
        return []

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
    # Sidebar for Organization Selection
    with st.sidebar:
        st.header("Client Management")
        orgs = fetch_data("organizations", token)
        
        if orgs:
            org_map = {o['name']: o['id'] for o in orgs}
            selected_org_name = st.selectbox("Select Client / Org", list(org_map.keys()))
            selected_org_id = org_map[selected_org_name]
        else:
            st.error("No organizations found in your Action1 account.")
            st.stop()

    # Fetch Detailed Endpoint Data
    # Path includes the org ID and requests all fields for deep auditing
    endpoint_path = f"endpoints/managed/{selected_org_id}"
    data = fetch_data(endpoint_path, token)
    df = pd.DataFrame(data)

    if not df.empty:
        # --- DATA CLEANING & REPAIR ---
        # Ensure numeric columns are actually numbers to prevent Plotly crashes
        numeric_map = {
            'missing_updates': 'Total Patches',
            'missing_critical_updates': 'Critical Risks',
            'vulnerabilities_count': 'Vulnerabilities'
        }
        for api_key, friendly in numeric_map.items():
            if api_key in df.columns:
                df[api_key] = pd.to_numeric(df[api_key], errors='coerce').fillna(0).astype(int)
            else:
                df[api_key] = 0

        # Find OS column (Action1 varies between os_name/os_version)
        os_col = next((c for c in ['os_name', 'os_version', 'os_family'] if c in df.columns), 'os_name')
        if os_col not in df.columns: df[os_col] = "Unknown OS"

        # Check for Reboot status
        reboot_col = next((c for c in ['reboot_required', 'pending_reboot'] if c in df.columns), None)
        
        # --- EXECUTIVE SUMMARY METRICS ---
        st.header(f"Executive Report: {selected_org_name}")
        m1, m2, m3, m4 = st.columns(4)
        
        total_crit = df['missing_critical_updates'].sum()
        
        m1.metric("Total Managed Assets", len(df))
        m2.metric("Critical Security Risks", total_crit, delta="Action Required" if total_crit > 0 else "Clear", delta_color="inverse")
        m3.metric("Pending Updates", df['missing_updates'].sum())
        
        # Simple Risk Grading
        risk_score = "Low"
        if total_crit > 5: risk_score = "CRITICAL"
        elif total_crit > 0: risk_score = "Medium"
        m4.metric("Overall Risk Level", risk_score)

        # --- VISUAL DASHBOARD ---
        st.divider()
        c1, c2 = st.columns(2)

        with c1:
            st.subheader("OS Distribution")
            df[os_col] = df[os_col].astype(str)
            fig_os = px.pie(df, names=os_col, hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_os, use_container_width=True)

        with c2:
            st.subheader("Patching Status by Device")
            if df['missing_updates'].sum() > 0:
                fig_bar = px.bar(df.nlargest(10, 'missing_updates'), 
                                 x='name', y='missing_updates', 
                                 color='missing_critical_updates',
                                 labels={'missing_updates': 'Updates', 'name': 'Device'},
                                 color_continuous_scale='Reds')
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("Perfect Compliance! No missing updates found.")

        # --- DETAILED AUDIT TABLE ---
        st.divider()
        st.subheader("📋 Full Endpoint Security Audit")
        
        # Create a combined 'Health' status for the report
        def get_health(row):
            if reboot_col and (row[reboot_col] is True or str(row[reboot_col]).lower() == 'true'):
                return "🔄 Reboot Needed"
            if row['missing_critical_updates'] > 0:
                return "⚠️ Vulnerable"
            return "✅ Secure"

        df['Health Status'] = df.apply(get_health, axis=1)

        # Build final display table
        final_cols = ['name', os_col, 'Health Status', 'missing_critical_updates', 'missing_updates', 'last_seen']
        audit_table = df[final_cols].copy()
        audit_table.columns = ['Device Name', 'OS Version', 'Security Status', 'Critical Risks', 'Total Patches', 'Last Seen']
        
        st.dataframe(audit_table, use_container_width=True)

        # --- RECOMMENDATIONS ---
        st.info(f"**Technician Note:** To remediate these issues, log into Action1 and deploy all 'Critical' and 'Security' updates to the {selected_org_name} group.")

    else:
        st.warning(f"No devices found for {selected_org_name}. Please verify the agent is active.")

else:
    st.error("Authentication failed. Verify your Client ID and Secret in the code.")
st.sidebar.divider()
st.sidebar.caption(f"✅ Secure Connection: Active")
st.sidebar.caption(f"📡 Source: Action1 Cloud API (AU Cluster)")
st.sidebar.caption(f"🕒 Last Sync: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}")
