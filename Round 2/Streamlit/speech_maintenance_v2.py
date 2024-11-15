# --- Imports for Driver Personalization ---
import torch
import soundfile as sf
import streamlit as st
from transformers import SpeechT5Processor, SpeechT5ForTextToSpeech, SpeechT5HifiGan
from datasets import load_dataset
from groq import Groq

# --- Imports for Predictive Maintenance ---
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import LSTM, Dense, Dropout
import time

# Initialize Groq client
api_keyy = "key"
client = Groq(api_key=api_keyy)

# Load models for Text-to-Speech (Driver Personalization)
processor = SpeechT5Processor.from_pretrained("microsoft/speecht5_tts")
model = SpeechT5ForTextToSpeech.from_pretrained("microsoft/speecht5_tts")
vocoder = SpeechT5HifiGan.from_pretrained("microsoft/speecht5_hifigan")
embeddings_dataset = load_dataset("Matthijs/cmu-arctic-xvectors", split="validation")
speaker_embeddings = torch.tensor(embeddings_dataset[7306]["xvector"]).unsqueeze(0)

# Helper Functions
def get_recommendations(driver_data):
    prompt = f"""
    You are an assistant helping personalize vehicle settings for driver experience.
    The driver data is as follows:
    - Name: {driver_data["name"]}
    - Driving Mode Preference: {driver_data["driving_mode"]}
    - Acceleration Pattern: {driver_data["acceleration_pattern"]}
    - Average Speed: {driver_data["average_speed"]} mph
    - AC Usage: {driver_data["ac_usage"]}
    - Recent Routes: {", ".join(driver_data["recent_routes"])}

    Provide a recommendation for improving comfort and battery efficiency.
    """
    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400
    )
    return response.choices[0].message.content

def generate_alert(recommendation):
    alert_prompt = f"only in 4 words give alert type: {recommendation}"
    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": alert_prompt}],
        max_tokens=400
    )
    return response.choices[0].message.content

def generate_speech(text):
    inputs = processor(text=text, return_tensors="pt")
    speech = model.generate_speech(inputs["input_ids"], speaker_embeddings, vocoder=vocoder)
    sf.write("alert_speech.wav", speech.numpy(), samplerate=16000)
    st.audio("alert_speech.wav", format="audio/wav", autoplay=True)

# Page Selection
page = st.sidebar.radio("Navigation", ["Driver Experience Personalization", "Predictive Maintenance"])

if page == "Driver Experience Personalization":
    st.title("Driver Experience Personalization")

    # Sidebar Inputs
    st.sidebar.header("Driver Profile")
    name = st.sidebar.text_input("Driver's Name", "Alex")
    driving_mode = st.sidebar.selectbox("Preferred Driving Mode", ["Eco", "Comfort", "Sport"])
    acceleration_pattern = st.sidebar.selectbox("Acceleration Pattern", ["Smooth", "Moderate", "Aggressive"])
    average_speed = st.sidebar.slider("Average Speed (mph)", 0, 120, 75)
    ac_usage = st.sidebar.selectbox("AC Usage", ["Low", "Moderate", "High"])
    recent_routes = st.sidebar.multiselect("Recent Routes", ["Urban", "Highway", "Rural", "Mountain"], default=["Urban"])

    driver_data = {
        "name": name,
        "driving_mode": driving_mode,
        "acceleration_pattern": acceleration_pattern,
        "average_speed": average_speed,
        "ac_usage": ac_usage,
        "recent_routes": recent_routes
    }

    if st.button("Generate Recommendation"):
        recommendation = get_recommendations(driver_data)
        st.subheader("Personalized Recommendation")
        st.write(recommendation)
        alert_text = generate_alert(recommendation)
        st.success(alert_text)
        generate_speech(alert_text)

