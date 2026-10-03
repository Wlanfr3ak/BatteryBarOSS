"""Floating, frameless, always-on-top battery bar (Tkinter, stdlib only)."""
from __future__ import annotations

import ctypes
import logging
import random
import threading
import time
import tkinter as tk
from tkinter import messagebox
import winsound

from . import (
    __app_name__,
    __version__,
    autostart,
    battery,
    config,
    estimate,
    sysinfo,
    updater,
)

log = logging.getLogger(__name__)

CHROMA = "#ff00ff"  # chroma-key color -> fully transparent window background
_CLICK_TOLERANCE_PX = 6
_DISPLAY_MODES = ("default", "time", "percent", "rate", "capacity", "health")
_RESIZE_MARGIN = 8  # px from right/bottom edge that acts as resize grip
_MIN_W, _MIN_H = 140, 18
_MAX_W, _MAX_H = 1200, 160
_TOOLTIP_DELAY_MS = 400
_TOOLTIP_ANIM_DELAY_MS = 5000  # hover duration before the ASCII animation
_TOOLTIP_ANIM_FRAMES = 16
_TOOLTIP_ANIM_FRAME_MS = 70
_ANIM_POOL = "!<>-_\\/[]{}=+*^?#%&@"

# 5-row block font for the version animation ('#' -> drawn as block char)
_ASCII_FONT: dict[str, tuple[str, ...]] = {
    "0": ("###", "# #", "# #", "# #", "###"),
    "1": (" # ", "## ", " # ", " # ", "###"),
    "2": ("###", "  #", "###", "#  ", "###"),
    "3": ("###", "  #", " ##", "  #", "###"),
    "4": ("# #", "# #", "###", "  #", "  #"),
    "5": ("###", "#  ", "###", "  #", "###"),
    "6": ("###", "#  ", "###", "# #", "###"),
    "7": ("###", "  #", "  #", " # ", " # "),
    "8": ("###", "# #", "###", "# #", "###"),
    "9": ("###", "# #", "###", "  #", "###"),
    ".": (" ", " ", " ", "#", "#"),
    "v": ("# #", "# #", "# #", "# #", " # "),
    "-": ("   ", "   ", "###", "   ", "   "),
}
_ANIM_BLOCK = "█"

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
        self._machine = sysinfo.read_machine_info()
        self._static: battery.BatteryStaticInfo | None = None
        self._static_at = 0.0
        self._resizing: str | None = None  # "we" | "ns" | "se" while edge-dragging
        self._tooltip: tk.Toplevel | None = None
        self._tooltip_after: str | None = None
        self._tooltip_label: tk.Label | None = None
        self._tipanim_after: str | None = None
        self._tipanim: dict | None = None

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

        self.root.after(2000, self._updates_init)
        self.root.after(0, self._tick)
        self.root.after(150, self._hotkey_poll)

    # ------------------------------------------------------------------ cfg
    def _make_estimator(self) -> estimate.TimeEstimator:
        est = self.settings.get("estimation", {})
        return estimate.TimeEstimator(
            soft_min_percent=float(est.get("soft_min_percent", 5.0)),
            stats_path=config.STATS_FILE,
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
        self.canvas.bind("<Motion>", self._motion)
        self.canvas.bind("<Enter>", self._motion)
        self.canvas.bind("<Leave>", self._leave)

    def _resize_mode(self, event: tk.Event) -> str | None:
        """Resize grip hit-test: right edge = width, bottom = height."""
        w = self._win_cfg()
        right = event.x >= int(w["width"]) - _RESIZE_MARGIN
        bottom = event.y >= int(w["height"]) - _RESIZE_MARGIN
        if right and bottom:
            return "se"
        if right:
            return "we"
        if bottom:
            return "ns"
        return None

    def _drag_start(self, event: tk.Event) -> None:
        self._drag_origin = (event.x_root, event.y_root)
        self._resizing = self._resize_mode(event)
        self._hide_tooltip()
        self._cancel_tooltip_timer()
        if self._resizing or self._win_cfg()["lock_position"]:
            self._drag_offset = None
        else:
            self._drag_offset = (
                event.x_root - self.root.winfo_x(),
                event.y_root - self.root.winfo_y(),
            )

    def _drag_move(self, event: tk.Event) -> None:
        if self._resizing:
            w = self._win_cfg()
            x0, y0 = self.root.winfo_x(), self.root.winfo_y()
            nw = int(w["width"])
            nh = int(w["height"])
            if self._resizing in ("we", "se"):
                nw = max(_MIN_W, min(_MAX_W, event.x_root - x0))
            if self._resizing in ("ns", "se"):
                nh = max(_MIN_H, min(_MAX_H, event.y_root - y0))
            w["width"], w["height"] = nw, nh
            self.root.geometry(f"{nw}x{nh}+{x0}+{y0}")
            if self._last is not None:
                self._redraw(*self._last)
            return
        if self._drag_offset is None:
            return
        x = event.x_root - self._drag_offset[0]
        y = event.y_root - self._drag_offset[1]
        self.root.geometry(f"+{x}+{y}")

    def _drag_end(self, event: tk.Event) -> None:
        origin = self._drag_origin
        self._drag_origin = None
        if self._resizing is not None:
            self._resizing = None
            w = self._win_cfg()
            config.save_local(
                {"window": {"width": int(w["width"]), "height": int(w["height"])}}
            )
            log.debug("saved size %sx%s", w["width"], w["height"])
            return
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

    # ------------------------------------------------------------- tooltip
    def _motion(self, event: tk.Event) -> None:
        """Update resize cursor + reschedule the hover tooltip."""
        if self._drag_origin is None and not self._resizing:
            mode = self._resize_mode(event)
            cursor = {"we": "size_we", "ns": "size_ns", "se": "size_nw_se"}.get(
                mode, ""
            )
            self.canvas.configure(cursor=cursor)
        x, y = event.x_root, event.y_root
        self._cancel_tooltip_timer()
        self._tooltip_after = self.root.after(
            _TOOLTIP_DELAY_MS, lambda: self._show_tooltip(x, y)
        )

    def _leave(self, _event: tk.Event) -> None:
        self.canvas.configure(cursor="")
        self._cancel_tooltip_timer()
        self._hide_tooltip()

    def _cancel_tooltip_timer(self) -> None:
        if self._tooltip_after is not None:
            try:
                self.root.after_cancel(self._tooltip_after)
            except tk.TclError:
                pass
            self._tooltip_after = None

    def _tooltip_text(self) -> str:
        status, details, est = self._last if self._last else (
            battery.read_status(**self._threshold_args()),
            battery.read_power_details(),
            None,
        )
        fields = battery.render_fields(
            status,
            est_seconds=est,
            details=details,
            estimated=self._estimator.source in ("slope", "learned"),
            static=self._static,
            machine=self._machine.product_name,
            bhm=self._hp_bhm(),
        )
        lines: list[str] = []
        if self._machine.product_name:
            lines.append(self._machine.product_name)
        head = f"{fields['percent']}% · {fields['state_text']}"
        if fields["time"] not in ("", "—"):
            head += f" · {fields['time']} remaining"
        lines.append(head)
        live = [p for p in (fields["capacity"], fields["rate"]) if p]
        if live:
            lines.append(" · ".join(live))
        if self._static is not None:
            stat = []
            if self._static.design_mwh:
                stat.append(f"Design {self._static.design_mwh / 1000:.1f} Wh")
            if self._static.full_charge_mwh:
                stat.append(f"Full {self._static.full_charge_mwh / 1000:.1f} Wh")
            if self._static.wear_percent is not None:
                stat.append(f"Wear {self._static.wear_percent:.1f} %")
            if self._static.cycle_count:
                stat.append(f"{self._static.cycle_count} cycles")
            if self._static.voltage_mv:
                stat.append(f"{self._static.voltage_mv / 1000:.1f} V")
            if stat:
                lines.append(" · ".join(stat))
        bhm = self._hp_bhm()
        if bhm:
            lines.append(f"BIOS battery mode: {bhm}")
        source = {
            "rate": "hardware fuel-gauge rate",
            "slope": "session average",
            "learned": "learned profile",
            "driver": "driver estimate",
            "windows": "Windows estimate",
        }.get(self._estimator.source or "")
        if source:
            lines.append(f"Estimate: {source} (soft-min {self._estimator.soft_min * 100:.0f} %)")
        return "\n".join(lines)

    def _show_tooltip(self, x_root: int, y_root: int) -> None:
        self._hide_tooltip()
        top = tk.Toplevel(self.root)
        top.overrideredirect(True)
        top.attributes("-topmost", True)
        frame = tk.Frame(top, bg="#ffffe1", highlightthickness=1,
                         highlightbackground="#7f7f7f")
        frame.pack()
        self._tooltip_label = tk.Label(
            frame, text=self._tooltip_text(), justify="left",
            bg="#ffffe1", fg="#000000",
            font=("Segoe UI", 9), padx=8, pady=6,
        )
        self._tooltip_label.pack()
        self._tipanim_after = self.root.after(
            _TOOLTIP_ANIM_DELAY_MS, self._tooltip_anim_start
        )
        top.update_idletasks()
        x = x_root + 14
        y = y_root + 18
        # keep the tooltip on screen
        x = min(x, top.winfo_screenwidth() - top.winfo_reqwidth() - 8)
        y = min(y, top.winfo_screenheight() - top.winfo_reqheight() - 8)
        top.geometry(f"+{x}+{y}")
        self._tooltip = top

    def _hide_tooltip(self) -> None:
        if self._tipanim_after is not None:
            try:
                self.root.after_cancel(self._tipanim_after)
            except tk.TclError:
                pass
            self._tipanim_after = None
        self._tipanim = None
        self._tooltip_label = None
        if self._tooltip is not None:
            try:
                self._tooltip.destroy()
            except tk.TclError:
                pass
            self._tooltip = None

    # ------------------------------------------------- tooltip ascii anim
    def _version_art(self) -> list[str]:
        """Big block-letter ASCII art of the version, e.g. 'v0.7.1'."""
        rows = ["", "", "", "", ""]
        for ch in f"v{__version__}":
            glyph = _ASCII_FONT.get(ch, ("   ",) * 5)
            for i in range(5):
                rows[i] += glyph[i].replace("#", _ANIM_BLOCK) + " "
        return [r.rstrip() for r in rows]

    def _anim_frame(self, art: list[str], step: int, total: int) -> str:
        """Decrypt effect: settled glyphs left of the sweep, glitchy
        random chars in a band ahead of it, sparse noise beyond."""
        width = max(len(r) for r in art)
        edge = int(step / total * (width + 8))
        out = []
        for row in art:
            line = []
            for x, ch in enumerate(row.ljust(width)):
                if ch == " ":
                    line.append(" ")
                elif x < edge:
                    line.append(ch)
                elif x < edge + 4:
                    line.append(random.choice(_ANIM_POOL))
                else:
                    line.append(
                        random.choice(_ANIM_POOL)
                        if random.random() < 0.35
                        else " "
                    )
            out.append("".join(line).rstrip())
        return "\n".join(out)

    def _tooltip_anim_start(self) -> None:
        if self._tooltip_label is None:
            return
        self._tipanim = {"art": self._version_art(), "step": 0}
        self._tooltip_label.configure(font=("Consolas", 9))
        self._tipanim_after = None
        self._tooltip_anim_tick()

    def _tooltip_anim_tick(self) -> None:
        state = self._tipanim
        if state is None or self._tooltip_label is None:
            return
        state["step"] += 1
        done = state["step"] >= _TOOLTIP_ANIM_FRAMES
        art, step, total = state["art"], state["step"], _TOOLTIP_ANIM_FRAMES
        if done:
            text = "\n".join(art)
            text += f"\n\n{__app_name__} · built with Devin (SWE-2 High)"
        else:
            text = self._anim_frame(art, step, total)
        try:
            self._tooltip_label.configure(text=text)
        except tk.TclError:
            self._tipanim = None
            return
        if not done:
            self._tipanim_after = self.root.after(
                _TOOLTIP_ANIM_FRAME_MS, self._tooltip_anim_tick
            )

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
        self._cancel_tooltip_timer()
        self._hide_tooltip()
        self.menu.tk_popup(event.x_root, event.y_root)

    def _build_menu(self) -> None:
        w = self._win_cfg()
        self._var_topmost = tk.BooleanVar(value=bool(w["always_on_top"]))
        self._var_click = tk.BooleanVar(value=bool(w["click_through"]))
        self._var_lock = tk.BooleanVar(value=bool(w["lock_position"]))
        self._var_autostart = tk.BooleanVar(value=autostart.is_enabled())

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
        menu.add_checkbutton(
            label="Start with Windows",
            variable=self._var_autostart,
            command=self._toggle_autostart,
        )
        menu.add_separator()
        menu.add_command(
            label=f"Reset size ({config.DEFAULT_SETTINGS['window']['width']}×"
                  f"{config.DEFAULT_SETTINGS['window']['height']})",
            command=self._reset_size,
        )
        if updater.available():
            menu.add_command(
                label="Check for updates now",
                command=lambda: self._schedule_update_check(
                    force=True, manual=True
                ),
            )
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

    def _toggle_autostart(self) -> None:
        try:
            if self._var_autostart.get():
                autostart.enable()
            else:
                autostart.disable()
        except OSError:
            log.exception("autostart toggle failed")
            self._var_autostart.set(autostart.is_enabled())
            self._toast("Could not change autostart entry")

    def _reset_size(self) -> None:
        w = self._win_cfg()
        d = config.DEFAULT_SETTINGS["window"]
        w["width"], w["height"] = int(d["width"]), int(d["height"])
        config.save_local({"window": {"width": w["width"], "height": w["height"]}})
        x, y = self.root.winfo_x(), self.root.winfo_y()
        self.root.geometry(f"{w['width']}x{w['height']}+{x}+{y}")
        if self._last is not None:
            self._redraw(*self._last)

    def _hp_bhm(self) -> str | None:
        if not self._machine.is_hp:
            return None
        cache = sysinfo.read_hp_bios_cache()
        return str(cache["mode"]) if cache else None

    # ------------------------------------------------------------- updater
    def _updates_init(self) -> None:
        """First-start consent question (once), then scheduled checks."""
        if not updater.available():
            return
        cfg = self.settings["updates"]
        if cfg.get("enabled") is None:
            ans = messagebox.askyesno(
                __app_name__,
                "Allow automatic update checks?\n\n"
                "The app will occasionally check github.com over HTTPS "
                "for new releases and can update itself in one step.\n"
                "Settings and stats are kept. You can change this later "
                'via "updates.enabled" in settings.local.json.',
            )
            config.save_local({"updates": {"enabled": bool(ans)}})
            cfg["enabled"] = bool(ans)
            log.info("update checks %s", "enabled" if ans else "declined")
        self._schedule_update_check(force=False, manual=False)

    def _schedule_update_check(self, force: bool, manual: bool = False) -> None:
        """Kick off a background check when due; `force` ignores the
        interval and the enabled flag (explicit menu request)."""
        if not updater.available():
            return
        cfg = self.settings["updates"]
        if not force and not cfg.get("enabled"):
            return
        interval_s = float(cfg.get("check_interval_hours", 24)) * 3600
        last = float(cfg.get("last_check") or 0)
        if not force and time.time() - last < interval_s:
            self._schedule_next_update_probe()
            return
        threading.Thread(
            target=self._update_check_worker, args=(manual,), daemon=True
        ).start()

    def _update_check_worker(self, manual: bool) -> None:
        try:
            info = updater.check_for_update()
            ok = True
        except Exception:
            log.exception("update check failed")
            info, ok = None, False
        self.root.after(
            0, lambda: self._update_check_done(info, ok, manual)
        )

    def _update_check_done(
        self, info: updater.UpdateInfo | None, ok: bool, manual: bool
    ) -> None:
        if ok:
            stamp = time.time()
            config.save_local({"updates": {"last_check": stamp}})
            self.settings["updates"]["last_check"] = stamp
        if manual and ok and info is None:
            self._toast(f"{__app_name__} is up to date (v{__version__})")
        if info is not None:
            log.info("update available: v%s", info.version)
            if messagebox.askyesno(
                __app_name__,
                f"Update v{info.version} is available "
                f"(installed: v{__version__}).\n\n"
                "Download and install now? The app restarts; "
                "settings are kept.",
            ):
                self._start_download(info)
        self._schedule_next_update_probe()

    def _schedule_next_update_probe(self) -> None:
        if self.settings["updates"].get("enabled"):
            self.root.after(
                3600_000,
                lambda: self._schedule_update_check(force=False),
            )

    def _start_download(self, info: updater.UpdateInfo) -> None:
        self._toast(f"Downloading v{info.version} …")
        threading.Thread(
            target=self._download_worker, args=(info,), daemon=True
        ).start()

    def _download_worker(self, info: updater.UpdateInfo) -> None:
        try:
            path = updater.download_verified(info)
        except updater.UpdateError as exc:
            log.warning("update download refused: %s", exc)
            self.root.after(0, lambda: self._toast(f"Update failed: {exc}"))
            return
        except Exception:
            log.exception("update download failed")
            self.root.after(0, lambda: self._toast("Update download failed"))
            return
        self.root.after(0, lambda: self._apply_update(path))

    def _apply_update(self, path) -> None:
        try:
            updater.apply_update(path)
        except Exception:
            log.exception("apply update failed")
            self._toast("Could not start the update helper")
            return
        self.root.destroy()


    def reload_settings(self) -> None:
        self.settings = config.load_settings()
        self._estimator = self._make_estimator()
        self._static = battery.read_static_info()
        self._static_at = time.monotonic()
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
            if self._static is None or time.monotonic() - self._static_at > 3600:
                self._static = battery.read_static_info()
                self._static_at = time.monotonic()
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
            estimated=self._estimator.source in ("slope", "learned"),
            static=self._static,
            machine=self._machine.product_name,
            bhm=self._hp_bhm(),
        )
        w = self._win_cfg()
        mode_fmt = {
            "time": "{time}",
            "percent": "{percent}%",
            "rate": "{rate}",
            "capacity": "{capacity}",
            "health": "{health}",
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
