#! /usr/bin/python
# File name   : move.py
# Description : Controlling all servos
# Website	 : www.adeept.com
# E-mail	  : support@adeept.com
# Author	  : William
# Date		: 2019/04/08

import json
import threading
import time

import Adafruit_PCA9685
from mpu6050_connection import mpu6050_connection

import Kalman_filter
import PID
from initialization import kalman_filter_X, kalman_filter_Y, X_pid, Y_pid, sensor, mpu6050_connection, sc, pwm, \
    CROUCH_POSITIONS, LAUNCH_POSITIONS, LANDING_POSITIONS
from lighting_utils import LightingError
from robotLight import RobotLight

# Initialize the servo controller using RPIservo's ServoCtrl class
sc.start()  # Start the servo control thread

# Initialize LED controller with error handling
try:
    led = RobotLight()
    led.start()
    led.setStatus('idle')
except LightingError as e:
    print(f"Warning: Light system initialization failed: {e}")
    led = None


def _safe_light_call(func, *args, **kwargs):
    """Helper to safely call light functions"""
    if led is not None:
        try:
            func(*args, **kwargs)
        except LightingError as e:
            print(f"Light system warning: {e}")


# Define desired targets for balance (in accelerometer units)
target_X = 0  # level (adjust if needed)
target_Y = 0

# Initialize PWM values
pwm0 = pwm1 = pwm2 = pwm3 = 300  # Base positions for legs
pwm4 = pwm5 = pwm6 = pwm7 = 300
pwm8 = pwm9 = pwm10 = pwm11 = 300
pwm12 = pwm13 = pwm14 = pwm15 = 300

# Create a dictionary to store PWM values for easier access
PWM_VALUES = {
    i: locals()[f'pwm{i}'] for i in range(16)
}


def get_pwm(channel):
    """Get PWM value for a channel"""
    return PWM_VALUES.get(channel, 300)  # Default to center position if not found


def set_pwm(channel, value):
    """Update PWM value for a channel"""
    PWM_VALUES[channel] = value
    pwm.set_pwm(channel, 0, value)


def set_all_servos(positions, speed):
    """
    Set all leg servos to the specified absolute positions using
    the ServoCtrl class for smooth transitions.
    """
    for i in range(12):
        # Here we assume your ServoCtrl class provides a way to get the current position.
        # Replace sc.getServoPosition(i) with your actual method if available.
        current_val = sc.getServoPosition(i) if hasattr(sc, 'getServoPosition') else 0
        diff = positions[i] - current_val
        direction = 1 if diff >= 0 else -1
        # singleServo(servo_index, direction, speed) initiates a controlled movement.
        sc.singleServo(i, direction, speed)
    # Allow time for the servos to reach close to the target.
    time.sleep(0.5)
    sc.stopWiggle()


def hop(crouch_delay=0.2, launch_delay=0.15, air_time=0.3, landing_delay=0.25, speed=20):
    """Execute a hopping sequence with smooth visual transitions"""
    global move_stu
    move_stu = 0

    _safe_light_call(led.setStatus, 'active')

    try:
        # Phase 1: Crouch - Fade to green
        _safe_light_call(led.fadeToColor, 0, 255, 0, steps=15)
        set_all_servos(CROUCH_POSITIONS, speed)
        time.sleep(crouch_delay)

        # Phase 2: Launch - Quick transition to cyan
        _safe_light_call(led.fadeToColor, 0, 255, 255, steps=10, delay=0.01)
        set_all_servos(LAUNCH_POSITIONS, speed)
        time.sleep(launch_delay)

        # Phase 3: Air time - Rainbow effect
        _safe_light_call(led.rainbow)
        start_time = time.time()
        while time.time() - start_time < air_time:
            if mpu6050_connection:
                accelerometer_data = sensor.get_accel_data()
                X = kalman_filter_X.kalman(accelerometer_data['x'])
                Y = kalman_filter_Y.kalman(accelerometer_data['y'])

                # Adjust brightness based on orientation
                tilt = abs(X) + abs(Y)
                brightness = max(50, 255 - int(tilt * 20))
                _safe_light_call(led.setBrightness, brightness)

            time.sleep(0.02)

        # Phase 4: Landing - Smooth transition to orange
        _safe_light_call(led.fadeToColor, 255, 165, 0, steps=20)
        set_all_servos(LANDING_POSITIONS, speed)
        time.sleep(landing_delay)

        move_stu = 1
        # Smooth transition back to idle
        _safe_light_call(led.fadeToColor, 0, 128, 255, steps=30)
        _safe_light_call(led.setStatus, 'idle')

    except Exception as e:
        _safe_light_call(led.setStatus, 'error')
        raise e


'''
change this variables to 0 to reverse all the servos.
'''
set_direction = 1

'''
change these two variables to reverse the direction of the legs.
'''
if set_direction:
    leftSide_direction = 1
    rightSide_direction = 0
else:
    leftSide_direction = 0
    rightSide_direction = 1

'''
change these two variables to reverse the height of the legs.
'''
if set_direction:
    leftSide_height = 0
    rightSide_height = 1
else:
    leftSide_height = 1
    rightSide_height = 0

'''
change this variable to set the range of the height range.
'''
height_change = 30

'''
change these two variables to adjuest the function for observing.
'''
if set_direction:
    Up_Down_direction = 1
    Left_Right_direction = 1
else:
    Up_Down_direction = 0
    Left_Right_direction = 0
Left_Right_input = 300
Up_Down_input = 300
Left_Right_Max = 500
Left_Right_Min = 100
Up_Down_Max = 500
Up_Down_Min = 270
look_wiggle = 30
move_stu = 1

'''
change these variable to adjuest the steady function.
'''
steady_range_Min = -40
steady_range_Max = 130
range_Mid = (steady_range_Min + steady_range_Max) / 2
X_fix_output = range_Mid
Y_fix_output = range_Mid
steady_X_set = 73

'''
Set PID
'''
P = 5
I = 0.01
D = 0

'''
>>> instantiation <<<
'''
X_pid = PID.PID()
X_pid.SetKp(P)
X_pid.SetKd(I)
X_pid.SetKi(D)
Y_pid = PID.PID()
Y_pid.SetKp(P)
Y_pid.SetKd(I)
Y_pid.SetKi(D)
pwm = Adafruit_PCA9685.PCA9685()
pwm.set_pwm_freq(50)
kalman_filter_X = Kalman_filter.Kalman_filter(0.001, 0.1)
kalman_filter_Y = Kalman_filter.Kalman_filter(0.001, 0.1)

