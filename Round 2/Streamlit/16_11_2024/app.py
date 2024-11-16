import streamlit as st

# Function to handle redirection based on the selected mode
def show_page(page_name):
    if page_name == "Eco":
        st.title("Eco Mode")
        st.write("You are now in Eco mode.")
        # Add any content related to Eco mode here.
    elif page_name == "Performance":
        st.title("Performance Mode")
        st.write("You are now in Performance mode.")
        # Add any content related to Performance mode here.
    elif page_name == "Analysis":
        st.title("Analysis Mode")
        st.write("You are now in Analysis mode.")
        # Add any content related to Analysis mode here.
    else:
        st.title("Welcome to BEAM: Battery Efficiency and AI Motor Optimization")
        st.write(
            """
            **BEAM (Battery Efficiency and AI Motor Optimization)** is a cutting-edge platform designed to optimize 
            the performance and energy efficiency of electric vehicles. Through the use of artificial intelligence 
            and advanced motor algorithms, BEAM helps in:
            
            - Maximizing battery life and efficiency.
            - Enhancing motor performance.
            - Providing deep analysis and diagnostics for optimization.
            
            Choose a mode to explore more:
            - **Eco Mode**: Focuses on energy conservation and battery optimization.
            - **Performance Mode**: Maximizes motor performance for an enhanced driving experience.
            - **Analysis Mode**: Offers insights and detailed analysis of motor and battery performance.
            """
        )

# Main app layout
def main():
    # Set page config to remove side navigation bar and set layout to wide
    st.set_page_config(page_title="BEAM: Battery Efficiency and AI Motor Optimization", layout="wide")

    st.title("BEAM: Battery Efficiency and AI Motor Optimization")

    # Dropdown menu at the center
    mode = st.selectbox(
        "Select Mode",
        ["Select", "Eco", "Performance", "Analysis"],
        index=0
    )

    # Show project description if no mode is selected, else redirect to the selected page
    show_page(mode)

if __name__ == "__main__":
    main()
