import streamlit as st
import requests
import pandas as pd
from groq import Groq
import plotly.express as px # For fancy charts

# --- SETUP ---
st.set_page_config(page_title="SecureH AI Assessor", layout="wide")
st.title("🚀 SecureH Automated IT Assessment")

# Secrets
CLIENT_ID = st.secrets["ACTION1_CLIENT_ID"]
CLIENT_SECRET = st.secrets["ACTION1_CLIENT_SECRET"]
client = Groq(api_key=st.secrets["GROQ_TOKEN"])

# --- AUTOMATION ENGINE ---
def get_token():
    url = "https://app.au.action1.com/api/3.0/oauth2/token"
    res = requests.post(url, data={"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET}, 
                        headers={"Content-Type": "application/x-www-form-urlencoded"})
    return res.json().get("access_token")

@st.cache_data(ttl=600)
def fetch_all_assessment_data(_token):
    # Using the broader 'endpoints' URL to ensure we catch 'Shivnit'
    url = "https://app.au.action1.com/api/3.0/endpoints"
    headers = {"Authorization": f"Bearer {_token}"}
    res = requests.get(url, headers=headers)
    return res.json().get("items", [])

# --- RUN LOGIC ---
token = get_token()
if token:
    data = fetch_all_assessment_data(token)
    
    if data:
        df = pd.DataFrame(data)
        
        # 1. TOP LEVEL METRICS
        total_pcs = len(df)
        # Ensure column names match Action1 API (usually 'missing_critical_updates')
        crit_col = 'missing_critical_updates' if 'missing_critical_updates' in df else 'missing_updates'
        total_crit = df[crit_col].sum()
        
        st.subheader("📊 Network Health Overview")
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Managed Assets", total_pcs)
        m2.metric("Critical Security Gaps", total_crit, delta="Immediate Risk", delta_color="inverse")
        
        # Calculate a Fancy 'SecureH Grade'
        grade = "A" if total_crit == 0 else "B" if total_crit < 5 else "D"
        m3.metric("Security Grade", grade)

        # 2. FANCY VISUALS
        col_left, col_right = st.columns(2)
        with col_left:
            st.write("### OS Distribution")
            fig = px.pie(df, names='os_name', hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig, use_container_width=True)
            
        with col_right:
            st.write("### Vulnerability Heatmap")
            # Creating a fake 'Risk' column based on patches for the chart
            df['Risk_Level'] = df[crit_col].apply(lambda x: 'High' if x > 5 else 'Medium' if x > 0 else 'Low')
            fig2 = px.bar(df, x='endpoint_name', y=crit_col, color='Risk_Level')
            st.plotly_chart(fig2, use_container_width=True)

        # 3. AI EXECUTIVE SUMMARY (The 'Closer')
        st.divider()
        st.subheader("🤖 AI Consultant Audit")
        if st.button("Generate Professional Assessment"):
            summary_stats = df[['endpoint_name', 'os_name', crit_col]].to_string()
            prompt = f"""You are a Cybersecurity Expert at SecureH. Write a professional 3-paragraph IT assessment for a business owner based on this data: {summary_stats}. 
            Identify the biggest risk and explain why they need SecureH Managed Services immediately."""
            
            with st.spinner("Analyzing vulnerabilities..."):
                response = client.chat.completions.create(messages=[{"role":"user","content":prompt}], model="llama3-8b-8192")
                st.markdown(f"### Assessment Report\n{response.choices[0].message.content}")

    else:
        st.error("No data returned. Check API Key Scopes (Permissions) in Action1.")
# --- AUTOMATED RISK SCORING ---
def calculate_risk_score(df):
    # Logic: Start at 100, subtract points for risks
    score = 100
    
    # -10 points for every Critical Vulnerability
    crit_count = df['missing_critical_updates'].sum() if 'missing_critical_updates' in df else 0
    score -= (crit_count * 10)
    
    # -20 points if any device is on Windows 10 (since it's EOL soon)
    if any(df['os_name'].str.contains("Windows 10", na=False)):
        score -= 20
        
    return max(0, score) # Score can't be below 0

# --- DISPLAY IN APP ---
current_score = calculate_risk_score(df)
st.gauge(current_score, min_value=0, max_value=100, label="SecureH Trust Score")
