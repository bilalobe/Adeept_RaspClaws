import os
import logging
import Adafruit_PCA9685
from mpu6050 import mpu6050
import Kalman_filter
import PID
import RPIservo

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variable to control hardware simulation
SIMULATE_HARDWARE = os.getenv('SIMULATE_HARDWARE', 'false').lower() == 'true'

# Initialize Kalman filters
kalman_filter_X = Kalman_filter.Kalman_filter(0.01, 0.1)
kalman_filter_Y = Kalman_filter.Kalman_filter(0.01, 0.1)

# Initialize PID controllers
X_pid = PID.PID()
X_pid.SetKp(5)
X_pid.SetKd(0.01)
X_pid.SetKi(0)
Y_pid = PID.PID()
Y_pid.SetKp(5)
Y_pid.SetKd(0.01)
Y_pid.SetKi(0)

# Initialize MPU6050 sensor
try:
    if not SIMULATE_HARDWARE:
        sensor = mpu6050(0x68)
        mpu6050_connection = True
        logger.info("MPU6050 initialized successfully")
    else:
        # Mock sensor for simulation
        class MockMPU6050:
            def get_accel_data(self):
                return {'x': 0.0, 'y': 0.0, 'z': 1.0}
        sensor = MockMPU6050()
        mpu6050_connection = True
        logger.info("Using simulated MPU6050")
except:
    mpu6050_connection = False
    logger.warning("MPU6050 initialization failed - balance control will be disabled")

# Initialize Servo Controller
sc = RPIservo.ServoCtrl()
sc.start()

# Initialize PWM
pwm = Adafruit_PCA9685.PCA9685()
pwm.set_pwm_freq(50)

# Define target servo positions (PWM values) for the 3 phases
CROUCH_POSITIONS = {
    0: 450, 1: 450, 2: 450, 3: 450, 4: 450, 5: 450,
    6: 450, 7: 450, 8: 450, 9: 450, 10: 450, 11: 450,
}

LAUNCH_POSITIONS = {
    0: 520, 1: 520, 2: 520, 3: 520, 4: 520, 5: 520,
    6: 520, 7: 520, 8: 520, 9: 520, 10: 520, 11: 520,
}

LANDING_POSITIONS = {
    0: 400, 1: 400, 2: 400, 3: 400, 4: 400, 5: 400,
    6: 400, 7: 400, 8: 400, 9: 400, 10: 400, 11: 400,
}
