import random
import time

class BatterySection:
    def __init__(self, section_id, capacity, health=100, temperature=25):
        self.section_id = section_id
        self.capacity = capacity
        self.charge = 0
        self.health = health
        self.temperature = temperature
        self.overload_threshold = capacity * 0.8

    def charge_section(self, amount):
        if self.charge + amount <= self.capacity and self.temperature < 45:
            self.charge += amount
            self.temperature += 0.2 * amount
            return True
        return False

    def discharge_section(self, amount):
        if self.charge >= amount:
            self.charge -= amount
            self.temperature -= 0.1 * amount
            return True
        return False

    def needs_charge(self):
        return self.charge < (self.capacity * 0.5) and self.health > 50

    def check_overload(self):
        return self.temperature > 40 or self.charge > self.overload_threshold

class NonSidewinderOptimizer:
    def __init__(self, sections):
        self.sections = sections

    def simple_charging(self, total_energy):
        print("\nNon-Sidewinder Charging:")
        for section in self.sections:
            if total_energy > 0:
                energy_to_charge = min(section.capacity - section.charge, total_energy)
                if section.charge_section(energy_to_charge):
                    total_energy -= energy_to_charge
                    print(f"  Charging Section {section.section_id} by {energy_to_charge} units")

    def simple_discharge(self, demand):
        print("\nNon-Sidewinder Discharge:")
        for section in self.sections:
            if demand > 0:
                energy_to_discharge = min(section.charge, demand)
                if section.discharge_section(energy_to_discharge):
                    demand -= energy_to_discharge
                    print(f"  Discharging Section {section.section_id} by {energy_to_discharge} units")

    def run_cycle(self, charge_amount, drive_distance):
        consumption_rate = 5
        total_demand = drive_distance * consumption_rate
        self.simple_charging(charge_amount)
        self.simple_discharge(total_demand)
        for section in self.sections:
            print(f"Section {section.section_id}: Charge = {section.charge}, Health = {section.health:.2f}%, Temp = {section.temperature:.1f}°C")

class SidewinderOptimizer:
    def __init__(self, sections):
        self.sections = sections

    def adaptive_charging(self, total_energy):
        print("\nSidewinder Adaptive Charging:")
        for section in sorted(self.sections, key=lambda x: x.charge):
            if section.needs_charge() and not section.check_overload() and total_energy > 0:
                energy_to_charge = min(section.capacity - section.charge, total_energy)
                if section.charge_section(energy_to_charge):
                    total_energy -= energy_to_charge
                    print(f"  Charging Section {section.section_id} by {energy_to_charge} units (Temp: {section.temperature:.1f}°C)")

    def sectional_balancing_discharge(self, demand):
        print("\nSidewinder Sectional Balancing for Discharge:")
        for section in sorted(self.sections, key=lambda x: -x.charge):
            if section.charge > 0 and demand > 0 and not section.check_overload():
                energy_to_discharge = min(section.charge, demand)
                if section.discharge_section(energy_to_discharge):
                    demand -= energy_to_discharge
                    print(f"  Discharging Section {section.section_id} by {energy_to_discharge} units (Temp: {section.temperature:.1f}°C)")

    def manage_section_health(self):
        print("\nHealth Monitoring and Maintenance:")
        for section in self.sections:
            if section.health < 60:
                print(f"  Section {section.section_id} has low health ({section.health}%), reducing capacity for safety.")
                section.capacity *= 0.9
            section.health -= random.uniform(0.1, 0.3) if section.charge > 0 else 0

    def simulate_drive(self, distance):
        consumption_rate = 5
        total_demand = distance * consumption_rate
        self.sectional_balancing_discharge(total_demand)

    def run_cycle(self, charge_amount, drive_distance):
        print("\n=== Sidewinder Optimization Cycle ===")
        self.adaptive_charging(charge_amount)
        self.simulate_drive(drive_distance)
        self.manage_section_health()
        for section in self.sections:
            print(f"Section {section.section_id}: Charge = {section.charge}, Health = {section.health:.2f}%, Temp = {section.temperature:.1f}°C")

# Initialize battery sections
sections = [BatterySection(section_id=i, capacity=100) for i in range(5)]
sections_copy = [BatterySection(section_id=i, capacity=100) for i in range(5)]

# Initialize optimizers
non_sidewinder_optimizer = NonSidewinderOptimizer(sections)
sidewinder_optimizer = SidewinderOptimizer(sections_copy)

# Run simulation for both optimizers
print("===== Non-Sidewinder Optimization =====")
for cycle in range(3):
    print(f"\nCycle {cycle + 1}")
    charge_amount = random.randint(50, 150)
    drive_distance = random.randint(20, 60)
    non_sidewinder_optimizer.run_cycle(charge_amount, drive_distance)
    time.sleep(1)

print("\n\n===== Sidewinder Optimization =====")
for cycle in range(3):
    print(f"\nCycle {cycle + 1}")
    charge_amount = random.randint(50, 150)
    drive_distance = random.randint(20, 60)
    sidewinder_optimizer.run_cycle(charge_amount, drive_distance)
    time.sleep(1)
