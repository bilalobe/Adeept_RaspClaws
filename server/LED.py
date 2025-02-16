#!/usr/bin/python3
# File name   : LED.py
# Description : WS_2812
# Website     : based on the code from https://github.com/rpi-ws281x/rpi-ws281x-python/blob/master/examples/strandtest.py
# E-mail      : support@adeept.com
# Author      : original code by Tony DiCola (tony@tonydicola.com)
# Date        : 2018/10/12
import time
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

# Try to import hardware-specific modules, fall back to mock if not available
try:
    from rpi_ws281x import Adafruit_NeoPixel, Color
    HARDWARE_AVAILABLE = True
except ImportError:
    logger.warning("Running in simulation mode - LED hardware not available")
    HARDWARE_AVAILABLE = False
    
    # Mock implementations for development/testing
    def Color(r, g, b):
        return (r << 16) | (g << 8) | b
        
    class MockNeoPixel:
        def __init__(self, num, pin, freq_hz, dma, invert, brightness, channel):
            self.num = num
            self.brightness = brightness
            self.pixels = [(0,0,0)] * num
            
        def begin(self):
            pass
            
        def numPixels(self):
            return self.num
            
        def setPixelColor(self, i, color):
            self.pixels[i] = color
            
        def setBrightness(self, brightness):
            self.brightness = brightness
            
        def show(self):
            # Log the current state for debugging
            logger.debug(f"LED Strip State - Brightness: {self.brightness}")
            logger.debug("First 3 pixels: " + 
                      ", ".join([str(self.pixels[i]) for i in range(min(3, self.num))]))
    
    Adafruit_NeoPixel = MockNeoPixel

class LightPattern(Enum):
    """Available light patterns"""
    SOLID = "solid"
    BREATH = "breath"
    RAINBOW = "rainbow"
    PULSE = "pulse"
    CHASE = "chase"
    OFF = "off"

