from __future__ import annotations

import asyncio

from ble_led.ble import BLEController
from ble_led.capture import create_capture
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

    logger.info(
        "Starting ble-led (device=%s, monitor=%s, fps=%s, gamma=%s, smoothing=%s)",
        args.device, args.monitor, args.fps, args.gamma, args.smoothing,
    )

    gamma = GammaCorrection(args.gamma)
    logger.debug("Gamma correction LUT built (gamma=%s)", args.gamma)

    processor = ColorProcessor(
        gamma,
        args.smoothing,
    )

    logger.info("Initializing screen capture (monitor=%s)...", args.monitor)
    capture = create_capture(
        args.monitor,
    )
    logger.info("Screen capture ready (backend=%s)", capture.backend)

    ble = BLEController(
        device_prefix=args.device,
    )

    logger.info(
        "Scanning for BLE device (prefix='%s', timeout=%ss)...",
        args.device, ble.timeout,
    )
    address = await ble.discover()

    if address is None:
        logger.error("No BLE device found with prefix '%s'.", args.device)
        capture.close()
        return

    logger.info("Found device: %s", address)

    logger.info("Connecting to %s...", address)
    await ble.connect()
    logger.info("Connected (characteristic=%s)", ble.characteristic)

    await ble.write(pack_init())
    logger.debug("Sent init packet: %s", pack_init().hex())

    interval = max(0.01, 1 / args.fps)
    logger.info(
        "Entering capture loop (interval=%.3fs, target=%.1f FPS)",
        interval, 1 / interval,
    )

    frame_count = 0

    try:

        while True:
            raw_color = capture.average_color()
            logger.debug("Frame %d captured: %s", frame_count, raw_color)

            color = processor.process(raw_color)
            logger.debug("Frame %d processed: %s", frame_count, color)

            packet = pack_color(RGBColor(*color.to_int()))

            await ble.write(packet)
            logger.debug("Frame %d packet sent: %s", frame_count, packet.hex())

            frame_count += 1

            await asyncio.sleep(interval)

    except KeyboardInterrupt:
        logger.info("Interrupted by user, shutting down...")

    except Exception:
        logger.exception("Unexpected error in capture loop")

    finally:

        capture.close()
        logger.debug("Capture backend closed")

        try:
            await ble.write(pack_color(RGBColor(0, 0, 0)))
            logger.debug("Sent shutdown (off) packet")
        except Exception:
            logger.warning("Failed to send shutdown packet", exc_info=True)

        await ble.disconnect()

        logger.info("Disconnected. Processed %d frames.", frame_count)


if __name__ == "__main__":
    asyncio.run(main())