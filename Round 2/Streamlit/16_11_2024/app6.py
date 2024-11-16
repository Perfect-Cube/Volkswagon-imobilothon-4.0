import streamlit as st
import random
import time
import matplotlib.pyplot as plt
import numpy as np
import torch
from transformers import SpeechT5Processor, SpeechT5ForTextToSpeech, SpeechT5HifiGan
from datasets import load_dataset
import soundfile as sf
from groq import Groq


# Groq Client initialization with API Key
api_key = "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"  # Replace with your actual API key
client = Groq(api_key=api_key)

# Load models for Text-to-Speech (TTS)
processor = SpeechT5Processor.from_pretrained("microsoft/speecht5_tts")
model = SpeechT5ForTextToSpeech.from_pretrained("microsoft/speecht5_tts")
vocoder = SpeechT5HifiGan.from_pretrained("microsoft/speecht5_hifigan")
embeddings_dataset = load_dataset("Matthijs/cmu-arctic-xvectors", split="validation")
speaker_embeddings = torch.tensor(embeddings_dataset[7306]["xvector"]).unsqueeze(0)
# Initialize battery pack with 8 cells, each with a charge level between 80-100% and temperature
# battery_pack = [{"charge": random.uniform(80, 100), "temp": random.uniform(25, 35)} for _ in range(8)]
min_charge = 20         # Minimum charge threshold to force resting
base_charge_rate = 5    # Base rate at which resting cells are charged per cycle
base_discharge_rate = 10  # Base rate at which active cells are discharged per cycle
overload_threshold = 30  # Maximum total discharge rate to avoid overload
temp_increase_rate = 5   # Temperature increase per cycle for active cells
temp_cooling_rate = 2    # Temperature decrease per cycle for resting cells
overheat_temp = 50       # Maximum safe operating temperature
target_distance = 1.0    # Target distance per cycle for efficient performance

# Define dynamic distance conditions
distance_ranges = {
    'city': (0.5, 1.5),     # Short distance, low drain
    'highway': (1.5, 3.0),  # Moderate distance, moderate drain
    'uphill': (0.3, 1.0),    # Short distance, high drain
    'traffic': (0.2, 1.0),  # Low speed in traffic, high drain
    'town': (0.5, 1.0),     # Low speed, moderate drain
    'downhill': (1.0, 2.0)  # Longer distance, low drain
}


def initialize_battery_pack(battery_percent, battery_temp):
    """Initialize the battery pack based on user input."""
    # Divide the user input evenly across the 8 cells
    battery_pack = [{"charge": battery_percent, "temp": battery_temp} for _ in range(8)]
    return battery_pack
def get_user_input():
    # Get battery percentage as a number input (between 80 and 100)
    battery_percent = st.slider("Enter Battery Percentage", min_value=5, max_value=100, value=90)
    
    # Get battery temperature as a number input (between 25 and 45 degrees Celsius)
    battery_temp = st.slider("Enter Battery Temperature (°C)", min_value=25, max_value=60, value=30)
    
    # Select driving condition from a dropdown
    conditions = ["Uphill", "Highway", "Traffic", "City", "Town", "Downhill"]
    driving_condition = st.selectbox("Select Driving Condition", conditions)

    # Charge rate as an input
    charge_rate = st.slider("Enter Charge Rate", min_value=1, max_value=20, value=base_charge_rate)

    # Store the result as a list of strings
    input_data = [
        f"Battery Percentage: {battery_percent}%",
        f"Battery Temperature: {battery_temp}°C",
        f"Driving Condition: {driving_condition}",
        f"Charge Rate: {charge_rate} units"
    ]
    
    return battery_percent, battery_temp, driving_condition, charge_rate, input_data

def get_recommendations(result):
    prompt = f"""
    You are an assistant helping personalize vehicle settings for driver experience.
    Provide a recommendation for improving performance and battery efficiency analyzing the result: {result}
    """
    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400
    )
    return response.choices[0].message.content
def generate_alert(simulation_results,prompt):
    """Generate an alert message using Groq."""
    alert_prompt = f"{prompt}:{simulation_results}"
    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": alert_prompt}],
        max_tokens=20
    )
    return response.choices[0].message.content

