#! /usr/bin/python
# File name   : car_dir.py
# Description : By controlling Servo,the camera can move Up and down,
#               left and right and the Ultrasonic wave can <- & ->.
# Website     : www.adeept.com
# E-mail      : support@adeept.com
# Author      : William
# Date        : 2018/08/22
import time


class PID:
    def __init__(self):
        self.Kp = 0
        self.Ki = 0
        self.Kd = 0

        self.windup_guard = 20.0
        self.sample_time = 0.01

        self.current_time = time.time()
        self.last_time = self.current_time

        self.PTerm = 0.0
        self.ITerm = 0.0
        self.DTerm = 0.0
        self.last_error = 0.0
        self.last_output = 0.0

        self.output = 0.0

    def get_status(self):
        """Get current PID controller status"""
        return {
            'P': self.PTerm,
            'I': self.ITerm,
            'D': self.DTerm,
            'output': self.output,
            'error': self.last_error,
            'settings': {
                'Kp': self.Kp,
                'Ki': self.Ki,
                'Kd': self.Kd,
                'windup_guard': self.windup_guard
            }
        }

    def SetWindup(self, windup):
        """Set the windup guard to prevent integral term from growing"""
        self.windup_guard = windup

    def SetKp(self, invar):
        self.Kp = invar

    def SetKi(self, invar):
        self.Ki = invar

    def SetKd(self, invar):
        self.Kd = invar

    def SetPrevError(self, preverror):
        self.prev_error = preverror

    def Initialize(self):
        self.currtime = time.time()
        self.prevtime = self.currtime

        self.prev_error = 0

        self.Cp = 0
        self.Ci = 0
        self.Cd = 0

    def GenOut(self, error):
        self.currtime = time.time()
        dt = self.currtime - self.prevtime
        de = error - self.prev_error

        self.Cp = self.Kp * error
        self.Ci += error * dt

        self.Cd = 0
        if dt > 0:
            self.Cd = de / dt

        self.prevtime = self.currtime
        self.prev_error = error

        return self.Cp + (self.Ki * self.Ci) + (self.Kd * self.Cd)


'''
pid = PID()
pid.SetKp(Kp)
pid.SetKd(Kd)
pid.SetKi(Ki)

fb = 0
outv = 0

PID_loop = True

while PID_loop:
    error = Sp - fb

    outv = pid.GenOut(error)
    AnalogOut(outv)

    time.sleep(0.05)

    fb = AnalogIn(fb_input)
    pass
'''
