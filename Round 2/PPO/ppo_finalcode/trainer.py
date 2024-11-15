import numpy as np
import gym
from stable_baselines3 import PPO
from gym import spaces

# Define a custom environment for motor optimization with dynamic parameters
class MotorEnvironment(gym.Env):
    def __init__(self):
        super(MotorEnvironment, self).__init__()
        
        # Initialize parameters with ranges for variability
        self.battery = np.random.uniform(80, 100)  # Initial battery level (percentage)
        self.temperature = np.random.uniform(25, 35)  # Initial temperature (°C)
        self.speed = np.random.uniform(30, 50)  # Initial speed (km/h)
        self.distance = 0  # Initial distance traveled (km)
        self.max_speed = 80  # Maximum motor speed (km/h)
        self.max_temperature = 50  # Maximum allowable temperature (°C)
        self.min_temperature = 20  # Minimum temperature to maintain
        self.charging_rate = 5  # Battery charging rate per step
        self.temperature_rise_factor = np.random.uniform(0.03, 0.07)  # Temperature sensitivity to speed
        self.battery_degradation_factor = np.random.uniform(0.01, 0.03)  # Battery consumption per unit speed

        # Action space: 0 = decrease speed, 1 = maintain speed, 2 = increase speed, 3 = activate cooling, 4 = charge
        self.action_space = spaces.Discrete(5)
        
        # Observation space: battery level, temperature, speed, distance
        self.observation_space = spaces.Box(
            low=np.array([0, 0, 0, 0]),
            high=np.array([100, self.max_temperature, self.max_speed, np.inf]),
            dtype=np.float32
        )
    
    def reset(self):
        # Reset environment to randomized initial conditions
        self.battery = np.random.uniform(80, 100)
        self.temperature = np.random.uniform(25, 35)
        self.speed = np.random.uniform(30, 50)
        self.distance = 0
        return np.array([self.battery, self.temperature, self.speed, self.distance])
    
    def step(self, action):
        # Apply action
        if action == 0:  # Decrease speed
            self.speed -= 5
        elif action == 2:  # Increase speed
            self.speed += 5
        elif action == 3:  # Activate cooling
            self.temperature -= 3
        elif action == 4:  # Charge battery
            self.battery += self.charging_rate
        
        # Ensure speed and battery stay within limits
        self.speed = np.clip(self.speed, 20, self.max_speed)
        self.battery = np.clip(self.battery, 0, 100)
        
        # Update dynamics
        if action != 4:  # Battery and temperature update only when not charging
            self.temperature += self.temperature_rise_factor * self.speed
            battery_consumption = self.battery_degradation_factor * self.speed
            self.battery -= battery_consumption
        
        self.distance += self.speed / 60  # Update distance (convert speed from km/h to km/min)
        
        # Calculate reward
        reward = -self.battery_degradation_factor * self.speed  # Penalize battery usage
        if self.temperature > 40:
            reward -= 1  # Penalty for high temperature
        if self.temperature >= self.max_temperature:
            reward -= 5  # Strong penalty for overheating
        if action == 3 and self.temperature > 35:
            reward += 3  # Reward for cooling when needed
        if action == 4 and self.battery < 50:
            reward += 5  # Reward for charging when battery is low
        
        # Episode termination
        done = False
        if self.battery <= 0:  # Battery depleted
            done = True
            reward -= 10
        elif self.temperature >= self.max_temperature:  # Overheating
            self.speed = 0  # Stop the motor
            done = True
            reward -= 10
        
        # Return new state, reward, done flag, and info dictionary
        return np.array([self.battery, self.temperature, self.speed, self.distance]), reward, done, {}

# Create the environment
env = MotorEnvironment()

# Initialize PPO model with the environment
model = PPO("MlpPolicy", env, verbose=1)

# Train the PPO model
model.learn(total_timesteps=20000)

# Save the trained model
model.save("ppo_motor_model_dynamic")

# Simulate the trained model
state = env.reset()

print("Simulation results with dynamic parameters:")
for i in range(100):
    action, _states = model.predict(state)  # Predict the next action
    state, reward, done, _ = env.step(action)  # Step the environment with the chosen action
    
    # Print the current state and reward for logging purposes
    print(f"Step {i + 1}:")
    print(f"  State: Battery={state[0]:.2f}, Temperature={state[1]:.2f}, Speed={state[2]:.2f}, Distance={state[3]:.2f} km")
    print(f"  Reward: {reward:.2f}")
    
    if done:
        if state[0] <= 0:
            print("Battery exhausted. Episode ended.")
        elif state[1] >= env.max_temperature:
            print("Overheating. Car stopped. Episode ended.")
        break
