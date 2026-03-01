# Avishkar_hyperloop
AVISHKAR Hyperloop Control Grid

A real-time simulation dashboard for managing and monitoring Hyperloop pods using Streamlit, live telemetry, MQTT messaging, weather integration, and interactive tracking maps.

## Project Overview

AVISHKAR Hyperloop Control Grid is a real-time control center simulation that:

1. Simulates 6 Hyperloop pods
2. Tracks live telemetry (speed, battery, pressure, wear, etc.)
3. Displays a live interactive map
4. Publishes pod data via MQTT
5. Integrates live weather data
6. Logs telemetry into CSV
7. Implements role-based authentication
8. Applies custom UI styling

## System Architecture
User Login → Dashboard → Simulation Engine → MQTT Publishing → Weather API → Live Map → CSV Logging


The system consists of:

1. Dashboard.py                      -	This file contains the main dashboard including metrics, dataframe, apis, comparison pods, maintenance forecast
2. helper_function.py                -	To run everything in the Dashboard.py, the functions are implementeed here 
3. Live_tracking.py                  -	This page contains the map where the pods are travelling. The location is to be given by the user.
4. Pod_Comp_and_Maintenance_Forecast -  This page contains the comparison metrics of any two pods and it displays the condition of the pods(maintenance, docked or operational)
5. style.css                         -	This file contains the styling of the buttons, hovering effects, title colors.


## Authentication System

Use this for login credentials

USERS = {

    "viewer": {"password": "123", "role": "Viewer"},
    "controller": {"password": "admin", "role": "Controller"},
    
}


**Roles:**
1. Viewer	Can only observe telemetry
2. Controller	Can control system settings


**Function: check_login()**

- Creates login sidebar
- Verifies credentials
- Stores login state using st.session_state
- Prevents access if not authenticated
- Displays branding screen if not logged in
- This ensures secure role-based access.

## UI Styling

**Features:**
- Animated buttons
- Styled metrics
- Colored headers

CSS is loaded using load_css() which injects custom styles into Streamlit.

## Dataframe Generation

**Function : generate_pod_data()**

Creates initial dataset of 6 pods with:
1. Speed
2. Pressure
3. Temperature
4. Levitation Gap
5. Battery
6. Wear Level
7. Status

Returns a Pandas DataFrame.


## Core Simulation Logic

**Function: update_simulation()**

It updates each pod based on its state.
There are 3 operational modes:

**Maintenance Mode**
  - Speed will become 0
  - Wear starts decreasing by 10
  - Levitation gap becomes 0
  - When wear reaches 0 status becomes "Docked"
     
**Docked Mode (Charging)**
  - Speed will become 0
  - Battery level starts increasing by 5
  - Levitation gap becomes 0
  - When battery reaches 100% status becomes "Operational"

**Operational Mode**
  - Speed fluctuates around the max speed limit set by us.
  - Battery decreases
  - Wear increases
  - Pressure fluctuates
  - Temperature fluctuates
  - Levitation gap changes

Whenever the Battery level reduces below 20% the status of the pod becomes Docked
Whenever the Wear Level of the pod goes above 85% the status of the pod becomes	Maintenance
This simulates realistic operational behavior.

## MQTT Telemetry Publishing

Inside update_simulation():
st.session_state.mqtt_client.publish(topic, json.dumps(payload), qos=1)

Each pod publishes:

```
{
  "id": "AV-i",(where i is from 1 to 6)
  "speed": 900,
  "pressure": 101,
  "temperature": 26,
  "lev_gap": 12,
  "battery": 80,
  "wear": 20,
  "status": "Operational"
}
```

**Topic avishkar/hyperloop/AV-i**

Since the 'avishkar/hyperloop' part is going to be the same for all the pods we can use the wildcard # 'avishkar/hyperloop/#' to subscribe to all the pods' messages
We can download an app called "MyMQTT" in our mobile and connect the host to "test.mosquitto.org" and port to 1883, and then subscribe to the above mentioned topic to get real time updates from our pods. This enables real-time IoT-style data streaming.

## Weather API Integration

**Function:**
get_weather_data(city)

This uses OpenWeatherMap API

API key stored securely in st.secrets gives us the following:
                                                        
- Temperature
- Condition
- Pressure
- Humidity
- Wind speed
- Latitude & Longitude


1. Based on the weather condition, we get adivised speed limits like for example if the condition is rainy or thunderstorm a message like reduce the speed level comes in our dashboard, the controller then can change the global speed limit so that all the pods travel within tha speed limit
2. Weather coordinates(latitude and longitude) are used to position pods on the map.

## Energy API
In this API, we do not need a key. It is a public API, when we click the get energy efficiency tips button, we get a random Latin text which is present in the API key.

## Funny Jokes API
This is also a public API where we just need to press the Get Joke button to get jokes from the API. The format of the content is type, setup and punchline where type says what topic the joke is about, setup asks a question and the punchline is the answer to that one. I have used only the setup and punchline.

## Live Map Tracking

Located in: Live_tracking.py

**Features:**

- Displays pod positions using st.map
- Uses real city coordinates
- Moves pods randomly if operational
- Stops pods if speed = 0

**Movement Logic:**

If pod is Operational:

lat += random small value                                                                                                                                         
lon += random small value


**Distance calculation:**                                                                                                                                      
distance += (speed / 3600) * 0.1 km                                                                                                                     
This simulates realistic movement per one-tenth of a second.

Live Telemetry Table in Live_tracking.py shows the following :
1. Pod ID
2. Speed
3. Status
4. Distance traveled



## CSV Logging
**Function:  log_data(data)**

- Saves telemetry to hyperloop_logs.csv
- Appends new data
- Adds timestamp
 Logging can be enabled/disabled in the save_data checkbox.


**Function:  refresh_and_catch_up()**

If browser pauses or user switches tabs the simulation "catches up" based on elapsed time. It basically calls the update_simulation function only but if the auto-enable is disabled and the user wants to get the present state of the pod, it calculates the value according to the time elapsed.


## Session State Management
Used extensively to store:

1. Login status
2. Pod data
3. Speed limit
4. MQTT client
5. Distance traveled
6. Logging toggle
7. Last simulation tick time

This allows persistent real-time behavior.


**In Live_tracking.py:**

Every 0.1 second:

- Update simulation
- Move operational pods
- Update distance
- Refresh map
- Refresh telemetry table


How To Run?

1. Install Dependencies
pip install streamlit pandas numpy requests
If using MQTT:
pip install paho-mqtt

2. Add Weather API Key
Create .streamlit/secrets.toml
WEATHER_API_KEY = "your_api_key_here"

3. Run App
streamlit run Dashboard.py

4. Enable Auto-Mode
This toggle is the heart of the dashboard as this calls the update_simulation function which is responsible for all the updates of our pod.


