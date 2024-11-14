from groq import Groq
import torch
import soundfile as sf
import streamlit as st
from transformers import SpeechT5Processor, SpeechT5ForTextToSpeech, SpeechT5HifiGan
from datasets import load_dataset

# Set OpenAI API key
api_keyy="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"
client=Groq(api_key=api_keyy)
# Load Text-to-Speech models
processor = SpeechT5Processor.from_pretrained("microsoft/speecht5_tts")
model = SpeechT5ForTextToSpeech.from_pretrained("microsoft/speecht5_tts")
vocoder = SpeechT5HifiGan.from_pretrained("microsoft/speecht5_hifigan")

# Load xvector for a generic speaker voice
embeddings_dataset = load_dataset("Matthijs/cmu-arctic-xvectors", split="validation")
speaker_embeddings = torch.tensor(embeddings_dataset[7306]["xvector"]).unsqueeze(0)

# Function to get recommendations from LLM
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
    max_tokens=400
    )
    
    return response.choices[0].message.content

# Function to generate alert text using GPT summarization
def generate_alert(recommendation):
    # Prompt GPT to create a concise alert message based on the recommendation
    alert_prompt = f"only in 4 words give alert type{recommendation}"
    
    response = client.chat.completions.create(
    model="llama3-8b-8192",  # or "gpt-4" if you have access
    messages=[
        {"role": "system", "content": "You are an AI log analysis assistant."},
        {"role": "user", "content": alert_prompt}
    ],
    max_tokens=400
    )
    
    return response.choices[0].message.content

# Streamlit UI
st.title("Driver Experience Personalization")

# Input fields for driver data
st.sidebar.header("Driver Profile")
name = st.sidebar.text_input("Driver's Name", "Alex")
driving_mode = st.sidebar.selectbox("Preferred Driving Mode", ["Eco", "Comfort", "Sport"], index=2)
acceleration_pattern = st.sidebar.selectbox("Acceleration Pattern", ["smooth", "moderate", "aggressive"], index=2)
average_speed = st.sidebar.slider("Average Speed (mph)", 0, 120, 75)
ac_usage = st.sidebar.selectbox("AC Usage", ["low", "moderate", "high"], index=2)
recent_routes = st.sidebar.multiselect("Recent Routes", ["urban", "highway", "rural", "mountain"], ["urban", "highway"])

# Compile driver data
driver_data = {
    "name": name,
    "driving_mode": driving_mode,
    "acceleration_pattern": acceleration_pattern,
    "average_speed": average_speed,
    "ac_usage": ac_usage,
    "recent_routes": recent_routes
}

# Button to get recommendation
if st.button("Generate Recommendation"):
    # Get recommendation from the LLM
    recommendation = get_recommendations(driver_data)
    st.subheader("Personalized Recommendation")
    st.write(recommendation)

    # Generate an alert/notification text using GPT
    alert_text = generate_alert(recommendation)
    st.success(alert_text)

    # Use the alert text for TTS
    inputs = processor(text=" ".join(alert_text.split('\n')[:2]), return_tensors="pt")
    
    try:
        # Generate speech for the alert text
        speech = model.generate_speech(inputs["input_ids"], speaker_embeddings, vocoder=vocoder)

        # Save and play the generated audio
        audio_path = "alert_speech.wav"
        sf.write(audio_path, speech.numpy(), samplerate=16000)
        
        # Autoplay the audio as soon as it's generated (when no button is pressed)
        st.audio(audio_path, format="audio/wav", autoplay=True)

        # Optional: Allow the user to manually play the audio
        st.button("Play Audio", on_click=lambda: st.audio(audio_path, format="audio/wav"))

    except RuntimeError as e:
        st.error(f"Error generating speech: {e}")
