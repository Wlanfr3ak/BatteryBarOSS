"""Floating, frameless, always-on-top battery bar (Tkinter, stdlib only)."""
from __future__ import annotations

import ctypes
import logging
import tkinter as tk
import winsound

from . import __app_name__, __version__, battery, config, estimate

log = logging.getLogger(__name__)

CHROMA = "#ff00ff"  # chroma-key color -> fully transparent window background
_CLICK_TOLERANCE_PX = 6
_DISPLAY_MODES = ("default", "time", "percent", "rate", "capacity")

_GWL_EXSTYLE = -20
_WS_EX_LAYERED = 0x00080000
_WS_EX_TRANSPARENT = 0x00000020
_VK_CONTROL = 0x11
_VK_MENU = 0x12  # Alt
_VK_B = 0x42
_VK_Q = 0x51

_SEVERITY = {"low": 1, "critical": 2}


def _hwnd(root: tk.Tk) -> int:
    return int(root.wm_frame(), 16)


class BarWindow:
    def __init__(self) -> None:
        self.settings = config.load_settings()
        self._estimator = self._make_estimator()
        self._last: tuple[battery.BatteryStatus, battery.PowerDetails | None, int | None] | None = None
        self._drag_offset: tuple[int, int] | None = None
        self._drag_origin: tuple[int, int] | None = None
        self._hotkey_latch = False
        self._warn_level = 0

        self.root = tk.Tk()
        self.root.title(f"{__app_name__} v{__version__}")
        self.root.overrideredirect(True)
        self.root.configure(bg=CHROMA)

        w = self._win_cfg()
        self.canvas = tk.Canvas(
            self.root,
            width=w["width"],
            height=w["height"],
            bg=CHROMA,
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack()

        self._apply_window_attrs()
        self._place_window()
        self._bind_events()
        self._build_menu()

        if self._win_cfg()["click_through"]:
            self.root.after(
                600,
                lambda: self._toast(
                    "Click-through mode active – press Ctrl+Alt+B to return"
                ),
            )

        self.root.after(0, self._tick)
        self.root.after(150, self._hotkey_poll)

    # ------------------------------------------------------------------ cfg
    def _make_estimator(self) -> estimate.TimeEstimator:
        est = self.settings.get("estimation", {})
        return estimate.TimeEstimator(
            soft_min_percent=float(est.get("soft_min_percent", 5.0))
        )

    def _win_cfg(self) -> dict:
        return self.settings["window"]

    def _colors(self) -> dict:
        return self.settings["colors"]

    # -------------------------------------------------------------- window
    def _apply_window_attrs(self) -> None:
        w = self._win_cfg()
        self.root.attributes("-topmost", bool(w["always_on_top"]))
        self.root.attributes("-alpha", float(w["opacity"]))
        self.root.attributes("-transparentcolor", CHROMA)
        self._set_click_through(bool(w["click_through"]))

    def _place_window(self) -> None:
        w = self._win_cfg()
        width, height = int(w["width"]), int(w["height"])
        if w["x"] is None or w["y"] is None:
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            ox, oy = int(w["offset_x"]), int(w["offset_y"])
            pos = {
                "top-left": (ox, oy),
                "top-right": (sw - width - ox, oy),
                "bottom-left": (ox, sh - height - oy),
                "bottom-right": (sw - width - ox, sh - height - oy),
            }
            x, y = pos.get(str(w["corner"]), pos["top-right"])
        else:
            x, y = int(w["x"]), int(w["y"])
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _set_click_through(self, enabled: bool) -> None:
        """WS_EX_TRANSPARENT passes mouse input to windows below."""
        self.root.update_idletasks()
        user32 = ctypes.windll.user32
        hwnd = _hwnd(self.root)
        style = user32.GetWindowLongPtrW(hwnd, _GWL_EXSTYLE)
        if enabled:
            style |= _WS_EX_LAYERED | _WS_EX_TRANSPARENT
        else:
            style &= ~_WS_EX_TRANSPARENT
        user32.SetWindowLongPtrW(hwnd, _GWL_EXSTYLE, style)

    # -------------------------------------------------------------- events
    def _bind_events(self) -> None:
        self.canvas.bind("<Button-1>", self._drag_start)
        self.canvas.bind("<B1-Motion>", self._drag_move)
        self.canvas.bind("<ButtonRelease-1>", self._drag_end)
        self.canvas.bind("<Button-3>", self._show_menu)

    def _drag_start(self, event: tk.Event) -> None:
        self._drag_origin = (event.x_root, event.y_root)
        if not self._win_cfg()["lock_position"]:
            self._drag_offset = (
                event.x_root - self.root.winfo_x(),
                event.y_root - self.root.winfo_y(),
            )

    def _drag_move(self, event: tk.Event) -> None:
        if self._drag_offset is None:
            return
        x = event.x_root - self._drag_offset[0]
        y = event.y_root - self._drag_offset[1]
        self.root.geometry(f"+{x}+{y}")

    def _drag_end(self, event: tk.Event) -> None:
        origin = self._drag_origin
        self._drag_origin = None
        if self._drag_offset is not None:
            self._drag_offset = None
            x, y = self.root.winfo_x(), self.root.winfo_y()
            config.save_local({"window": {"x": x, "y": y}})
            log.debug("saved position %s,%s", x, y)
        if origin is None:
            return
        moved = max(
            abs(event.x_root - origin[0]), abs(event.y_root - origin[1])
        ) >= _CLICK_TOLERANCE_PX
        if not moved:
            self._cycle_display_mode()

    def _cycle_display_mode(self) -> None:
        w = self._win_cfg()
        cur = str(w.get("display_mode", "default"))
        nxt = _DISPLAY_MODES[
            (_DISPLAY_MODES.index(cur) + 1) % len(_DISPLAY_MODES)
        ] if cur in _DISPLAY_MODES else _DISPLAY_MODES[0]
        w["display_mode"] = nxt
        config.save_local({"window": {"display_mode": nxt}})
        if self._last is not None:
            self._redraw(*self._last)

    def _show_menu(self, event: tk.Event) -> None:
        if self._win_cfg()["click_through"]:
            return
        self.menu.tk_popup(event.x_root, event.y_root)

    def _build_menu(self) -> None:
        w = self._win_cfg()
        self._var_topmost = tk.BooleanVar(value=bool(w["always_on_top"]))
        self._var_click = tk.BooleanVar(value=bool(w["click_through"]))
        self._var_lock = tk.BooleanVar(value=bool(w["lock_position"]))

        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(
            label=f"{__app_name__} v{__version__}",
            state="disabled",
        )
        menu.add_command(
            label="built with Devin (SWE-2 High)",
            state="disabled",
        )
        menu.add_separator()
        menu.add_checkbutton(
            label="Always on top",
            variable=self._var_topmost,
            command=self._toggle_topmost,
        )
        menu.add_checkbutton(
            label="Click-through  (Ctrl+Alt+B)",
            variable=self._var_click,
            command=self._toggle_click_through,
        )
        menu.add_checkbutton(
            label="Lock position",
            variable=self._var_lock,
            command=self._toggle_lock,
        )
        menu.add_separator()
        menu.add_command(label="Reload settings", command=self.reload_settings)
        menu.add_command(label="Exit  (Ctrl+Alt+Q)", command=self.root.destroy)
        self.menu = menu

    def _toggle_topmost(self) -> None:
        value = self._var_topmost.get()
        self.root.attributes("-topmost", value)
        config.save_local({"window": {"always_on_top": value}})

    def _toggle_click_through(self) -> None:
        value = self._var_click.get()
        self._set_click_through(value)
        config.save_local({"window": {"click_through": value}})
        if value:
            self._toast("Click-through mode active – press Ctrl+Alt+B to return")

    def _toggle_lock(self) -> None:
        config.save_local({"window": {"lock_position": self._var_lock.get()}})

    def reload_settings(self) -> None:
        self.settings = config.load_settings()
        self._estimator = self._make_estimator()
        self._var_topmost.set(bool(self._win_cfg()["always_on_top"]))
        self._var_click.set(bool(self._win_cfg()["click_through"]))
        self._var_lock.set(bool(self._win_cfg()["lock_position"]))
        self._apply_window_attrs()
        self._place_window()
        if self._last is not None:
            self._redraw(*self._last)
        else:
            self._redraw(battery.read_status(**self._threshold_args()))
        log.info("settings reloaded")

    # -------------------------------------------------------------- hotkeys
    def _hotkey_poll(self) -> None:
        """Global hotkeys via GetAsyncKeyState polling (works without focus)."""
        try:
            user32 = ctypes.windll.user32
            pressed = (
                bool(user32.GetAsyncKeyState(_VK_CONTROL) & 0x8000)
                and bool(user32.GetAsyncKeyState(_VK_MENU) & 0x8000)
            )
            if pressed and (user32.GetAsyncKeyState(_VK_B) & 0x8000):
                if not self._hotkey_latch:
                    self._hotkey_latch = True
                    self._var_click.set(not self._var_click.get())
                    self._toggle_click_through()
            elif pressed and (user32.GetAsyncKeyState(_VK_Q) & 0x8000):
                self.root.destroy()
                return
            elif not pressed:
                self._hotkey_latch = False
        except Exception:
            log.exception("hotkey poll failed")
        self.root.after(150, self._hotkey_poll)

    # ---------------------------------------------------------------- loop
    def _threshold_args(self) -> dict:
        t = self.settings["thresholds"]
        return {"low_threshold": int(t["low"]), "critical_threshold": int(t["critical"])}

    def _tick(self) -> None:
        try:
            status = battery.read_status(**self._threshold_args())
            details = battery.read_power_details()
            est = self._estimator.remaining_seconds(status, details)
            self._last = (status, details, est)
            self._redraw(status, details, est)
            self._check_warning(status)
        except Exception:
            log.exception("update tick failed")
        self.root.after(int(self.settings["update_interval_ms"]), self._tick)

    # ---------------------------------------------------------------- draw
    def _redraw(
        self,
        status: battery.BatteryStatus,
        details: battery.PowerDetails | None = None,
        est_seconds: int | None = None,
    ) -> None:
        c = self.canvas
        w = self._win_cfg()
        col = self._colors()
        disp = self.settings["display"]
        width, height = int(w["width"]), int(w["height"])
        pad = int(disp["padding"])
        percent = status.percent if status.percent is not None else 0

        c.delete("all")
        c.configure(width=width, height=height)
        c.create_rectangle(0, 0, width, height, fill=col["background"], outline=col["border"])
        fill_w = int((width - 2 * pad) * min(percent, 100) / 100)
        if status.present and fill_w > 0:
            c.create_rectangle(
                pad, pad, pad + fill_w, height - pad,
                fill=col[battery.fill_color_key(status.state)], outline="",
            )
        c.create_text(
            width / 2, height / 2, text=self._format_text(status, details, est_seconds),
            fill=col["text"],
            font=(disp["font_family"], int(disp["font_size"]), disp["font_weight"]),
        )

    def _format_text(
        self,
        status: battery.BatteryStatus,
        details: battery.PowerDetails | None = None,
        est_seconds: int | None = None,
    ) -> str:
        fields = battery.render_fields(
            status,
            est_seconds=est_seconds,
            details=details,
            estimated=self._estimator.source == "slope",
        )
        w = self._win_cfg()
        mode_fmt = {
            "time": "{time}",
            "percent": "{percent}%",
            "rate": "{rate}",
            "capacity": "{capacity}",
        }
        fmt = mode_fmt.get(str(w.get("display_mode", "default"))) or str(
            w.get("format") or "{percent}%"
        )
        try:
            text = " ".join(fmt.format(**fields).split())
        except (KeyError, ValueError):
            text = ""
        return text or f"{fields['percent']}%"

    # ------------------------------------------------------------ warnings
    def _check_warning(self, status: battery.BatteryStatus) -> None:
        level = _SEVERITY.get(status.state, 0)
        if level > self._warn_level and self.settings["warnings"]["enabled"]:
            label = battery.STATE_TEXT.get(status.state, status.state)
            pct = f"{status.percent}%" if status.percent is not None else "?"
            self._toast(f"Battery {label}: {pct}")
            if self.settings["warnings"]["beep"]:
                try:
                    winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                except RuntimeError:
                    pass
        self._warn_level = level

    def _toast(self, text: str) -> None:
        seconds = float(self.settings["warnings"]["toast_seconds"])
        top = tk.Toplevel(self.root)
        top.overrideredirect(True)
        top.attributes("-topmost", True)
        top.attributes("-alpha", 0.95)
        tk.Label(
            top, text=text, bg="#f44336", fg="white",
            font=("Segoe UI", 10, "bold"), padx=14, pady=8,
        ).pack()
        top.update_idletasks()
        x = top.winfo_screenwidth() - top.winfo_reqwidth() - 20
        y = top.winfo_screenheight() - top.winfo_reqheight() - 60
        top.geometry(f"+{x}+{y}")
        top.after(int(seconds * 1000), top.destroy)

    # ----------------------------------------------------------------- run
    def run(self) -> None:
        log.info("%s v%s started", __app_name__, __version__)
        self.root.mainloop()
        log.info("shutdown")
