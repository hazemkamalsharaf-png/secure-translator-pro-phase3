"""
Sidebar navigation item — icon + label with hover and active states.

Usage:
    nav = NavItem(sidebar_frame, icon_name="book", label="Translation", command=cb)
    nav.pack(fill="x", padx=12, pady=2)
    nav.activate() / nav.deactivate()
"""

import customtkinter as ctk
from ui.theme import ThemeManager, THEMES, token_pair
from ui.icon_factory import render_icon

theme = ThemeManager.get_instance()

ICON_DISPLAY = 20   # logical size
ICON_RENDER = 40    # rendered at 2x so it stays sharp on HiDPI

# The sidebar is dark in BOTH themes, so icons use fixed colours
# (never the light/dark image swap that caused the black squares).
_ICON_NORMAL = THEMES["dark"]["sidebar_icon"]
_ICON_ACTIVE = THEMES["dark"]["sidebar_active_icon"]


def _hover_color():
    try:
        return token_pair("sidebar_hover")
    except KeyError:  # token not added yet
        return token_pair("sidebar_active")


class NavItem(ctk.CTkFrame):
    """A single sidebar navigation item with icon, label, hover, and active states."""

    HEIGHT = 42

    def __init__(self, master, icon_name: str, label: str, command=None,
                 group: str = "nav"):
        super().__init__(master, fg_color="transparent", corner_radius=10,
                         height=self.HEIGHT)
        self._command = command
        self._icon_name = icon_name
        self._label = label
        self._active = False

        # Row layout: [accent bar] [icon] [label ........]
        self.grid_propagate(False)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(2, weight=1)

        self._accent = ctk.CTkFrame(
            self, width=3, height=20, corner_radius=2, fg_color="transparent",
        )
        self._accent.grid(row=0, column=0, padx=(8, 0))

        self._icon_normal, self._icon_active = self._build_icons()
        self._icon_label = ctk.CTkLabel(
            self,
            text="" if self._icon_normal else _icon_char(icon_name),
            image=self._icon_normal,
            width=24,
            font=ctk.CTkFont(size=16),
            text_color=token_pair("sidebar_icon"),
        )
        self._icon_label.grid(row=0, column=1, padx=(10, 10))

        self._text_label = ctk.CTkLabel(
            self,
            text=label,
            font=theme.ctk_font("body"),
            text_color=token_pair("sidebar_icon"),
            anchor="w",
        )
        self._text_label.grid(row=0, column=2, sticky="ew", padx=(0, 12))

        for w in (self, self._accent, self._icon_label, self._text_label):
            w.bind("<Enter>", self._on_enter, add="+")
            w.bind("<Leave>", self._on_leave, add="+")
            w.bind("<Button-1>", self._on_click, add="+")
            try:
                w.configure(cursor="hand2")
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Icons
    # ------------------------------------------------------------------
    def _build_icons(self):
        normal = render_icon(self._icon_name, _ICON_NORMAL, ICON_RENDER)
        active = render_icon(self._icon_name, _ICON_ACTIVE, ICON_RENDER)
        if normal is None or active is None:
            return None, None
        size = (ICON_DISPLAY, ICON_DISPLAY)
        return (
            ctk.CTkImage(light_image=normal, dark_image=normal, size=size),
            ctk.CTkImage(light_image=active, dark_image=active, size=size),
        )

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------
    def _pointer_inside(self):
        try:
            widget = self.winfo_containing(self.winfo_pointerx(), self.winfo_pointery())
        except Exception:
            return False
        while widget is not None:
            if widget is self:
                return True
            widget = getattr(widget, "master", None)
        return False

    def _on_enter(self, event=None):
        if not self._active:
            self.configure(fg_color=_hover_color())

    def _on_leave(self, event=None):
        if self._active or self._pointer_inside():
            return
        self.configure(fg_color="transparent")

    def _on_click(self, event=None):
        if self._command:
            self._command()
        return "break"

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------
    def activate(self):
        self._active = True
        self.configure(fg_color=token_pair("sidebar_active"))
        self._accent.configure(fg_color=token_pair("primary"))
        if self._icon_active:
            self._icon_label.configure(image=self._icon_active)
        else:
            self._icon_label.configure(text_color=token_pair("sidebar_active_icon"))
        self._text_label.configure(
            text_color=token_pair("sidebar_active_icon"),
            font=theme.ctk_font("body", weight="bold"),
        )

    def deactivate(self):
        self._active = False
        self.configure(fg_color="transparent")
        self._accent.configure(fg_color="transparent")
        if self._icon_normal:
            self._icon_label.configure(image=self._icon_normal)
        else:
            self._icon_label.configure(text_color=token_pair("sidebar_icon"))
        self._text_label.configure(
            text_color=token_pair("sidebar_icon"),
            font=theme.ctk_font("body"),
        )

    def is_active(self):
        return self._active


def _icon_char(name: str) -> str:
    """Plain-symbol fallback (no emoji: Tk often can't render them on Linux)."""
    icons = {
        "book": "▤",
        "glossary": "▥",
        "settings": "⚙",
        "theme": "◐",
        "search": "⌕",
        "check": "✓",
        "x": "✕",
        "close": "✕",
        "play": "▶",
        "save": "▣",
        "delete": "✕",
        "file": "▤",
        "folder": "▸",
        "moon": "☾",
        "sun": "☀",
        "translate": "⇄",
    }
    return icons.get(name, "●")