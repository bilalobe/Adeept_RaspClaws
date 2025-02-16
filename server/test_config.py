# Test configuration for RaspClaws test suite
from dataclasses import dataclass


@dataclass
class KalmanConfig:
    initial_Q: float = 0.01
    initial_R: float = 0.1
    history_max_size: int = 50
    min_samples_for_em: int = 10
    em_batch_size: int = 30


@dataclass
class SimulatorConfig:
    timestep: float = 0.01  # 10ms simulation step
    accel_noise_std: float = 0.1
    position_noise_std: float = 0.05
    gravity: float = -9.81


@dataclass
class HopTestConfig:
    launch_force: float = 5.0
    duration: float = 1.0
    crouch_delay: float = 0.2
    launch_delay: float = 0.15 
    air_time: float = 0.3
    landing_delay: float = 0.25
    speed: int = 20


@dataclass
class BalanceTestConfig:
    target_x: float = 0.0
    target_y: float = 0.0
    max_tilt: float = 30.0
    stability_threshold: float = 2.0
    test_duration: float = 5.0
    sample_rate: float = 50.0


# Test scenarios definition
TEST_SCENARIOS = {
    'steady_state': {
        'description': 'Test filter behavior with constant input',
        'duration': 2.0,
        'noise_level': 0.1,
        'expected_max_error': 0.2
    },
    'step_change': {
        'description': 'Test filter response to sudden value changes',
        'step_size': 50,
        'settling_time': 0.3,
        'max_overshoot': 10
    },
    'noisy_measurement': {
        'description': 'Test filter with increasing noise levels',
        'initial_noise': 0.1,
        'final_noise': 0.5,
        'duration': 3.0
    }
}

# Default configurations
default_kalman = KalmanConfig()
default_simulator = SimulatorConfig()
default_hop = HopTestConfig()
default_balance = BalanceTestConfig()
