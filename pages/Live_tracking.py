import streamlit as st
import pandas as pd
import numpy as np
import time
from helper_function import get_weather_data, update_simulation
st.set_page_config(layout="wide")
route_city = st.session_state.get("route_city")
df = st.session_state.get("pod_data")

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("⚠ Please login first.")
    st.stop()

st.title("Hyperloop Live Tracking")

# -------------------------
# SETTINGS
# -------------------------
chennai = get_weather_data("chennai")
NUM_PODS = 6
if route_city:
   details = get_weather_data(route_city)
   longitudes = details['longitude'] + np.random.uniform(-0.01, 0.01, NUM_PODS)
   latitudes = details['latitude'] + np.random.uniform(-0.01, 0.01, NUM_PODS)
else:
   longitudes = chennai['longitude'] + np.random.uniform(-0.01, 0.01, NUM_PODS)
   latitudes = chennai['latitude'] + np.random.uniform(-0.01, 0.01, NUM_PODS)   


col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Live Map")
    placeholder = st.empty()


with col2:
    st.subheader("Live Telemetry")
    table_placeholder = st.empty()
while st.session_state.logged_in:

    speeds = df["Speed (km/h)"].tolist()
    status = []
    for speed in speeds:
        if speed != 0:
            status.append("Operational")
        else:
            status.append("Stopped")


    operational_pods = np.array(status) == "Operational"
    
    latitudes[operational_pods] += np.random.uniform(-0.001, 0.001)
    longitudes[operational_pods] += np.random.uniform(-0.001, 0.001)

    pod_data = pd.DataFrame({
        "latitude": latitudes,
        "longitude": longitudes
    })

    update_simulation()
    if "distance" not in st.session_state:
         st.session_state.distance = [0 for _ in range(NUM_PODS)]
    for i in range(NUM_PODS):
         st.session_state.distance[i] += float(speeds[i]/3600)*0.1
     
    status_df = pd.DataFrame({
        "Pod ID": [f"AV-{i+1}" for i in range(NUM_PODS)],
        "Speed (km/h)": [min(df.iloc[i]["Speed (km/h)"], st.session_state.speed_limit) for i in range(NUM_PODS)],
        "Status": status,
        'distance (km)': [st.session_state.distance[i] for i in range(NUM_PODS)]
    })
    
    placeholder.map(pod_data, zoom=12, use_container_width=True)
    
    table_placeholder.dataframe(
        status_df, 
        use_container_width=True,
        hide_index=True
    )    

    time.sleep(0.1)
