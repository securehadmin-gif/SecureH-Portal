import streamlit as st
import requests
import pandas as pd
from groq import Groq

# --- 1. SETTINGS & AUTH ---
st.set_page_config(page_title="SecureH IT Assessment", layout="wide")
st.title("🛡️ SecureH Free IT Assessment Portal")

# Use these exact names in your Streamlit Secrets
CLIENT_ID = st.secrets["ACTION1_CLIENT_ID"]
CLIENT_SECRET = st.secrets["ACTION1_CLIENT_SECRET"]
GROQ_KEY = st.secrets["GROQ_TOKEN"]
client = Groq(api_key=GROQ_KEY)

# --- 2. THE AUTHENTICATION ENGINE ---
def get_action1_token():
    """Exchanges Client ID/Secret for a temporary Bearer Token"""
    url = "https://app.au.action1.com/api/3.0/oauth2/token"
    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    try:
        res = requests.post(url, data=payload, headers=headers)
        return res.json().get("access_token")
    except Exception as e:
        st.error(f"Auth Error: {e}")
        return None

# --- 3. DATA FETCHING FUNCTIONS ---
@st.cache_data(ttl=300)
def get_action1_orgs(_token):
    headers = {"Authorization": f"Bearer {_token}"}
    url = "https://app.au.action1.com/api/3.0/organizations"
    res = requests.get(url, headers=headers)
    return res.json().get("items", []) if res.status_code == 200 else []

@st.cache_data(ttl=60)
def get_org_details(_token, org_id):
    headers = {"Authorization": f"Bearer {_token}"}
    # Step 1: Fetch ALL managed endpoints available to your API key
    url = "https://app.au.action1.com/api/3.0/endpoints/managed"
    
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            all_items = res.json().get("items", [])
            # Step 2: Manually filter for the selected Org ID to be 100% sure
            # Action1 IDs can sometimes be strings or integers, we cast to string to match
            filtered_data = [i for i in all_items if str(i.get('organization_id')) == str(org_id)]
            
            # DEBUG: If still empty, let's see what's actually coming back
            if not filtered_data and all_items:
                st.sidebar.write(f"Found {len(all_items)} total devices, but none matched Org ID: {org_id}")
            
            return filtered_data
    except Exception as e:
        st.error(f"Data Fetch Error: {e}")
    return []

# --- 4. MAIN APP LOGIC ---
token = get_action1_token()

if token:
    orgs = get_action1_orgs(token)
    
    if orgs:
        org_names = [o['name'] for o in orgs]
        selected_name = st.sidebar.selectbox("Select Organization:", org_names)
        selected_id = next(o['id'] for o in orgs if o['name'] == selected_name)

        # Get the real data using the token and the ID
        raw_data = get_org_details(token, selected_id)

        if raw_data:
            df = pd.DataFrame(raw_data)
            
            # --- CALCULATE METRICS ---
            total = len(df)
            crit = df['missing_critical_updates'].sum() if 'missing_critical_updates' in df else 0
            # A simple Risk Score formula: 100 minus (Critical updates * 5), minimum 0.
            risk_score = max(0, 100 - (crit * 5)) 

            # --- DISPLAY DASHBOARD ---
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Devices", total)
            col2.metric("Critical Risks", crit, delta="Fix Needed", delta_color="inverse")
            col3.metric("Health Score", f"{risk_score}/100")

            # --- AI ASSESSMENT ---
            st.divider()
            if st.button("Generate AI Assessment Report"):
                prompt = f"Client {selected_name} has {total} devices with {crit} critical vulnerabilities. Write a short urgent report for the CEO recommending SecureH's patching service."
                completion = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama3-8b-8192"
                )
                st.info(completion.choices[0].message.content)
            
            st.subheader("Device Inventory Details")
            st.dataframe(df[['endpoint_name', 'os_name', 'ip_address']])
        else:
            st.info("No devices found for this organization.")
    else:
        st.error("No organizations found in your Action1 account.")
else:
    st.error("Authentication failed. Check your Client ID and Secret.")
