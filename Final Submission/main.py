# ------------------------Import Required Libraries---------------------------

import json
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
import gym
from gym import spaces
from stable_baselines3 import PPO
from streamlit_lottie import st_lottie


#-------------------------Groq Client initialization with API Key------------------------------------

api_key = "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"  # Replace with your actual API key
client = Groq(api_key=api_key)


#------------------------Load models for Text-to-Speech (TTS)------------------------------

processor = SpeechT5Processor.from_pretrained("microsoft/speecht5_tts")
model = SpeechT5ForTextToSpeech.from_pretrained("microsoft/speecht5_tts")
vocoder = SpeechT5HifiGan.from_pretrained("microsoft/speecht5_hifigan")
embeddings_dataset = load_dataset("Matthijs/cmu-arctic-xvectors", split="validation")
speaker_embeddings = torch.tensor(embeddings_dataset[7306]["xvector"]).unsqueeze(0)


#-------------Initialize battery pack with 8 cells, each with a charge level between 5-100% and temperature-----------------

def initialize_battery_pack(battery_percent, battery_temp):
    """Initialize the battery pack based on user input."""
    # Divide the user input evenly across the 8 cells
    battery_pack = [{"charge": battery_percent, "temp": battery_temp} for _ in range(8)]
    return battery_pack

min_charge = 20         # Minimum charge threshold to force resting
base_charge_rate = 5    # Base rate at which resting cells are charged per cycle
base_discharge_rate = 10  # Base rate at which active cells are discharged per cycle
overload_threshold = 30  # Maximum total discharge rate to avoid overload
temp_increase_rate = 5   # Temperature increase per cycle for active cells
temp_cooling_rate = 2    # Temperature decrease per cycle for resting cells
overheat_temp = 50       # Maximum safe operating temperature
target_distance = 1.0    # Target distance per cycle for efficient performance


#-------------------------------Define dynamic distance conditions-------------------------------------

distance_ranges = {
    'city': (0.5, 1.5),     # Short distance, low drain
    'highway': (1.5, 3.0),  # Moderate distance, moderate drain
    'uphill': (0.3, 1.0),    # Short distance, high drain
    'traffic': (0.2, 1.0),  # Low speed in traffic, high drain
    'town': (0.5, 1.0),     # Low speed, moderate drain
    'downhill': (1.0, 2.0)  # Longer distance, low drain
}


#-------------------------------User Input for Eco Mode-------------------------------------
def get_user_input():
    # Get battery percentage as a number input (between 80 and 100)
    battery_percent = st.slider("**Enter Battery Percentage:**", min_value=5, max_value=100, value=90)
    
    # Get battery temperature as a number input (between 25 and 45 degrees Celsius)
    battery_temp = st.slider("**Enter Battery Temperature (°C):**", min_value=25, max_value=60, value=30)
    
    # Select driving condition from a dropdown
    conditions = ["Uphill", "Highway", "Traffic", "City", "Town", "Downhill"]
    driving_condition = st.selectbox("**Select Driving Condition:**", conditions)

    # Charge rate as an input
    charge_rate = st.slider("**Enter Charge Rate:**", min_value=1, max_value=20, value=base_charge_rate)

    # Store the result as a list of strings
    input_data = [
        f"Battery Percentage: {battery_percent}%",
        f"Battery Temperature: {battery_temp}°C",
        f"Driving Condition: {driving_condition}",
        f"Charge Rate: {charge_rate} units"
    ]
    
    return battery_percent, battery_temp, driving_condition, charge_rate, input_data


#-----------------------------Generating Recommendations using Llama3-8b------------------------------

def get_recommendations(result):
    prompt = f"""
    You are an assistant helping personalize vehicle settings for driver experience.
    Provide a recommendation for improving performance and battery efficiency analyzing the result: {result}
    Also tell distance to nearest charging point
    """
    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400
    )
    return response.choices[0].message.content


#-------------------------Generate an alert message using Groq-------------------------------------

def generate_alert(simulation_results,prompt):
    alert_prompt = f"{prompt}:{simulation_results}"
    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": alert_prompt}],
        max_tokens=20
    )
    return response.choices[0].message.content