try:
    sensor = mpu6050_connection(0x68)
    mpu6050_connection = 1
except:
    mpu6050_connection = 0

'''
change these two variable to adjuest the steady status.
	   (X+)
	   /|\
  (Y+)<-+->(Y-)
	    |
	   (X-)
Example: If you want the forhead of the robot to point down,
         you need to increase the value target_X.
'''
target_X = 0
target_Y = 0

'''
Set a default pwm value for all servos.
'''
for i in range(0, 16):
    exec('pwm%d=RPIservo.init_pwm%d' % (i, i))

'''
Get raw data from mpu6050.
'''


def mpu6050Test():
    while 1:
        accelerometer_data = sensor.get_accel_data()
        print('X=%f,Y=%f,Z=%f' % (accelerometer_data['x'], accelerometer_data['y'], accelerometer_data['x']))
        time.sleep(0.3)


def init_all():
    pwm.set_pwm(0, 0, pwm0)
    pwm.set_pwm(1, 0, pwm1)
    pwm.set_pwm(2, 0, pwm2)
    pwm.set_pwm(3, 0, pwm3)

    pwm.set_pwm(4, 0, pwm4)
    pwm.set_pwm(5, 0, pwm5)
    pwm.set_pwm(6, 0, pwm6)
    pwm.set_pwm(7, 0, pwm7)

    pwm.set_pwm(8, 0, pwm8)
    pwm.set_pwm(9, 0, pwm9)
    pwm.set_pwm(10, 0, pwm10)
    pwm.set_pwm(11, 0, pwm11)

    pwm.set_pwm(12, 0, pwm12)
    pwm.set_pwm(13, 0, pwm13)
    pwm.set_pwm(14, 0, pwm14)
    pwm.set_pwm(15, 0, pwm15)


init_all()


def ctrl_range(raw, max_genout, min_genout):
    if raw > max_genout:
        raw_output = max_genout
    elif raw < min_genout:
        raw_output = min_genout
    else:
        raw_output = raw
    return int(raw_output)


'''
left_I   -<forward>-- right_III
left_II  ---<BODY>---  right_II
left_III -<Backward>-   right_I

            pos=1
           /     \
          /       \
         /         \
    pos=2---pos=3---pos=4

Change the value of wiggle to set the range and direction that the legs moves.
'''


def left_I(pos, wiggle, heightAdjust=0):
    if pos == 0:
        # pwm.set_pwm(0,0,pwm0)
        if leftSide_height:
            pwm.set_pwm(1, 0, pwm1 + heightAdjust)
        else:
            pwm.set_pwm(1, 0, pwm1 - heightAdjust)
    else:
        if leftSide_direction:
            if pos == 1:
                pwm.set_pwm(0, 0, pwm0)
                if leftSide_height:
                    pwm.set_pwm(1, 0, pwm1 + 3 * height_change)
                else:
                    pwm.set_pwm(1, 0, pwm1 - 3 * height_change)
            elif pos == 2:
                pwm.set_pwm(0, 0, pwm0 + wiggle)
                if leftSide_height:
                    pwm.set_pwm(1, 0, pwm1 - height_change)
                else:
                    pwm.set_pwm(1, 0, pwm1 + height_change)
            elif pos == 3:
                pwm.set_pwm(0, 0, pwm0)
                if leftSide_height:
                    pwm.set_pwm(1, 0, pwm1 - height_change)
                else:
                    pwm.set_pwm(1, 0, pwm1 + height_change)
            elif pos == 4:
                pwm.set_pwm(0, 0, pwm0 - wiggle)
                if leftSide_height:
                    pwm.set_pwm(1, 0, pwm1 - height_change)
                else:
                    pwm.set_pwm(1, 0, pwm1 + height_change)
        else:
            if pos == 1:
                pwm.set_pwm(0, 0, pwm0)
                if leftSide_height:
                    pwm.set_pwm(1, 0, pwm1 + 3 * wiggle)
                else:
                    pwm.set_pwm(1, 0, pwm1 - 3 * wiggle)
            elif pos == 2:
                pwm.set_pwm(0, 0, pwm0 - wiggle)
                if leftSide_height:
                    pwm.set_pwm(1, 0, pwm1 - wiggle)
                else:
                    pwm.set_pwm(1, 0, pwm1 + wiggle)
            elif pos == 3:
                pwm.set_pwm(0, 0, pwm0)
                if leftSide_height:
                    pwm.set_pwm(1, 0, pwm1 - wiggle)
                else:
                    pwm.set_pwm(1, 0, pwm1 + wiggle)
            elif pos == 4:
                pwm.set_pwm(0, 0, pwm0 + wiggle)
                if leftSide_height:
                    pwm.set_pwm(1, 0, pwm1 - wiggle)
                else:
                    pwm.set_pwm(1, 0, pwm1 + wiggle)


def left_II(pos, wiggle, heightAdjust=0):
    if pos == 0:
        # pwm.set_pwm(2,0,pwm2)
        if leftSide_height:
            pwm.set_pwm(3, 0, pwm3 + heightAdjust)
        else:
            pwm.set_pwm(3, 0, pwm3 - heightAdjust)
    else:
        if leftSide_direction:
            if pos == 1:
                pwm.set_pwm(2, 0, pwm2)
                if leftSide_height:
                    pwm.set_pwm(3, 0, pwm3 + 3 * height_change)
                else:
                    pwm.set_pwm(3, 0, pwm3 - 3 * height_change)
            elif pos == 2:
                pwm.set_pwm(2, 0, pwm2 + wiggle)
                if leftSide_height:
                    pwm.set_pwm(3, 0, pwm3 - height_change)
                else:
                    pwm.set_pwm(3, 0, pwm3 + height_change)
            elif pos == 3:
                pwm.set_pwm(2, 0, pwm2)
                if leftSide_height:
                    pwm.set_pwm(3, 0, pwm3 - height_change)
                else:
                    pwm.set_pwm(3, 0, pwm3 + height_change)
            elif pos == 4:
                pwm.set_pwm(2, 0, pwm2 - wiggle)
                if leftSide_height:
                    pwm.set_pwm(3, 0, pwm3 - height_change)
                else:
                    pwm.set_pwm(3, 0, pwm3 + height_change)
        else:
            if pos == 1:
                pwm.set_pwm(2, 0, pwm2)
                if leftSide_height:
                    pwm.set_pwm(3, 0, pwm3 + 3 * wiggle)
                else:
                    pwm.set_pwm(3, 0, pwm3 - 3 * wiggle)
            elif pos == 2:
                pwm.set_pwm(2, 0, pwm2 - wiggle)
                if leftSide_height:
                    pwm.set_pwm(3, 0, pwm3 - wiggle)
                else:
                    pwm.set_pwm(3, 0, pwm3 + wiggle)
            elif pos == 3:
                pwm.set_pwm(2, 0, pwm2)
                if leftSide_height:
                    pwm.set_pwm(3, 0, pwm3 - wiggle)
                else:
                    pwm.set_pwm(3, 0, pwm3 + wiggle)
            elif pos == 4:
                pwm.set_pwm(2, 0, pwm2 + wiggle)
                if leftSide_height:
                    pwm.set_pwm(3, 0, pwm3 - wiggle)
                else:
                    pwm.set_pwm(3, 0, pwm3 + wiggle)


