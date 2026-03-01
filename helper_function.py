import streamlit as st
import random
import pandas as pd
import os

from datetime import datetime
import json
import requests

USERS = {
    "viewer": {"password": "123", "role": "Viewer"},
    "controller": {"password": "admin", "role": "Controller"},
}

def load_css():
    with open("css/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
def check_login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.role = None

    if not st.session_state.logged_in:
        st.sidebar.title("Login")
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        
        if st.sidebar.button("Login",type='secondary'):
            if username in USERS and USERS[username]["password"] == password:
                st.session_state.logged_in = True
                st.session_state.role = USERS[username]["role"]
                st.rerun()
            else:
                st.sidebar.error("Access Denied")
        st.markdown("""
        <h1 style='text-align: center; font-size: 80px; color: green'>
            AVISHKAR
        </h1>
        <h3 style='text-align: center; color: #aaaaaa; letter-spacing: 5px; margin-top: 0;'>
            HYPERLOOP CONTROL GRID
        </h3>""", unsafe_allow_html=True)
        k1, k2, k3 = st.columns([1, 1.5, 1])
        with k2:
            st.image(
            "https://www.avishkarhyperloop.com/_next/image?url=%2F_next%2Fstatic%2Fmedia%2Fimage.2a717b25.png&w=96&q=75", width=400)
            st.stop()

def generate_pod_data():
    pods = []
    for i in range(1, 7):
        pods.append({
            "Pod ID": f"AV-{i}",
            "Speed (km/h)": random.randint(400, 1100),
            "Pressure (kPa)": 100,
            "Temperature (°C)": random.randint(15, 30),
            "Lev. Gap (mm)": random.randint(9, 18),
            "Battery": random.randint(15, 100),
            "Wear Level": random.randint(5, 95),
            "Status": "Operational",
        })
    return pd.DataFrame(pods)     

def log_data(data):
    filename = "hyperloop_logs.csv"
    timestamp = datetime.now()
    log = data.copy()
    log = log.set_index("Pod ID")
    log["timestamp"] = timestamp.strftime("%H:%M:%S")
    header = not os.path.exists(filename)
    log.to_csv(filename, index=True, header=header, mode='a')

def update_simulation():
    df = st.session_state.pod_data
    
    for index, row in df.iterrows():
        current_status = row["Status"]
        current_battery = row["Battery"]
        current_wear = row["Wear Level"]
        current_pressure = row["Pressure (kPa)"]
        current_temperature = row["Temperature (°C)"]
        
        # -------------------------------
        # LOGIC 1: MAINTENANCE HANDLING
        # -------------------------------
        if current_status == "Maintenance":
            df.at[index, "Speed (km/h)"] = 0  # STOP!
            df.at[index, "Wear Level"] = max(0, current_wear - 10)     
            df.at[index,"Lev. Gap (mm)"] = 0
            if df.at[index, "Wear Level"] <= 0:
                df.at[index, "Status"] = "Docked"

        # -------------------------------
        # LOGIC 2: DOCKED / CHARGING
        # -------------------------------
        elif current_status == "Docked":
            df.at[index, "Speed (km/h)"] = 0  # STOP!
            new_battery = min(100, current_battery + 5) 
            df.at[index,"Lev. Gap (mm)"] = 0
            df.at[index, "Battery"] = new_battery
            if new_battery == 100:
                df.at[index, "Status"] = "Operational"
        
        # -------------------------------
        # LOGIC 3: OPERATIONAL
        # -------------------------------
        else: # Status is Operational
            df.at[index, "Pressure (kPa)"] = max(90, min(110, current_pressure + random.randint(-2, 2)))
            df.at[index, "Temperature (°C)"] = max(10, min(35, current_temperature + random.randint(-1, 1)))
            df.at[index, "Battery"] = max(0, current_battery - random.randint(0, 2))
            df.at[index, "Wear Level"] = min(100, current_wear + random.randint(0, 2))
            df.at[index,"Lev. Gap (mm)"] = random.randint(9, 18)
            current_speed = st.session_state.speed_limit
            new_speed = max(0, min(1200, current_speed + random.randint(-50, 50)))
            df.at[index, "Speed (km/h)"] = new_speed
            if df.at[index, "Battery"] < 20:
                df.at[index, "Status"] = "Docked" # Force Docking
            elif df.at[index, "Wear Level"] > 85:
                df.at[index, "Status"] = "Maintenance" # Force Maintenance
        payload = {
            "id": row["Pod ID"],
            "speed": int(row["Speed (km/h)"]),
            "pressure": int(row["Pressure (kPa)"]),
            "temperature": int(row["Temperature (°C)"]),
            "lev_gap": int(row["Lev. Gap (mm)"]),
            "battery": int(row["Battery"]),
            "wear": int(row["Wear Level"]),
            "status": row["Status"]
        }
        
        topic = f"avishkar/hyperloop/{row['Pod ID']}"
        st.session_state.mqtt_client.publish(topic, json.dumps(payload), qos=1)
        st.session_state.pod_data = df
    
    if st.session_state.get("logging_enabled", False):
        log_data(df)        
@st.cache_data(ttl=1800)  
def get_weather_data(city):
    try:
        api_key = st.secrets["WEATHER_API_KEY"]
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        response = requests.get(url)
        data = response.json()
        
        return {
                "weather": data["weather"][0]["main"],
                "temperature": data["main"]["temp"],
                "pressure": data["main"]["pressure"],
                "tempature": data["main"]["temp"],
                "humidity": data["main"]["humidity"],
                'wind_speed': data["wind"]["speed"],
                "success": True,
                "latitude": data["coord"]["lat"],
                "longitude": data["coord"]["lon"]}
        
    except Exception as e:
        return {"success": False}
    
def get_energy_tips():
    i = random.randint(1, 50)
    url = f'https://jsonplaceholder.typicode.com/posts/{i}'
    response = requests.get(url)
    data = response.json()
    return data['body']     

def get_random_jokes():
    url = "https://official-joke-api.appspot.com/random_joke"
    response = requests.get(url)
    data = response.json()
    return f"{data['setup']} - {data['punchline']}"

def refresh_and_catch_up():
    now = datetime.now()
    time_diff = (now - st.session_state.last_tick_time).total_seconds()
    ticks_to_run = int(time_diff // 5)
    if ticks_to_run > 0:
        for _ in range(ticks_to_run):
            update_simulation()
            st.session_state.last_tick_time = now   