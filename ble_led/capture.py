from __future__ import annotations

from mss import mss
from mss.exception import ScreenShotError

from ble_led.color import Color

import logging

logger = logging.getLogger("ble-led")

class ScreenCapture:

    def __init__(self, monitor: int = 1):
        self.monitor = monitor
        self.sct = mss()

    def close(self):
        self.sct.close()

    def grab(self):

        monitor = self.sct.monitors[self.monitor]

        return self.sct.grab(monitor)
    
    def average_color(self) -> Color:

        try:
            img = self.grab()

            rgb = img.rgb

            pixels = len(rgb) // 3

            r = sum(rgb[0::3]) // pixels
            g = sum(rgb[1::3]) // pixels
            b = sum(rgb[2::3]) // pixels

            return Color(r, g, b)
        
        except ScreenShotError as e:
            logger.exception("Screen capture failed: %s", e)
            return Color()
        
        except Exception as e:
            logger.exception(e)
            return Color()