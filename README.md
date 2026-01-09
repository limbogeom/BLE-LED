# Ambient BLE LED Controller

A lightweight Python script that captures the average screen color and sends it to a BLE LED device in real-time.

* Supports **Windows, Linux, and macOS**
* Adjustable **gamma correction** with **LUT** for high FPS
* Smooth color transitions using a simple **smoothing algorithm**
* **No GUI required** – runs in the terminal
* Graceful **Ctrl+C exit**, automatically turning off the LED

---

## Features

* **Automatic BLE device discovery** (prefix-based)
* **Gamma correction** configurable via code or command-line (`--gamma`)
* **Smooth transitions** with `SMOOTHING` variable
* Ultra-light, minimal dependencies: `bleak`, `mss`
* Fast screen sampling without PIL or numpy

---

## Installation

```bash
pip install -r requirements.txt
```

**Optional:** Linux may require `bluez` installed and running:

```bash
sudo apt install bluez
sudo systemctl enable --now bluetooth
```

---

## Usage

```bash
python led.py [--gamma GAMMA]
```

Example:

```bash
python led.py --gamma 1.2
```

* `--gamma` (float): Gamma correction for LED brightness (default 0.8)
* Press **Ctrl+C** to stop the script and turn off the LED

---

## Configuration

Inside the script:

```python
DEVICE_PREFIX = "ELK-BLEDOB"   # BLE device name prefix
FPS = 10                        # Frames per second
SMOOTHING = 0.2                 # Color smoothing (0-1)
DEFAULT_GAMMA = 0.8             # Default gamma
```

* Adjust **FPS** for smoother or lighter updates
* **SMOOTHING** closer to 1 → slower transitions
* **DEFAULT_GAMMA** adjusts LED brightness

---

## Troubleshooting

### 1. `[org.freedesktop.DBus.Error.ServiceUnknown]` on Linux

* Cause: BlueZ or D-Bus not running
* Solution:

```bash
sudo systemctl enable --now bluetooth
sudo systemctl start bluetooth
sudo usermod -aG bluetooth $USER
```

* Log out and log back in

### 2. Script does not detect your device

* Make sure the BLE device name **starts with DEVICE_PREFIX**
* Ensure the device is **powered on and in range**
* Increase BLE scan timeout if needed

### 3. Screen capture returns black or fails

* On Linux, check if you are running **X11** (not Wayland)
* Some Wayland sessions may block `mss`
* Try a smaller monitor region for faster sampling

### 4. BLE write errors

* Ensure **correct characteristic UUIDs** are listed in `WRITE_UUIDS`
* If using multiple BLE devices, verify which one is active

### 5. Gamma or color too dark/bright

* Adjust gamma via command line or in `DEFAULT_GAMMA`
* Example: `--gamma 1.5` brightens, `--gamma 0.7` darkens

---

## License

MIT License – free to use, modify, and distribute

**By Limbogeom**
