"""
Toast notification — non-blocking overlay that auto-disappears.

Usage:
    toast = Toast(root)
    toast.show("Success", "Translation complete!", "success")
"""

import customtkinter as ctk
import threading
from ui.theme import ThemeManager, token_pair

theme = ThemeManager.get_instance()

_CLOSE_ICON = "\u2715"  # ✕ — Unicode close icon


def _toast_colors(kind: str):
    """Lazy theme colour lookup for a toast kind."""
    tc = theme.color
    return {
        "success": (tc("success"), tc("surface")),
        "error": (tc("danger"), tc("surface")),
        "warning": (tc("warning"), tc("surface")),
        "info": (tc("primary"), tc("surface")),
    }.get(kind, (tc("primary"), tc("surface")))


# Legacy dict kept for backward compat
TOAST_COLORS = {}  # deprecated; use _toast_colors()


class Toast:
    """
    In-app toast notification system.

    Creates transient overlay windows anchored to the top-right of the master window.
    Stacks vertically when multiple toasts appear simultaneously.
    """

    TOAST_WIDTH = 360
    TOAST_HEIGHT = 64
    MARGIN_RIGHT = 16
    MARGIN_TOP = 16
    STACK_GAP = 8

    def __init__(self, master):
        self.master = master
        self._toasts = []  # list of (top, destroy_timer_id)
        # Start periodic cleanup to prevent memory accumulation
        self._schedule_cleanup()

    def _schedule_cleanup(self, interval_ms=5000):
        """Periodically clean up destroyed toasts."""
        try:
            self._cleanup_idle_toasts()
            self.master.after(interval_ms, lambda: self._schedule_cleanup(interval_ms))
        except Exception:
            pass  # Master may be destroyed

    def show(self, title: str, message: str, kind: str = "info", duration: int = 4000):
        """Show a toast notification anchored to the top-right of master."""
        self.master.after(0, lambda: self._show_impl(title, message, kind, duration))

    def _show_impl(self, title, message, kind, duration):
        # Determine colour (lazy lookup)
        fg_col, bg_col = _toast_colors(kind)

        # Calculate position relative to master's screen position
        master_x = self.master.winfo_rootx()
        master_y = self.master.winfo_rooty()
        master_w = self.master.winfo_width()

        # Find how many active toasts exist for stacking
        active_count = len([t for t in self._toasts if t[0].winfo_exists()])

        x = master_x + master_w - self.TOAST_WIDTH - self.MARGIN_RIGHT
        y = master_y + self.MARGIN_TOP + (active_count * (self.TOAST_HEIGHT + self.STACK_GAP))

        # Create a temporary top-level positioned next to master
        top = ctk.CTkToplevel(self.master)
        top.overrideredirect(True)
        top.attributes("-topmost", True)
        top.attributes("-alpha", 0.0)
        top.geometry(f"{self.TOAST_WIDTH}x{self.TOAST_HEIGHT}+{x}+{y}")

        # Build content
        frame = ctk.CTkFrame(
            top, fg_color=bg_col, corner_radius=12,
            border_width=1, border_color=fg_col,
        )
        frame.pack(fill="both", expand=True, padx=2, pady=2)

        # Title
        lbl_title = ctk.CTkLabel(
            frame, text=title,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=fg_col, anchor="w",
        )
        lbl_title.pack(side="top", padx=14, pady=(8, 0), anchor="w", fill="x")

        # Message
        lbl_msg = ctk.CTkLabel(
            frame, text=message, font=ctk.CTkFont(size=11),
            text_color=token_pair("text_muted"), anchor="w",
            wraplength=self.TOAST_WIDTH - 60,
        )
        lbl_msg.pack(side="top", padx=14, pady=(0, 8), anchor="w", fill="x")

        # Close button
        btn_close = ctk.CTkButton(
            frame, text=_CLOSE_ICON, width=22, height=22, corner_radius=6,
            fg_color="transparent", hover_color=bg_col,
            text_color=token_pair("text_muted"),
            command=lambda: self._dismiss(top),
        )
        btn_close.pack(side="right", padx=10, pady=6)

        top.configure(window=frame)
        self._toasts.append((top, None))

        # Animate in (fade)
        self._animate_in(top, 0, 0.95, 0.08)

        # Auto-dismiss
        top.after(duration, lambda: self._dismiss(top))

    def _animate_in(self, widget, start, end, step):
        current = start
        if current >= end:
            return
        widget.attributes("-alpha", current + step)
        widget.after(15, lambda: self._animate_in(widget, current + step, end, step))

    def _dismiss(self, top):
        if top.winfo_exists():
            # Remove from list
            self._toasts = [(t, d) for t, d in self._toasts if t is not top]
            # Animate out then destroy
            top.attributes("-alpha", 0.0)
            top.after(200, lambda: top.destroy() if top.winfo_exists() else None)

    def _cleanup_idle_toasts(self):
        """Remove any destroyed toasts from the list."""
        self._toasts = [(t, d) for t, d in self._toasts if t.winfo_exists()]


class ToastBanner(ctk.CTkFrame):
    """
    A persistent banner that appears at the top of a frame and can be dismissed.
    Useful for success/error messages within a tab.
    """

    def __init__(self, master, kind: str = "success"):
        fg_col, bg_col = _toast_colors(kind)
        super().__init__(master, fg_color=bg_col, corner_radius=0, height=40)
        self._kind = kind
        self.configure(fg_color=bg_col)

        self.lbl = ctk.CTkLabel(
            self, text=kind.title(), font=ctk.CTkFont(size=13, weight="bold"),
            text_color=fg_col, anchor="w",
        )
        self.lbl.pack(side="left", padx=14, pady=8)

        btn = ctk.CTkButton(
            self, text=_CLOSE_ICON, width=24, height=24, corner_radius=6,
            fg_color="transparent", hover_color=bg_col,
            text_color=fg_col, command=self.hide,
        )
        btn.pack(side="right", padx=14, pady=8)

    def set_message(self, text: str):
        self.lbl.configure(text=text)

    def hide(self):
        self.pack_forget()

    def show(self):
        self.pack(fill="x", side="top")
