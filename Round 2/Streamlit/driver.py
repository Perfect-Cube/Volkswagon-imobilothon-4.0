import openai
import streamlit as st


from groq import Groq
api_keyy="key"

client=Groq(api_key=api_keyy)
# Simulated Driver Data
driver_data = {
    "name": "Alex",
    "driving_mode": "Sport",
    "acceleration_pattern": "aggressive",
    "average_speed": 75,  # mph
    "ac_usage": "high",
    "recent_routes": ["urban", "highway"]
}

# Function to get LLM recommendations based on driver data
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

    Based on this data, provide a recommendation on improving comfort and battery efficiency.
    """
    
    response = client.chat.completions.create(
    model="llama3-8b-8192",  # or "gpt-4" if you have access
    messages=[
        {"role": "system", "content": "You are an AI log analysis assistant."},
        {"role": "user", "content": prompt}
    ],
    max_tokens=250
    )
    
    
    return response.choices[0].message.content

# Get LLM recommendations
recommendation = get_recommendations(driver_data)

# Streamlit Dashboard
st.title("Driver Experience Personalization")

# Display Driver Profile Information
st.subheader("Driver Profile")
st.write("**Name:**", driver_data["name"])
st.write("**Preferred Driving Mode:**", driver_data["driving_mode"])
st.write("**Acceleration Pattern:**", driver_data["acceleration_pattern"])
st.write("**Average Speed:**", driver_data["average_speed"], "mph")
st.write("**AC Usage:**", driver_data["ac_usage"])

# Display Recommendation from LLM
st.subheader("Personalized Recommendation")
st.write(recommendation)

# Mode Toggle (Driver can switch modes)
st.subheader("Adjust Driving Mode")
mode = st.radio(
    "Select Driving Mode",
    ("Eco", "Comfort", "Sport"),
    index=["Eco", "Comfort", "Sport"].index(driver_data["driving_mode"])
)
st.write(f"Current Mode: {mode}")

# AC Settings
st.subheader("AC Settings")
ac_usage = st.slider("Adjust AC Level", 0, 100, 75 if driver_data["ac_usage"] == "high" else 25)
st.write("AC Usage:", ac_usage, "%")

# Battery Efficiency Tips
if mode == "Eco":
    st.write("Switching to Eco Mode could save approximately 10% battery.")

# Finalize and update the profile
if st.button("Update Preferences"):
    driver_data["driving_mode"] = mode
    driver_data["ac_usage"] = "high" if ac_usage > 50 else "low"
    st.write("Preferences updated!")

# Display updated driver profile
st.subheader("Updated Driver Profile")
st.json(driver_data)
