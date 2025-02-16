#!/usr/bin/env python3
import unittest
import time
from unittest.mock import MagicMock, patch
import numpy as np

from initialization import kalman_filter_X, kalman_filter_Y, sensor, mpu6050_connection
from move import hop, steady, get_pwm, set_pwm
from test_config import TEST_SCENARIOS, default_kalman, default_simulator, default_hop, default_balance


class TestIntegratedSystem(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.original_sensor = sensor
        self.mock_sensor = MagicMock()
        self.mock_sensor.get_accel_data.return_value = {'x': 0, 'y': 0, 'z': 1}

    def test_hop_sequence(self):
        """Test hopping motion with Kalman filtering"""
        config = default_hop
        
        # Mock sensor readings for a hop sequence
        readings = [
            {'x': 0, 'y': 0, 'z': 1},    # Start
            {'x': 0.1, 'y': 0.1, 'z': 2}, # Crouch
            {'x': 0.2, 'y': 0.2, 'z': 3}, # Launch
            {'x': 0, 'y': 0, 'z': 0.5},   # Air
            {'x': -0.1, 'y': -0.1, 'z': 2}, # Landing
            {'x': 0, 'y': 0, 'z': 1}      # Stabilize
        ]
        
        self.mock_sensor.get_accel_data.side_effect = readings
        
        with patch('initialization.sensor', self.mock_sensor):
            # Execute hop
            hop(crouch_delay=config.crouch_delay,
                launch_delay=config.launch_delay,
                air_time=config.air_time,
                landing_delay=config.landing_delay,
                speed=config.speed)

            # Verify sensor was read the expected number of times
            expected_reads = len(readings)
            actual_reads = self.mock_sensor.get_accel_data.call_count
            self.assertGreaterEqual(actual_reads, expected_reads)

    def test_balance_control(self):
        """Test balance control system"""
        config = default_balance
        
        # Generate simulated motion with increasing tilt
        timestamps = np.linspace(0, config.test_duration, int(config.test_duration * config.sample_rate))
        test_data = []
        
        for t in timestamps:
            # Simulate gentle swaying motion
            x = 5 * np.sin(2 * np.pi * 0.5 * t)  # 0.5 Hz sway
            y = 3 * np.cos(2 * np.pi * 0.3 * t)  # 0.3 Hz sway
            
            reading = {'x': x, 'y': y, 'z': 1}
            filtered_x = kalman_filter_X.kalman(reading['x'])
            filtered_y = kalman_filter_Y.kalman(reading['y'])
            
            test_data.append({
                'raw': reading,
                'filtered': {'x': filtered_x, 'y': filtered_y}
            })
            
            # Verify filtered values are within expected ranges
            self.assertLess(abs(filtered_x), config.max_tilt)
            self.assertLess(abs(filtered_y), config.max_tilt)
            
            # Small delay to simulate real-time processing
            time.sleep(1/config.sample_rate)

    def test_servo_control(self):
        """Test servo control functions"""
        # Test PWM get/set operations
        test_channel = 0
        test_value = 350
        
        # Set PWM value
        set_pwm(test_channel, test_value)
        
        # Verify we can read back the value
        read_value = get_pwm(test_channel)
        self.assertEqual(read_value, test_value)
        
        # Test PWM bounds
        max_test = 600
        min_test = 100
        
        set_pwm(test_channel, max_test)
        self.assertEqual(get_pwm(test_channel), max_test)
        
        set_pwm(test_channel, min_test)
        self.assertEqual(get_pwm(test_channel), min_test)

    def tearDown(self):
        """Clean up after tests"""
        # Restore original sensor
        globals()['sensor'] = self.original_sensor


def run_tests():
    unittest.main()
