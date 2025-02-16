#!/usr/bin/env python3
import time
from unittest.mock import MagicMock

from initialization import kalman_filter_X, kalman_filter_Y, sensor, mpu6050_connection, CROUCH_POSITIONS, \
    LAUNCH_POSITIONS, LANDING_POSITIONS


class HopTest:
    def __init__(self, simulation_mode=True):
        self.simulation_mode = simulation_mode
        if simulation_mode:
            self.setup_simulation()
        else:
            import move
            self.move = move

    def setup_simulation(self):
        """Setup mock objects for simulation"""
        self.move = MagicMock()
        self.move.CROUCH_POSITIONS = CROUCH_POSITIONS
        self.move.LAUNCH_POSITIONS = LAUNCH_POSITIONS
        self.move.LANDING_POSITIONS = LANDING_POSITIONS
        self.move.mpu6050_connection = mpu6050_connection

        # Mock sensor data
        self.move.sensor = sensor
        self.move.sensor.get_accel_data.return_value = {'x': 0.0, 'y': 0.0, 'z': 1.0}

        # Mock Kalman filters
        self.move.kalman_filter_X = kalman_filter_X
        self.move.kalman_filter_Y = kalman_filter_Y
        self.move.kalman_filter_X.kalman.return_value = 0.0
        self.move.kalman_filter_Y.kalman.return_value = 0.0

    def test_positions(self):
        """Test each position set without actually hopping"""
        print("\nTesting servo positions:")

        print("Testing CROUCH positions...")
        print(f"Setting servos to: {self.move.CROUCH_POSITIONS}")
        if not self.simulation_mode:
            self.move.set_all_servos(self.move.CROUCH_POSITIONS, 10)
        time.sleep(1)

        print("\nTesting LAUNCH positions...")
        print(f"Setting servos to: {self.move.LAUNCH_POSITIONS}")
        if not self.simulation_mode:
            self.move.set_all_servos(self.move.LAUNCH_POSITIONS, 10)
        time.sleep(1)

        print("\nTesting LANDING positions...")
        print(f"Setting servos to: {self.move.LANDING_POSITIONS}")
        if not self.simulation_mode:
            self.move.set_all_servos(self.move.LANDING_POSITIONS, 10)
        time.sleep(1)

        if not self.simulation_mode:
            self.move.stand()

    def test_hop_speeds(self):
        """Test hop with different speeds"""
        print("\nTesting hop sequence with different speeds:")

        for speed in [10, 20, 30]:
            print(f"Testing hop with speed {speed}...")
            if not self.simulation_mode:
                self.move.hop(speed=speed)
            time.sleep(1)

    def test_balance_sensor(self):
        """Test MPU6050 readings and Kalman filter"""
        if self.simulation_mode:
            print("\nSimulating balance sensor readings...")
            for i in range(5):
                print(f"Sample {i + 1}:")
                print("Raw X/Y: 0.00/0.00 (simulated)")
                print("Filtered X/Y: 0.00/0.00 (simulated)")
                time.sleep(0.5)
            return

        if not self.move.mpu6050_connection:
            print("MPU6050 not connected!")
            return

        print("\nTesting real balance sensor readings...")
        for i in range(5):
            accel_data = self.move.sensor.get_accel_data()
            filtered_x = self.move.kalman_filter_X.kalman(accel_data['x'])
            filtered_y = self.move.kalman_filter_Y.kalman(accel_data['y'])
            print(f"Sample {i + 1}:")
            print(f"Raw X/Y: {accel_data['x']:.2f}/{accel_data['y']:.2f}")
            print(f"Filtered X/Y: {filtered_x:.2f}/{filtered_y:.2f}")
            time.sleep(0.5)


def main():
    print("RaspClaws Hop Test Utility")
    print("-------------------------")
    print("This utility can run in simulation mode or hardware mode.")
    simulation = input("Run in simulation mode? (Y/n): ").lower() != 'n'

    tester = HopTest(simulation_mode=simulation)

    while True:
        print("\nHop Testing Menu:")
        print("1. Test servo positions")
        print("2. Test hop sequence")
        print("3. Test balance sensor")
        print("4. Exit")

        try:
            choice = input("\nSelect test (1-4): ")

            if choice == '1':
                tester.test_positions()
            elif choice == '2':
                tester.test_hop_speeds()
            elif choice == '3':
                tester.test_balance_sensor()
            elif choice == '4':
                break
            else:
                print("Invalid choice")
        except KeyboardInterrupt:
            print("\nTest interrupted by user")
            break
        except Exception as e:
            print(f"Error during test: {e}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting test utility")
    except Exception as e:
        print(f"Fatal error: {e}")
    finally:
        print("Test complete")
