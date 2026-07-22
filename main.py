from __future__ import annotations

import asyncio

from ble_led.ble import BLEController
from ble_led.capture import ScreenCapture
from ble_led.config import (
    SMOOTHING,
    parse_args,
)
from ble_led.gamma import GammaCorrection
from ble_led.protocol import (
    RGBColor,
    pack_color,
    pack_init,
)
from ble_led.processor import ColorProcessor
from ble_led.logger import setup_logger


async def main():

    args = parse_args()

    logger = setup_logger(args.debug)

    gamma = GammaCorrection(args.gamma)

    processor = ColorProcessor(
        gamma,
        args.smoothing,
    )

    capture = ScreenCapture(
        monitor=args.monitor,
    )

    ble = BLEController(
        device_prefix=args.device,
    )

    address = await ble.discover()

    if address is None:
        logger.error("Device not found.")
        return

    logger.info("Found device: %s", address)

    logger.info("Connecting...")

    await ble.connect()

    logger.info("Connected.")

    await ble.write(pack_init())

    interval = max(0.01, 1 / args.fps)

    try:

        while True:

            color = processor.process(
                capture.average_color()
            )

            packet = pack_color(
                RGBColor(
                    *color.to_int()
                )
            )

            await ble.write(packet)

            await asyncio.sleep(interval)

    except KeyboardInterrupt:

        logger.info("Stopping...")

    finally:

        capture.close()

        try:
            await ble.write(
                pack_color(
                    RGBColor(0, 0, 0)
                )
            )
        except Exception:
            pass

        await ble.disconnect()

        logger.info("Disconnected.")


if __name__ == "__main__":
    asyncio.run(main())