from __future__ import annotations

import json
import shutil
import subprocess
import time
from io import BytesIO
from urllib.parse import unquote, urlparse

from PIL import Image

from ble_led.color import Color


def _average_from_png_bytes(data: bytes) -> Color:
    img = Image.open(BytesIO(data)).convert("RGB")
    img = img.resize((64, 36))  # downscale hard, we only need an average

    pixels = list(img.getdata())
    n = len(pixels)
    r = sum(p[0] for p in pixels) // n
    g = sum(p[1] for p in pixels) // n
    b = sum(p[2] for p in pixels) // n
    return Color(red=r, green=g, blue=b)


# ---------------------------------------------------------------------
# grim: works on wlroots-based compositors (Sway, Hyprland, river, ...).
# No permission dialog, fast, simplest option when available.
# ---------------------------------------------------------------------
class GrimCapture:
    def __init__(self, monitor: int = 1):
        if shutil.which("grim") is None:
            raise RuntimeError("grim executable not found on PATH")

        self._output = None
        outputs = self._sway_output_names()
        if outputs and 0 < monitor <= len(outputs):
            self._output = outputs[monitor - 1]

        # Fail fast here rather than lazily on first average_color() call,
        # so ScreenCapture can fall through to the next backend.
        self._run(probe=True)

    @staticmethod
    def _sway_output_names() -> list[str]:
        """Best-effort per-monitor support via `swaymsg` (sway only).
        Returns [] on any other wlroots compositor / if unavailable,
        in which case grim just captures the whole virtual screen."""
        if shutil.which("swaymsg") is None:
            return []
        try:
            out = subprocess.run(
                ["swaymsg", "-t", "get_outputs", "-r"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                check=True,
                timeout=2,
            ).stdout
            return [o["name"] for o in json.loads(out)]
        except Exception:
            return []

    def _run(self, probe: bool = False) -> bytes:
        cmd = ["grim", "-t", "png"]
        if self._output:
            cmd += ["-o", self._output]
        cmd.append("-")

        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            timeout=5,
        )
        return proc.stdout

    def average_color(self) -> Color:
        return _average_from_png_bytes(self._run())

    def close(self) -> None:
        pass


# ---------------------------------------------------------------------
# XDG Desktop Portal Screenshot interface: works on GNOME, KDE, and any
# other portal-backed compositor. Most implementations show a consent
# dialog (at least the first time, sometimes every call depending on
# the desktop). Good for periodic sampling; not ideal for tight polling
# loops. Requires PyGObject (python3-gi) system package.
# ---------------------------------------------------------------------
_BUS_NAME = "org.freedesktop.portal.Desktop"
_OBJ_PATH = "/org/freedesktop/portal/desktop"
_IFACE = "org.freedesktop.portal.Screenshot"


class PortalScreenshotCapture:
    def __init__(self):
        try:
            import gi

            gi.require_version("Gio", "2.0")
            gi.require_version("GLib", "2.0")
            from gi.repository import Gio, GLib
        except (ImportError, ValueError) as exc:
            raise RuntimeError(
                "PyGObject (python3-gi) is required for the xdg-desktop-"
                "portal Wayland fallback"
            ) from exc

        self._Gio = Gio
        self._GLib = GLib
        self._connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        sender = self._connection.get_unique_name()
        self._sender_token = sender.lstrip(":").replace(".", "_")
        self._counter = 0

        # Fail fast if the interface truly isn't available (rather than
        # discovering that on the first real average_color() call).
        self._request_screenshot(timeout=5)

    def _request_screenshot(self, timeout: float = 30) -> str:
        Gio, GLib = self._Gio, self._GLib

        self._counter += 1
        token = f"blecap{self._counter}"
        request_path = (
            f"/org/freedesktop/portal/desktop/request/"
            f"{self._sender_token}/{token}"
        )

        state = {"done": False, "code": None, "results": None}

        def on_response(connection, sender_name, object_path, iface, signal, params):
            state["code"], state["results"] = params.unpack()
            state["done"] = True

        sub_id = self._connection.signal_subscribe(
            _BUS_NAME,
            "org.freedesktop.portal.Request",
            "Response",
            request_path,
            None,
            Gio.DBusSignalFlags.NONE,
            on_response,
        )

        try:
            options = {
                "handle_token": GLib.Variant("s", token),
                "interactive": GLib.Variant("b", False),
            }
            params = GLib.Variant("(sa{sv})", ("", options))

            self._connection.call_sync(
                _BUS_NAME,
                _OBJ_PATH,
                _IFACE,
                "Screenshot",
                params,
                GLib.VariantType.new("(o)"),
                Gio.DBusCallFlags.NONE,
                -1,
                None,
            )

            ctx = GLib.MainContext.default()
            deadline = time.monotonic() + timeout
            while not state["done"] and time.monotonic() < deadline:
                ctx.iteration(True)
        finally:
            self._connection.signal_unsubscribe(sub_id)

        if not state["done"]:
            raise TimeoutError("Timed out waiting for portal Screenshot response")
        if state["code"] != 0:
            raise RuntimeError(
                f"Screenshot portal request failed or was cancelled "
                f"(code {state['code']})"
            )

        return state["results"]["uri"]

    def average_color(self) -> Color:
        uri = self._request_screenshot()
        path = unquote(urlparse(uri).path)

        with open(path, "rb") as f:
            data = f.read()

        return _average_from_png_bytes(data)

    def close(self) -> None:
        pass