!pip install -q -U groq
api_keyy="your_key"
from groq import Groq
client=Groq(api_key=api_keyy)
# Example of sensor data with potential anomalies
sensor_data = [
    "Cycle 1",
    "Non-Sidewinder Charging: Charging Section 0 by 74 units",
    "Non-Sidewinder Discharge: Discharging Section 0 by 74 units",
    "Non-Sidewinder Discharge: Discharging Section 1 by 0 units",
    "Non-Sidewinder Discharge: Discharging Section 2 by 0 units",
    "Non-Sidewinder Discharge: Discharging Section 3 by 0 units",
    "Non-Sidewinder Discharge: Discharging Section 4 by 0 units",
    "Section 0: Charge = 0, Health = 100.00%, Temp = 32.4°C",
    "Section 1: Charge = 0, Health = 100.00%, Temp = 25.0°C",
    "Section 2: Charge = 0, Health = 100.00%, Temp = 25.0°C",
    "Section 3: Charge = 0, Health = 100.00%, Temp = 25.0°C",
    "Section 4: Charge = 0, Health = 100.00%, Temp = 25.0°C",
    "=== Sidewinder Optimization Cycle ===",
    "Sidewinder Adaptive Charging: Charging Section 0 by 74 units (Temp: 39.8°C)",
    "Sidewinder Sectional Balancing for Discharge: Discharging Section 0 by 74 units (Temp: 32.4°C)",
    "Health Monitoring and Maintenance:",
    "Section 0: Charge = 0, Health = 100.00%, Temp = 32.4°C",
    "Section 1: Charge = 0, Health = 100.00%, Temp = 25.0°C",
    "Section 2: Charge = 0, Health = 100.00%, Temp = 25.0°C",
    "Section 3: Charge = 0, Health = 100.00%, Temp = 25.0°C",
    "Section 4: Charge = 0, Health = 100.00%, Temp = 25.0°C",

    "Cycle 2",
    "Non-Sidewinder Charging: Charging Section 0 by 76 units",
    "Non-Sidewinder Discharge: Discharging Section 0 by 76 units",
    "Non-Sidewinder Discharge: Discharging Section 1 by 0 units",
    "Non-Sidewinder Discharge: Discharging Section 2 by 0 units",
    "Non-Sidewinder Discharge: Discharging Section 3 by 0 units",
    "Non-Sidewinder Discharge: Discharging Section 4 by 0 units",
    "Section 0: Charge = 0, Health = 100.00%, Temp = 40.0°C",
    "Section 1: Charge = 0, Health = 100.00%, Temp = 25.0°C",
    "Section 2: Charge = 0, Health = 100.00%, Temp = 25.0°C",
    "Section 3: Charge = 0, Health = 100.00%, Temp = 25.0°C",
    "Section 4: Charge = 0, Health = 100.00%, Temp = 25.0°C",
    "=== Sidewinder Optimization Cycle ===",
    "Sidewinder Adaptive Charging: Charging Section 0 by 76 units (Temp: 47.6°C)",
    "Sidewinder Sectional Balancing for Discharge:",
    "Health Monitoring and Maintenance:",
    "Section 0: Charge = 76, Health = 99.89%, Temp = 47.6°C",
    "Section 1: Charge = 0, Health = 100.00%, Temp = 25.0°C",
    "Section 2: Charge = 0, Health = 100.00%, Temp = 25.0°C",
    "Section 3: Charge = 0, Health = 100.00%, Temp = 25.0°C",
    "Section 4: Charge = 0, Health = 100.00%, Temp = 25.0°C",

    "Cycle 3",
    "Non-Sidewinder Charging: Charging Section 0 by 100 units",
    "Non-Sidewinder Charging: Charging Section 1 by 20 units",
    "Non-Sidewinder Discharge: Discharging Section 0 by 100 units",
    "Non-Sidewinder Discharge: Discharging Section 1 by 20 units",
    "Non-Sidewinder Discharge: Discharging Section 2 by 0 units",
    "Non-Sidewinder Discharge: Discharging Section 3 by 0 units",
    "Non-Sidewinder Discharge: Discharging Section 4 by 0 units",
    "Section 0: Charge = 0, Health = 100.00%, Temp = 50.0°C",
    "Section 1: Charge = 0, Health = 100.00%, Temp = 27.0°C",
    "Section 2: Charge = 0, Health = 100.00%, Temp = 25.0°C",
    "Section 3: Charge = 0, Health = 100.00%, Temp = 25.0°C",
    "Section 4: Charge = 0, Health = 100.00%, Temp = 25.0°C",
    "=== Sidewinder Optimization Cycle ===",
    "Sidewinder Adaptive Charging: Charging Section 1 by 100 units (Temp: 45.0°C)",
    "Sidewinder Adaptive Charging: Charging Section 2 by 20 units (Temp: 29.0°C)",
    "Sidewinder Sectional Balancing for Discharge: Discharging Section 2 by 20 units (Temp: 27.0°C)",
    "Health Monitoring and Maintenance:",
    "Section 0: Charge = 76, Health = 99.79%, Temp = 47.6°C",
    "Section 1: Charge = 100, Health = 99.81%, Temp = 45.0°C",
    "Section 2: Charge = 0, Health = 100.00%, Temp = 27.0°C",
    "Section 3: Charge = 0, Health = 100.00%, Temp = 25.0°C",
    "Section 4: Charge = 0, Health = 100.00%, Temp = 25.0°C",

    "--- Comparison ---",
    "Non-Sidewinder Average Health: 100.00, Overload Events: 1",
    "Sidewinder Average Health: 99.97, Overload Events: 3"
]

# Prepare the log data
sensor_log = "\n".join(sensor_data)

# Send the log data to LLaMA for anomaly detection
response = client.chat.completions.create(
    model="llama3-8b-8192",
    messages=[
        {"role": "system", "content": "You are an AI assistant specialized in detecting anomalies in sensor data."},
        {"role": "user", "content": f"Please analyze the following sensor data and highlight any anomalies:\n\n{sensor_log}"}
    ],
    max_tokens=150
)

# Print the anomaly detection results
print("Anomaly Detection Result:", response.choices[0].message.content)
