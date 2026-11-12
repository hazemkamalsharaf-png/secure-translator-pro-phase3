"""
Styled button variants with hover and disabled states.

Usage:
    btn = PrimaryButton(parent, text="Start", command=cb)
    btn = SecondaryButton(parent, text="Cancel", command=cb)
    btn = DangerButton(parent, text="Delete", command=cb)
    btn = GhostButton(parent, text="Reset", command=cb)
"""

import customtkinter as ctk
from ui.theme import ThemeManager, token_pair

theme = ThemeManager.get_instance()

_ON_FILL = ("#ffffff", "#ffffff")


class StyledButton(ctk.CTkButton):
    """Base styled button with theme-aware colours."""

    def __init__(self, master, text, command=None, variant="primary",
                 font_name=None, height=36, width=None, **kwargs):
        btn_font = theme.ctk_font("label", weight="bold") if font_name is None else ctk.CTkFont(
            family=font_name, size=13, weight="bold"
        )
        self._variant = variant

        super().__init__(
            master,
            text=text,
            font=btn_font,
            height=height,
            width=width,
            corner_radius=theme.radius("sm"),
            border_width=0,
            command=command,
            **kwargs,
        )
        self._set_colors(variant)

    def _set_colors(self, variant="primary"):
        border_width = 0
        border_color = token_pair("border")

        if variant == "primary":
            fg = token_pair("primary")
            hover = token_pair("primary_hover")
            text = _ON_FILL
        elif variant == "secondary":
            fg = token_pair("surface")
            hover = token_pair("surface_hover")
            text = token_pair("text")
            border_width = 1
        elif variant == "ghost":
            fg = "transparent"
            hover = token_pair("surface_hover")
            text = token_pair("text")
        elif variant == "danger":
            fg = token_pair("danger")
            hover = token_pair("danger_hover")
            text = _ON_FILL
        elif variant == "danger-ghost":
            fg = "transparent"
            hover = token_pair("danger_soft")
            text = token_pair("danger")
        else:
            fg = token_pair("primary")
            hover = token_pair("primary_hover")
            text = _ON_FILL

        self.configure(
            fg_color=fg,
            hover_color=hover,
            text_color=text,
            text_color_disabled=token_pair("text_secondary"),
            border_width=border_width,
            border_color=border_color,
        )

    def set_variant(self, variant):
        self._variant = variant
        self._set_colors(variant)


class PrimaryButton(StyledButton):
    def __init__(self, master, text, command=None, **kwargs):
        super().__init__(master, text, command, variant="primary", **kwargs)


class SecondaryButton(StyledButton):
    def __init__(self, master, text, command=None, **kwargs):
        super().__init__(master, text, command, variant="secondary", **kwargs)


class GhostButton(StyledButton):
    def __init__(self, master, text, command=None, **kwargs):
        super().__init__(master, text, command, variant="ghost", **kwargs)


class DangerButton(StyledButton):
    def __init__(self, master, text, command=None, **kwargs):
        super().__init__(master, text, command, variant="danger", **kwargs)


class DangerGhostButton(StyledButton):
    def __init__(self, master, text, command=None, **kwargs):
        super().__init__(master, text, command, variant="danger-ghost", **kwargs)
