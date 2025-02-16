#! /usr/bin/python
# File name   : car_dir.py
# Description : By controlling Servo,thecamera can move Up and down,left and right and the Ultrasonic wave can move to left and right.
# Website     : www.adeept.com
# E-mail      : support@adeept.com
# Author      : William
# Date        : 2018/08/22


# Additional methods in the Kalman_filter class for adaptive parameter learning.
class Kalman_filter:
    def __init__(self, Q, R):
        self.Q = Q  # Process noise covariance
        self.R = R  # Measurement noise covariance

        # Filter state
        self.P_k_k1 = 1  # Prior error covariance
        self.Kg = 0  # Kalman gain
        self.P_k1_k1 = 1  # Posterior error covariance
        self.x_k_k1 = 0  # Prior state estimate
        self.x_k1_k1 = 0  # Posterior state estimate
        self.Z_k = 0  # Current measurement
        self.kalman_adc_old = 0

        # EM Statistics
        self.innovation_history = []  # Store recent innovations
        self.state_history = []  # Store recent state estimates
        self.measurement_history = []  # Store recent measurements
        self.history_max_size = 50  # Maximum history size for EM
        self.min_samples_for_em = 10  # Minimum samples before EM update
        self.em_batch_size = 30  # Number of samples to use for each EM update

        # Learning rates
        self.alpha_R = 0.01  # Learning rate for R (measurement noise)
        self.alpha_Q = 0.001  # Learning rate for Q (process noise)

    def _update_histories(self, innovation, state, measurement):
        """Update sliding windows of historical values"""
        self.innovation_history.append(innovation)
        self.state_history.append(state)
        self.measurement_history.append(measurement)

        # Maintain fixed window size
        if len(self.innovation_history) > self.history_max_size:
            self.innovation_history.pop(0)
            self.state_history.pop(0)
            self.measurement_history.pop(0)

    def _expectation_step(self):
        """E-step: Compute expected statistics given current parameters"""
        if len(self.state_history) < self.min_samples_for_em:
            return None, None

        # Use recent samples up to em_batch_size
        history_size = min(self.em_batch_size, len(self.state_history))
        recent_innovations = self.innovation_history[-history_size:]
        recent_states = self.state_history[-history_size:]
        recent_measurements = self.measurement_history[-history_size:]

        # Compute innovation statistics
        innovation_variance = sum(inn * inn for inn in recent_innovations) / history_size

        # Compute state transition statistics
        state_transitions = []
        for i in range(1, len(recent_states)):
            transition = recent_states[i] - recent_states[i - 1]
            state_transitions.append(transition * transition)

        process_variance = sum(state_transitions) / (len(state_transitions) or 1)

        return innovation_variance, process_variance

    def _maximization_step(self, innovation_variance, process_variance):
        """M-step: Update parameters based on computed statistics"""
        if innovation_variance is not None:
            # Update measurement noise estimate (R)
            self.R = (1 - self.alpha_R) * self.R + self.alpha_R * innovation_variance

            # Update process noise estimate (Q)
            # We use a smaller learning rate and scale for Q to maintain stability
            self.Q = (1 - self.alpha_Q) * self.Q + self.alpha_Q * (process_variance * 0.1)

            # Ensure parameters stay positive
            self.R = max(1e-6, self.R)
            self.Q = max(1e-7, self.Q)

    def kalman(self, ADC_Value):
        """
        Main Kalman filter update with integrated EM parameter learning
        """
        self.Z_k = ADC_Value

        # Handle large jumps (outlier management)
        if abs(self.kalman_adc_old - ADC_Value) >= 60:
            self.x_k1_k1 = ADC_Value * 0.382 + self.kalman_adc_old * 0.618
        else:
            self.x_k1_k1 = self.kalman_adc_old

        # Prediction step
        self.x_k_k1 = self.x_k1_k1
        self.P_k_k1 = self.P_k1_k1 + self.Q

        # Update step
        self.Kg = self.P_k_k1 / (self.P_k_k1 + self.R)
        innovation = self.Z_k - self.kalman_adc_old
        kalman_adc = self.x_k_k1 + self.Kg * innovation
        self.P_k1_k1 = (1 - self.Kg) * self.P_k_k1
        self.P_k_k1 = self.P_k1_k1

        # Update histories for EM
        self._update_histories(innovation, kalman_adc, ADC_Value)

        # Perform EM update
        innovation_variance, process_variance = self._expectation_step()
        self._maximization_step(innovation_variance, process_variance)

        self.kalman_adc_old = kalman_adc
        return kalman_adc

    def get_parameters(self):
        """Return current filter parameters"""
        return {
            'Q': self.Q,
            'R': self.R,
            'P': self.P_k1_k1,
            'history_size': len(self.state_history)
        }
