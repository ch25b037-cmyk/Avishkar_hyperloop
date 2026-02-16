import streamlit as st
import pandas as pd
import time

from helper_function import refresh_and_catch_up

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("⚠ Please login first.")
    st.stop()
c1, c2 = st.columns(2)
df = st.session_state.pod_data
with c1:
    st.subheader("Pod Comparison")
    pod_options = df["Pod ID"].tolist()
    p1_name = st.selectbox("Pod A", pod_options, index=0)
    p2_name = st.selectbox("Pod B", pod_options, index=1)
    
    row1 = df[df["Pod ID"] == p1_name].iloc[0]
    row2 = df[df["Pod ID"] == p2_name].iloc[0]
    
    comp_data = pd.DataFrame({
        "Metric": ["Battery", "Velocity", "Wear Level"],
        p1_name: [row1["Battery"], row1["Speed (km/h)"], row1["Wear Level"]],
        p2_name: [row2["Battery"], row2["Speed (km/h)"], row2["Wear Level"]]
    }).set_index("Metric")
    
    st.table(comp_data)

with c2:
    st.markdown("##### Maintenance Forecast")
    any_alerts = False
    maintenance = df[df["Status"] == "Maintenance"]
    docked = df[df["Status"] == "Docked"]
    if not maintenance.empty :
        for index, row in maintenance.iterrows():
            any_alerts = True
            if row["Wear Level"] > 85:
                st.error(f"{row['Pod ID']} requires service (Wear: {row['Wear Level']}%)")
            else:
                st.info(f"{row['Pod ID']} is under service (Wear: {row['Wear Level']}%)")
           
                   
    if not docked.empty:    
        for index, row in docked.iterrows():
            any_alerts = True
            battery = max(0, min(100, row["Battery"]))  # clamp safety

            if battery < 20:
                st.error(f"{row['Pod ID']} critically low battery (Battery: {battery}%)")

            elif battery >= 100:
                st.success(f"{row['Pod ID']} fully charged and ready (Battery: 100%)")

            else:
              st.info(f"{row['Pod ID']} is charging (Battery: {battery}%)")

    if not any_alerts:       
        st.success("All systems nominal.")
        
if "auto_mode" not in st.session_state:
    st.session_state.auto_mode = False

st.session_state.auto_mode = st.sidebar.toggle(
    "Enable Auto Mode",
    value=st.session_state.auto_mode
)

if st.session_state.auto_mode:
    refresh_and_catch_up()
    time.sleep(1)
    st.rerun()
                