import numpy as np
import gym
from stable_baselines3 import PPO

# Custom environment for real-time use
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
        if action != 4:# Normal operation, not charging
            if action!=3: 
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

# Load the trained model
model = PPO.load("/content/ppo_motor_model_dynamic.zip")  # Replace with your model's saved filename

# Create the environment
env = RealTimeMotorEnvironment()

# Real-time loop
while True:
    # Get real-time data (replace with actual sensor/API inputs)
    real_time_battery = float(input("Enter current battery level (%): "))
    real_time_temperature = float(input("Enter current temperature (°C): "))
    real_time_speed = float(input("Enter current speed (km/h): "))
    real_time_distance = float(input("Enter current distance traveled (km): "))
    
    # Reset environment with real-time data
    state = env.reset(real_time_battery, real_time_temperature, real_time_speed, real_time_distance)
    
    while True:
        # Predict the next action
        action, _ = model.predict(state)
        print(f"Predicted Action: {action}")
        
        # Execute action in the environment
        state, reward, done, _ = env.step(action)
        if state[1]<0:
          print("Frozen state")
          break
        # Log results
        print(f"State: Battery={state[0]:.2f}, Temperature={state[1]:.2f}, Speed={state[2]:.2f}, Distance={state[3]:.2f}")
        print(f"Reward: {reward:.2f}")
        
        # Implement real-world system adjustments (example output)
        if action == 0:
            print("Action: Decrease speed")
        elif action == 1:
            print("Action: Maintain speed")
        elif action == 2:
            print("Action: Increase speed")
        elif action == 3:
            print("Action: Activate cooling")
        elif action == 4:
            print("Action: Start charging")
        
        # Check for end of episode
        if done:
            if state[0] <= 0:
                print("Battery exhausted. Ending simulation.")
            elif state[1] >= env.max_temperature:
                print("Car stopped due to overheating.")
            break