def left_III(pos, wiggle, heightAdjust=0):
    if pos == 0:
        # pwm.set_pwm(4,0,pwm4)
        if leftSide_height:
            pwm.set_pwm(5, 0, pwm5 + heightAdjust)
        else:
            pwm.set_pwm(5, 0, pwm5 - heightAdjust)
    else:
        if leftSide_direction:
            if pos == 1:
                pwm.set_pwm(4, 0, pwm4)
                if leftSide_height:
                    pwm.set_pwm(5, 0, pwm5 + 3 * height_change)
                else:
                    pwm.set_pwm(5, 0, pwm5 - 3 * height_change)
            elif pos == 2:
                pwm.set_pwm(4, 0, pwm4 + wiggle)
                if leftSide_height:
                    pwm.set_pwm(5, 0, pwm5 - height_change)
                else:
                    pwm.set_pwm(5, 0, pwm5 + height_change)
            elif pos == 3:
                pwm.set_pwm(4, 0, pwm4)
                if leftSide_height:
                    pwm.set_pwm(5, 0, pwm5 - height_change)
                else:
                    pwm.set_pwm(5, 0, pwm5 + height_change)
            elif pos == 4:
                pwm.set_pwm(4, 0, pwm4 - wiggle)
                if leftSide_height:
                    pwm.set_pwm(5, 0, pwm5 - height_change)
                else:
                    pwm.set_pwm(5, 0, pwm5 + height_change)
        else:
            if pos == 1:
                pwm.set_pwm(4, 0, pwm4)
                if leftSide_height:
                    pwm.set_pwm(5, 0, pwm5 + 3 * wiggle)
                else:
                    pwm.set_pwm(5, 0, pwm5 - 3 * wiggle)
            elif pos == 2:
                pwm.set_pwm(4, 0, pwm4 - wiggle)
                if leftSide_height:
                    pwm.set_pwm(5, 0, pwm5 - wiggle)
                else:
                    pwm.set_pwm(5, 0, pwm5 + wiggle)
            elif pos == 3:
                pwm.set_pwm(4, 0, pwm4)
                if leftSide_height:
                    pwm.set_pwm(5, 0, pwm5 - wiggle)
                else:
                    pwm.set_pwm(5, 0, pwm5 + wiggle)
            elif pos == 4:
                pwm.set_pwm(4, 0, pwm4 + wiggle)
                if leftSide_height:
                    pwm.set_pwm(5, 0, pwm5 - wiggle)
                else:
                    pwm.set_pwm(5, 0, pwm5 + wiggle)


def right_I(pos, wiggle, heightAdjust=0):
    # wiggle = -wiggle
    if pos == 0:
        # pwm.set_pwm(6,0,pwm6)
        if rightSide_height:
            pwm.set_pwm(7, 0, pwm7 + heightAdjust)
        else:
            pwm.set_pwm(7, 0, pwm7 - heightAdjust)
    else:
        if rightSide_direction:
            if pos == 1:
                pwm.set_pwm(6, 0, pwm6)
                if rightSide_height:
                    pwm.set_pwm(7, 0, pwm7 + 3 * height_change)
                else:
                    pwm.set_pwm(7, 0, pwm7 - 3 * height_change)
            elif pos == 2:
                pwm.set_pwm(6, 0, pwm6 + wiggle)
                if rightSide_height:
                    pwm.set_pwm(7, 0, pwm7 - height_change)
                else:
                    pwm.set_pwm(7, 0, pwm7 + height_change)
            elif pos == 3:
                pwm.set_pwm(6, 0, pwm6)
                if rightSide_height:
                    pwm.set_pwm(7, 0, pwm7 - height_change)
                else:
                    pwm.set_pwm(7, 0, pwm7 + height_change)
            elif pos == 4:
                pwm.set_pwm(6, 0, pwm6 - wiggle)
                if rightSide_height:
                    pwm.set_pwm(7, 0, pwm7 - height_change)
                else:
                    pwm.set_pwm(7, 0, pwm7 + height_change)
        else:
            if pos == 1:
                pwm.set_pwm(6, 0, pwm6)
                if rightSide_height:
                    pwm.set_pwm(7, 0, pwm7 + 3 * height_change)
                else:
                    pwm.set_pwm(7, 0, pwm7 - 3 * height_change)
            elif pos == 2:
                pwm.set_pwm(6, 0, pwm6 - wiggle)
                if rightSide_height:
                    pwm.set_pwm(7, 0, pwm7 - height_change)
                else:
                    pwm.set_pwm(7, 0, pwm7 + height_change)
            elif pos == 3:
                pwm.set_pwm(6, 0, pwm6)
                if rightSide_height:
                    pwm.set_pwm(7, 0, pwm7 - height_change)
                else:
                    pwm.set_pwm(7, 0, pwm7 + height_change)
            elif pos == 4:
                pwm.set_pwm(6, 0, pwm6 + wiggle)
                if rightSide_height:
                    pwm.set_pwm(7, 0, pwm7 - height_change)
                else:
                    pwm.set_pwm(7, 0, pwm7 + height_change)


