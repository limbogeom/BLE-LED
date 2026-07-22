from typing import List

LUT_SIZE = 256

class GammaCorrection:

    def __init__(self, gamma: float):
        self.gamma = gamma
        self.lut = self._build()

    def _build(self) -> List[int]:

        return [
            int((i / 255) ** self.gamma * 255)
            for i in range(LUT_SIZE)
        ]
    
    def apply(self, value: int) -> int:
        value = max(0, min(255, value))
        return self.lut[value]
    
    def apply_rgb(self, rgb):

        return (
            self.apply(rgb[0]),
            self.apply(rgb[1]),
            self.apply(rgb[2]),
        )