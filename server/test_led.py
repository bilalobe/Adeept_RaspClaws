#!/usr/bin/env python3
"""Test suite for LED control module."""
import unittest
from unittest.mock import patch, MagicMock
import time
from LED import LED, LightPattern, HARDWARE_AVAILABLE

class TestLEDControl(unittest.TestCase):
    def setUp(self):
        """Set up test cases"""
        self.led = LED()

    def test_initialization(self):
        """Test LED initialization"""
        self.assertEqual(self.led._current_pattern, LightPattern.OFF)
        self.assertTrue(self.led._running)
        self.assertEqual(self.led._brightness, LED.DEFAULT_CONFIG['brightness'])
        self.assertEqual(self.led._color, (0, 0, 0))

    def test_pattern_setting(self):
        """Test pattern setting functionality"""
        test_color = (255, 0, 0)
        # Test solid pattern
        self.assertTrue(self.led.set_pattern(LightPattern.SOLID, color=test_color))
        self.assertEqual(self.led._current_pattern, LightPattern.SOLID)
        self.assertEqual(self.led._color, test_color)

        # Test breath pattern
        self.assertTrue(self.led.set_pattern(LightPattern.BREATH, color=test_color))
        self.assertEqual(self.led._current_pattern, LightPattern.BREATH)

        # Test off pattern
        self.assertTrue(self.led.set_pattern(LightPattern.OFF))
        self.assertEqual(self.led._current_pattern, LightPattern.OFF)

    def test_brightness_control(self):
        """Test brightness control"""
        test_values = [-10, 0, 127, 255, 300]
        expected = [0, 0, 127, 255, 255]  # Expected after clamping
        
        for test, expect in zip(test_values, expected):
            self.led.set_brightness(test)
            self.assertEqual(self.led._brightness, expect)

    def test_color_setting(self):
        """Test color setting functionality"""
        test_colors = [
            (255, 0, 0),    # Red
            (0, 255, 0),    # Green
            (0, 0, 255),    # Blue
            (255, 255, 255) # White
        ]
        
        for color in test_colors:
            self.assertTrue(self.led.set_color(color))
            self.assertEqual(self.led._color, color)

    def test_cleanup(self):
        """Test cleanup functionality"""
        self.led.cleanup()
        self.assertFalse(self.led._running)
        # Verify LEDs are cleared
        pixels = self.led.strip.pixels if not HARDWARE_AVAILABLE else None
        if pixels:  # Only check in simulation mode
            self.assertTrue(all(p == (0,0,0) for p in pixels))

    def test_status_reporting(self):
        """Test status reporting"""
        test_color = (255, 0, 0)
        test_brightness = 128
        
        self.led.set_color(test_color)
        self.led.set_brightness(test_brightness)
        self.led.set_pattern(LightPattern.SOLID)
        
        status = self.led.get_status()
        self.assertEqual(status['pattern'], LightPattern.SOLID.value)
        self.assertEqual(status['color'], test_color)
        self.assertEqual(status['brightness'], test_brightness)
        self.assertTrue(status['running'])

    @unittest.skipIf(not HARDWARE_AVAILABLE, "Hardware not available")
    def test_hardware_specific(self):
        """Test hardware-specific functionality"""
        # These tests only run on actual hardware
        test_color = (255, 0, 0)
        self.led.set_pattern(LightPattern.SOLID, color=test_color)
        time.sleep(0.1)  # Allow time for hardware update
        
        # Test rainbow pattern
        self.led.set_pattern(LightPattern.RAINBOW)
        time.sleep(0.1)  # Allow time for hardware update
        
        # Test breathing pattern
        self.led.set_pattern(LightPattern.BREATH, color=(0, 255, 0))
        time.sleep(0.1)  # Allow time for hardware update

def run_tests():
    unittest.main(verbosity=2)