def right_II(pos, wiggle, heightAdjust=0):
    # wiggle = -wiggle
    if pos == 0:
        # pwm.set_pwm(8,0,pwm8)
        if rightSide_height:
            pwm.set_pwm(9, 0, pwm9 + heightAdjust)
        else:
            pwm.set_pwm(9, 0, pwm9 - heightAdjust)
    else:
        if rightSide_direction:
            if pos == 1:
                pwm.set_pwm(8, 0, pwm8)
                if rightSide_height:
                    pwm.set_pwm(9, 0, pwm9 + 3 * height_change)
                else:
                    pwm.set_pwm(9, 0, pwm9 - 3 * height_change)
            elif pos == 2:
                pwm.set_pwm(8, 0, pwm8 + wiggle)
                if rightSide_height:
                    pwm.set_pwm(9, 0, pwm9 - height_change)
                else:
                    pwm.set_pwm(9, 0, pwm9 + height_change)
            elif pos == 3:
                pwm.set_pwm(8, 0, pwm8)
                if rightSide_height:
                    pwm.set_pwm(9, 0, pwm9 - height_change)
                else:
                    pwm.set_pwm(9, 0, pwm9 + height_change)
            elif pos == 4:
                pwm.set_pwm(8, 0, pwm8 - wiggle)
                if rightSide_height:
                    pwm.set_pwm(9, 0, pwm9 - height_change)
                else:
                    pwm.set_pwm(9, 0, pwm9 + height_change)
        else:
            if pos == 1:
                pwm.set_pwm(8, 0, pwm8)
                if rightSide_height:
                    pwm.set_pwm(9, 0, pwm9 + 3 * height_change)
                else:
                    pwm.set_pwm(9, 0, pwm9 - 3 * height_change)
            elif pos == 2:
                pwm.set_pwm(8, 0, pwm8 - wiggle)
                if rightSide_height:
                    pwm.set_pwm(9, 0, pwm9 - height_change)
                else:
                    pwm.set_pwm(9, 0, pwm9 + height_change)
            elif pos == 3:
                pwm.set_pwm(8, 0, pwm8)
                if rightSide_height:
                    pwm.set_pwm(9, 0, pwm9 - height_change)
                else:
                    pwm.set_pwm(9, 0, pwm9 + height_change)
            elif pos == 4:
                pwm.set_pwm(8, 0, pwm8 + wiggle)
                if rightSide_height:
                    pwm.set_pwm(9, 0, pwm9 - height_change)
                else:
                    pwm.set_pwm(9, 0, pwm9 + height_change)


def right_III(pos, wiggle, heightAdjust=0):
    # wiggle = -wiggle
    if pos == 0:
        # pwm.set_pwm(10,0,pwm10)
        if rightSide_height:
            pwm.set_pwm(11, 0, pwm11 + heightAdjust)
        else:
            pwm.set_pwm(11, 0, pwm11 - heightAdjust)
    else:
        if rightSide_direction:
            if pos == 1:
                pwm.set_pwm(10, 0, pwm10)
                if rightSide_height:
                    pwm.set_pwm(11, 0, pwm11 + 3 * height_change)
                else:
                    pwm.set_pwm(11, 0, pwm11 - 3 * height_change)
            elif pos == 2:
                pwm.set_pwm(10, 0, pwm10 + wiggle)
                if rightSide_height:
                    pwm.set_pwm(11, 0, pwm11 - height_change)
                else:
                    pwm.set_pwm(11, 0, pwm11 + height_change)
            elif pos == 3:
                pwm.set_pwm(10, 0, pwm10)
                if rightSide_height:
                    pwm.set_pwm(11, 0, pwm11 - height_change)
                else:
                    pwm.set_pwm(11, 0, pwm11 + height_change)
            elif pos == 4:
                pwm.set_pwm(10, 0, pwm10 - wiggle)
                if rightSide_height:
                    pwm.set_pwm(11, 0, pwm11 - height_change)
                else:
                    pwm.set_pwm(11, 0, pwm11 + height_change)
        else:
            if pos == 1:
                pwm.set_pwm(10, 0, pwm10)
                if rightSide_height:
                    pwm.set_pwm(11, 0, pwm11 + 3 * height_change)
                else:
                    pwm.set_pwm(11, 0, pwm11 - 3 * height_change)
            elif pos == 2:
                pwm.set_pwm(10, 0, pwm10 - wiggle)
                if rightSide_height:
                    pwm.set_pwm(11, 0, pwm11 - height_change)
                else:
                    pwm.set_pwm(11, 0, pwm11 + height_change)
            elif pos == 3:
                pwm.set_pwm(10, 0, pwm10)
                if rightSide_height:
                    pwm.set_pwm(11, 0, pwm11 - height_change)
                else:
                    pwm.set_pwm(11, 0, pwm11 + height_change)
            elif pos == 4:
                pwm.set_pwm(10, 0, pwm10 + wiggle)
                if rightSide_height:
                    pwm.set_pwm(11, 0, pwm11 - height_change)
                else:
                    pwm.set_pwm(11, 0, pwm11 + height_change)


def move(step_input, speed, command):
    """Movement control with visual feedback"""
    step_I = step_input
    step_II = step_input + 2

    if step_II > 4:
        step_II = step_II - 4
    if speed == 0:
        _safe_light_call(led.setStatus, 'idle')
        return

    _safe_light_call(led.setStatus, 'active')
    if command == 'no':
        right_I(step_I, speed, 0)
        left_II(step_I, speed, 0)
        right_III(step_I, speed, 0)

        left_I(step_II, speed, 0)
        right_II(step_II, speed, 0)
        left_III(step_II, speed, 0)
    elif command == 'left':
        right_I(step_I, speed, 0)
        left_II(step_I, -speed, 0)
        right_III(step_I, speed, 0)

        left_I(step_II, -speed, 0)
        right_II(step_II, speed, 0)
        left_III(step_II, -speed, 0)
    elif command == 'right':
        right_I(step_I, -speed, 0)
        left_II(step_I, speed, 0)
        right_III(step_I, -speed, 0)

        left_I(step_II, speed, 0)
        right_II(step_II, -speed, 0)
        left_III(step_II, speed, 0)


def stand():
    pwm.set_pwm(0, 0, 300)
    pwm.set_pwm(1, 0, 300)
    pwm.set_pwm(2, 0, 300)
    pwm.set_pwm(3, 0, 300)
    pwm.set_pwm(4, 0, 300)
    pwm.set_pwm(5, 0, 300)
    pwm.set_pwm(6, 0, 300)
    pwm.set_pwm(7, 0, 300)
    pwm.set_pwm(8, 0, 300)
    pwm.set_pwm(9, 0, 300)
    pwm.set_pwm(10, 0, 300)
    pwm.set_pwm(11, 0, 300)


'''
---Dove---
making the servo moves smooth.
'''


def dove_Left_I(horizontal, vertical):
    if leftSide_direction:
        pwm.set_pwm(0, 0, pwm0 + horizontal)
    else:
        pwm.set_pwm(0, 0, pwm0 - horizontal)

    if leftSide_height:
        pwm.set_pwm(1, 0, pwm1 + vertical)
    else:
        pwm.set_pwm(1, 0, pwm1 - vertical)


