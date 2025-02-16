#!/usr/bin/env python3
import unittest
from typing import List, Tuple

import matplotlib.pyplot as plt
import numpy as np

from initialization import kalman_filter_X
from test_config import TEST_SCENARIOS


def generate_scenario_data(scenario_name: str) -> Tuple[List[float], List[float]]:
    """Generate test data for different scenarios"""
    scenario = TEST_SCENARIOS[scenario_name]

    if scenario_name == 'steady_state':
        t = np.linspace(0, scenario['duration'], 200)
        true_signal = np.ones_like(t) * 100
        noise = np.random.normal(0, scenario['noise_level'], len(t))
        measurements = true_signal + noise

    elif scenario_name == 'step_change':
        t = np.linspace(0, 2.0, 200)
        true_signal = np.zeros_like(t)
        true_signal[len(t) // 2:] = scenario['step_size']
        noise = np.random.normal(0, 0.1, len(t))
        measurements = true_signal + noise

    elif scenario_name == 'noisy_measurement':
        t = np.linspace(0, scenario['duration'], 300)
        true_signal = 100 * np.sin(t)
        noise_level = np.linspace(scenario['initial_noise'],
                                  scenario['final_noise'],
                                  len(t))
        noise = noise_level * np.random.normal(0, 1, len(t))
        measurements = true_signal + noise

    return true_signal.tolist(), measurements.tolist()


class TestKalmanAdaptation(unittest.TestCase):
    def setUp(self):
        """Initialize a fresh Kalman filter for each test"""
        self.kf = kalman_filter_X

    def test_steady_state_adaptation(self):
        """Test parameter adaptation with steady state input"""
        true_signal, measurements = generate_scenario_data('steady_state')

        # Process measurements
        filtered_values = []
        r_values = []

        for measurement in measurements:
            filtered = self.kf.kalman(measurement)
            filtered_values.append(filtered)
            r_values.append(self.kf.R)

        # R should converge to actual noise variance
        final_r = np.mean(r_values[-20:])  # Average of last 20 values
        noise_variance = np.var(measurements)
        self.assertAlmostEqual(final_r, noise_variance, delta=0.2)

    def test_step_response_adaptation(self):
        """Test adaptation behavior during step changes"""
        true_signal, measurements = generate_scenario_data('step_change')

        filtered_values = []
        q_values = []

        for measurement in measurements:
            filtered = self.kf.kalman(measurement)
            filtered_values.append(filtered)
            q_values.append(self.kf.Q)

        # Q should increase during the step change
        pre_step_q = np.mean(q_values[40:80])  # Before step
        step_q = np.mean(q_values[90:110])  # During step
        self.assertGreater(step_q, pre_step_q)

    def test_increasing_noise_adaptation(self):
        """Test adaptation to gradually increasing noise"""
        true_signal, measurements = generate_scenario_data('noisy_measurement')

        filtered_values = []
        r_values = []

        for measurement in measurements:
            filtered = self.kf.kalman(measurement)
            filtered_values.append(filtered)
            r_values.append(self.kf.R)

        # R should increase as noise increases
        initial_r = np.mean(r_values[10:30])
        final_r = np.mean(r_values[-30:])
        self.assertGreater(final_r, initial_r)

    def visualize_adaptation(self, scenario_name: str):
        """Generate visualization for a specific test scenario"""
        true_signal, measurements = generate_scenario_data(scenario_name)

        filtered_values = []
        r_values = []
        q_values = []

        for measurement in measurements:
            filtered = self.kf.kalman(measurement)
            filtered_values.append(filtered)
            r_values.append(self.kf.R)
            q_values.append(self.kf.Q)

        # Create visualization
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

        # Plot signals
        ax1.plot(true_signal, 'g-', label='True', alpha=0.5)
        ax1.plot(measurements, 'r.', label='Measured', alpha=0.3)
        ax1.plot(filtered_values, 'b-', label='Filtered', linewidth=2)
        ax1.set_title(f'Signal Filtering - {scenario_name}')
        ax1.legend()
        ax1.grid(True)

        # Plot parameter adaptation
        ax2.plot(r_values, 'r-', label='R (Measurement Noise)', alpha=0.7)
        ax2.plot(q_values, 'b-', label='Q (Process Noise)', alpha=0.7)
        ax2.set_title('Parameter Adaptation')
        ax2.set_yscale('log')
        ax2.legend()
        ax2.grid(True)

        plt.tight_layout()
        plt.savefig(f'kalman_adaptation_{scenario_name}.png')
        plt.close()


def run_tests():
    # Run all tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestKalmanAdaptation)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Generate visualizations if tests pass
    if result.wasSuccessful():
        test = TestKalmanAdaptation()
        test.setUp()
        for scenario in TEST_SCENARIOS:
            test.visualize_adaptation(scenario)


if __name__ == "__main__":
    run_tests()
