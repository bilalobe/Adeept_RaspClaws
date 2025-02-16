#!/usr/bin/env python3
import time

import move
from initialization import kalman_filter_X


def test_kalman_filter():
    """Test the adaptive Kalman filter by feeding it a sequence of values"""
    print("Testing Kalman Filter Adaptation...")
    # Use existing filter instance
    test_values = [300, 305, 340, 280, 290, 310, 305]  # Simulated sensor readings

    print("Initial Q:", kalman_filter_X.Q)
    print("Initial R:", kalman_filter_X.R)

    for val in test_values:
        filtered = kalman_filter_X.kalman(val)
        print(f"Raw: {val}, Filtered: {filtered:.2f}")

    print("Final Q:", kalman_filter_X.Q)
    print("Final R:", kalman_filter_X.R)


def test_hop_sequence():
    """Test the hopping sequence with different parameters"""
    print("Testing Hop Sequence...")

    # Test basic hop
    print("Basic hop...")
    move.hop(speed=20)
    time.sleep(1)

    # Test faster hop
    print("Faster hop...")
    move.hop(speed=30)
    time.sleep(1)

    # Test hop with longer air time
    print("Long air time hop...")
    move.hop(air_time=0.4, speed=20)
    time.sleep(1)


if __name__ == '__main__':
    try:
        # Initialize servo controller
        move.init_all()
        time.sleep(1)

        # Run tests
        test_kalman_filter()
        time.sleep(2)
        test_hop_sequence()

    except KeyboardInterrupt:
        move.pwm.set_all_pwm(0, 300)
        time.sleep(1)
        move.clean_all()