def dove_Left_II(horizontal, vertical):
    if leftSide_direction:
        pwm.set_pwm(2, 0, pwm2 + horizontal)
    else:
        pwm.set_pwm(2, 0, pwm2 - horizontal)

    if leftSide_height:
        pwm.set_pwm(3, 0, pwm3 + vertical)
    else:
        pwm.set_pwm(3, 0, pwm3 - vertical)


def dove_Left_III(horizontal, vertical):
    if leftSide_direction:
        pwm.set_pwm(4, 0, pwm4 + horizontal)
    else:
        pwm.set_pwm(4, 0, pwm4 - horizontal)

    if leftSide_height:
        pwm.set_pwm(5, 0, pwm5 + vertical)
    else:
        pwm.set_pwm(5, 0, pwm5 - vertical)


def dove_Right_I(horizontal, vertical):
    if rightSide_direction:
        pwm.set_pwm(6, 0, pwm6 + horizontal)
    else:
        pwm.set_pwm(6, 0, pwm6 - horizontal)

    if rightSide_height:
        pwm.set_pwm(7, 0, pwm7 + vertical)
    else:
        pwm.set_pwm(7, 0, pwm7 - vertical)


def dove_Right_II(horizontal, vertical):
    if rightSide_direction:
        pwm.set_pwm(8, 0, pwm8 + horizontal)
    else:
        pwm.set_pwm(8, 0, pwm8 - horizontal)

    if rightSide_height:
        pwm.set_pwm(9, 0, pwm9 + vertical)
    else:
        pwm.set_pwm(9, 0, pwm9 - vertical)


def dove_Right_III(horizontal, vertical):
    if rightSide_direction:
        pwm.set_pwm(10, 0, pwm10 + horizontal)
    else:
        pwm.set_pwm(10, 0, pwm10 - horizontal)

    if rightSide_height:
        pwm.set_pwm(11, 0, pwm11 + vertical)
    else:
        pwm.set_pwm(11, 0, pwm11 - vertical)


