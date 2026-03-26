import streamlit as st
import requests
from groq import Groq

# --- DASHBOARD CONFIG ---
st.set_page_config(page_title="SecureH Client Portal", layout="wide")
st.title("SecureH Managed IT Dashboard")

# --- SECURE KEYS ---
ACTION1_KEY = st.secrets["ACTION1_TOKEN"]
GROQ_KEY = st.secrets["GROQ_TOKEN"]
client = Groq(api_key=GROQ_KEY)

# --- CUSTOMER SELECTION ---
customer = st.sidebar.selectbox(
    "Select Organization:",
    ("All Customers", "Customer A - Law Firm", "Customer B - Medical Clinic", "Customer C - Retail")
)

st.sidebar.write(f"Logged in as: SecureH Admin")
st.sidebar.info("System Status: Monitoring Active")

# --- FETCH DATA FUNCTION ---
def get_action1_data(org_name):
    headers = {"Authorization": f"Bearer {ACTION1_KEY}"}
    if org_name == "Customer A - Law Firm":
        return {"critical": 8, "high": 12, "uptodate": "85%"}
    elif org_name == "Customer B - Medical Clinic":
        return {"critical": 2, "high": 5, "uptodate": "98%"}
    else:
        return {"critical": 15, "high": 30, "uptodate": "70%"}

data = get_action1_data(customer)

# --- VISUALS ---
st.subheader(f"Security Overview for: {customer}")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Critical Vulnerabilities", data["critical"], delta="-2 from yesterday", delta_color="inverse")
with col2:
    st.metric("High Risks", data["high"])
with col3:
    st.metric("Patch Compliance", data["uptodate"])

# --- AI ANALYSIS (GROQ) ---
st.divider()
st.subheader("AI Executive Security Analysis")

ai_prompt = f"""
You are the Lead Security Engineer for SecureH. 
Write a 3-sentence summary for the owner of {customer}. 
They have {data['critical']} critical vulnerabilities. 
Explain the risk simply and tell them SecureH is fixing it tonight.
"""

if st.button('Generate AI Report'):
    with st.spinner('AI is analyzing network data...'):
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": ai_prompt}],
            model="llama3-8b-8192",
        )
        st.success(completion.choices[0].message.content)

st.caption("Data provided by Action1 RMM. Analysis by Groq Llama3 AI.")



import streamlit as st
import requests

# 1. Fetch the list of real Organizations from Action1
@st.cache_data(ttl=600) # Cache for 10 mins so you don't hit API limits
def get_real_organizations():
    headers = {"Authorization": f"Bearer {st.secrets['ACTION1_TOKEN']}"}
    url = "https://app.action1.com/api/3.0/organizations"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        # Returns a list of dicts with 'name' and 'id'
        return response.json().get("items", [])
    return []

# 2. Fetch real vulnerability/patch data for a specific Org
def get_action1_live_metrics(org_id):
    headers = {"Authorization": f"Bearer {st.secrets['ACTION1_TOKEN']}"}
    # Endpoint for managed endpoints status
    url = f"https://app.action1.com/api/3.0/endpoints/managed/{org_id}"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json().get("items", [])
        # Example logic: Count critical updates across all endpoints in this org
        critical_count = sum(1 for e in data if e.get("missing_critical_updates", 0) > 0)
        high_count = sum(1 for e in data if e.get("missing_important_updates", 0) > 0)
        
        # Calculate a basic compliance %
        total = len(data)
        clean = sum(1 for e in data if e.get("missing_updates", 0) == 0)
        compliance = f"{(clean/total)*100:.0f}%" if total > 0 else "100%"
        
        return {"critical": critical_count, "high": high_count, "uptodate": compliance}
    return {"critical": 0, "high": 0, "uptodate": "N/A"}

# --- Updated Sidebar ---
orgs = get_real_organizations()
org_names = [o['name'] for o in orgs]
selected_org_name = st.sidebar.selectbox("Select Organization:", org_names)

# Get the ID for the selected name
selected_org_id = next(o['id'] for o in orgs if o['name'] == selected_org_name)

# Pull the real data
data = get_action1_live_metrics(selected_org_id)
