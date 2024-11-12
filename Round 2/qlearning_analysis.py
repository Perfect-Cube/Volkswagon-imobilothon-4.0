from groq import Groq
api_keyy="key"
client=Groq(api_key=api_keyy)
# Example of sensor data with potential anomalies
training_log = [
    "Episode 1: Total Reward: -3.5356266966340817, Distance: 37.12 km, Energy: 3.54 units",
    "Episode 2: Total Reward: -3.3863984000110823, Distance: 37.59 km, Energy: 3.39 units",
    "Episode 3: Total Reward: -3.5469663293224922, Distance: 41.68 km, Energy: 3.55 units",
    "Episode 4: Total Reward: -2.76440433057698, Distance: 40.70 km, Energy: 2.76 units",
    "Episode 5: Total Reward: -3.6283312438870485, Distance: 47.03 km, Energy: 3.63 units",
    "Episode 6: Total Reward: -3.5867127068825053, Distance: 50.42 km, Energy: 3.59 units",
    "Episode 7: Total Reward: -2.009544586548487, Distance: 33.64 km, Energy: 2.01 units",
    "Episode 8: Total Reward: -2.903262020740318, Distance: 36.39 km, Energy: 2.90 units",
    "Episode 9: Total Reward: -3.5033476312848686, Distance: 42.05 km, Energy: 3.50 units",
    "Episode 10: Total Reward: -3.638711519058919, Distance: 32.44 km, Energy: 3.64 units",
    "Episode 11: Total Reward: -2.3250165193696652, Distance: 32.46 km, Energy: 2.33 units",
    "Episode 12: Total Reward: -2.5341150239129155, Distance: 32.47 km, Energy: 2.53 units",
    "Episode 13: Total Reward: -3.2762791344484956, Distance: 43.47 km, Energy: 3.28 units",
    "Episode 14: Total Reward: -3.3945251784690273, Distance: 33.32 km, Energy: 3.39 units",
    "Episode 15: Total Reward: -3.00868613026187, Distance: 40.54 km, Energy: 3.01 units",
    "Episode 16: Total Reward: -2.965849767951053, Distance: 37.54 km, Energy: 2.97 units",
    "Episode 17: Total Reward: -2.900206223259797, Distance: 38.69 km, Energy: 2.90 units",
    "Episode 18: Total Reward: -2.1963288577472455, Distance: 36.29 km, Energy: 2.20 units",
    "Episode 19: Total Reward: -2.978383177055786, Distance: 56.48 km, Energy: 2.98 units",
    "Episode 20: Total Reward: -2.8389946992946284, Distance: 40.21 km, Energy: 2.84 units",
    "Episode 21: Total Reward: -3.2553473893618423, Distance: 43.95 km, Energy: 3.26 units",
    "Episode 22: Total Reward: -2.655995747874592, Distance: 34.67 km, Energy: 2.66 units",
    "Episode 23: Total Reward: -1.8138742155985754, Distance: 36.35 km, Energy: 1.81 units",
    "Episode 24: Total Reward: -2.5734047993366707, Distance: 32.39 km, Energy: 2.57 units",
    "Episode 25: Total Reward: -2.776127293168404, Distance: 54.54 km, Energy: 2.78 units",
    "Episode 26: Total Reward: -2.2764182322976385, Distance: 42.94 km, Energy: 2.28 units",
    "Episode 27: Total Reward: -2.6376316822530126, Distance: 42.96 km, Energy: 2.64 units",
    "Episode 28: Total Reward: -3.9956112579020964, Distance: 47.54 km, Energy: 4.00 units",
    "Episode 29: Total Reward: -3.2921232922147756, Distance: 33.29 km, Energy: 3.29 units",
    "Episode 30: Total Reward: -3.331590665574241, Distance: 33.00 km, Energy: 3.33 units",
    "Episode 31: Total Reward: -3.354162576825596, Distance: 39.94 km, Energy: 3.35 units",
    "Episode 32: Total Reward: -2.686992454698852, Distance: 41.44 km, Energy: 2.69 units",
    "Episode 33: Total Reward: -2.7961944060265713, Distance: 43.93 km, Energy: 2.80 units",
    "Episode 34: Total Reward: -3.0495746401861887, Distance: 32.75 km, Energy: 3.05 units",
    "Episode 35: Total Reward: -3.049424787674971, Distance: 40.00 km, Energy: 3.05 units",
    "Episode 36: Total Reward: -2.8193287887352025, Distance: 35.43 km, Energy: 2.82 units",
    "Episode 37: Total Reward: -2.0674240459043998, Distance: 38.03 km, Energy: 2.07 units",
    "Episode 38: Total Reward: -4.603257672171388, Distance: 35.50 km, Energy: 4.60 units",
    "Episode 39: Total Reward: -3.2761700635472937, Distance: 41.87 km, Energy: 3.28 units",
    "Episode 40: Total Reward: -2.643005971053116, Distance: 37.26 km, Energy: 2.64 units",
    "Episode 41: Total Reward: -2.9369671601689253, Distance: 31.64 km, Energy: 2.94 units",
    "Episode 42: Total Reward: -1.645401514681755, Distance: 45.04 km, Energy: 1.65 units",
    "Episode 43: Total Reward: -2.9210325889533313, Distance: 41.33 km, Energy: 2.92 units",
    "Episode 44: Total Reward: -3.0026715508323534, Distance: 59.05 km, Energy: 3.00 units",
    "Episode 45: Total Reward: -2.7778533507052234, Distance: 33.62 km, Energy: 2.78 units",
    "Episode 46: Total Reward: -2.062075938900233, Distance: 32.16 km, Energy: 2.06 units",
    "Episode 47: Total Reward: -2.691353721078693, Distance: 38.92 km, Energy: 2.69 units",
    "Episode 48: Total Reward: -2.804318301109272, Distance: 33.30 km, Energy: 2.80 units",
    "Episode 49: Total Reward: -2.2174394933725914, Distance: 47.33 km, Energy: 2.22 units",
    "Episode 50: Total Reward: -2.7029647618048687, Distance: 33.02 km, Energy: 2.70 units",
    "Final battery levels and health after training:",
    "Cell 1: Level 0.50, Health 1.00 (Resting)",
    "Cell 2: Level 0.72, Health 1.00 (Active)",
    "Cell 3: Level 0.32, Health 1.00 (Active)",
    "Cell 4: Level 0.14, Health 0.98 (Active)",
    "Cell 5: Level 0.60, Health 1.00 (Active)",
    "Cell 6: Level 0.93, Health 1.00 (Resting)",
    "Cell 7: Level 0.57, Health 1.00 (Resting)",
    "Cell 8: Level 1.00, Health 1.00 (Resting)"
]


# Prepare the log data
sensor_log = "\n".join(training_log)

# Send the log data to LLaMA for anomaly detection
response = client.chat.completions.create(
    model="llama3-8b-8192",
    messages=[
        {"role": "system", "content": "You are an AI assistant for an Electric Vehicle."},
        {"role": "user", "content": f"Analyze the following  q learning data and battery log data of car find anomalies and provide a summary of battery health and give solution and tell where the nearest charging point required in minimum distance:\n\n{sensor_log}"}
    ],
    max_tokens=400
)

# Print the anomaly detection results
print("Anomaly Detection Result:", response.choices[0].message.content)
