"""
Styled button variants with hover/pressed/disabled states.

Usage:
    btn = PrimaryButton(parent, text="Start", command=cb)
    btn = SecondaryButton(parent, text="Cancel", command=cb)
    btn = DangerButton(parent, text="Delete", command=cb)
    btn = GhostButton(parent, text="Reset", command=cb)
"""

import customtkinter as ctk
from ui.theme import ThemeManager

theme = ThemeManager.get_instance()


class StyledButton(ctk.CTkButton):
    """Base styled button with theme-aware colours."""

    def __init__(self, master, text, command=None, variant="primary",
                 font_name=None, height=36, width=None, **kwargs):
        # Default font
        btn_font = theme.ctk_font("label") if font_name is None else ctk.CTkFont(
            family=font_name, size=13, weight="normal"
        )

        super().__init__(
            master,
            text=text,
            font=btn_font,
            height=height,
            width=width,
            corner_radius=theme.radius("sm"),
            command=command,
            **kwargs,
        )
        self._variant = variant
        self._original_hover = None
        self._original_fg = None

    def _set_colors(self, variant="primary"):
        if variant == "primary":
            fg = theme.color("primary")
            hover = theme.color("primary_hover")
            disabled_fg = theme.color("text_secondary")
        elif variant == "secondary":
            fg = theme.color("surface_hover")
            hover = theme.color("border")
            disabled_fg = theme.color("text_muted")
        elif variant == "ghost":
            fg = "transparent"
            hover = theme.color("surface_hover")
            disabled_fg = theme.color("text_muted")
        elif variant == "danger":
            fg = theme.color("danger")
            hover = theme.color("danger_hover")
            disabled_fg = theme.color("danger")
        else:
            fg = theme.color("primary")
            hover = theme.color("primary_hover")
            disabled_fg = theme.color("text_secondary")

        self.configure(
            fg_color=fg,
            hover_color=hover,
            text_color=theme.color("text") if variant == "ghost" else theme.color("text_accent"),
        )
        self._original_hover = hover
        self._original_fg = fg

    def set_variant(self, variant):
        self._variant = variant
        self._set_colors(variant)

    def configure(self, **kwargs):
        # Override fg_color and hover_color for variant buttons
        if "fg_color" in kwargs:
            # Let the variant system handle it for styled variants
            if kwargs["fg_color"] not in ("transparent",):
                pass  # variant system will override
        if "hover_color" in kwargs:
            pass  # variant system handles it
        super().configure(**kwargs)


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
