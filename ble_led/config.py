from argparse import ArgumentParser, Namespace

DEVICE_PREFIX = "ELK-BLEDOB"

WRITE_UUIDS = (
    "0000fff3-0000-1000-8000-00805f9b34fb",
    "0000ffd9-0000-1000-8000-00805f9b34fb",
)

FPS = 10
SMOOTHING = 0.20
DEFAULT_GAMMA = 0.5

WRITE_WITH_RESPONSE = False
DISCOVERY_TIMEOUT = 5


def parse_args() -> Namespace:
    parser = ArgumentParser(
        prog="ble-led",
        description="Cross-platform BLE Ambilight for Lotus Lantern controllers.",
    )

    parser.add_argument(
        "--gamma",
        type=float,
        default=DEFAULT_GAMMA,
        help="Gamma correction (>0).",
    )

    parser.add_argument(
        "--fps",
        type=int,
        default=FPS,
        help="Update rate (FPS).",
    )

    parser.add_argument(
        "--device",
        type=str,
        default=DEVICE_PREFIX,
        help="BLE device prefix.",
    )

    parser.add_argument(
        "--monitor",
        type=int,
        default=1,
        help="Monitor index.",
    )

    parser.add_argument(
        "--smoothing",
        type=float,
        default=SMOOTHING,
        help="Color smoothing factor (0.0-1.0).",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging.",
    )

    args = parser.parse_args()

    if args.gamma <= 0:
        parser.error("--gamma must be greater than 0.")

    if args.fps <= 0:
        parser.error("--fps must be greater than 0.")

    if not 0 <= args.smoothing <= 1:
        parser.error("--smoothing must be between 0 and 1.")

    return args