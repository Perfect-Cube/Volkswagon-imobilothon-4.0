import streamlit as st
import random
import time
import matplotlib.pyplot as plt
import numpy as np

# Initialize battery pack with 8 cells, each with a charge level between 80-100% and temperature
battery_pack = [{"charge": random.uniform(80, 100), "temp": random.uniform(25, 35)} for _ in range(8)]
min_charge = 20         # Minimum charge threshold to force resting
base_charge_rate = 5    # Base rate at which resting cells are charged per cycle
base_discharge_rate = 10  # Base rate at which active cells are discharged per cycle
overload_threshold = 30  # Maximum total discharge rate to avoid overload
temp_increase_rate = 2   # Temperature increase per cycle for active cells
temp_cooling_rate = 1    # Temperature decrease per cycle for resting cells
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

def get_user_input():
    # Get battery percentage as a number input (between 80 and 100)
    battery_percent = st.slider("Enter Battery Percentage", min_value=80, max_value=100, value=90)
    
    # Get battery temperature as a number input (between 25 and 45 degrees Celsius)
    battery_temp = st.slider("Enter Battery Temperature (°C)", min_value=25, max_value=45, value=30)
    
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

def display_battery_status(cycle_distance, condition):
    """Print the battery status, temperature, and distance covered in the current cycle."""
    status = " | ".join(f"Cell {i+1}: {battery_pack[i]['charge']:.1f}%, {battery_pack[i]['temp']:.1f}°C"
                        for i in range(8))
    st.write(f"[Battery Status] {status}")
    st.write(f"[Condition: {condition.capitalize()}] Distance Covered: {cycle_distance:.2f} km")

