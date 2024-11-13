import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
import time  # Import the time module

# --- Step 1: Generate Realistic Sample Data ---

np.random.seed(42)
data_size = 10000
time_data = np.arange(data_size)  # Rename time to time_data to avoid conflict

# Generate sensor data with added noise and patterns
voltage = 3.5 + 0.1 * np.sin(0.01 * time_data) + 0.05 * np.random.normal(size=data_size)
current = 1.5 + 0.1 * np.cos(0.01 * time_data) + 0.05 * np.random.normal(size=data_size)
temperature = 25 + 0.5 * np.sin(0.005 * time_data) + 0.2 * np.random.normal(size=data_size)
vibrations = 0.2 + 0.1 * np.sin(0.02 * time_data) + 0.03 * np.random.normal(size=data_size)

# Simulate failure logs based on temperature and vibration thresholds
failure_log = np.where((temperature > 26) & (vibrations > 0.25), 1, 0)

# Combine into a DataFrame
data = pd.DataFrame({
    'voltage': voltage,
    'current': current,
    'temperature': temperature,
    'vibrations': vibrations,
    'failure_log': failure_log
})

# --- Step 2: Train LSTM Model for Failure Prediction ---

# Scale data
scaler = MinMaxScaler(feature_range=(0, 1))
scaled_data = scaler.fit_transform(data.drop(columns=['failure_log']))

# Function to create sequences for LSTM input
def create_sequences(data, target, look_back=30):
    X, y = [], []
    for i in range(len(data) - look_back):
        X.append(data[i:i + look_back])
        y.append(target[i + look_back])
    return np.array(X), np.array(y)

# Create sequences
X, y = create_sequences(scaled_data, data['failure_log'].values)

# Build and train the LSTM model
model = Sequential([
    LSTM(units=50, return_sequences=True, input_shape=(X.shape[1], X.shape[2])),
    Dropout(0.2),
    LSTM(units=50),
    Dropout(0.2),
    Dense(1, activation='sigmoid')
])

# --- Step 3: Streamlit Frontend ---

# Define Streamlit layout
st.title("Enhanced Predictive Maintenance for EVs")
st.write("Predict and prevent failures in critical EV components using real-time sensor data.")

# Sidebar for simulation speed control
speed = st.sidebar.slider("Simulation Speed (seconds per step)", 0.1, 1.0, 0.5)

# --- Step 4: Add More Variables and Controls for User Adjustments ---

# User inputs for real-time adjustments
battery_health = st.sidebar.slider("Battery Health (%)", 50, 100, 85)
motor_rpm = st.sidebar.slider("Motor RPM", 0, 10000, 4000)
cooling_efficiency = st.sidebar.slider("Cooling System Efficiency (%)", 50, 100, 85)
failure_threshold = st.sidebar.slider("Failure Threshold (Temperature / Vibration)", 0.1, 1.0, 0.5)

# Display initial data overview
st.subheader("Data Overview")
st.write("Real-time sensor data is displayed below:")

# --- Data Overview: Interactive Plot ---
fig = go.Figure()
fig.add_trace(go.Scatter(x=time_data[:500], y=data['voltage'][:500], mode='lines', name='Voltage'))
fig.add_trace(go.Scatter(x=time_data[:500], y=data['current'][:500], mode='lines', name='Current'))
fig.add_trace(go.Scatter(x=time_data[:500], y=data['temperature'][:500], mode='lines', name='Temperature'))
fig.add_trace(go.Scatter(x=time_data[:500], y=data['vibrations'][:500], mode='lines', name='Vibrations'))

fig.update_layout(
    title="Sensor Data Overview (First 500 Samples)",
    xaxis_title="Time",
    yaxis_title="Sensor Value",
    template="plotly_dark"
)
st.plotly_chart(fig)

# Real-time prediction loop (simulated data flow)
look_back = 30
idx = 0

# Initialize containers for live data and predictions
placeholder_data = st.empty()
placeholder_prediction = st.empty()

# Show loading screen while training
with st.spinner('Training the model, please wait...'):
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    model.fit(X, y, epochs=5, batch_size=32, validation_split=0.2)

st.success("Model Training Complete!")

# Create a placeholder for the real-time graph
fig, ax = plt.subplots(figsize=(8, 4))

# Initialize plot with first data points
ax.plot(time_data[:look_back], data['temperature'][:look_back], label="Temperature", color="orange")
ax.plot(time_data[:look_back], data['vibrations'][:look_back], label="Vibrations", color="purple")
ax.set_title("Temperature and Vibration Over Time")
ax.set_xlabel("Time")
ax.set_ylabel("Value")
ax.legend()

# Show the plot in Streamlit
st.pyplot(fig)

# Loop through data, showing predictions and updating in real-time
while idx < len(data) - look_back:
    # Prepare input data for the model with real-time adjustments
    adjusted_temperature = data['temperature'].values[idx:idx + look_back] * (battery_health / 100)  # Simulating effect of battery health
    adjusted_vibrations = data['vibrations'].values[idx:idx + look_back] * (cooling_efficiency / 100)  # Simulating effect of cooling system efficiency
    
    # Combine adjusted features
    adjusted_data = np.column_stack((data['voltage'][idx:idx + look_back], 
                                     data['current'][idx:idx + look_back], 
                                     adjusted_temperature, 
                                     adjusted_vibrations))

    # Scale data and reshape for LSTM input
    adjusted_scaled_data = scaler.transform(adjusted_data)
    input_data = adjusted_scaled_data.reshape(1, look_back, -1)
    
    # Prediction
    prediction = model.predict(input_data)
    is_anomaly = (prediction > failure_threshold).astype(int)[0][0]
    
    # Extract and display current data row
    current_data = data.iloc[idx + look_back]
    placeholder_data.write(f"Current Data:\nVoltage: {current_data['voltage']:.2f}, "
                           f"Current: {current_data['current']:.2f}, "
                           f"Temperature: {current_data['temperature']:.2f}, "
                           f"Vibrations: {current_data['vibrations']:.2f}, "
                           f"Motor RPM: {motor_rpm}, Battery Health: {battery_health}%, "
                           f"Cooling Efficiency: {cooling_efficiency}%")
    
    # Display prediction
    if is_anomaly:
        placeholder_prediction.warning("⚠️ Anomaly Detected! Possible Failure Imminent.")
    else:
        placeholder_prediction.success("✔️ System Operating Normally.")
    
    # Update the temperature and vibration plot in real-time
    ax.plot(time_data[idx:idx + look_back], adjusted_temperature, color="orange")
    ax.plot(time_data[idx:idx + look_back], adjusted_vibrations, color="purple")
    ax.set_xlim([time_data[idx], time_data[idx + look_back - 1]])  # Scroll the x-axis
    
    # Redraw the updated plot
    st.pyplot(fig)

    # Advance the index and wait for the next update
    idx += 1
    time.sleep(speed)  # Correct usage of time.sleep
