import random
import time

class BatterySection:
    def __init__(self, section_id, capacity, health=100, temperature=25):
        self.section_id = section_id
        self.capacity = capacity  # Max capacity of the section in units
        self.charge = 0  # Current charge level
        self.health = health  # Health level (0-100)
        self.temperature = temperature  # Temperature in degrees Celsius
        self.overload_threshold = capacity * 0.8  # Threshold for overload condition

    def charge_section(self, amount):
        if self.charge + amount <= self.capacity and self.temperature < 45:
            self.charge += amount
            self.temperature += 0.2 * amount  # Increase temperature with charging
            return True
        return False

    def discharge_section(self, amount):
        if self.charge >= amount:
            self.charge -= amount
            self.temperature -= 0.1 * amount  # Decrease temperature with discharging
            return True
        return False

    def needs_charge(self):
        # A section needs charge if below 50% capacity and health is stable
        return self.charge < (self.capacity * 0.5) and self.health > 50

    def check_overload(self):
        # Avoids charging/discharging if temperature is too high
        return self.temperature > 40 or self.charge > self.overload_threshold

class SidewinderBatteryOptimizer:
    def __init__(self, sections):
        self.sections = sections  # List of BatterySection objects

    def adaptive_charging(self, total_energy):
        # Distribute energy using a priority-based adaptive approach
        print("\nAdaptive Charging Initiated:")
        for section in sorted(self.sections, key=lambda x: x.charge):
            if section.needs_charge() and not section.check_overload() and total_energy > 0:
                energy_to_charge = min(section.capacity - section.charge, total_energy)
                if section.charge_section(energy_to_charge):
                    total_energy -= energy_to_charge
                    print(f"  Charging Section {section.section_id} by {energy_to_charge} units (Temp: {section.temperature:.1f}°C)")

    def sectional_balancing_discharge(self, demand):
        # Discharge sections in a balanced manner, avoiding overloaded sections
        print("\nSectional Balancing for Discharge:")
        for section in sorted(self.sections, key=lambda x: -x.charge):
            if section.charge > 0 and demand > 0 and not section.check_overload():
                energy_to_discharge = min(section.charge, demand)
                if section.discharge_section(energy_to_discharge):
                    demand -= energy_to_discharge
                    print(f"  Discharging Section {section.section_id} by {energy_to_discharge} units (Temp: {section.temperature:.1f}°C)")

    def manage_section_health(self):
        # Adjust usage based on health; reduce load if health is low
        print("\nHealth Monitoring and Maintenance:")
        for section in self.sections:
            if section.health < 60:
                print(f"  Section {section.section_id} has low health ({section.health}%), reducing capacity for safety.")
                section.capacity *= 0.9  # Reduce capacity to avoid further degradation
            # Simulate gradual health degradation with use
            section.health -= random.uniform(0.1, 0.3) if section.charge > 0 else 0

    def simulate_drive(self, distance):
        # Simulate energy consumption based on distance driven
        consumption_rate = 5  # Energy units per km
        total_demand = distance * consumption_rate
        print(f"\n--- Driving Simulation ---\nDriving {distance} km requires {total_demand} energy units.")
        
        # Perform discharge with sectional balancing
        self.sectional_balancing_discharge(total_demand)

    def run_cycle(self, charge_amount, drive_distance):
        print("\n=== New Optimization Cycle ===")
        # Adaptive charging step
        self.adaptive_charging(charge_amount)
        # Driving simulation to consume energy
        self.simulate_drive(drive_distance)
        # Health monitoring and adjustment step
        self.manage_section_health()

        # Display status of each section
        for section in self.sections:
            print(f"Section {section.section_id}: Charge = {section.charge}, Health = {section.health:.2f}%, Temp = {section.temperature:.1f}°C")

# Sample battery sections
sections = [BatterySection(section_id=i, capacity=100) for i in range(5)]
optimizer = SidewinderBatteryOptimizer(sections)

# Simulate optimization cycles with charging and driving
for cycle in range(3):
    charge_amount = random.randint(50, 150)
    drive_distance = random.randint(20, 60)  # Random distance in km for each cycle
    optimizer.run_cycle(charge_amount, drive_distance)
    time.sleep(1)  # Optional delay for readability in simulation output
