import streamlit as st
import requests
import pandas as pd
from groq import Groq

# --- CONFIG ---
st.set_page_config(page_title="SecureH IT Assessment", layout="wide")
st.title("🛡️ SecureH Free IT Assessment Portal")

# --- SECURE KEYS ---
# Ensure these are in your Streamlit Cloud Secrets!
ACTION1_KEY = st.secrets["ACTION1_TOKEN"]
GROQ_KEY = st.secrets["GROQ_TOKEN"]
client = Groq(api_key=GROQ_KEY)

# --- API FUNCTIONS ---
@st.cache_data(ttl=300)
def get_action1_orgs():
    headers = {"Authorization": f"Bearer {ACTION1_KEY}"}
    # Note: Replace with your actual Action1 region URL if different
    url = "https://app.action1.com/api/3.0/organizations"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json().get("items", [])
    except Exception as e:
        st.error(f"Connection Error: {e}")
    return []

def get_org_details(org_id):
    headers = {"Authorization": f"Bearer {ACTION1_KEY}"}
    url = f"https://app.action1.com/api/3.0/endpoints/managed?organization_id={org_id}"
    try:
        res = requests.get(url, headers=headers)
        return res.json().get("items", [])
    except:
        return []

# --- SIDEBAR & LOGIC ---
orgs = get_action1_orgs()

if not orgs:
    st.warning("⚠️ No organizations found. Check your Action1 API Key and permissions.")
    st.stop() # Stops the app here so it doesn't crash below

org_names = [o['name'] for o in orgs]
selected_org_name = st.sidebar.selectbox("Select Client to Assess:", org_names)

# Safely get the ID
selected_org_id = next((o['id'] for o in orgs if o['name'] == selected_org_name), None)

# --- DATA PROCESSING ---
raw_data = get_org_details(selected_org_id)

if raw_data:
    df = pd.DataFrame(raw_data)
    # Summarize data for the AI
    total_endpoints = len(df)
    crit_patches = df['missing_critical_updates'].sum() if 'missing_critical_updates' in df else 0
    eol_systems = len(df[df['os_name'].str.contains("Windows 7|Windows 8", na=False)])
    
    # --- DASHBOARD UI ---
    st.subheader(f"Assessment Results: {selected_org_name}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Endpoints", total_endpoints)
    c2.metric("Critical Risks", crit_patches, delta="Action Required", delta_color="inverse")
    c3.metric("Legacy/EOL Systems", eol_systems)

    st.divider()

    # --- AI EXECUTIVE ASSESSMENT ---
    st.subheader("🤖 AI Security Consultant Assessment")
    
    # Professional Sales-Focused Prompt
    ai_prompt = f"""
    You are a Senior Cybersecurity Auditor for SecureH. 
    Analyze these findings for the client '{selected_org_name}':
    - Total Computers: {total_endpoints}
    - Critical Unpatched Vulnerabilities: {crit_patches}
    - End-of-Life (Old) Operating Systems: {eol_systems}
    
    Write a professional 3-paragraph executive summary. 
    Paragraph 1: State the current security posture (use a 'Risk Score' out of 100).
    Paragraph 2: Explain the danger of unpatched systems and EOL software in simple business terms.
    Paragraph 3: Recommend that they sign up for SecureH Managed Services to automate this protection.
    """

    if st.button('Generate Professional Assessment'):
        with st.spinner('Analyzing risk vectors...'):
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": ai_prompt}],
                model="llama3-8b-8192",
            )
            st.markdown(f"> {chat_completion.choices[0].message.content}")

    # --- INVENTORY TABLE ---
    st.subheader("Detailed Device Audit")
    st.dataframe(df[['endpoint_name', 'os_name', 'ip_address', 'last_seen']])

else:
    st.info("No devices found for this organization in Action1.")
