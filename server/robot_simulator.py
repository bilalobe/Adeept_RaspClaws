#!/usr/bin/env python3
import numpy as np


class RobotSimulator:
    """Simulates robot behavior for testing without hardware"""

    def __init__(self):
        self.position = np.array([0., 0., 0.])  # x, y, z
        self.velocity = np.array([0., 0., 0.])
        self.acceleration = np.array([0., 0., 0.])
        self.time = 0.0
        self.dt = 0.01  # 10ms simulation timestep

        # Simulated sensor noise parameters
        self.accel_noise_std = 0.1
        self.position_noise_std = 0.05

    def add_noise(self, value, noise_std):
        """Add Gaussian noise to a value"""
        return value + np.random.normal(0, noise_std)

    def update(self):
        """Update simulation state"""
        self.velocity += self.acceleration * self.dt
        self.position += self.velocity * self.dt
        self.time += self.dt

        # Add gravity
        self.acceleration[2] = -9.81  # m/s^2

    def simulate_hop(self, launch_force=5.0, duration=1.0):
        """Simulate a hopping motion"""
        results = []

        # Reset state
        self.position = np.array([0., 0., 0.])
        self.velocity = np.array([0., 0., 0.])

        # Initial launch
        self.acceleration[2] = launch_force

        # Simulate motion
        while self.time < duration:
            self.update()

            # Get noisy sensor readings
            accel_reading = self.add_noise(self.acceleration, self.accel_noise_std)
            pos_reading = self.add_noise(self.position, self.position_noise_std)

            results.append({
                'time': self.time,
                'true_position': self.position.copy(),
                'measured_position': pos_reading,
                'true_acceleration': self.acceleration.copy(),
                'measured_acceleration': accel_reading,
            })

        return results

    def simulate_balance_disturbance(self, duration=2.0, disturbance_magnitude=1.0):
        """Simulate balance disturbances and recovery"""
        results = []

        # Reset state
        self.position = np.array([0., 0., 0.])
        self.velocity = np.array([0., 0., 0.])
        self.time = 0.0

        while self.time < duration:
            # Add random disturbance forces
            if 0.5 < self.time < 1.0:  # Disturbance period
                self.acceleration[0] = disturbance_magnitude * np.sin(2 * np.pi * self.time)
                self.acceleration[1] = disturbance_magnitude * np.cos(2 * np.pi * self.time)
            else:
                self.acceleration[0] = 0.0
                self.acceleration[1] = 0.0

            self.update()

            # Get noisy sensor readings
            accel_reading = self.add_noise(self.acceleration, self.accel_noise_std)
            pos_reading = self.add_noise(self.position, self.position_noise_std)

            results.append({
                'time': self.time,
                'true_position': self.position.copy(),
                'measured_position': pos_reading,
                'true_acceleration': self.acceleration.copy(),
                'measured_acceleration': accel_reading,
            })

        return results
