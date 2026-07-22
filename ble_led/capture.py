from __future__ import annotations

import os
import platform
import sys
import warnings

from mss import mss

from ble_led.color import Color


def _windows_version() -> tuple[int, int]:
    v = sys.getwindowsversion()  # type: ignore[attr-defined]
    return v.major, v.minor


def _dxcam_supported() -> bool:
    """dxcam relies on the DXGI Desktop Duplication API, introduced in
    Windows 8 (6.2). Windows 7 (6.1) and older must use the GDI-based
    mss backend instead."""
    return _windows_version() >= (6, 2)


class ScreenCapture:
    """Cross-platform average-screen-color sampler.

    Backend selection, with automatic fallback:
      * Windows 8/10/11 -> dxcam, falling back to mss if dxcam fails
                            to initialize (VM, RDP session, old/no GPU
                            driver, etc.)
      * Windows 7        -> mss (GDI BitBlt; dxcam is not supported)
      * macOS             -> mss
      * Linux X11          -> mss
      * Linux Wayland     -> grim (wlroots compositors: Sway, Hyprland,
                              river, ...), falling back to the
                              XDG Desktop Portal Screenshot interface
                              (GNOME, KDE, and other portal-backed
                              compositors)
    """

    def __init__(self, monitor: int = 1):
        self.monitor = monitor
        self.backend: str | None = None
        self.camera = None

        system = platform.system()

        if system == "Windows":
            self._init_windows()
        elif system == "Linux":
            self._init_linux()
        elif system == "Darwin":
            self._init_mss()
        else:
            raise RuntimeError(f"Unsupported platform: {system}")

    # -- backend init --------------------------------------------------

    def _init_mss(self) -> None:
        self.backend = "mss"
        self.camera = MSS()

    def _init_windows(self) -> None:
        if _dxcam_supported():
            try:
                import dxcam

                camera = dxcam.create(output_idx=self.monitor - 1)
                if camera is None:
                    raise RuntimeError("dxcam.create() returned None")
                self.backend = "dxcam"
                self.camera = camera
                return
            except Exception as exc:  # pragma: no cover - hardware dependent
                warnings.warn(f"dxcam unavailable ({exc}); falling back to mss")

        # Windows 7, or dxcam failed to initialize.
        self._init_mss()

    def _init_linux(self) -> None:
        is_wayland = (
            os.getenv("XDG_SESSION_TYPE") == "wayland"
            or bool(os.getenv("WAYLAND_DISPLAY"))
        )

        if is_wayland:
            from ble_led._wayland import GrimCapture, PortalScreenshotCapture

            try:
                self.camera = GrimCapture(monitor=self.monitor)
                self.backend = "grim"
                return
            except Exception as exc:
                warnings.warn(
                    f"grim unavailable ({exc}); trying xdg-desktop-portal"
                )

            try:
                self.camera = PortalScreenshotCapture()
                self.backend = "portal"
                return
            except Exception as exc:
                raise RuntimeError(
                    "No working Wayland capture backend found. Install "
                    "`grim` (wlroots compositors: Sway, Hyprland, river, "
                    "...) or ensure org.freedesktop.portal.Desktop with "
                    "the Screenshot interface and PyGObject (python3-gi) "
                    "are available (GNOME, KDE, ...)."
                ) from exc

        self._init_mss()

    # -- capture ---------------------------------------------------------

    def average_color(self) -> Color:
        if self.backend == "dxcam":
            return self._average_dxcam()
        if self.backend == "mss":
            return self._average_mss()
        if self.backend in ("grim", "portal"):
            return self.camera.average_color()
        return Color()

    def _average_dxcam(self) -> Color:
        frame = self.camera.grab()
        if frame is None:
            return Color()
        return Color(
            red=int(frame[:, :, 2].mean()),
            green=int(frame[:, :, 1].mean()),
            blue=int(frame[:, :, 0].mean()),
        )

    def _average_mss(self) -> Color:
        img = self.camera.grab(self.camera.monitors[self.monitor])
        rgb = img.rgb
        pixels = len(rgb) // 3
        return Color(
            red=sum(rgb[0::3]) // pixels,
            green=sum(rgb[1::3]) // pixels,
            blue=sum(rgb[2::3]) // pixels,
        )

    def close(self) -> None:
        if self.backend == "mss":
            self.camera.close()
        elif self.backend in ("grim", "portal"):
            self.camera.close()


def create_capture(monitor: int = 1) -> ScreenCapture:
    """Factory used by main.py. Kept separate from __init__ so future
    setup that can fail (e.g. probing multiple backends) has a clean
    place to live without complicating the class itself."""
    return ScreenCapture(monitor=monitor)
