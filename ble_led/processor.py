from __future__ import annotations

from ble_led.color import Color
from ble_led.gamma import GammaCorrection

import logging

logger = logging.getLogger("ble-led")

class ColorProcessor:

    def __init__(
            self,
            gamma: GammaCorrection,
            smoothing: float,
    ):
        self.gamma = gamma
        self.smoothing = smoothing
        self.previous = Color()

    def process(self, color: Color) -> Color:

        corrected = Color(
            self.gamma.apply(int(color.red)),
            self.gamma.apply(int(color.green)),
            self.gamma.apply(int(color.blue)),
        )

        logger.debug("Color %s -> %s", color, corrected)

        self.previous.smooth(
            corrected,
            self.smoothing
        )

        logger.debug("Smoothing: %s", self.previous)

        return Color(
            *self.previous.to_int()
        )