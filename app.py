import streamlit as st
import requests
import pandas as pd
from groq import Groq

# --- 1. SETTINGS & AUTH ---
st.set_page_config(page_title="SecureH IT Assessment", layout="wide")
st.title("🛡️ SecureH Free IT Assessment Portal")

# Ensure these match your Streamlit Cloud Secrets exactly
CLIENT_ID = st.secrets["ACTION1_CLIENT_ID"]
CLIENT_SECRET = st.secrets["ACTION1_CLIENT_SECRET"]
GROQ_KEY = st.secrets["GROQ_TOKEN"]
client = Groq(api_key=GROQ_KEY)

# --- 2. AUTHENTICATION ---
def get_action1_token():
    url = "https://app.au.action1.com/api/3.0/oauth2/token"
    payload = {"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET}
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    try:
        res = requests.post(url, data=payload, headers=headers)
        return res.json().get("access_token")
    except:
        return None

# --- 3. DATA FETCHING ---
@st.cache_data(ttl=300)
def get_action1_orgs(_token):
    headers = {"Authorization": f"Bearer {_token}"}
    url = "https://app.au.action1.com/api/3.0/organizations"
    res = requests.get(url, headers=headers)
    return res.json().get("items", []) if res.status_code == 200 else []

def get_org_details(_token, org_id, org_name):
    headers = {"Authorization": f"Bearer {_token}"}
    # Using the Search API - it's more 'aggressive' at finding devices
    url = "https://app.au.action1.com/api/3.0/endpoints" 
    
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            all_devices = res.json().get("items", [])
            
            if org_name == "All Organizations":
                return all_devices
            return [d for d in all_devices if str(d.get('organization_id')) == str(org_id)]
    except:
        pass
    return []

# --- 4. MAIN UI LOGIC ---
token = get_action1_token()

if token:
    orgs = get_action1_orgs(token)
    
    if orgs:
        # Create list for sidebar
        options = ["All Organizations"] + [o['name'] for o in orgs]
        selected_name = st.sidebar.selectbox("Select Organization:", options, key="org_selector")
        
        # Get ID (None if 'All Organizations' is picked)
        selected_id = next((o['id'] for o in orgs if o['name'] == selected_name), None)

        # Fetch devices
        raw_data = get_org_details(token, selected_id, selected_name)

        if raw_data:
            df = pd.DataFrame(raw_data)
            
            # --- METRICS ---
            total = len(df)
            # Action1 field names might vary; checking common ones:
            crit = df['missing_critical_updates'].sum() if 'missing_critical_updates' in df else 0
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Devices", total)
            col2.metric("Critical Risks", crit, delta="Action Required", delta_color="inverse")
            col3.metric("Status", "Monitoring Active" if total > 0 else "Idle")

            # --- AI REPORT ---
            st.divider()
            if st.button("Generate AI Executive Assessment"):
                with st.spinner("AI is analyzing device health..."):
                    prompt = f"Analyze: Organization '{selected_name}' has {total} devices with {crit} critical vulnerabilities. Write a 3-sentence risk summary for a CEO."
                    chat = client.chat.completions.create(messages=[{"role":"user","content":prompt}], model="llama3-8b-8192")
                    st.info(chat.choices[0].message.content)

            # --- DATA TABLE ---
            st.subheader("Inventory View")
            # Show name 'Shivnit' if it exists
            display_cols = ['endpoint_name', 'os_name', 'ip_address']
            st.dataframe(df[[c for c in display_cols if c in df]])
            
        else:
            st.warning(f"No devices found for {selected_name}. Ensure the Action1 agent is active on 'Shivnit'.")
    else:
        st.error("No organizations found in this Action1 account.")
else:
    st.error("Authentication failed. Check your Action1 Secrets.")