#--------------------------------Generate speech from the alert text-----------------------------

def generate_speech(text):
    inputs = processor(text=text, return_tensors="pt")
    speech = model.generate_speech(inputs["input_ids"], speaker_embeddings, vocoder=vocoder)
    sf.write("alert_speech.wav", speech.numpy(), samplerate=16000)
    st.audio("alert_speech.wav", format="audio/wav", autoplay=True)


#---------------------------Sidewinder Snake Algorithm for Eco Mode--------------------------------------------------

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
    return fig# Return the figure for plotting


#------------------------------PPO for Performance Mode----------------------------------

#---------------------Custom environment for real-time use-----------------------
class RealTimeMotorEnvironment(gym.Env):
    def __init__(self):
        super(RealTimeMotorEnvironment, self).__init__()
        
        # Define state parameters
        self.battery = 100
        self.temperature = 30
        self.speed = 50
        self.distance = 0
        self.max_speed = 180
        self.max_temperature = 70
        self.min_temperature = 15
        self.charging_rate = 3  # Battery charge rate per action
        
        # Define action space:
        # 0 = decrease speed, 1 = maintain speed, 2 = increase speed, 3 = activate cooling, 4 = start charging
        self.action_space = spaces.Discrete(5)
        
        # Define observation space: battery level, temperature, speed, distance
        self.observation_space = spaces.Box(low=np.array([0, 0, 0, 0]), 
                                             high=np.array([100, self.max_temperature, self.max_speed, np.inf]), 
                                             dtype=np.float32)
    
    def reset(self, battery, temperature, speed, distance):
        # Reset environment with real-time data
        self.battery = battery
        self.temperature = temperature
        self.speed = speed
        self.distance = distance
        return np.array([self.battery, self.temperature, self.speed, self.distance])
    
    def step(self, action):
        # Simulate the effect of action
        if action == 0:  # Decrease speed
            self.speed -= 5
        elif action == 2:  # Increase speed
            self.speed += 5
        elif action == 3:  # Activate cooling
            self.temperature -= 2
        elif action == 4:  # Start charging
            self.battery += self.charging_rate
        
        # Ensure speed stays within limits and charging doesn't exceed 100%
        self.speed = np.clip(self.speed, 0, self.max_speed)
        self.battery = np.clip(self.battery, 0, 100)
        
        # Update temperature and battery based on speed
        if action != 4:  # Normal operation, not charging
            if action != 3:
                self.temperature += 0.05 * self.speed
            battery_consumption = 0.02 * self.speed
            self.battery -= battery_consumption
        
        # Update distance based on speed
        self.distance += self.speed / 60
        
        # Automatic stop if overheated
        if self.temperature >= self.max_temperature:
            self.speed = 0  # Stop the car
            reward = -10  # Heavy penalty for overheating
            done = True
            return np.array([self.battery, self.temperature, self.speed, self.distance]), reward, done, {}

        # Determine if the episode is done
        done = self.battery <= 0
        
        # Reward function
        reward = -0.02 * self.speed  # Penalize for high speed (battery consumption)
        if self.temperature > 40:
            reward -= 1  # Additional penalty for high temperature
        if action == 3 and self.temperature > 35:
            reward += 2  # Reward for cooling when necessary
        if action == 4 and self.battery < 50:
            reward += 3  # Reward for charging when battery is low
        
        return np.array([self.battery, self.temperature, self.speed, self.distance]), reward, done, {}

# Initialize data lists for plotting
performance_battery_data = []
performance_temperature_data = []
performance_speed_data = []
performance_distance_data = []
performance_time_data = []

