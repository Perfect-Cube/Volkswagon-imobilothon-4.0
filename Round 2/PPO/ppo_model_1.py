import numpy as np
import gym
from stable_baselines3 import PPO
from gym import spaces

# Define a custom environment for motor optimization with temperature control
class MotorEnvironment(gym.Env):
    def __init__(self):
        super(MotorEnvironment, self).__init__()
        
        # Initial conditions for battery, temperature, speed, and distance
        self.battery = 100  # Initial battery level (percentage)
        self.temperature = 30  # Initial temperature (in Celsius)
        self.speed = 50  # Initial speed (km/h)
        self.distance = 0  # Initial distance traveled (km)
        self.max_speed = 80  # Maximum motor speed (km/h)
        self.max_temperature = 50  # Maximum allowable temperature (°C)
        self.min_temperature = 30  # Minimum temperature to maintain
        
        # Define action space: 0 = decrease speed, 1 = maintain speed, 2 = increase speed, 3 = activate cooling
        self.action_space = spaces.Discrete(4)
        
        # Define observation space: battery level, temperature, speed, distance
        self.observation_space = spaces.Box(low=np.array([0, 0, 0, 0]), 
                                             high=np.array([100, self.max_temperature, self.max_speed, np.inf]), 
                                             dtype=np.float32)
    
    def reset(self):
        # Reset environment to initial conditions and return the initial state
        self.battery = 100
        self.temperature = 30
        self.speed = 50
        self.distance = 0
        return np.array([self.battery, self.temperature, self.speed, self.distance])
    
    def step(self, action):
        # Apply action: modify motor speed or activate cooling
        if action == 0:
            self.speed -= 5  # Decrease speed
        elif action == 2:
            self.speed += 5  # Increase speed
        elif action == 3:
            self.temperature -= 2  # Activate cooling and reduce temperature
        
        # Ensure speed stays within defined limits
        self.speed = np.clip(self.speed, 20, self.max_speed)
        
        # Update temperature and battery consumption based on speed
        self.temperature += 0.05 * self.speed  # Temperature increases with speed
        battery_consumption = 0.02 * self.speed  # Battery consumption depends on speed
        self.battery -= battery_consumption  # Decrease battery
        
        # Update distance based on speed (assume 1 time step = 1 hour)
        self.distance += self.speed / 60  # Convert speed from km/h to km/min
        
        # Ensure the temperature does not exceed the max temperature
        if self.temperature > self.max_temperature:
            self.temperature = self.max_temperature
        
        # If battery is empty, end the episode
        done = self.battery <= 0
        
        # Reward function: Penalize for battery consumption, penalize more for high temperature, reward for lowering temperature
        reward = -battery_consumption
        if self.temperature > 40:
            reward -= 1  # Strong penalty if temperature is high
        if self.temperature >= self.max_temperature:
            reward -= 5  # Strong penalty for exceeding max temperature
        if self.temperature < self.min_temperature:
            reward += 1  # Reward for maintaining temperature below a certain threshold
        
        # Return new state, reward, done (episode end), and additional info (not used here)
        return np.array([self.battery, self.temperature, self.speed, self.distance]), reward, done, {}

# Create the environment
env = MotorEnvironment()

# Initialize PPO model with the environment
model = PPO("MlpPolicy", env, verbose=1)

# Train the PPO model on the environment
model.learn(total_timesteps=10000)

model.save("ppo_motor_model")
# Simulate the trained PPO model
state = env.reset()

# Run for a fixed number of time steps (e.g., 100 steps)
for i in range(100):
    action, _states = model.predict(state)  # Use the PPO model to predict the next action
    state, reward, done, _ = env.step(action)  # Step the environment with the chosen action
    
    # Print the current state and reward for logging purposes
    print(f"Step {i + 1}:")
    print(f"  State: Battery={state[0]:.2f}, Temperature={state[1]:.2f}, Speed={state[2]:.2f}, Distance={state[3]:.2f} km")
    print(f"  Reward: {reward:.2f}")
    
    if done:
        print("Episode finished. Battery exhausted.")
        break