def dove(step_input, speed, timeLast, dpi, command):
    step_I = step_input
    step_II = step_input + 2

    if step_II > 4:
        step_II = step_II - 4

    if speed > 0:
        if step_input == 1:
            for speed_I in range(0, (speed + int(speed / dpi)), int(speed / dpi)):
                if move_stu and command == 'no':
                    speed_II = speed_I
                    speed_I = speed - speed_I
                    dove_Left_I(-speed_I, 3 * speed_II)
                    dove_Right_II(-speed_I, 3 * speed_II)
                    dove_Left_III(-speed_I, 3 * speed_II)

                    dove_Right_I(speed_I, -10)
                    dove_Left_II(speed_I, -10)
                    dove_Right_III(speed_I, -10)
                    time.sleep(timeLast / dpi)
                else:
                    pass

                if command == 'left':
                    speed_II = speed_I
                    speed_I = speed - speed_I
                    dove_Left_I(speed_I, 3 * speed_II)
                    dove_Right_II(-speed_I, 3 * speed_II)
                    dove_Left_III(speed_I, 3 * speed_II)

                    dove_Right_I(speed_I, -10)
                    dove_Left_II(-speed_I, -10)
                    dove_Right_III(speed_I, -10)
                    time.sleep(timeLast / dpi)
                elif command == 'right':
                    speed_II = speed_I
                    speed_I = speed - speed_I
                    dove_Left_I(-speed_I, 3 * speed_II)
                    dove_Right_II(speed_I, 3 * speed_II)
                    dove_Left_III(-speed_I, 3 * speed_II)

                    dove_Right_I(-speed_I, -10)
                    dove_Left_II(speed_I, -10)
                    dove_Right_III(-speed_I, -10)
                    time.sleep(timeLast / dpi)
                else:
                    pass

                if move_stu == 0 and command == 'no':
                    break

        elif step_input == 2:
            for speed_I in range(0, (speed + int(speed / dpi)), int(speed / dpi)):
                if move_stu and command == 'no':
                    speed_II = speed_I
                    speed_I = speed - speed_I
                    dove_Left_I(speed_II, 3 * (speed - speed_II))
                    dove_Right_II(speed_II, 3 * (speed - speed_II))
                    dove_Left_III(speed_II, 3 * (speed - speed_II))

                    dove_Right_I(-speed_II, -10)
                    dove_Left_II(-speed_II, -10)
                    dove_Right_III(-speed_II, -10)
                    time.sleep(timeLast / dpi)
                else:
                    pass

                if command == 'left':
                    speed_II = speed_I
                    speed_I = speed - speed_I
                    dove_Left_I(-speed_II, 3 * (speed - speed_II))
                    dove_Right_II(speed_II, 3 * (speed - speed_II))
                    dove_Left_III(-speed_II, 3 * (speed - speed_II))

                    dove_Right_I(-speed_II, -10)
                    dove_Left_II(speed_II, -10)
                    dove_Right_III(-speed_II, -10)
                    time.sleep(timeLast / dpi)
                elif command == 'right':
                    speed_II = speed_I
                    speed_I = speed - speed_I
                    dove_Left_I(speed_II, 3 * (speed - speed_II))
                    dove_Right_II(-speed_II, 3 * (speed - speed_II))
                    dove_Left_III(speed_II, 3 * (speed - speed_II))

                    dove_Right_I(speed_II, -10)
                    dove_Left_II(-speed_II, -10)
                    dove_Right_III(speed_II, -10)
                    time.sleep(timeLast / dpi)
                else:
                    pass

                if move_stu == 0 and command == 'no':
                    break
        elif step_input == 3:
            for speed_I in range(0, (speed + int(speed / dpi)), int(speed / dpi)):
                if move_stu and command == 'no':
                    speed_II = speed_I
                    speed_I = speed - speed_I
                    dove_Left_I(speed_I, -10)
                    dove_Right_II(speed_I, -10)
                    dove_Left_III(speed_I, -10)

                    dove_Right_I(-speed_I, 3 * speed_II)
                    dove_Left_II(-speed_I, 3 * speed_II)
                    dove_Right_III(-speed_I, 3 * speed_II)
                    time.sleep(timeLast / dpi)
                else:
                    pass

                if command == 'left':
                    speed_II = speed_I
                    speed_I = speed - speed_I
                    dove_Left_I(-speed_I, -10)
                    dove_Right_II(speed_I, -10)
                    dove_Left_III(-speed_I, -10)

                    dove_Right_I(-speed_I, 3 * speed_II)
                    dove_Left_II(speed_I, 3 * speed_II)
                    dove_Right_III(-speed_I, 3 * speed_II)
                    time.sleep(timeLast / dpi)
                elif command == 'right':
                    speed_II = speed_I
                    speed_I = speed - speed_I
                    dove_Left_I(speed_I, -10)
                    dove_Right_II(-speed_I, -10)
                    dove_Left_III(speed_I, -10)

                    dove_Right_I(speed_I, 3 * speed_II)
                    dove_Left_II(-speed_I, 3 * speed_II)
                    dove_Right_III(speed_I, 3 * speed_II)
                    time.sleep(timeLast / dpi)
                else:
                    pass

                if move_stu == 0 and command == 'no':
                    break
        elif step_input == 4:
            for speed_I in range(0, (speed + int(speed / dpi)), int(speed / dpi)):
                if move_stu and command == 'no':
                    speed_II = speed_I
                    speed_I = speed - speed_I
                    dove_Left_I(-speed_II, -10)
                    dove_Right_II(-speed_II, -10)
                    dove_Left_III(-speed_II, -10)

                    dove_Right_I(speed_II, 3 * (speed - speed_II))
                    dove_Left_II(speed_II, 3 * (speed - speed_II))
                    dove_Right_III(speed_II, 3 * (speed - speed_II))
                    time.sleep(timeLast / dpi)
                else:
                    pass

                if command == 'left':
                    speed_II = speed_I
                    speed_I = speed - speed_I
                    dove_Left_I(speed_II, -10)
                    dove_Right_II(-speed_II, -10)
                    dove_Left_III(speed_II, -10)

                    dove_Right_I(speed_II, 3 * (speed - speed_II))
                    dove_Left_II(-speed_II, 3 * (speed - speed_II))
                    dove_Right_III(speed_II, 3 * (speed - speed_II))
                    time.sleep(timeLast / dpi)
                elif command == 'right':
                    speed_II = speed_I
                    speed_I = speed - speed_I
                    dove_Left_I(-speed_II, -10)
                    dove_Right_II(speed_II, -10)
                    dove_Left_III(-speed_II, -10)

                    dove_Right_I(-speed_II, 3 * (speed - speed_II))
                    dove_Left_II(speed_II, 3 * (speed - speed_II))
                    dove_Right_III(-speed_II, 3 * (speed - speed_II))
                    time.sleep(timeLast / dpi)
                else:
                    pass

                if move_stu == 0 and command == 'no':
                    break
    else:
        speed = -speed
        if step_input == 1:
            for speed_I in range(0, (speed + int(speed / dpi)), int(speed / dpi)):
                if move_stu and command == 'no':
                    speed_II = speed_I
                    speed_I = speed - speed_I
                    dove_Left_I(speed_I, 3 * speed_II)
                    dove_Right_II(speed_I, 3 * speed_II)
                    dove_Left_III(speed_I, 3 * speed_II)

                    dove_Right_I(-speed_I, -10)
                    dove_Left_II(-speed_I, -10)
                    dove_Right_III(-speed_I, -10)
                    time.sleep(timeLast / dpi)
                else:
                    pass
        elif step_input == 2:
            for speed_I in range(0, (speed + int(speed / dpi)), int(speed / dpi)):
                if move_stu and command == 'no':
                    speed_II = speed_I
                    speed_I = speed - speed_I
                    dove_Left_I(-speed_II, 3 * (speed - speed_II))
                    dove_Right_II(-speed_II, 3 * (speed - speed_II))
                    dove_Left_III(-speed_II, 3 * (speed - speed_II))

                    dove_Right_I(speed_II, -10)
                    dove_Left_II(speed_II, -10)
                    dove_Right_III(speed_II, -10)
                    time.sleep(timeLast / dpi)
                else:
                    pass
        elif step_input == 3:
            for speed_I in range(0, (speed + int(speed / dpi)), int(speed / dpi)):
                if move_stu and command == 'no':
                    speed_II = speed_I
                    speed_I = speed - speed_I
                    dove_Left_I(-speed_I, -10)
                    dove_Right_II(-speed_I, -10)
                    dove_Left_III(-speed_I, -10)

                    dove_Right_I(speed_I, 3 * speed_II)
                    dove_Left_II(speed_I, 3 * speed_II)
                    dove_Right_III(speed_I, 3 * speed_II)
                    time.sleep(timeLast / dpi)
                else:
                    pass
        elif step_input == 4:
            for speed_I in range(0, (speed + int(speed / dpi)), int(speed / dpi)):
                if move_stu and command == 'no':
                    speed_II = speed_I
                    speed_I = speed - speed_I
                    dove_Left_I(speed_II, -10)
                    dove_Right_II(speed_II, -10)
                    dove_Left_III(speed_II, -10)

                    dove_Right_I(-speed_II, 3 * (speed - speed_II))
                    dove_Left_II(-speed_II, 3 * (speed - speed_II))
                    dove_Right_III(-speed_II, 3 * (speed - speed_II))
                    time.sleep(timeLast / dpi)
                else:
                    pass


def steady_X():
    if leftSide_direction:
        pwm.set_pwm(0, 0, pwm0 + steady_X_set)
        pwm.set_pwm(2, 0, pwm2)
        pwm.set_pwm(4, 0, pwm4 - steady_X_set)
    else:
        pwm.set_pwm(0, 0, pwm0 + steady_X_set)
        pwm.set_pwm(2, 0, pwm2)
        pwm.set_pwm(4, 0, pwm4 - steady_X_set)

    if rightSide_direction:
        pwm.set_pwm(10, 0, pwm10 + steady_X_set)
        pwm.set_pwm(8, 0, pwm8)
        pwm.set_pwm(6, 0, pwm6 - steady_X_set)
    else:
        pwm.set_pwm(10, 0, pwm10 - steady_X_set)
        pwm.set_pwm(8, 0, pwm8)
        pwm.set_pwm(6, 0, pwm6 + steady_X_set)


