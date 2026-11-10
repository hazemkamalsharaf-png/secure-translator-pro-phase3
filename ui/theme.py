"""
Central design system for SecureTranslatorPro.

Color tokens, spacing, radius, and fonts for Light/Dark modes.
No hard-coded colors in widgets — all styles reference theme tokens.
"""

import customtkinter as ctk
import sys
import os


# ---------------------------------------------------------------------------
# Theme colour tokens — Light and Dark variants
# ---------------------------------------------------------------------------
THEMES = {
    "light": {
        "bg":            "#f0f2f5",
        "surface":       "#ffffff",
        "surface_hover": "#f5f6f8",
        "elevated":      "#ffffff",
        "border":        "#e0e3e8",
        "border_light":  "#eef0f3",
        "primary":       "#4a6cf7",
        "primary_hover": "#3b5de7",
        "accent":        "#6366f1",
        "success":       "#22c55e",
        "warning":       "#f59e0b",
        "danger":        "#ef4444",
        "danger_hover":  "#dc2626",
        "text":          "#1e293b",
        "text_muted":    "#64748b",
        "text_secondary":"#94a3b8",
        "sidebar_bg":    "#0f172a",
        "sidebar_fg":    "#e2e8f0",
        "sidebar_active":"#1e293b",
        "sidebar_icon":  "#64748b",
        "sidebar_active_icon": "#f1f5f9",
        "text_accent":       "#ffffff",  # always light text on colored buttons
    },
    "dark": {
        "bg":            "#0f172a",
        "surface":       "#1e293b",
        "surface_hover": "#263348",
        "elevated":      "#1e293b",
        "border":        "#334155",
        "border_light":  "#1e293b",
        "primary":       "#6366f1",
        "primary_hover": "#818cf8",
        "accent":        "#818cf8",
        "success":       "#4ade80",
        "warning":       "#fbbf24",
        "danger":        "#f87171",
        "danger_hover":  "#fca5a5",
        "text":          "#f1f5f9",
        "text_muted":    "#94a3b8",
        "text_secondary":"#64748b",
        "sidebar_bg":    "#0b1120",
        "sidebar_fg":    "#e2e8f0",
        "sidebar_active":"#1e293b",
        "sidebar_icon":    "#64748b",
        "sidebar_active_icon": "#f1f5f9",
        "text_accent":       "#ffffff",  # always light text on colored buttons
    },
}


# ---------------------------------------------------------------------------
# Spacing / radius scale
# ---------------------------------------------------------------------------
SPACING = {"4": 4, "8": 8, "12": 12, "16": 16, "20": 20, "24": 24}
RADIUS = {"sm": 6, "md": 10, "lg": 14, "xl": 20}
PAD = {"sm": 8, "md": 14, "lg": 20, "xl": 28}

# ---------------------------------------------------------------------------
# Font scale — consistent type hierarchy
# ---------------------------------------------------------------------------
FONTS = {
    "heading":  (24, "bold"),      # Page titles
    "subhead":  (16, "bold"),      # Section headers
    "label":    (13, "normal"),    # Form labels
    "small":    (11, "normal"),    # Secondary text
    "body":     (13, "normal"),    # Body text
    "muted":    (12, "normal"),    # Muted/placeholder text
    "mega":     (28, "bold"),      # Hero / display
}

# ---------------------------------------------------------------------------
# Arabic font fallback chain — loaded at app startup
# ---------------------------------------------------------------------------
ARABIC_FONT_FAMILY = "IBM Plex Sans Arabic"
ARABIC_FONT_FALLBACK = "Arial"

# ---------------------------------------------------------------------------
# Token lookup helpers
# ---------------------------------------------------------------------------

