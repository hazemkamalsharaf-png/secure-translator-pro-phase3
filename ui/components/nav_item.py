"""
Sidebar navigation item — icon + label with hover and active states.

Usage:
    nav = NavItem(sidebar_frame, icon="book", label="Translation", command=cb)
    nav.pack(fill="x", padx=12, pady=2)
    nav.activate() / nav.deactivate()
"""

import customtkinter as ctk
from ui.theme import ThemeManager
from ui.asset_path import assets_path

theme = ThemeManager.get_instance()


class NavItem(ctk.CTkFrame):
    """A single sidebar navigation item with icon, label, hover, and active states."""

    def __init__(self, master, icon_name: str, label: str, command=None,
                 group: str = "nav"):
        super().__init__(master, fg_color="transparent", corner_radius=8)
        self._command = command
        self._icon_name = icon_name
        self._label = label
        self._active = False

        # Internal content frame (this gets the hover/active bg color)
        self._content = ctk.CTkFrame(self, fg_color="transparent", corner_radius=8)
        self._content.pack(fill="x", padx=10, pady=3)

        # Icon + label in a tight row
        icon_row = ctk.CTkFrame(self._content, fg_color="transparent")
        icon_row.pack(side="left", fill="y")

        # Icon label — load CTkImage from assets or fallback to Unicode
        self._icon_label = ctk.CTkLabel(
            icon_row,
            text="",
            font=ctk.CTkFont(size=16),
            text_color=theme.color("sidebar_icon"),
        )
        self._icon_label.pack(side="left", padx=(0, 10), pady=4)
        self._icon_image = None
        self._update_icon()

        # Text label
        self._text_label = ctk.CTkLabel(
            icon_row,
            text=label,
            font=theme.ctk_font("body"),
            text_color=theme.color("sidebar_icon"),
            anchor="w",
        )
        self._text_label.pack(side="left", pady=4, fill="y")

        # Bind hover events to the outer frame and content frame
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self._content.bind("<Enter>", self._on_enter)
        self._content.bind("<Leave>", self._on_leave)
        self._content.bind("<Button-1>", self._on_click)

    def _get_icon_paths(self, name: str):
        """Return (light_path, dark_path) for the given icon name."""
        light_path = assets_path(f"icons/{name}_light.png")
        dark_path = assets_path(f"icons/{name}_dark.png")
        return light_path, dark_path

    def _update_icon(self):
        """Update the icon image based on current theme."""
        light_path, dark_path = self._get_icon_paths(self._icon_name)
        try:
            from PIL import Image
            light_pil = Image.open(light_path)
            dark_pil = Image.open(dark_path)
            size = (20, 20)
            light_pil = light_pil.resize(size, Image.LANCZOS)
            dark_pil = dark_pil.resize(size, Image.LANCZOS)
            self._icon_image = ctk.CTkImage(
                light_image=light_pil, dark_image=dark_pil, size=size
            )
            self._icon_label.configure(image=self._icon_image, text="")
        except Exception:
            # Fallback: Unicode icon character
            self._icon_image = None
            self._icon_label.configure(image=None, text=_icon_char(self._icon_name))

    def _on_enter(self, event=None):
        if not self._active:
            self._content.configure(fg_color=theme.color("sidebar_active"))

    def _on_leave(self, event=None):
        if not self._active:
            self._content.configure(fg_color="transparent")

    def _on_click(self, event=None):
        if self._command:
            self._command()

    def activate(self):
        """Set this item to active state."""
        self._active = True
        self.configure(fg_color="transparent")
        # Active background with rounded corners
        self._content.configure(
            fg_color=theme.color("sidebar_active"),
        )
        self._icon_label.configure(text_color=theme.color("sidebar_active_icon"))
        self._text_label.configure(
            text_color=theme.color("sidebar_active_icon"),
            font=ctk.CTkFont(size=13, weight="bold"),
        )

    def deactivate(self):
        """Set this item to inactive state."""
        self._active = False
        self.configure(fg_color="transparent")
        self._content.configure(fg_color="transparent")
        self._icon_label.configure(text_color=theme.color("sidebar_icon"))
        self._text_label.configure(
            text_color=theme.color("sidebar_icon"),
            font=theme.ctk_font("body"),
        )

    def is_active(self):
        return self._active


def _icon_char(name: str) -> str:
    """Return a Unicode icon character fallback for the given icon name."""
    icons = {
        "book":       "\U0001F4D6",      # 📖 Open book
        "glossary":   "\U0001F5A7\ufe0f", # 🖧 Notebook with decorative cover
        "settings":   "\u2699\ufe0f",     # ⚙️ Gear
        "theme":      "\U0001F319",       # 🌙 Crescent moon
        "search":     "\U0001F50D",       # 🔍 Magnifying glass
        "check":      "\u2705",           # ✅ White check mark
        "x":          "\u274C",           # ❌ Cross mark (better contrast than ✖)
        "play":       "\u25B6\ufe0f",     # ▶️ Play button
        "save":       "\U0001F4BE",       # 💾 Floppy disk
        "delete":     "\U0001F5D1\ufe0f", # 🗑️ Wastebasket
        "file":       "\U0001F4C4",       # 📄 Page facing up
        "folder":     "\U0001F4C1",       # 📁 File folder
        "close":      "\u274C",           # ❌ Cross mark
        "moon":       "\U0001F319",       # 🌙 Crescent moon
        "sun":        "\u2600\ufe0f",     # ☀️ Sun
        "translate":  "\U0001F4E1",       # 📡 Satellite antenna / translation
    }
    return icons.get(name, "\u25CF")