def generate_speech(text):
    """Generate speech from the alert text."""
    inputs = processor(text=text, return_tensors="pt")
    speech = model.generate_speech(inputs["input_ids"], speaker_embeddings, vocoder=vocoder)
    sf.write("alert_speech.wav", speech.numpy(), samplerate=16000)
    st.audio("alert_speech.wav", format="audio/wav", autoplay=True)
def get_cycle_distance(driving_condition):
    """Get random distance and discharge rate for current cycle based on driving conditions."""
    distance = random.uniform(*distance_ranges[driving_condition.lower()])
    adjusted_discharge_rate = base_discharge_rate * (distance / 1.5)  # Higher distance means higher drain
    return distance, adjusted_discharge_rate

def discharge_group(group, discharge_rate):
    """Discharge the cells in the active group and increase their temperature."""
    for i in group:
        battery_pack[i]["charge"] = max(0, battery_pack[i]["charge"] - discharge_rate)
        battery_pack[i]["temp"] = min(overheat_temp, battery_pack[i]["temp"] + temp_increase_rate)

def charge_group(group, charge_rate):
    """Charge the cells in the resting group and reduce their temperature."""
    for i in group:
        battery_pack[i]["charge"] = min(100, battery_pack[i]["charge"] + charge_rate)
        battery_pack[i]["temp"] = max(20, battery_pack[i]["temp"] - temp_cooling_rate)

def rotate_groups(wave_index, max_active_cells):
    """Rotate cells between active and resting groups in a wave-like pattern."""
    active_group = [(wave_index + i) % len(battery_pack) for i in range(max_active_cells)]
    resting_group = [i for i in range(len(battery_pack)) if i not in active_group]
    return active_group, resting_group

def check_average_battery_level():
    """Calculate and check the average battery level across all cells."""
    total_charge = sum(cell["charge"] for cell in battery_pack)
    avg_battery_level = total_charge / len(battery_pack)
    return avg_battery_level

def plot_graphs():
    """Plot individual graphs for battery stats"""
    fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(10, 12))

    # Plot Battery Percentage
    ax1.set_title('Battery Percentage')
    ax1.plot(time_data, battery_percent_data, color='tab:blue', label="Battery %")
    ax1.set_xlabel('Cycle')
    ax1.set_ylabel('Battery %')
    
    # Plot Temperature
    ax2.set_title('Battery Temperature')
    ax2.plot(time_data, temperature_data, color='tab:green', label="Temperature (°C)")
    ax2.set_xlabel('Cycle')
    ax2.set_ylabel('Temperature (°C)')

    # Plot Charge Rate
    ax3.set_title('Charge Rate')
    ax3.plot(time_data, charge_rate_data, color='tab:red', label="Charge Rate")
    ax3.set_xlabel('Cycle')
    ax3.set_ylabel('Charge Rate')

    # Plot Discharge Rate
    ax4.set_title('Discharge Rate')
    ax4.plot(time_data, discharge_rate_data, color='tab:orange', label="Discharge Rate")
    ax4.set_xlabel('Cycle')
    ax4.set_ylabel('Discharge Rate')

    fig.tight_layout()
    with graph_placeholder:
        st.pyplot(fig)  # Return the figure for plotting

graph_placeholder = st.empty()  # This will hold the graph below the button

