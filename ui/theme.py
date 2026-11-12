"""
Central design system for SecureTranslatorPro.

Color tokens, spacing, radius, and fonts for Light/Dark modes.
No hard-coded colors in widgets — all styles reference theme tokens.
"""

import os
import sys
import customtkinter as ctk


# ---------------------------------------------------------------------------
# Theme colour tokens — Light and Dark variants
# Surfaces are layered: bg < surface (cards) < elevated; inputs sit apart.
# ---------------------------------------------------------------------------
THEMES = {
    "light": {
        "bg":            "#f3f5f9",
        "surface":       "#ffffff",
        "surface_hover": "#eef1f7",
        "elevated":      "#ffffff",
        "input":         "#f8fafc",
        "border":        "#e2e6ef",
        "border_light":  "#eef1f6",
        "primary":       "#4f46e5",
        "primary_hover": "#4338ca",
        "primary_soft":  "#eef2ff",
        "accent":        "#4f46e5",
        "success":       "#15803d",
        "warning":       "#b45309",
        "danger":        "#dc2626",
        "danger_hover":  "#b91c1c",
        "danger_soft":   "#fef2f2",
        "text":          "#0f172a",
        "text_muted":    "#64748b",
        "text_secondary": "#748096",
        "sidebar_bg":    "#10172a",
        "sidebar_fg":    "#f8fafc",
        "sidebar_active": "#1c2744",
        "sidebar_hover": "#172039",  # NEW
        "sidebar_icon":  "#94a3b8",
        "sidebar_active_icon": "#ffffff",
        "text_accent":   "#ffffff",
    },
    "dark": {
        "bg":            "#0b1020",
        "surface":       "#141a2e",
        "surface_hover": "#1c2540",
        "elevated":      "#1a2238",
        "input":         "#0f1528",
        "border":        "#2a3554",
        "border_light":  "#222c48",
        "primary":       "#6366f1",
        "primary_hover": "#818cf8",
        "primary_soft":  "#1e1b4b",
        "accent":        "#818cf8",
        "success":       "#4ade80",
        "warning":       "#fbbf24",
        "danger":        "#f87171",
        "danger_hover":  "#fca5a5",
        "danger_soft":   "#3f1d24",
        "text":          "#f8fafc",
        "text_muted":    "#94a3b8",
        "text_secondary": "#7b88a1",
        "sidebar_bg":    "#080d1a",
        "sidebar_fg":    "#f8fafc",
        "sidebar_active": "#1c2744",
        "sidebar_hover": "#121a30",  # NEW
        "sidebar_icon":  "#94a3b8",
        "sidebar_active_icon": "#ffffff",
        "text_accent":   "#ffffff",
    },
}


def token_pair(name: str):
    """(light, dark) colour pair so CustomTkinter swaps with appearance mode."""
    return (THEMES["light"][name], THEMES["dark"][name])


def entry_style():
    """Shared colours for text fields, combo boxes, and text areas."""
    return {
        "fg_color": token_pair("input"),
        "border_color": token_pair("border"),
        "text_color": token_pair("text"),
        "placeholder_text_color": token_pair("text_secondary"),
    }


def combo_style():
    style = entry_style()
    style.pop("placeholder_text_color", None)
    style.update({
        "button_color": token_pair("surface_hover"),
        "button_hover_color": token_pair("border"),
        "dropdown_fg_color": token_pair("surface"),
        "dropdown_hover_color": token_pair("surface_hover"),
        "dropdown_text_color": token_pair("text"),
    })
    return style


def radio_style():
    return {
        "fg_color": token_pair("primary"),
        "hover_color": token_pair("primary_hover"),
        "border_color": token_pair("border"),
        "text_color": token_pair("text"),
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

ARABIC_FONT_FAMILY = "IBM Plex Sans Arabic"


def _fallback_family() -> str:
    """Best system UI font per platform (Tk falls back further if missing)."""
    if sys.platform == "win32":
        return "Segoe UI"
    if sys.platform == "darwin":
        return "Helvetica Neue"
    return "Noto Sans"


# ---------------------------------------------------------------------------
# Theme manager
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
        self._current_mode = "light"
        self._fonts = {}
        self._font_cache = {}
        self._icon_cache = {}
        self._register_arabic_font()

    def _register_arabic_font(self):
        """Load IBM Plex Sans Arabic (works on Windows and Linux via CTk's FontManager)."""
        try:
            from ui.asset_path import assets_path
            font_path = assets_path("fonts/IBM_Plex_Sans_Arabic.ttf")
            if os.path.exists(font_path):
                ctk.FontManager.load_font(font_path)
                self._fonts[ARABIC_FONT_FAMILY] = font_path
        except Exception:
            pass  # best-effort; falls back to the system font

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
            ctk.FontManager.load_font(path)
        except Exception:
            pass
        self._fonts[family] = path

    def font(self, name: str, size: int = None, weight: str = None, mode: str = None):
        h, w = FONTS.get(name, (13, "normal"))
        family = ARABIC_FONT_FAMILY if ARABIC_FONT_FAMILY in self._fonts else _fallback_family()
        size = size if size is not None else h
        weight = weight if weight else w
        key = (family, size, weight)
        if key not in self._font_cache:
            self._font_cache[key] = ctk.CTkFont(family=family, size=size, weight=weight)
        return self._font_cache[key]

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
        """Return a cached CTkImage for the given icon name (None if not registered)."""
        mode = mode or self._current_mode
        return self._icon_cache.get(f"{name}_{mode}")

    def register_icon(self, name: str, light_img, dark_img):
        self._icon_cache[f"{name}_light"] = light_img
        self._icon_cache[f"{name}_dark"] = dark_img

    def icon_image(self, name: str, mode: str = None):
        mode = mode or self._current_mode
        return self._icon_cache.get(f"{name}_{mode}")


# ---------------------------------------------------------------------------
# Appearance sync
# ---------------------------------------------------------------------------
def sync_appearance(mode: str):
    """Keep CustomTkinter's built-in light/dark swap aligned with our tokens."""
    if mode not in ("light", "dark"):
        return
    ctk.set_appearance_mode(mode)


# ---------------------------------------------------------------------------
# Backward-compat no-ops.
# Widgets use (light, dark) colour pairs, so appearance mode already restyles
# everything. The old recursive painters flattened cards/sidebar to one colour.
# ---------------------------------------------------------------------------
def apply_theme(widget, theme_tokens: dict, dark: bool = True):
    return None


def apply_theme_to_widget(widget, cfg: dict, dark: bool = True):
    return None


def apply_app_theme(app, theme_tokens: dict, dark: bool = True):
    return None