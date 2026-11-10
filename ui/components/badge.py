"""
Status badge — small coloured label indicating state.

Usage:
    badge = StatusBadge(parent, "Running")
    badge.pack(side="right")
"""

import customtkinter as ctk
from ui.theme import ThemeManager

theme = ThemeManager.get_instance()


def _badge_colors(state: str):
    """Lazy theme colour lookup for a badge state."""
    tc = theme.color
    return {
        "idle":       (tc("text_muted"), tc("surface_hover")),
        "pending":    (tc("warning"), tc("surface_hover")),
        "running":    (tc("primary"), tc("surface_hover")),
        "done":       (tc("success"), tc("surface_hover")),
        "success":    (tc("success"), tc("surface_hover")),
        "error":      (tc("danger"), tc("surface_hover")),
        "needs_review": (tc("accent"), tc("surface_hover")),
    }.get(state, (tc("text_muted"), tc("surface_hover")))


def _indicator_colors(state: str):
    """Lazy theme colour lookup for a status indicator."""
    tc = theme.color
    return {
        "idle": tc("text_muted"),
        "pending": tc("warning"),
        "running": tc("primary"),
        "done": tc("success"),
        "success": tc("success"),
        "error": tc("danger"),
        "needs_review": tc("accent"),
    }.get(state, tc("text_muted"))


# Legacy dict kept for backward compat — now delegates to lazy lookup
BADGE_COLORS = {}  # deprecated; use _badge_colors()


class StatusBadge(ctk.CTkLabel):
    """A small coloured status badge."""

    def __init__(self, master, state: str = "idle", text: str = None):
        if text is None:
            text = state.replace("_", " ").title()
        bg = _badge_colors(state)
        super().__init__(
            master,
            text=text,
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=bg[0],
            fg_color=bg[1],
            corner_radius=6,
            width=70,
            height=22,
            anchor="center",
        )
        self._state = state

    def set_state(self, state: str):
        self._state = state
        bg = _badge_colors(state)
        self.configure(text_color=bg[0], fg_color=bg[1])


class StatusIndicator(ctk.CTkLabel):
    """A small dot + label indicator (for compact rows)."""

    def __init__(self, master, state: str = "idle"):
        dot_color = _indicator_colors(state)

        super().__init__(
            master,
            text=f"  {state.replace('_', ' ').title()}",
            font=ctk.CTkFont(size=11),
            text_color=dot_color,
            fg_color="transparent",
            anchor="w",
        )

    def set_state(self, state: str):
        dot_color = _indicator_colors(state)
        self.configure(text_color=dot_color, text=f"  {state.replace('_', ' ').title()}")
