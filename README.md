# BLE-LED-AMBILIGHT

Turn your screen into an Ambilight setup. This grabs the average color of
your display in real time and streams it straight to your ELK-BLEDOB LED
strip over Bluetooth — smooth, gamma-corrected, no extra hardware needed.

## Install

```bash
git clone https://github.com/limbogeom/BLE-LED.git
cd BLE-LED
python3 -m venv .venv
source .venv/bin/activate   # .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

That's it — it'll scan for your LED strip, connect, and start mirroring your
screen. Tune it with a few flags if you want:

| Flag           | Default        | What it does                        |
| -------------- | -------------- | ------------------------------------ |
| `--device`     | `ELK-BLEDOB`   | BLE device name prefix to scan for   |
| `--monitor`    | `1`            | Which monitor to capture             |
| `--gamma`      | `0.5`          | Gamma correction                     |
| `--fps`        | `10`           | Update rate                          |
| `--smoothing`  | `0.20`         | How much color transitions ease in   |
| `--debug`      | off            | Verbose per-frame logging            |

## How it works

Screen color → gamma correction + smoothing → packed into the LED strip's
protocol → sent over BLE. Simple pipeline, tuned to avoid flicker while
still feeling responsive.

## License

MIT — see [LICENSE](LICENSE).