def plot_performance_graphs():
    """Plot performance graphs for battery percentage, temperature, speed, and distance."""
    fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(10, 12))

    # Battery Percentage Graph
    ax1.set_title("Battery Percentage Over Time")
    ax1.plot(performance_time_data, performance_battery_data, label="Battery %", color="tab:blue")
    ax1.set_xlabel("Cycle")
    ax1.set_ylabel("Battery %")
    ax1.legend()

    # Temperature Graph
    ax2.set_title("Temperature Over Time")
    ax2.plot(performance_time_data, performance_temperature_data, label="Temperature (°C)", color="tab:green")
    ax2.set_xlabel("Cycle")
    ax2.set_ylabel("Temperature (°C)")
    ax2.legend()

    # Speed Graph
    ax3.set_title("Speed Over Time")
    ax3.plot(performance_time_data, performance_speed_data, label="Speed (km/h)", color="tab:red")
    ax3.set_xlabel("Cycle")
    ax3.set_ylabel("Speed (km/h)")
    ax3.legend()

    # Distance Graph
    ax4.set_title("Distance Over Time")
    ax4.plot(performance_time_data, performance_distance_data, label="Distance (km)", color="tab:orange")
    ax4.set_xlabel("Cycle")
    ax4.set_ylabel("Distance (km)")
    ax4.legend()

    fig.tight_layout()
    return fig


#--------------------------------------------Main Function----------------------------------------