def steady():
    """Enhanced balance control with responsive visual feedback"""
    global X_fix_output, Y_fix_output
    if mpu6050_connection:
        try:
            accelerometer_data = sensor.get_accel_data()
            X = kalman_filter_X.kalman(accelerometer_data['x'])
            Y = kalman_filter_Y.kalman(accelerometer_data['y'])

            # Calculate tilt severity
            tilt_magnitude = (abs(X) + abs(Y)) / 2

            if tilt_magnitude > 5:
                # Red warning for severe tilt
                _safe_light_call(led.fadeToColor, 255, 0, 0)
            elif tilt_magnitude > 2:
                # Yellow warning for moderate tilt
                _safe_light_call(led.fadeToColor, 255, 255, 0)
            else:
                # Green for stable
                _safe_light_call(led.fadeToColor, 0, 255, 0)

            # Adjust brightness based on motion
            brightness = max(50, 255 - int(tilt_magnitude * 20))
            _safe_light_call(led.setBrightness, brightness)

            if X < -2:
                _safe_light_call(led.turnLeft)
            elif X > 2:
                _safe_light_call(led.turnRight)

            # Return to idle if very stable
            if abs(X) <= 1 and abs(Y) <= 1:
                _safe_light_call(led.setStatus, 'idle')

        except Exception as e:
            _safe_light_call(led.setStatus, 'error')
            print(f"Balance error: {e}")


def steadyTest():
    if leftSide_direction:
        pwm.set_pwm(0, 0, pwm0 + steady_X)
        pwm.set_pwm(2, 0, pwm2)
        pwm.set_pwm(4, 0, pwm4 - steady_X)
    else:
        pwm.set_pwm(0, 0, pwm0 + steady_X)
        pwm.set_pwm(2, 0, pwm2)
        pwm.set_pwm(4, 0, pwm4 - steady_X)

    if rightSide_direction:
        pwm.set_pwm(10, 0, pwm10 + steady_X)
        pwm.set_pwm(8, 0, pwm8)
        pwm.set_pwm(6, 0, pwm6 - steady_X)
    else:
        pwm.set_pwm(10, 0, pwm10 - steady_X)
        pwm.set_pwm(8, 0, pwm8)
        pwm.set_pwm(6, 0, pwm6 + steady_X)

    while 1:
        left_H = steady_range_Min
        right_H = steady_range_Max
        left_I(0, 35, left_H)
        left_II(0, 35, left_H)
        left_III(0, 35, left_H)

        right_I(0, 35, right_H)
        right_II(0, 35, right_H)
        right_III(0, 35, right_H)

        time.sleep(1)

        left_H = 130
        right_H = -40
        left_I(0, 35, left_H)
        left_II(0, 35, left_H)
        left_III(0, 35, left_H)

        right_I(0, 35, right_H)
        right_II(0, 35, right_H)
        right_III(0, 35, right_H)

        time.sleep(1)


def look_up(wiggle=look_wiggle):
    global Up_Down_input
    if Up_Down_direction:
        Up_Down_input += wiggle
        Up_Down_input = ctrl_range(Up_Down_input, Up_Down_Max, Up_Down_Min)
    else:
        Up_Down_input -= wiggle
        Up_Down_input = ctrl_range(Up_Down_input, Up_Down_Max, Up_Down_Min)
    pwm.set_pwm(13, 0, Up_Down_input)


def look_down(wiggle=look_wiggle):
    global Up_Down_input
    if Up_Down_direction:
        Up_Down_input -= wiggle
        Up_Down_input = ctrl_range(Up_Down_input, Up_Down_Max, Up_Down_Min)
    else:
        Up_Down_input += wiggle
        Up_Down_input = ctrl_range(Up_Down_input, Up_Down_Max, Up_Down_Min)
    pwm.set_pwm(13, 0, Up_Down_input)


def look_left(wiggle=look_wiggle):
    global Left_Right_input
    if Left_Right_direction:
        Left_Right_input += wiggle
        Left_Right_input = ctrl_range(Left_Right_input, Left_Right_Max, Left_Right_Min)
    else:
        Left_Right_input -= wiggle
        Left_Right_input = ctrl_range(Left_Right_input, Left_Right_Max, Left_Right_Min)
    pwm.set_pwm(12, 0, Left_Right_input)


def look_right(wiggle=look_wiggle):
    global Left_Right_input
    if Left_Right_direction:
        Left_Right_input -= wiggle
        Left_Right_input = ctrl_range(Left_Right_input, Left_Right_Max, Left_Right_Min)
    else:
        Left_Right_input += wiggle
        Left_Right_input = ctrl_range(Left_Right_input, Left_Right_Max, Left_Right_Min)
    pwm.set_pwm(12, 0, Left_Right_input)


def look_home():
    global Left_Right_input, Up_Down_input
    pwm.set_pwm(13, 0, 300)
    pwm.set_pwm(12, 0, 300)
    Left_Right_input = 300
    Up_Down_input = 300


def relesae():
    pwm.set_all_pwm(0, 0)


def clean_all():
    """Clean shutdown with visual indication"""
    _safe_light_call(led.setStatus, 'warning')  # Show warning state
    time.sleep(0.5)
    pwm.set_all_pwm(0, 0)
    _safe_light_call(led.pause)
    _safe_light_call(led.setColor, 0, 0, 0)  # Turn off all LEDs


def destroy():
    clean_all()


SmoothMode = 0
steadyMode = 0

step_set = 1
speed_set = 100
DPI = 17

new_frame = 0
direction_command = 'no'
turn_command = 'no'


def move_thread():
    global step_set
    stand_stu = 1
    if not steadyMode:
        if direction_command == 'forward' and turn_command == 'no':
            if SmoothMode:
                dove(step_set, 35, 0.001, DPI, 'no')
                step_set += 1
                if step_set == 5:
                    step_set = 1

            else:
                move(step_set, 35, 'no')
                time.sleep(0.1)
                step_set += 1
                if step_set == 5:
                    step_set = 1

        elif direction_command == 'backward' and turn_command == 'no':
            if SmoothMode:
                dove(step_set, -35, 0.001, DPI, 'no')
                step_set += 1
                if step_set == 5:
                    step_set = 1

            else:
                move(step_set, -35, 'no')
                time.sleep(0.1)
                step_set += 1
                if step_set == 5:
                    step_set = 1

        else:
            pass

        if turn_command != 'no':
            if SmoothMode:
                dove(step_set, 35, 0.001, DPI, turn_command)
                step_set += 1
                if step_set == 5:
                    step_set = 1

            else:
                move(step_set, 35, turn_command)
                time.sleep(0.1)
                step_set += 1
                if step_set == 5:
                    step_set = 1

        else:
            pass

        if turn_command == 'no' and direction_command == 'stand':
            stand()
            step_set = 1
        pass
    else:
        steady_X()
        steady()


class RobotM(threading.Thread):
    def __init__(self, *args, **kwargs):
        super(RobotM, self).__init__(*args, **kwargs)
        self.__flag = threading.Event()
        self.__flag.clear()

    def pause(self):
        # print('......................pause..........................')
        self.__flag.clear()

    def resume(self):
        self.__flag.set()

    def run(self):
        while 1:
            self.__flag.wait()
            move_thread()
            pass


