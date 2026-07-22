from dataclasses import dataclass

START_BYTE = 0x7E
END_BYTE = 0xEF

@dataclass(slots=True)
class RGBColor:
    red: int
    green: int
    blue: int

    def clamp(self) -> "RGBColor":
        self.red = max(0, min(255, self.red))
        self.green = max(0, min(255, self.green))
        self.blue = max(0, min(255, self.blue))
        return self
    
def pack_init() -> bytes:
    return bytes.fromhex(
        "7E0600830F200C0600EF"
    )

def pack_color(color: RGBColor) -> bytes:
    color.clamp()

    return bytes([
        START_BYTE,
        0x07,
        0x05,
        0x03,
        color.red,
        color.green,
        color.blue,
        0x10,
        END_BYTE
    ])

def power(on: bool) -> bytes:

    return bytes([
        START_BYTE,
        0x04,
        0x04,
        0x01 if on else 0x00,
        END_BYTE
    ])

def brightness(level: int) -> bytes:
    level = max(0, min(255, level))

    return bytes([
        START_BYTE,
        0x04,
        0x01,
        level,
        END_BYTE
    ])