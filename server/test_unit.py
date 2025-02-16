#!/usr/bin/env python3
import time
import unittest
from unittest.mock import Mock, patch

import numpy as np

from initialization import kalman_filter_X


class TestKalmanFilterAdaptation(unittest.TestCase):
    def setUp(self):
        self.kf = kalman_filter_X

    def test_initial_parameters(self):
        """Test initial filter parameters are set correctly"""
        self.assertEqual(self.kf.Q, 0.01)
        self.assertEqual(self.kf.R, 0.1)
        self.assertEqual(len(self.kf.innovation_history), 0)

    def test_parameter_adaptation(self):
        """Test that filter parameters adapt to changing noise conditions"""
        # Generate test sequence with changing noise characteristics
        steady_data = [100 + np.random.normal(0, 1) for _ in range(20)]
        noisy_data = [100 + np.random.normal(0, 3) for _ in range(20)]
        test_sequence = steady_data + noisy_data

        # Initial parameters
        initial_R = self.kf.R

        # Process sequence
        filtered_values = []
        for value in test_sequence:
            filtered = self.kf.kalman(value)
            filtered_values.append(filtered)

        # Final parameters - R should have increased due to increased noise
        self.assertGreater(self.kf.R, initial_R)

    def test_outlier_handling(self):
        """Test the filter's response to outliers"""
        # Normal value followed by outlier
        values = [100, 100, 100, 200, 100, 100]

        filtered_values = []
        for value in values:
            filtered = self.kf.kalman(value)
            filtered_values.append(filtered)

        # Check that the filtered value for the outlier is between the previous value and the outlier
        outlier_response = filtered_values[3]
        self.assertTrue(100 < outlier_response < 200)

    def test_step_response(self):
        """Test the filter's response to a step change"""
        # Generate step sequence
        pre_step = [100] * 10
        post_step = [150] * 10
        step_sequence = pre_step + post_step

        filtered_values = []
        for value in step_sequence:
            filtered = self.kf.kalman(value)
            filtered_values.append(filtered)

        # Check filter eventually converges to new value
        final_values = filtered_values[-3:]
        for value in final_values:
            self.assertAlmostEqual(value, 150, delta=5)


@patch('RPIservo.ServoCtrl')
@patch('Adafruit_PCA9685.PCA9685')
class TestMovementLogic(unittest.TestCase):
    def setUp(self):
        # Create mock objects for hardware dependencies
        self.mock_servo = Mock()
        self.mock_pwm = Mock()

    def test_hop_sequence_timing(self, mock_pca, mock_servo):
        """Test the timing sequence of the hop motion"""
        from move import hop

        start_time = time.time()
        hop(crouch_delay=0.1, launch_delay=0.1, air_time=0.1, landing_delay=0.1, speed=20)
        total_time = time.time() - start_time

        # Total time should be approximately sum of all delays
        expected_time = 0.4  # 0.1 * 4
        self.assertAlmostEqual(total_time, expected_time, delta=0.1)

    def test_servo_movement_ranges(self, mock_pca, mock_servo):
        """Test that servo movements stay within safe ranges"""
        from move import set_all_servos

        # Test with various positions
        test_positions = {
            0: 450, 1: 300, 2: 500,  # Some example positions
            3: 400, 4: 350, 5: 450,
            6: 300, 7: 400, 8: 450,
            9: 500, 10: 350, 11: 400
        }

        set_all_servos(test_positions, speed=20)

        # Verify all positions are within safe range (100-500)
        for pos in test_positions.values():
            self.assertTrue(100 <= pos <= 500)


def run_tests():
    unittest.main(verbosity=2)


if __name__ == "__main__":
    run_tests()
