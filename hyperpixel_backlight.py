"""
Support class to control the backlight power on a HyperPixel display.
"""
import logging
import os

_LOGGER = logging.getLogger(__name__)

try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None


BACKLIGHT_PIN = 19


class Backlight():

    def __init__(self, initial_value=False):
        """Initialize the backlight instance."""
        if not GPIO:
            self.active = False
            _LOGGER.error("Backlight control not available, please ensure RPi.GPIO python3 package is installed")
            return

        GPIO.setwarnings(False)
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(BACKLIGHT_PIN, GPIO.OUT)
            self.active = True
        except RuntimeError:
            self.active = False
            username = os.environ.get('USER')
            _LOGGER.error("Backlight control not available, please ensure '%s' is part of group 'gpio'.", username)
            _LOGGER.error("  To add user to group: `sudo gpasswd -a %s gpio`", username)
        else:
            self.power = initial_value

    def set_power(self, new_state):
        """Control the backlight power of the HyperPixel display."""
        if not self.active:
            return

        if new_state is False and self.power:
            _LOGGER.debug("Going idle, turning backlight off")
        self.power = new_state
        GPIO.output(BACKLIGHT_PIN, new_state)

    def cleanup(self):
        """Return the GPIO setup to initial state."""
        if self.active:
            GPIO.output(BACKLIGHT_PIN, True)
            GPIO.cleanup()