class LED:
    """WS2812 LED strip controller with enhanced functionality"""
    
    # LED strip configuration
    DEFAULT_CONFIG = {
        'count': 16,
        'pin': 12,
        'freq_hz': 800000,
        'dma': 10,
        'brightness': 255,
        'invert': False,
        'channel': 0
    }

    def __init__(self, **kwargs):
        """Initialize LED controller with optional custom configuration"""
        self.config = {**self.DEFAULT_CONFIG, **kwargs}
        
        # State tracking
        self._current_pattern = LightPattern.OFF
        self._running = True
        self._brightness = self.config['brightness']
        self._color = (0, 0, 0)
        
        try:
            self.strip = Adafruit_NeoPixel(
                self.config['count'],
                self.config['pin'],
                self.config['freq_hz'],
                self.config['dma'],
                self.config['invert'],
                self._brightness,
                self.config['channel']
            )
            self.strip.begin()
            logger.info("LED strip initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize LED strip: {e}")
            raise

    def set_pattern(self, pattern: LightPattern, **kwargs) -> bool:
        """Set the current light pattern with optional parameters"""
        try:
            self._current_pattern = pattern
            if pattern == LightPattern.OFF:
                self.clear()
            elif pattern == LightPattern.SOLID:
                self.set_color(kwargs.get('color', self._color))
            elif pattern == LightPattern.BREATH:
                self._start_breath(
                    kwargs.get('color', self._color),
                    kwargs.get('speed', 50),
                    kwargs.get('min_brightness', 0),
                    kwargs.get('max_brightness', 255)
                )
            elif pattern == LightPattern.RAINBOW:
                self._start_rainbow(kwargs.get('speed', 20))
            elif pattern == LightPattern.PULSE:
                self._start_pulse(
                    kwargs.get('color', self._color),
                    kwargs.get('speed', 50)
                )
            return True
        except Exception as e:
            logger.error(f"Failed to set pattern {pattern}: {e}")
            return False

    def set_color(self, color: Tuple[int, int, int]) -> bool:
        """Set a solid color for all LEDs"""
        try:
            self._color = color
            color_value = Color(*color)
            for i in range(self.strip.numPixels()):
                self.strip.setPixelColor(i, color_value)
            self.strip.show()
            return True
        except Exception as e:
            logger.error(f"Failed to set color {color}: {e}")
            return False

    def set_brightness(self, brightness: int) -> bool:
        """Set the brightness level (0-255)"""
        try:
            self._brightness = max(0, min(255, brightness))
            self.strip.setBrightness(self._brightness)
            self.strip.show()
            return True
        except Exception as e:
            logger.error(f"Failed to set brightness {brightness}: {e}")
            return False

    def clear(self) -> bool:
        """Turn off all LEDs"""
        try:
            for i in range(self.strip.numPixels()):
                self.strip.setPixelColor(i, Color(0, 0, 0))
            self.strip.show()
            return True
        except Exception as e:
            logger.error(f"Failed to clear LEDs: {e}")
            return False

    def cleanup(self):
        """Clean up resources"""
        self._running = False
        self.clear()

    def _start_breath(self, color: Tuple[int, int, int], speed: int, 
                     min_brightness: int, max_brightness: int):
        """Start breathing pattern"""
        r, g, b = color
        while self._running and self._current_pattern == LightPattern.BREATH:
            for brightness in range(min_brightness, max_brightness, speed):
                if not self._running or self._current_pattern != LightPattern.BREATH:
                    break
                scaled_color = tuple(int(c * brightness / 255) for c in (r, g, b))
                self.set_color(scaled_color)
                time.sleep(0.01)
            for brightness in range(max_brightness, min_brightness, -speed):
                if not self._running or self._current_pattern != LightPattern.BREATH:
                    break
                scaled_color = tuple(int(c * brightness / 255) for c in (r, g, b))
                self.set_color(scaled_color)
                time.sleep(0.01)

    def _start_rainbow(self, speed: int):
        """Start rainbow pattern"""
        def wheel(pos):
            if pos < 85:
                return Color(pos * 3, 255 - pos * 3, 0)
            elif pos < 170:
                pos -= 85
                return Color(255 - pos * 3, 0, pos * 3)
            else:
                pos -= 170
                return Color(0, pos * 3, 255 - pos * 3)

        while self._running and self._current_pattern == LightPattern.RAINBOW:
            for j in range(256):
                if not self._running or self._current_pattern != LightPattern.RAINBOW:
                    break
                for i in range(self.strip.numPixels()):
                    self.strip.setPixelColor(i, wheel((i + j) & 255))
                self.strip.show()
                time.sleep(speed / 1000.0)

    def _start_pulse(self, color: Tuple[int, int, int], speed: int):
        """Start pulse pattern"""
        r, g, b = color
        while self._running and self._current_pattern == LightPattern.PULSE:
            # Quick bright pulse
            self.set_color((r, g, b))
            time.sleep(0.1)
            self.set_color((r//4, g//4, b//4))
            time.sleep(speed / 100.0)

    def get_status(self) -> dict:
        """Get current LED strip status"""
        return {
            'pattern': self._current_pattern.value,
            'color': self._color,
            'brightness': self._brightness,
            'running': self._running
        }

if __name__ == '__main__':
    # Example usage
    led = LED()
    try:
        # Demo different patterns
        led.set_pattern(LightPattern.SOLID, color=(255, 0, 0))  # Red
        time.sleep(1)
        led.set_pattern(LightPattern.BREATH, color=(0, 255, 0))  # Breathing green
        time.sleep(5)
        led.set_pattern(LightPattern.RAINBOW)  # Rainbow effect
        time.sleep(5)
        led.set_pattern(LightPattern.OFF)  # Turn off
    except KeyboardInterrupt:
        led.cleanup()
    except Exception as e:
        logger.error(f"LED demo failed: {e}")
        led.cleanup()