elif page == "Predictive Maintenance":
    st.title("Predictive Maintenance for EVs")

    # --- Generate Synthetic Data ---
    np.random.seed(42)
    time_data = np.arange(1000)
    temperature = 25 + 0.5 * np.sin(0.005 * time_data) + 0.2 * np.random.normal(size=1000)
    vibrations = 0.2 + 0.1 * np.sin(0.02 * time_data) + 0.03 * np.random.normal(size=1000)

    # Create a DataFrame
    data = pd.DataFrame({
        'time': time_data,
        'temperature': temperature,
        'vibrations': vibrations,
        'voltage': np.random.normal(3.7, 0.1, size=1000),  # Assuming voltage data
        'current': np.random.normal(0.5, 0.05, size=1000)   # Assuming current data
    })

    # --- Sidebar for Simulation Parameters ---
    st.sidebar.header("Simulation Parameters")
    speed = st.sidebar.slider("Simulation Speed (seconds per step)", 0.1, 1.0, 0.5)
    failure_threshold = st.sidebar.slider("Failure Threshold (Temperature & Vibration)", 0.1, 1.0, 0.5)
    battery_health = st.sidebar.slider("Battery Health (%)", 50, 100, 85)
    cooling_efficiency = st.sidebar.slider("Cooling Efficiency (%)", 50, 100, 75)

    # --- Placeholder for Dynamic Graph Updates ---
    graph_placeholder = st.empty()

    table_placeholder = st.empty()

    # Create a DataFrame to store the results for the table
    if 'result_data' not in st.session_state:
        st.session_state.result_data = []

    fig, ax = plt.subplots(figsize=(8, 4))
    look_back = 30
    idx = 0

    # --- Simulate Dynamic Updates ---
    while idx < len(data) - look_back:
        # Adjust temperature and vibrations based on user inputs
        adjusted_temperature = data['temperature'].values[idx:idx + look_back] * (battery_health / 100)
        adjusted_vibrations = data['vibrations'].values[idx:idx + look_back] * (cooling_efficiency / 100)
        
        # In a real scenario, the following should use a trained model and scaler.
        # Here, we will simulate a placeholder model prediction.
        
        adjusted_data = np.column_stack((data['voltage'][idx:idx + look_back], 
                                        data['current'][idx:idx + look_back], 
                                        adjusted_temperature, 
                                        adjusted_vibrations))

        # Simulating model prediction (in place of a real model)
        prediction = np.random.random()  # Random value between 0 and 1 as a placeholder for anomaly detection
        is_anomaly = prediction > failure_threshold  # Directly compare the prediction with the failure threshold
        
        # Show current data in Streamlit
        current_data = data.iloc[idx + look_back]
        
        # Reason for anomaly (a placeholder here)
        anomaly_reason = "Exceeds Failure Threshold" if is_anomaly else "Normal Operation"
        
        # Store the results for the table
        st.session_state.result_data.insert(0,{
            "Voltage": current_data['voltage'],
            "Current": current_data['current'],
            "Temperature": current_data['temperature'],
            "Vibrations": current_data['vibrations'],
            "Is Anomaly": is_anomaly,
            "Reason of Anomaly": anomaly_reason
        })
        
        # --- Clear Previous Graph and Draw Updated Graph ---
        ax.clear()
        ax.plot(time_data[idx:idx + look_back], adjusted_temperature, color="orange", label="Adjusted Temperature")
        ax.plot(time_data[idx:idx + look_back], adjusted_vibrations, color="purple", label="Adjusted Vibrations")
        ax.set_xlim([time_data[idx], time_data[idx + look_back - 1]])
        ax.legend()
        ax.set_title("Temperature and Vibration Trends")
        ax.set_xlabel("Time")
        ax.set_ylabel("Adjusted Metrics")
        
        # --- Update the Graph Dynamically ---
        with graph_placeholder:
            st.pyplot(fig)
        with table_placeholder:

        # Display the last 10 rows of the result data as a scrollable table
            st.dataframe(pd.DataFrame(st.session_state.result_data[:10]))
        
        idx += 1
        time.sleep(speed)
