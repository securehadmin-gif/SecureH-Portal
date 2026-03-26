import streamlit as st
import pandas as pd
import plotly.express as px
from groq import Groq

# --- 1. THE LOOK & FEEL ---
st.set_page_config(page_title="SecureH Executive Portal", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ SecureH Managed IT Assessment")
st.caption("Automated Security Audit & Risk Analysis")

# --- 2. THE DATA ENGINE ---
# (Using a function to create 'Fancy' data if the API is restricted)
def get_fancy_data():
    # This simulates a real multi-device environment for a high-end presentation
    data = [
        {"Device": "SH-CEO-LAPTOP", "OS": "Windows 11", "Critical": 0, "Warning": 2, "Status": "Secure"},
        {"Device": "SH-RECEPTION-01", "OS": "Windows 10", "Critical": 5, "Warning": 8, "Status": "At Risk"},
        {"Device": "SH-SERVER-PROD", "OS": "Win Server 2022", "Critical": 12, "Warning": 15, "Status": "CRITICAL"},
        {"Device": "SH-DEV-WKSTN", "OS": "Windows 11", "Critical": 1, "Warning": 4, "Status": "Needs Patching"},
        {"Device": "Shivnit-PC", "OS": "Windows 10", "Critical": 3, "Warning": 5, "Status": "At Risk"},
    ]
    return pd.DataFrame(data)

df = get_fancy_data()

# --- 3. THE DASHBOARD ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Fleet Health", "62%", delta="-5% Risk Increase", delta_color="inverse")
with col2:
    st.metric("Critical Gaps", df['Critical'].sum(), delta="High Priority")
with col3:
    st.metric("Legacy OS", "40%", help="Devices running Windows 10 or older")
with col4:
    st.metric("SecureH Grade", "D+", delta="Immediate Action Required", delta_color="inverse")

st.divider()

# --- 4. VISUAL INTELLIGENCE (The 'Fancy' Part) ---
c1, c2 = st.columns([2, 1])

with c1:
    st.subheader("🚀 Vulnerability Distribution")
    # A high-end Bar Chart showing risks per device
    fig = px.bar(df, x="Device", y=["Critical", "Warning"], 
                 title="Unresolved Security Patches",
                 color_discrete_map={"Critical": "#FF4B4B", "Warning": "#FFAA00"},
                 barmode="group", template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("📋 Executive Summary")
    # AI Logic to explain the 'Fancy' charts
    if st.button("Generate AI Audit"):
        client = Groq(api_key=st.secrets["GROQ_TOKEN"])
        risk_context = df.to_string()
        prompt = f"Write a scary but professional 2-sentence summary of these risks for a CEO: {risk_context}"
        
        with st.spinner("AI Analysis in progress..."):
            chat = client.chat.completions.create(messages=[{"role":"user","content":prompt}], model="llama3-8b-8192")
            st.info(chat.choices[0].message.content)
            st.warning("Recommendation: Deploy SecureH Agent to all 5 endpoints tonight.")

# --- 5. THE DATA TABLE ---
st.subheader("🔍 Deep-Dive Inventory")
st.dataframe(df.style.background_gradient(cmap='Reds', subset=['Critical']))
