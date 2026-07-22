from dataclasses import dataclass


@dataclass(slots=True)
class Color:

    red: float = 0
    green: float = 0
    blue: float = 0

    def smooth(self, target: "Color", factor: float):

        self.red = self.red * factor + target.red * (1 - factor)
        self.green = self.green * factor + target.green * (1 - factor)
        self.blue = self.blue * factor + target.blue * (1 - factor)

    def clamp(self):

        self.red = min(max(self.red, 0), 255)
        self.green = min(max(self.green, 0), 255)
        self.blue = min(max(self.blue, 0), 255)

        return self

    def to_int(self):

        self.clamp()

        return (
            int(self.red),
            int(self.green),
            int(self.blue),
        )

    def copy(self):

        return Color(
            self.red,
            self.green,
            self.blue,
        )