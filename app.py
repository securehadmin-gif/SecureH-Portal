import streamlit as st

import requests

import pandas as pd

import plotly.express as px



# --- CONFIGURATION ---

CLIENT_ID = "api-key-42129c27-66f0-4af0-ab7e-eec58245e89aa9ee04d8-c021-7000-9100-463e86ad7d4f@action1.com"

CLIENT_SECRET = "41f772f5a1e40b609a5f4baf14a8b6b6"

BASE_URL = "https://app.au.action1.com/api/3.0"



# --- API FUNCTIONS ---

def get_access_token():

    auth_url = f"{BASE_URL}/oauth2/token"

    payload = {

        'client_id': CLIENT_ID,

        'client_secret': CLIENT_SECRET,

        'grant_type': 'client_credentials' 

    }

    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    response = requests.post(auth_url, data=payload, headers=headers)

    return response.json().get('access_token')



def get_data(endpoint, token):

    headers = {'Authorization': f'Bearer {token}'}

    response = requests.get(f"{BASE_URL}/{endpoint}", headers=headers)

    return response.json().get('items', [])



# --- STREAMLIT UI ---

st.set_page_config(page_title="SecureH | IT Audit Portal", layout="wide")

st.title("??? Automated IT Audit Report")



# 1. Authenticate

token = get_access_token()



if token:

    # 2. Get Organizations for the Dropdown

    orgs = get_data("organizations", token)

    org_names = {o['name']: o['id'] for o in orgs}

    

    selected_org_name = st.sidebar.selectbox("Select Customer / Organization", list(org_names.keys()))

    org_id = org_names[selected_org_name]



    st.header(f"Report for: {selected_org_name}")

    

    # 3. Fetch Endpoint Data for this Org

    # Using fields=* gets us the 'missing_critical_updates' data

    endpoints = get_data(f"endpoints/managed/{org_id}?fields=*", token)

    df = pd.DataFrame(endpoints)



    if not df.empty:

        # --- FANCY DASHBOARD ---

        col1, col2, col3 = st.columns(3)

        

        with col1:

            total_devices = len(df)

            st.metric("Total Managed Devices", total_devices)

            

        with col2:

            # Check for a column like 'missing_critical_updates'

            crit_val = df['missing_critical_updates'].sum() if 'missing_critical_updates' in df else 0

            st.metric("Critical Patches Missing", crit_val, delta_color="inverse")



        # --- VISUALS WITH SAFETY CHECKS ---

st.divider()



if not df.empty:

    # Print columns to the console/logs so you can see the REAL names

    # st.write(df.columns.tolist()) 



    c1, c2 = st.columns(2)

    

    with c1:

        st.subheader("OS Distribution")

        # Action1 3.0 often uses 'os_family' or 'os_version' 

        # Let's check for 'os_name' or fallback to a column that definitely exists

        target_col = None

        for col in ['os_name', 'os_family', 'operating_system']:

            if col in df.columns:

                target_col = col

                break

        

        if target_col:

            fig_os = px.pie(df, names=target_col, hole=0.4, 

                            color_discrete_sequence=px.colors.qualitative.Pastel)

            st.plotly_chart(fig_os)

        else:

            st.info("OS data not found in API response.")

            

    with c2:

        st.subheader("Endpoint Health Status")

        # Search for a status column

        status_col = next((c for c in ['connection_status', 'status', 'state'] if c in df.columns), None)

        

        if status_col:

            fig_stat = px.bar(df, x=status_col, color=status_col)

            st.plotly_chart(fig_stat)

        else:

            st.info("Status data not found.")

else:

    st.warning("No data available for the selected organization.")


        # --- DATA TABLE ---

        st.subheader("Detailed Audit List")

        st.dataframe(df[['name', 'os_name', 'ip_address', 'last_seen']])

        

    else:

        st.warning("No devices found in this organization.")

else:

    st.error("Failed to authenticate. Check your Client ID and Secret.")
