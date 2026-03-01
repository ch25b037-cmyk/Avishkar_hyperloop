import streamlit as st
import pandas as pd
import random
import os
from datetime import datetime
import time
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
from helper_function import check_login, generate_pod_data, get_random_jokes, load_css, get_weather_data, get_energy_tips, refresh_and_catch_up, update_simulation


#----------------------
#    MQTT SETUP
#---------------------
port = 1883
broker = "test.mosquitto.org"
if 'mqtt_client' not in st.session_state:

    def on_connect(client, userdata, flags, rc, properties):
        if rc == 0:
            print("Connected to broker")

        else:
            print("Connection failed with code", rc)
    client = mqtt.Client(CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.connect(broker, port)
    client.loop_start()        
    st.session_state.mqtt_client = client

# ------------------------------
# 0. INITIAL SETUP
# ------------------------------
st.set_page_config(
    page_title="Avishkar Hyperloop Control Center 2035",
    layout="wide",
    initial_sidebar_state="expanded"
)

load_css()
st.markdown("""
    <style>
    .stMetric {
        padding: 15px;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)


# ------------------------------
#   AUTHENTICATION SYSTEM
# ------------------------------
USERS = {
    "viewer": {"password": "123", "role": "Viewer"},
    "controller": {"password": "admin", "role": "Controller"},
}

check_login()

st.sidebar.success(f"Logged in as: **{st.session_state.role}**")
#----------------------------------
# --- LOG MANAGEMENT SECTION ---
#----------------------------------
st.sidebar.subheader("Data Log")
st.session_state.logging_enabled = st.sidebar.checkbox("Save data to CSV file", value=True)


file = "hyperloop_logs.csv"
if st.session_state.role == 'Controller':
   clear_clicked = st.sidebar.button("Clear Log",type="secondary",key="clear_log")

   if clear_clicked:
      if os.path.exists(file):
        os.remove(file)
      st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("Log Information")

if os.path.exists(file):
    size = os.path.getsize(file) / 1024
    st.sidebar.caption(f"Log Size: {size:.2f} KB")

    with open(file, "rb") as f:
        st.sidebar.download_button(
            label="Download",
            data=f,
            file_name="hyperloop_logs.csv",
        )

    if st.session_state.role == "Controller":
        st.sidebar.write("### Last 6 Entries")
        try:
            preview_df = pd.read_csv(file).tail(6)
            st.sidebar.dataframe(preview_df, hide_index=True)
        except:
            st.sidebar.info("Log file is empty.")
else:
    st.sidebar.caption("No data stored.")


if "speed_limit" not in st.session_state:
    st.session_state.speed_limit = 1000
if "pod_data" not in st.session_state:
    st.session_state.pod_data = generate_pod_data()
if 'route_city' not in st.session_state: 
    st.session_state.route_city = "Chennai"

df = st.session_state.pod_data.copy()
current_limit = st.session_state.speed_limit
df.loc[df["Speed (km/h)"] > current_limit, "Speed (km/h)"] = current_limit

# ------------------------------
#      DASHBOARD UI
# ------------------------------

st.title("Avishkar Hyperloop Control Dashboard")
st.markdown(f"**System Time:** {datetime.now().strftime('%H:%M:%S')} | **Mode:** {st.session_state.role}")

m1, m2, m3, m4, m5 = st.columns(5)
active_pods = len(df[df["Status"] == "Operational"])
avg_speed = int(df[df["Status"] == "Operational"]["Speed (km/h)"].mean())
no_pods_maintenance = len(df[df["Status"] == "Maintenance"])
no_pods_charging = len(df[df["Status"] == "Docked"])
load = 50 + random.choice([-1, 0,1,2])
m1.metric("Active Pods", active_pods, delta=f"{active_pods - 6} offline", delta_color="normal")
m2.metric("Avg pod Speed", f"{avg_speed} km/h",delta ='High' if avg_speed >1000 else 'normal', delta_color='inverse' if avg_speed >1000 else 'normal')
m3.metric("System Load", f"{load}%",delta="High" if load > 80 else "Normal", delta_color="inverse" if load > 80 else "normal")
m4.metric("Under Maintenance", no_pods_maintenance, delta="High" if no_pods_maintenance > 1 else "Low", delta_color="inverse" if no_pods_maintenance > 1 else "normal")
m5.metric("Charging", no_pods_charging,delta = f'{no_pods_charging}🔋' if no_pods_charging > 0 else 'normal', delta_color='blue')


m6,m7,m8,m9,m10 = st.columns(5)

st.divider()
#------------------------------
#    MAIN CONTROLS & DATA
#------------------------------
col_main, col_sidebar = st.columns([3, 1])

if "last_tick_time" not in st.session_state:
    st.session_state.last_tick_time = datetime.now()

with col_sidebar:
    st.subheader("Operations")
    if st.button("Refresh / Simulate Live Data", type="secondary"):
        refresh_and_catch_up()
        st.rerun()


    st.write("---")
    st.write("**Global Speed Governor**")
    if st.session_state.role == "Controller":
        new_speed = st.slider("Max Limit (km/h)", 500, 1200, st.session_state.speed_limit)
        if new_speed != st.session_state.speed_limit:
            st.session_state.speed_limit = new_speed
            st.rerun()
    else:
        st.progress(st.session_state.speed_limit / 1200)
        st.caption(f"Locked at {st.session_state.speed_limit} km/h (Read-Only)")

    st.write("---")
    filter_status = st.selectbox("Filter Status", ["All", "Operational", "Docked", "Maintenance"])
    
with col_main:
    st.subheader("Live Pod Tracker")
    display_df = df if filter_status == "All" else df[df["Status"] == filter_status]
    st.dataframe(
        display_df,
        column_config={
            "Pod ID": st.column_config.TextColumn("Pod ID", help="Unique Identifier"),
            "Wear Level": st.column_config.ProgressColumn(
                "Wear Level",
                format="%d%%",
                min_value=0,
                max_value=100,
                color="grey" if display_df["Wear Level"].max() > 85 else "green"
            ),
            "Battery": st.column_config.ProgressColumn(
                "Battery Level", 
                format="%d%%", 
                min_value=0, 
                max_value=100,
                color="red" if display_df["Battery"].min() < 20 else "blue"
            ),
            "Speed (km/h)": st.column_config.NumberColumn(
                "Velocity",
                format="%d km/h"
            ),
            "Status": st.column_config.TextColumn("System Status"),
        },
        hide_index=True
    )

    st.subheader("Weather Conditions")
    w_col1, w_col2 = st.columns([1, 2])


#--------------------
#    Weather API
#--------------------
    
st.divider()
route_city = w_col1.text_input("**Enter City**",value=st.session_state.route_city)
condition = get_weather_data(st.session_state.route_city)
st.session_state.route_city = route_city
if st.session_state.route_city:
 if condition["success"]:
  weather = condition["weather"]
  temp = condition["temperature"]
  m6.metric(f"Weather in {route_city}", weather )
  m7.metric("Temperature", f"{temp}°C")
  m8.metric("Humidity", f"{condition['humidity']}%")
  m9.metric("Wind Speed", f"{int(condition['wind_speed']*18/5)} km/h")
  m10.metric("Pressure", f"{condition['pressure']} kPa")
    
  if condition["weather"] in ["Rain", "Thunderstorm", "Snow"]:
        rec_speed = 700
        w_col2.error(f"CRITICAL WEATHER: Reduce max speed to {rec_speed} km/h immediately.")

  elif condition["weather"] == "Clouds":
        rec_speed = 900
        w_col2.warning(f"ADVISORY: Suggested speed limit {rec_speed} km/h.")
       
  else:
        rec_speed = 1200
        w_col2.success(f"CONDITIONS OPTIMAL: Safe for max velocity.")
 else:
    w_col2.error("Failed to fetch weather data. Check city name or API key.")  
 

else:
    w_col2.info("Enter a city to get current weather conditions and recommendations.")
      
#-----------------------------
#  JSON Placeholder API
# -----------------------------    


st.subheader("Energy Efficiency Tips")
w1, w2 = st.columns([1,2])

if 'current_energy_tip' not in st.session_state:
    st.session_state.current_energy_tip = None

if w1.button("Get Energy Efficiency Tips", type="secondary"):
    st.session_state.current_energy_tip = get_energy_tips()

if st.session_state.current_energy_tip:
    w2.success(st.session_state.current_energy_tip)
st.divider()   

#-----------------------------
# Random Jokes API
# -----------------------------   

st.subheader("Random Jokes")
v1, v2 = st.columns([1,2])

if 'current_joke' not in st.session_state:
    st.session_state.current_joke = None

if v1.button("Get Joke", type="secondary"):
    st.session_state.current_joke = get_random_jokes()

if st.session_state.current_joke:
    v2.success(st.session_state.current_joke)
    
#-----------------------------
#    LOGOUT & AUTO MODE
#-----------------------------

if st.sidebar.button("Logout",type='secondary'):
    st.session_state.logged_in = False
    st.rerun()

with col_sidebar:
 if "auto_mode" not in st.session_state:
    st.session_state.auto_mode = False

 st.session_state.auto_mode = st.toggle(
    "Enable Auto Mode",
    value=st.session_state.auto_mode
)

 if st.session_state.auto_mode:
    update_simulation()
    time.sleep(1)
    st.rerun()

