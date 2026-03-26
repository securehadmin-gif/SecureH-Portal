import streamlit as stimport requestsfrom groq import Groq
# --- DASHBOARD CONFIG ---st.set_page_config(page_title="SecureH Client Portal", layout="wide")st.title(" SecureH Managed IT Dashboard")
# --- SECURE KEYS (Hiding your passwords) ---ACTION1_KEY = st.secrets["ACTION1_TOKEN"]GROQ_KEY = st.secrets["GROQ_TOKEN"]client = Groq(api_key=GROQ_KEY)
# --- CUSTOMER SELECTION ---# Add your real customer names herecustomer = st.sidebar.selectbox(    "Select Organization:",    ("All Customers", "Customer A - Law Firm", "Customer B - Medical Clinic", "Customer C - Retail"))
st.sidebar.write(f"Logged in as: SecureH Admin")st.sidebar.info("System Status: Monitoring Active")
# --- FETCH DATA FUNCTION ---def get_action1_data(org_name):    headers = {"Authorization": f"Bearer {ACTION1_KEY}"}    # In reality, you'd filter the Action1 API by organization ID    # For this demo, we use data based on your selection    if org_name == "Customer A - Law Firm":        return {"critical": 8, "high": 12, "uptodate": "85%"}    elif org_name == "Customer B - Medical Clinic":        return {"critical": 2, "high": 5, "uptodate": "98%"}    else:        return {"critical": 15, "high": 30, "uptodate": "70%"}
data = get_action1_data(customer)
# --- FANCY VISUALS ---st.subheader(f"Security Overview for: {customer}")col1, col2, col3 = st.columns(3)
with col1:    st.metric("Critical Vulnerabilities", data["critical"], delta="-2 from yesterday", delta_color="inverse")with col2:    st.metric("High Risks", data["high"])with col3:    st.metric("Patch Compliance", data["uptodate"])
# --- AI ANALYSIS (GROQ) ---st.divider()st.subheader(" AI Executive Security Analysis")
# This is the prompt that tells the AI how to actai_prompt = f"""You are the Lead Security Engineer for SecureH. Write a 3-sentence summary for the owner of {customer}. They have {data['critical']} critical vulnerabilities. Explain the risk simply and tell them SecureH is fixing it tonight."""
if st.button('Generate AI Report'):    with st.spinner('AI is analyzing network data...'):        completion = client.chat.completions.create(            messages=[{"role": "user", "content": ai_prompt}],            model="llama3-8b-8192",        )        st.success(completion.choices[0].message.content)
st.caption("Data provided by Action1 RMM. Analysis by Groq Llama3 AI.")