def feedback_system(cycle_distance, discharge_rate, charge_rate, max_active_cells, condition):
    """Evaluate system performance and provide feedback, adjusting discharge/recharge rates based on speed."""
    feedback = []

    # Adjust discharge and charge rates based on speed (driving condition)
    if condition in ['highway', 'uphill']:
        discharge_rate *= 1.2  # Increase discharge rate for faster speeds
        charge_rate *= 0.7     # Decrease recharge rate for faster speeds
        feedback.append(f"Speed: {condition.capitalize()} | Increased discharge rate to {discharge_rate:.2f} and decreased recharge rate to {charge_rate:.2f}.")
    else:
        discharge_rate *= 0.8  # Lower discharge rate for city conditions
        charge_rate *= 1.2     # Increase recharge rate for city conditions
        feedback.append(f"Speed: {condition.capitalize()} | Decreased discharge rate to {discharge_rate:.2f} and increased recharge rate to {charge_rate:.2f}.")

    # Charge feedback: If any cell's charge drops below the threshold, provide feedback to adjust
    for i in range(len(battery_pack)):
        if battery_pack[i]["charge"] < min_charge:
            feedback.append(f"Warning: Cell {i+1} charge below {min_charge}%")

    # Temperature feedback: If any cell overheats, reduce active cells
    for i in range(len(battery_pack)):
        if battery_pack[i]["temp"] > overheat_temp:
            feedback.append(f"Warning: Cell {i+1} temperature above {overheat_temp}°C")

    # Performance feedback: If distance covered is less than target, reduce discharge rate
    if cycle_distance < target_distance:
        feedback.append(f"Performance: Distance covered ({cycle_distance:.2f} km) is below target.")
        # Suggest reducing discharge rate for better balance
        discharge_rate *= 0.8
        feedback.append(f"Suggestion: Reducing discharge rate to {discharge_rate:.2f} for next cycle.")

    # Overload feedback: If overload happens, suggest reducing active cells
    if discharge_rate * max_active_cells > overload_threshold:
        max_active_cells = max(1, int(overload_threshold // discharge_rate))
        feedback.append(f"Warning: Overload detected. Reducing active cells to {max_active_cells} due to high load.")

    return feedback, discharge_rate, charge_rate, max_active_cells

def check_average_battery_level():
    """Calculate and check the average battery level across all cells."""
    total_charge = sum(cell["charge"] for cell in battery_pack)
    avg_battery_level = total_charge / len(battery_pack)
    return avg_battery_level

def charging_alert(avg_battery_level):
    """Alert for charging if average battery level is below 25%."""
    if avg_battery_level < 25:
        st.write("[ALERT] Battery level below 25%! Head to the nearest charging station.")

# Simulation graph data
battery_percent_data = []
temperature_data = []
charge_rate_data = []
discharge_rate_data = []
time_data = []

def plot_graphs():
    # Plot Battery Percent, Temperature, Charge and Discharge Rate in real-time
    fig, ax1 = plt.subplots(figsize=(10, 6))
    
    ax1.set_xlabel('Cycle')
    ax1.set_ylabel('Battery % and Temperature (°C)', color='tab:blue')
    ax1.plot(time_data, battery_percent_data, color='tab:blue', label="Battery %")
    ax1.plot(time_data, temperature_data, color='tab:green', label="Temperature (°C)")
    ax1.tick_params(axis='y', labelcolor='tab:blue')
    
    ax2 = ax1.twinx()
    ax2.set_ylabel('Charge/Discharge Rate', color='tab:red')
    ax2.plot(time_data, charge_rate_data, color='tab:red', label="Charge Rate")
    ax2.plot(time_data, discharge_rate_data, color='tab:orange', label="Discharge Rate")
    ax2.tick_params(axis='y', labelcolor='tab:red')

    fig.tight_layout()
    st.pyplot(fig)

def main():
    st.title("Battery Efficiency and AI Motor Optimization")

    # Get the user input
    battery_percent, battery_temp, driving_condition, charge_rate, input_data = get_user_input()

    # Display input data
    st.write("Input Data:")
    for item in input_data:
        st.write(item)

    # Run the simulation when the "Run Simulation" button is clicked
    if st.button("Run Simulation"):
        # Store initial values
        wave_index = 0
        total_distance = 0
        max_active_cells = 4
        st.write("\nStarting Simulation...")

        for cycle in range(1, 11):  # Run for 10 cycles
            st.write(f"\n[Cycle {cycle}]")

            # Get the cycle's distance and discharge rate based on driving condition
            cycle_distance, discharge_rate = get_cycle_distance(driving_condition)
            total_distance += cycle_distance

            display_battery_status(cycle_distance, driving_condition)

            # Determine active and resting groups using wave rotation
            active_group, resting_group = rotate_groups(wave_index, max_active_cells)
            st.write(f"Selected Active Group: {[i+1 for i in active_group]}")
            st.write(f"Selected Resting Group: {[i+1 for i in resting_group]}")

            # Discharge active group and charge resting group
            discharge_group(active_group, discharge_rate)
            charge_group(resting_group, charge_rate)

            # Feedback
            feedback, discharge_rate, charge_rate, max_active_cells = feedback_system(cycle_distance, discharge_rate, charge_rate, max_active_cells, driving_condition)
            for msg in feedback:
                st.write(f"[Feedback] {msg}")

            # Store data for graphing
            avg_battery_level = check_average_battery_level()
            battery_percent_data.append(avg_battery_level)
            temperature_data.append(np.mean([cell["temp"] for cell in battery_pack]))
            charge_rate_data.append(charge_rate)
            discharge_rate_data.append(discharge_rate)
            time_data.append(cycle)

            charging_alert(avg_battery_level)

            # Increment wave index for the next cycle to shift the group pattern
            wave_index += 1

            # Short delay to simulate real-time processing
            time.sleep(1)

        # Plot the graphs after the simulation
        plot_graphs()

        st.write("\n[Final Battery Status and Total Distance]")
        display_battery_status(0, "Final")
        st.write(f"Total Distance Covered: {total_distance:.2f} km")

if __name__ == "__main__":
    main()