def main():

    if "result_data" not in st.session_state:
        st.session_state.result_data = []
    
    st.title("Battery Efficiency and AI Motor Optimization")

    # Dropdown for mode selection
    mode = st.selectbox(
        "Select Mode",
        ["Home", "Eco Mode", "Performance Mode", "Analysis Mode"]
    )

    # Display content based on the selected mode
    if mode == "Home":
        st.write("### BEAM (Battery Efficiency and AI Motor Optimization)")
        st.write("BEAM focuses on optimizing battery performance by dynamically adjusting battery charge/discharge rates and managing temperature. "
                 "This results in a more efficient and longer-lasting battery, especially for electric vehicles. "
                 "The system takes into account various driving conditions such as city traffic, highway speeds, and temperature, ensuring optimal battery performance at all times.")
    
    elif mode == "Eco Mode":
        st.write("### Battery Management (Eco Mode)")
        st.write("In Eco Mode, the system prioritizes energy conservation, limiting the battery's charge rate and discharge rate to preserve energy and increase battery life.")
        
        # Get the user input
        battery_percent, battery_temp, driving_condition, charge_rate, input_data = get_user_input()

        # Initialize battery pack based on user input
        global battery_pack
        battery_pack = initialize_battery_pack(battery_percent, battery_temp)
        # Display input data
        st.write("Input Data:")
        for item in input_data:
            st.write(item)

        # Initialize total_distance here to avoid reference errors
        total_distance = 0

        # Add a button to run the simulation
        if st.button("Run Simulation"):
            # Store initial values
            wave_index = 0
            max_active_cells = 4
            
            # Initialize data lists for graphs
            battery_percent_data.clear()
            temperature_data.clear()
            charge_rate_data.clear()
            discharge_rate_data.clear()
            time_data.clear()
            
            

            for cycle in range(1, 16):  # Run for 10 cycles
                # Get the cycle's distance and discharge rate based on driving condition
                cycle_distance, discharge_rate = get_cycle_distance(driving_condition)
                total_distance += cycle_distance  # Update total distance

                # Determine active and resting groups using wave rotation
                active_group, resting_group = rotate_groups(wave_index, max_active_cells)

                # Discharge active group and charge resting group
                discharge_group(active_group, discharge_rate)
                charge_group(resting_group, charge_rate)

                # Store data for graphing
                avg_battery_level = check_average_battery_level()
                battery_percent_data.append(avg_battery_level)
                temperature_data.append(np.mean([cell["temp"] for cell in battery_pack]))
                charge_rate_data.append(charge_rate)
                discharge_rate_data.append(discharge_rate)
                time_data.append(cycle)

                # Add the results to result_data list
                st.session_state.result_data.append(
                    f"Cycle {cycle} - Distance: {cycle_distance:.2f} km, "
                    f"Avg Battery Level: {avg_battery_level:.2f}%, "
                    f"Avg Temperature: {np.mean([cell['temp'] for cell in battery_pack]):.2f}°C"
                )

                plot_graphs()
                # Increment wave index for the next cycle to shift the group pattern
                wave_index += 1

                # Short delay to simulate real-time processing
                time.sleep(1)

            # Show total distance covered
            st.write(f"Total Distance Covered: {total_distance:.2f} km")
            
            # Show detailed results
            st.write("### Simulation Results")
            for result in st.session_state.result_data:
                st.write(result)

        
            simulation_summary = f"Total Distance: {total_distance:.2f} km, Avg Battery: {avg_battery_level:.2f}%"
            alert="Give alert in 5 words only"
            suggestion="Give suggestion in 6 words only, don't include numeric data"
            alert_text = generate_alert("\n".join(st.session_state.result_data),alert)
            st.write(f"**Alert**: {alert_text}")
            generate_speech(alert_text)

            suggestion_text=generate_alert("\n".join(st.session_state.result_data),suggestion)
            st.write(f"**Suggestion**:{suggestion_text}")
            generate_speech(suggestion_text)
    elif mode == "Performance Mode":
        st.write("### Performance Mode")
        st.write("In Performance Mode, the system prioritizes performance and speed, with higher charge and discharge rates to maximize the power available to the motor.")
        
    elif mode == "Analysis Mode":
        st.write("### Analysis Mode")
        st.write("In Analysis Mode, detailed insights into battery performance are provided, allowing for deeper understanding of how various factors like charge rates, discharge rates, and temperature affect the overall system performance.")
        st.title("Driver Experience Personalization")
        if st.session_state.result_data:
            if st.button("Generate Recommendation"):
                recommendation = get_recommendations(st.session_state.result_data)
                st.subheader("Personalized Recommendation")
                st.write(recommendation)
                alert=f"Give only 4 words alert: {st.session_state.result_data}"
                alert_text = generate_alert(st.session_state.result_data,alert)
                st.success(alert_text)
                generate_speech(alert_text)
        else:
            st.warning("No Data Available")
# Run the app
if __name__ == "__main__":
    # Initialize the data lists
    battery_percent_data = []
    temperature_data = []
    charge_rate_data = []
    discharge_rate_data = []
    time_data = []

    main()