rm = RobotM()
rm.start()
rm.pause()

"""Movement and control parameter handling"""


class ParameterHandler:
    def __init__(self):
        self.movement_sensitivity = 1.0
        self.head_speed = 1.0
        self.color_threshold = 50

    def scale_movement(self, command, value):
        """Scale movement commands based on sensitivity"""
        return value * self.movement_sensitivity

    def scale_head_movement(self, command, value):
        """Scale head movement based on speed setting"""
        return value * self.head_speed

    def update_parameters(self, **kwargs):
        """Update runtime parameters"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, float(value))

    def get_color_threshold(self):
        """Get current color detection threshold"""
        return self.color_threshold


# Singleton instance
params = ParameterHandler()


# --- Modify commandInput to integrate hop with a speed parameter ---
def commandInput(command_input, speed=20):
    global direction_command, turn_command, SmoothMode, steadyMode

    if command_input == 'forward':
        direction_command = 'forward'
        rm.resume()
    elif command_input == 'backward':
        direction_command = 'backward'
        rm.resume()
    elif 'stand' in command_input:
        direction_command = 'stand'
        rm.pause()
    elif command_input == 'left':
        turn_command = 'left'
        rm.resume()
    elif command_input == 'right':
        turn_command = 'right'
        rm.resume()
    elif 'TS' in command_input:
        turn_command = 'no'
        rm.pause()
    elif command_input == 'hop':
        hop(speed=speed)
        return
    elif command_input == 'automaticOff':
        SmoothMode = 0
        steadyMode = 0
        rm.pause()
    elif command_input == 'automatic':
        rm.resume()
        SmoothMode = 1
    elif command_input == 'KD':
        steadyMode = 1
        rm.resume()
    elif command_input == 'speech':
        steadyMode = 1
        rm.resume()
    elif command_input == 'speechOff':
        SmoothMode = 0
        steadyMode = 0
        rm.pause()


# ... (Other command handling as needed) ...


def handle_parameter_update(params, command_data):
    """Handle parameter update commands from client"""
    try:
        # Parse parameter command: "param_update name value"
        _, param_name, value = command_data.split()
        value = float(value)  # Convert to float as all our params are numeric

        # Kalman filter parameters
        if param_name in ['Q', 'R', 'alpha', 'history']:
            if param_name == 'Q':
                kalman_filter_X.Q = value
                kalman_filter_Y.Q = value
            elif param_name == 'R':
                kalman_filter_X.R = value
                kalman_filter_Y.R = value
            elif param_name == 'alpha':
                kalman_filter_X.alpha_R = value
                kalman_filter_Y.alpha_R = value
                kalman_filter_X.alpha_Q = value * 0.1  # Keep Q learning rate lower
                kalman_filter_Y.alpha_Q = value * 0.1
            elif param_name == 'history':
                kalman_filter_X.history_max_size = int(value)
                kalman_filter_Y.history_max_size = int(value)

        # PID parameters
        elif param_name in ['P', 'I', 'D', 'windup']:
            if param_name == 'P':
                X_pid.SetKp(value)
                Y_pid.SetKp(value)
            elif param_name == 'I':
                X_pid.SetKi(value)
                Y_pid.SetKi(value)
            elif param_name == 'D':
                X_pid.SetKd(value)
                Y_pid.SetKd(value)
            elif param_name == 'windup':
                X_pid.SetWindup(value)
                Y_pid.SetWindup(value)

        # Movement parameters
        elif param_name in ['speed_scale', 'turn_scale', 'step_size', 'smoothing']:
            if param_name == 'speed_scale':
                params.movement_sensitivity = value
            elif param_name == 'turn_scale':
                params.turn_sensitivity = value
            elif param_name == 'step_size':
                global step_set
                step_set = int(value)
            elif param_name == 'smoothing':
                params.movement_smoothing = value

        # Balance parameters
        elif param_name in ['x_target', 'y_target', 'sensitivity', 'threshold']:
            if param_name == 'x_target':
                global target_X
                target_X = value
            elif param_name == 'y_target':
                global target_Y
                target_Y = value
            elif param_name == 'sensitivity':
                params.balance_sensitivity = value
            elif param_name == 'threshold':
                params.stability_threshold = value

        return True
    except Exception as e:
        print(f"Error updating parameter: {e}")
        return False


def get_monitor_data():
    """Collect current monitoring data for parameter panel"""
    monitor_data = {
        'kalman_x': kalman_filter_X.get_parameters(),
        'kalman_y': kalman_filter_Y.get_parameters(),
        'pid_x': X_pid.get_status(),
        'pid_y': Y_pid.get_status(),
        'balance_error': abs(target_X - kalman_filter_X.kalman_adc_old) + abs(
            target_Y - kalman_filter_Y.kalman_adc_old),
        'stability': calc_stability_metric()
    }
    return json.dumps(monitor_data)


def calc_stability_metric():
    """Calculate overall stability metric from 0-100%"""
    if not mpu6050_connection:
        return 0

    try:
        accel_data = sensor.get_accel_data()
        x_error = abs(accel_data['x'] - target_X)
        y_error = abs(accel_data['y'] - target_Y)

        # Convert errors to a percentage (lower is better)
        max_error = 2.0  # Maximum expected error in g's
        error_percent = ((x_error + y_error) / 2) / max_error

        # Convert to stability percentage (higher is better)
        stability = max(0, min(100, 100 * (1 - error_percent)))
        return stability
    except:
        return 0


if __name__ == '__main__':
    step = 1
    move_stu = 1
    try:
        # '''
        while 1:
            move(step, 35, 'no')
            step += 1
            if step > 4:
                step = 1
            time.sleep(0.08)
        # '''
        '''
        while 1:
            dove(1,-35,0.01,17,'no')
            dove(2,-35,0.01,17,'no')
            dove(3,-35,0.01,17,'no')
            dove(4,-35,0.01,17,'no')
        '''

        # mpu6050Test()
        # print(sensor.get_temp())
        '''
        steady_X()
        while 1:
            steady()
            time.sleep(0.02)
        '''

        '''
        for i in range(0,9):
            look_left()
            time.sleep(1)
        for i in range(0,16):
            look_right()
            time.sleep(1)	
        time.sleep(1)
        look_home()
        '''

    # pwm.set_all_pwm(0,0)
    # pwm.set_all_pwm(0, 300)
    # time.sleep(10)
    except KeyboardInterrupt:
        pwm.set_all_pwm(0, 300)
        time.sleep(1)
# clean_all()