class ThemeManager:
    """Manages the current theme and provides colour tokens."""
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._current_mode = "light"  # will be set during init
        self._fonts = {}
        self._icon_cache = {}
        # Register Arabic font at startup
        self._register_arabic_font()

    def _register_arabic_font(self):
        """Register IBM Plex Sans Arabic font so Arabic text renders correctly."""
        try:
            from ui.asset_path import assets_path
            font_path = assets_path("fonts/IBM_Plex_Sans_Arabic.ttf")
            if os.path.exists(font_path):
                fm = ctk.FontManager()
                fm.windows_load_font(font_path, "IBM Plex Sans Arabic")
                self._fonts[ARABIC_FONT_FAMILY] = font_path
        except Exception:
            pass  # Font registration is best-effort; app falls back gracefully

    # -- colour helpers -----------------------------------------------------
    def color(self, token: str, mode: str = None) -> str:
        mode = mode or self._current_mode
        return THEMES[mode][token]

    def get_all(self, mode: str = None) -> dict:
        mode = mode or self._current_mode
        return dict(THEMES[mode])

    def set_mode(self, mode: str):
        if mode not in ("light", "dark"):
            return
        self._current_mode = mode

    @property
    def mode(self) -> str:
        return self._current_mode

    # -- font helpers -------------------------------------------------------
    def register_font(self, family: str, path: str):
        try:
            ctk.CTkFont.register_font(family=family, source=path)
        except Exception:
            pass
        self._fonts[family] = path

    def font(self, name: str, size: int = None, weight: str = None, mode: str = None):
        h, w = FONTS.get(name, (13, "normal"))
        return ctk.CTkFont(
            family=self._fonts.get(ARABIC_FONT_FAMILY, "sans-serif"),
            size=(size if size is not None else h),
            weight=(weight if weight else w),
        )

    def ctk_font(self, name: str, size: int = None, weight: str = None):
        return self.font(name, size, weight)

    # -- spacing helpers ----------------------------------------------------
    def pad(self, level: str) -> int:
        return PAD.get(level, 16)

    def radius(self, level: str) -> int:
        return RADIUS.get(level, 10)

    def spacing(self, level: str) -> int:
        return SPACING.get(level, 8)

    # -- icon helpers -------------------------------------------------------
    def get_icon(self, name: str, mode: str = None):
        """Return a cached CTkImage for the given icon name."""
        mode = mode or self._current_mode
        key = f"{name}_{mode}"
        if key in self._icon_cache:
            return self._icon_cache[key]
        return None

    def register_icon(self, name: str, light_img, dark_img):
        self._icon_cache[f"{name}_light"] = light_img
        self._icon_cache[f"{name}_dark"] = dark_img

    def icon_image(self, name: str, mode: str = None):
        mode = mode or self._current_mode
        return self._icon_cache.get(f"{name}_{mode}")


# ---------------------------------------------------------------------------
# Apply theme to a CTk widget recursively
# ---------------------------------------------------------------------------
def apply_theme(widget, theme_tokens: dict, dark: bool = True):
    """Apply colour tokens to a widget and all its children (recursive)."""
    wfg = theme_tokens["surface"] if dark else theme_tokens["bg"]
    if hasattr(widget, "configure"):
        if hasattr(widget, "fg_color") and widget.cget("fg_color") not in ("transparent", "system"):
            widget.configure(fg_color=wfg)
        if hasattr(widget, "bg") and not hasattr(widget, "fg_color"):
            try:
                widget.configure(bg=wfg)
            except tk.TclError:
                pass
        if hasattr(widget, "text_color") and hasattr(widget, "cget") and "color" in str(widget.cget("text_color")):
            pass  # handled separately
    for child in widget.winfo_children():
        apply_theme(child, theme_tokens, dark)


def apply_theme_to_widget(widget, cfg: dict, dark: bool = True):
    """Apply a specific config dict to a widget (single level, no recursion)."""
    fg = cfg.get("surface" if dark else "bg")
    border = cfg.get("border_light" if dark else "border")
    if hasattr(widget, "configure"):
        if hasattr(widget, "fg_color"):
            widget.configure(fg_color=fg)
        if hasattr(widget, "border_color"):
            widget.configure(border_color=border)


# ---------------------------------------------------------------------------
# Apply theme to CustomTkinter appearance mode (light/dark)
# ---------------------------------------------------------------------------
def apply_app_theme(app, theme_tokens: dict, dark: bool = True):
    """Apply colours to the main window and all children."""
    fg = theme_tokens["bg"]
    bg = theme_tokens["bg"]
    if hasattr(app, "configure"):
        app.configure(fg_color=fg)
    for child in app.winfo_children():
        _style_widget(child, theme_tokens, dark)
    # Progress bar
    if hasattr(app, "progress_bar"):
        try:
            app.progress_bar.configure(
                progress_color=theme_tokens["primary"],
                fg_color=theme_tokens["border_light"] if dark else theme_tokens["border"],
            )
        except Exception:
            pass


def _style_widget(widget, theme_tokens, dark=True):
    """Apply theme colours to a single widget level."""
    fg = theme_tokens["surface"] if dark else theme_tokens["bg"]
    border = theme_tokens["border_light"] if dark else theme_tokens["border"]
    text = theme_tokens["text"]
    muted = theme_tokens["text_muted"]

    attrs = {}
    if hasattr(widget, "fg_color"):
        val = widget.cget("fg_color")
        if val not in ("transparent",):
            attrs["fg_color"] = fg
    if hasattr(widget, "border_color"):
        attrs["border_color"] = border
    if hasattr(widget, "text_color") and not hasattr(widget, "fg_color"):
        attrs["text_color"] = text
    for k, v in attrs.items():
        try:
            widget.configure(**{k: v})
        except Exception:
            pass
    for child in widget.winfo_children():
        _style_widget(child, theme_tokens, dark)