def main():

    if "result_data" not in st.session_state:
        st.session_state.result_data = []

    if "performance_results" not in st.session_state:
        st.session_state.performance_results = []

    if "result" not in st.session_state:
        st.session_state.result = []
    
    st.title("BEAM: Battery Efficiency and AI Motor Optimization")
    with open("Animation - 1731759700152.json") as source:

        animation1=json.load(source)

    st_lottie(animation1)

    # Dropdown for mode selection
    mode = st.selectbox(
        "Select Mode",
        ["Home", "Eco Mode", "Performance Mode", "Analysis & Feedback"]
    )

    #----------------------------------Display content based on the selected mode--------------------------

    #-----------------------------------Home--------------------------------------
    if mode == "Home":
        st.write("### BEAM (Battery Efficiency and AI Motor Optimization)")
        st.write(
    """
    Welcome to **BEAM**, where cutting-edge AI meets sustainable innovation. BEAM is an advanced solution designed to redefine the electric vehicle (EV) experience by optimizing battery performance, extending lifespan, and enhancing motor efficiency.

    ### Key Features:
    - **Eco Mode:** Sidewinder-inspired wave strategies for maximum energy efficiency and fault tolerance.
    - **Performance Mode:** Reinforcement learning-powered acceleration with real-time cooling and energy optimization.

    With BEAM, drivers enjoy unparalleled efficiency, thermal stability, and a seamless blend of performance and sustainability.  
    **Experience the future of EV technology today with BEAM!**
    """
)
    
    #-----------------------------------------Eco Mode--------------------------------------------------
    elif mode == "Eco Mode":
        st.title("Eco Mode: Redefining Efficiency in EVs")
        st.write(
    """
    **BEAM's Eco Mode** is designed to revolutionize energy efficiency without compromising driving performance. Inspired by the movement of the sidewinder snake, this mode minimizes energy usage while ensuring thermal stability and extended battery life.

    ### Why Choose Eco Mode?
    - **Wave Strategy Innovation:** Selectively activates battery cells, reducing wear and optimizing energy usage.
    - **Enhanced Thermal Performance:** Minimizes overheating for prolonged battery health.
    - **Fault Tolerance:** Intelligent algorithms ensure uninterrupted operation by isolating faulty cells.
    - **Seamless Driving Experience:** Enjoy superior efficiency without sacrificing acceleration or comfort.

    Real-time alerts and notifications keep drivers informed about:
    - Battery usage
    - Thermal conditions
    - Suggestions for optimal driving

    With BEAM's Eco Mode, you get the perfect balance of efficiency and performance, making every journey smarter and more sustainable.
    """
)
        
        with open("Animation - 1731760236187.json") as source:

            animation2=json.load(source)

        st_lottie(animation2,height=400,width=800)

        # Get the user input
        battery_percent, battery_temp, driving_condition, charge_rate, input_data = get_user_input()

        # Initialize battery pack based on user input
        global battery_pack
        battery_pack = initialize_battery_pack(battery_percent, battery_temp)
        # Display input data
        st.write("**Input Data:**")
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
            
            graph_placeholder = st.empty()  # This will hold the graph below the button

            
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
                
                with graph_placeholder:
                    fig=plot_graphs()
                    st.pyplot(fig)
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
            st.error(f"**Alert**: {alert_text}")
            generate_speech(alert_text)

            suggestion_text=generate_alert("\n".join(st.session_state.result_data),suggestion)
            st.success(f"**Suggestion**:{suggestion_text}")
            generate_speech(suggestion_text)
    
    #-----------------------------------------Performance Mode-----------------------------------------------
    elif mode == "Performance Mode":
        st.title("Performance Mode: Unleashing the Power of EVs")
        st.write(
    """
    **BEAM's Performance Mode** delivers the ultimate driving experience by combining high-speed performance with intelligent energy optimization. Powered by the **Proximal Policy Optimization (PPO)** reinforcement learning algorithm, this mode ensures thrilling acceleration without compromising battery health or thermal stability.

    ### Key Features:
    - **Dynamic Power Management:** Adjusts power output in real-time for maximum performance and efficiency.
    - **Smart Cooling System:** Actively monitors and manages thermal conditions to prevent overheating.
    - **Energy Optimization:** Minimizes energy spikes and reduces wastage for smoother performance.
    - **AI-Driven Insights:** Provides real-time notifications about energy trends, thermal conditions, and driving recommendations.

    In **Performance Mode**, drivers experience:
    - Superior acceleration and speed
    - Optimized energy consumption
    - Extended battery lifespan

    Whether you're navigating city streets or hitting the open road, BEAM's Performance Mode ensures a thrilling yet sustainable driving experience, setting a new benchmark for EV performance.
    """
)
        # Reset data lists
        performance_battery_data.clear()
        performance_temperature_data.clear()
        performance_speed_data.clear()
        performance_distance_data.clear()
        performance_time_data.clear()

        # Load PPO model
        try:
            model = PPO.load("ppo_motor_model_dynamic.zip")  # Replace with your model's path
            st.success("PPO Model loaded successfully!")
        except Exception as e:
            st.error(f"Failed to load the PPO model: {e}")
            return

        # Real-time data inputs
        battery = st.number_input("Enter current battery level (%)", min_value=0.0, max_value=100.0, step=1.0, value=100.0)
        temperature = st.number_input("Enter current temperature (°C)", min_value=0.0, max_value=100.0, step=1.0, value=30.0)
        speed = st.number_input("Enter current speed (km/h)", min_value=0.0, max_value=180.0, step=1.0, value=50.0)
        distance = st.number_input("Enter current distance traveled (km)", min_value=0.0, step=1.0, value=0.0)

        # Create environment and reset with inputs
        env = RealTimeMotorEnvironment()
        state = env.reset(battery, temperature, speed, distance)

        # Run Performance Mode simulation
        if st.button("Run Performance Mode"):
            st.session_state.performance_results.clear()
            st.write("### Simulation Results (Performance Mode)")

            graph_placeholder_2=st.empty()


            for cycle in range(1,16):
                # Predict the next action using the PPO model
                action, _ = model.predict(state)
                st.write(f"Predicted Action: {action}")

                # Execute action in the environment
                state, reward, done, _ = env.step(action)

                # Log data for plotting
                performance_battery_data.append(state[0])  # Battery %
                performance_temperature_data.append(state[1])  # Temperature
                performance_speed_data.append(state[2])  # Speed
                performance_distance_data.append(state[3])  # Distance
                performance_time_data.append(cycle)

                # Plot graphs in real-time
                with graph_placeholder_2:
                    fig=plot_performance_graphs()
                    st.pyplot(fig)

                
                st.session_state.performance_results.append(f"Battery: {state[0]},"
                    f"Temperature: {state[1]},"
                    f"Speed: {state[2]},"
                    f"Distance: {state[3]},"
                    f"Action: {action},"
                    f"Reward: {reward},")

                # Display real-time updates
                st.write(f"State: Battery={state[0]:.2f}%, Temperature={state[1]:.2f}°C, Speed={state[2]:.2f} km/h, Distance={state[3]:.2f} km")
                st.write(f"Reward: {reward:.2f}")

                # Real-time action adjustments
                if action == 0:
                    st.write("Action: Decrease speed")
                elif action == 1:
                    st.write("Action: Maintain speed")
                elif action == 2:
                    st.write("Action: Increase speed")
                elif action == 3:
                    st.write("Action: Activate cooling")
                elif action == 4:
                    st.write("Action: Start charging")

                # Stop simulation if done
                if done:
                    if state[0] <= 0:
                        st.warning("Battery exhausted. Ending simulation.")
                    elif state[1] >= env.max_temperature:
                        st.warning("Car stopped due to overheating.")
                    elif state[1] < 15:
                        st.warning("Frozen State")
                        break
                    break
            alert="Give alert in 5 words only"
            suggestion="Give suggestion in 6 words only, don't include numeric data"
            alert_text = generate_alert("\n".join(st.session_state.performance_results),alert)
            st.error(f"**Alert**: {alert_text}")
            generate_speech(alert_text)

            suggestion_text=generate_alert("\n".join(st.session_state.performance_results),suggestion)
            st.success(f"**Suggestion**:{suggestion_text}")
            generate_speech(suggestion_text)

    #---------------------------------------Analysis & Feedback----------------------------------------
    elif mode == "Analysis & Feedback":
        st.title("Analysis and Feedback: Insights for Smarter Driving")
        st.write(
    """
    **BEAM's Analysis and Feedback System** empowers drivers with actionable insights to optimize their electric vehicle's performance and efficiency. By leveraging advanced AI models and real-time data monitoring, BEAM provides comprehensive feedback tailored to your driving habits and vehicle conditions.

    ### Key Features:
    - **Real-Time Performance Metrics:** Track energy consumption, battery health, and thermal stability during your journey.
    - **Driving Recommendations:** Get personalized suggestions to enhance efficiency or boost performance based on your selected mode.
    - **Alerts and Notifications:** Stay informed with mode-specific alerts, such as thermal warnings or energy usage trends.
    - **AI-Powered Insights:** Powered by a fine-tuned LLM, BEAM provides easy-to-understand feedback and actionable guidance.

    ### Benefits:
    - Make informed decisions to maximize battery lifespan and optimize energy usage.
    - Improve your driving habits with data-driven recommendations.
    - Enjoy a seamless and intelligent driving experience with continuous feedback.

    **Discover how BEAM helps you drive smarter and more sustainably, ensuring you get the most out of every journey!**
    """
)
        st.title("Driver Experience Personalization")
        if st.session_state.result_data or st.session_state.performance_results:
            if st.button("Generate Recommendation"):
                
                if st.session_state.result_data and st.session_state.performance_results:
                    st.session_state.result=st.session_state.result_data+st.session_state.performance_results
                elif st.session_state.result_data and not st.session_state.performance_results:
                    st.session_state.result=st.session_state.result_data
                elif st.session_state.performance_results and not st.session_state.result_data:
                    st.session_state.result=st.session_state.performance_results
                recommendation = get_recommendations(st.session_state.result)
                st.subheader("Personalized Recommendation")
                st.write(recommendation)
                alert=f"Give only 4 words alert: {st.session_state.result}"
                alert_text = generate_alert(st.session_state.result,alert)
                if 'critical' not in alert_text.lower() and 'low' not in alert_text.lower() and 'overheat' not in alert_text.lower() and 'high' not in alert_text.lower() and 'fall' not in alert_text.lower() and 'falling' not in alert_text.lower() and 'drop' not in alert_text.lower() and 'dropping' not in alert_text.lower():
                    st.success("System operating normally.")
                else:
                    st.error("System alert: "+alert_text)
                generate_speech(alert_text)

                
        else:
            st.warning("No Data Available")


#-----------------------------------------Run the app--------------------------------------------------

if __name__ == "__main__":
    # Initialize the data lists
    battery_percent_data = []
    temperature_data = []
    charge_rate_data = []
    discharge_rate_data = []
    time_data = []

    main()

#--------------------------------------------End-------------------------------------------