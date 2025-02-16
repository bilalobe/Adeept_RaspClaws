#!/usr/bin/env python3
# File name   : servo.py
# Description : Control lights
# Author	  : William
# Date		: 2019/02/23
import math
import threading
import time

import RPi.GPIO as GPIO
from rpi_ws281x import PixelStrip
from lighting_utils import safe_light_command
from Adeept_RaspClaws.server.LED import Color


class RobotLight(threading.Thread):
    def __init__(self, *args, **kwargs):
        self.LED_COUNT = 16  # Number of LED pixels.
        self.LED_PIN = 12  # GPIO pin connected to the pixels (18 uses PWM!).
        self.LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
        self.LED_DMA = 10  # DMA channel to use for generating signal (try 10)
        self.LED_BRIGHTNESS = 255  # Set to 0 for darkest and 255 for brightest
        self.LED_INVERT = False  # True to invert the signal (when using NPN transistor level shift)
        self.LED_CHANNEL = 0  # set to '1' for GPIOs 13, 19, 41, 45 or 53

        self.colorBreathR = 0
        self.colorBreathG = 0
        self.colorBreathB = 0
        self.breathSteps = 30  # Increased for smoother transitions
        self.currentBrightness = 255

        self.left_R = 22
        self.left_G = 23
        self.left_B = 24

        self.right_R = 10
        self.right_G = 9
        self.right_B = 25

        self.on = GPIO.LOW
        self.off = GPIO.HIGH

        self.lightMode = 'none'  # 'none' 'police' 'breath' 'pulse' 'rainbow' 'status'
        self.currentStatus = 'idle'  # 'idle', 'active', 'warning', 'error'

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(5, GPIO.OUT)
        GPIO.setup(6, GPIO.OUT)
        GPIO.setup(13, GPIO.OUT)

        GPIO.setup(self.left_R, GPIO.OUT)
        GPIO.setup(self.left_G, GPIO.OUT)
        GPIO.setup(self.left_B, GPIO.OUT)
        GPIO.setup(self.right_R, GPIO.OUT)
        GPIO.setup(self.right_G, GPIO.OUT)
        GPIO.setup(self.right_B, GPIO.OUT)

        # Create NeoPixel object with appropriate configuration.
        self.strip = PixelStrip(self.LED_COUNT, self.LED_PIN, self.LED_FREQ_HZ, self.LED_DMA, self.LED_INVERT,
                                self.LED_BRIGHTNESS, self.LED_CHANNEL)
        # Intialize the library (must be called once before other functions).
        self.strip.begin()

        super(RobotLight, self).__init__(*args, **kwargs)
        self.__flag = threading.Event()
        self.__flag.clear()

    def both_off(self):
        GPIO.output(self.left_R, self.off)
        GPIO.output(self.left_G, self.off)
        GPIO.output(self.left_B, self.off)

        GPIO.output(self.right_R, self.off)
        GPIO.output(self.right_G, self.off)
        GPIO.output(self.right_B, self.off)

    def both_on(self):
        GPIO.output(self.left_R, self.on)
        GPIO.output(self.left_G, self.on)
        GPIO.output(self.left_B, self.on)

        GPIO.output(self.right_R, self.on)
        GPIO.output(self.right_G, self.on)
        GPIO.output(self.right_B, self.on)

    def side_on(self, side_X):
        GPIO.output(side_X, self.on)

    def side_off(self, side_X):
        GPIO.output(side_X, self.off)

    def red(self):
        self.side_on(self.right_R)
        self.side_on(self.left_R)

    def green(self):
        self.side_on(self.right_G)
        self.side_on(self.left_G)

    def blue(self):
        self.side_on(self.right_B)
        self.side_on(self.left_B)

    def yellow(self):
        self.red()
        self.green()

    def pink(self):
        self.red()
        self.blue()

    def cyan(self):
        self.blue()
        self.green()

    def turnLeft(self):
        GPIO.output(self.left_G, self.on)
        GPIO.output(self.left_R, self.on)

    def turnRight(self):
        GPIO.output(self.right_G, self.on)
        GPIO.output(self.right_R, self.on)

    # Define functions which animate LEDs in various ways.
    def setColor(self, R, G, B):
        """Wipe color across display a pixel at a time."""
        color = Color(int(R), int(G), int(B))
        for i in range(self.strip.numPixels()):
            self.strip.setPixelColor(i, color)
            self.strip.show()

    def setSomeColor(self, R, G, B, ID):
        color = Color(int(R), int(G), int(B))
        # print(int(R),'  ',int(G),'  ',int(B))
        for i in ID:
            self.strip.setPixelColor(i, color)
            self.strip.show()

    def pause(self):
        self.lightMode = 'none'
        self.setColor(0, 0, 0)
        self.__flag.clear()

    def resume(self):
        self.__flag.set()

    def police(self):
        self.lightMode = 'police'
        self.resume()

    def policeProcessing(self):
        while self.lightMode == 'police':
            for i in range(0, 3):
                self.setSomeColor(0, 0, 255, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11])
                self.blue()
                time.sleep(0.05)
                self.setSomeColor(0, 0, 0, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11])
                self.both_off()
                time.sleep(0.05)
            if self.lightMode != 'police':
                break
            time.sleep(0.1)
            for i in range(0, 3):
                self.setSomeColor(255, 0, 0, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11])
                self.red()
                time.sleep(0.05)
                self.setSomeColor(0, 0, 0, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11])
                self.both_off()
                time.sleep(0.05)
            time.sleep(0.1)

    def breath(self, R_input, G_input, B_input):
        self.lightMode = 'breath'
        self.colorBreathR = R_input
        self.colorBreathG = G_input
        self.colorBreathB = B_input
        self.resume()

    def breathProcessing(self):
        while self.lightMode == 'breath':
            for i in range(0, self.breathSteps):
                if self.lightMode != 'breath':
                    break
                self.setColor(self.colorBreathR * i / self.breathSteps, self.colorBreathG * i / self.breathSteps,
                              self.colorBreathB * i / self.breathSteps)
                time.sleep(0.03)
            for i in range(0, self.breathSteps):
                if self.lightMode != 'breath':
                    break
                self.setColor(self.colorBreathR - (self.colorBreathR * i / self.breathSteps),
                              self.colorBreathG - (self.colorBreathG * i / self.breathSteps),
                              self.colorBreathB - (self.colorBreathB * i / self.breathSteps))
                time.sleep(0.03)

    def frontLight(self, switch):
        if switch == 'on':
            GPIO.output(6, GPIO.HIGH)
            GPIO.output(13, GPIO.HIGH)
        elif switch == 'off':
            GPIO.output(5, GPIO.LOW)
            GPIO.output(13, GPIO.LOW)

    def switch(self, port, status):
        if port == 1:
            if status == 1:
                GPIO.output(5, GPIO.HIGH)
            elif status == 0:
                GPIO.output(5, GPIO.LOW)
            else:
                pass
        elif port == 2:
            if status == 1:
                GPIO.output(6, GPIO.HIGH)
            elif status == 0:
                GPIO.output(6, GPIO.LOW)
            else:
                pass
        elif port == 3:
            if status == 1:
                GPIO.output(13, GPIO.HIGH)
            elif status == 0:
                GPIO.output(13, GPIO.LOW)
            else:
                pass
        else:
            print('Wrong Command: Example--switch(3, 1)->to switch on port3')

    def set_all_switch_off(self):
        self.switch(1, 0)
        self.switch(2, 0)
        self.switch(3, 0)

    def headLight(self, switch):
        if switch == 'on':
            GPIO.output(5, GPIO.HIGH)
        elif switch == 'off':
            GPIO.output(5, GPIO.LOW)

    @safe_light_command
    def setBrightness(self, brightness):
        """Set the overall brightness level (0-255)"""
        self.currentBrightness = max(0, min(255, brightness))
        self.strip.setBrightness(self.currentBrightness)
        self.strip.show()

    @safe_light_command
    def fadeToColor(self, target_R, target_G, target_B, steps=30, delay=0.02):
        """Smoothly transition to a new color"""
        current_R = self.colorBreathR
        current_G = self.colorBreathG
        current_B = self.colorBreathB

        for step in range(steps):
            ratio = step / float(steps)
            r = int(current_R + (target_R - current_R) * ratio)
            g = int(current_G + (target_G - current_G) * ratio)
            b = int(current_B + (target_B - current_B) * ratio)
            self.setColor(r, g, b)
            time.sleep(delay)

        self.colorBreathR = target_R
        self.colorBreathG = target_G
        self.colorBreathB = target_B

    @safe_light_command
    def setStatus(self, status):
        """Set robot status with corresponding light pattern"""
        self.currentStatus = status
        if status == 'idle':
            self.breath(0, 128, 255)  # Calm blue breathing
        elif status == 'active':
            self.breath(0, 255, 0)  # Green breathing
        elif status == 'warning':
            self.breath(255, 165, 0)  # Orange breathing
        elif status == 'error':
            self.breath(255, 0, 0)  # Red breathing

    @safe_light_command
    def rainbow(self):
        """Start rainbow pattern"""
        self.lightMode = 'rainbow'
        self.resume()

    @safe_light_command
    def rainbowProcessing(self):
        """Process rainbow animation"""
        while self.lightMode == 'rainbow':
            for j in range(256):
                if self.lightMode != 'rainbow':
                    break
                for i in range(self.strip.numPixels()):
                    self.strip.setPixelColor(i, self.wheel((i + j) & 255))
                self.strip.show()
                time.sleep(0.02)

    @safe_light_command
    def pulse(self, R, G, B):
        """Start pulsing pattern"""
        self.lightMode = 'pulse'
        self.colorBreathR = R
        self.colorBreathG = G
        self.colorBreathB = B
        self.resume()

    @safe_light_command
    def pulseProcessing(self):
        """Process pulse animation with smoother sine wave"""
        while self.lightMode == 'pulse':
            for i in range(0, 360, 5):  # Smoother steps
                if self.lightMode != 'pulse':
                    break
                ratio = (math.sin(math.radians(i)) + 1) / 2  # Smooth sine wave
                r = int(self.colorBreathR * ratio)
                g = int(self.colorBreathG * ratio)
                b = int(self.colorBreathB * ratio)
                self.setColor(r, g, b)
                time.sleep(0.03)

    def wheel(self, pos):
        """Generate rainbow colors across 0-255 positions."""
        if pos < 85:
            return Color(pos * 3, 255 - pos * 3, 0)
        elif pos < 170:
            pos -= 85
            return Color(255 - pos * 3, 0, pos * 3)
        else:
            pos -= 170
            return Color(0, pos * 3, 255 - pos * 3)

    def lightChange(self):
        if self.lightMode == 'none':
            self.pause()
        elif self.lightMode == 'police':
            self.policeProcessing()
        elif self.lightMode == 'breath':
            self.breathProcessing()
        elif self.lightMode == 'rainbow':
            self.rainbowProcessing()
        elif self.lightMode == 'pulse':
            self.pulseProcessing()

    def run(self):
        while 1:
            self.__flag.wait()
            self.lightChange()
            pass


if __name__ == '__main__':
    RL = RobotLight()
    RL.start()
    RL.breath(70, 70, 255)
    time.sleep(15)
    RL.pause()
    RL.frontLight('off')
    time.sleep(2)
    RL.police()
