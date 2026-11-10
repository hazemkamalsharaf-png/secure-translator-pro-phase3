"""
Card component — elevated panel with rounded corners and subtle border.

Usage:
    card = Card(parent, title="Section Name")
    card.pack(fill="x", padx=20, pady=8)
    card.body_frame.grid(...)  # use body_frame for child widgets
"""

import customtkinter as ctk
from ui.theme import ThemeManager

theme = ThemeManager.get_instance()


class Card(ctk.CTkFrame):
    """A content card with optional title, padding, and elevated styling."""

    def __init__(self, master, title: str = None, padding: str = "md",
                 height: int = None, width: int = None, **kwargs):
        _pad = theme.spacing(padding)
        _radius = theme.radius("lg")  # 14px radius for a modern look

        super().__init__(
            master,
            corner_radius=_radius,
            border_width=1,
            border_color=theme.color("border"),
            fg_color=theme.color("surface"),
            **kwargs,
        )

        self._title = title
        self._padding = _pad
        self._radius = _radius

        # Internal padding frame (content goes here)
        self.body_frame = ctk.CTkFrame(self, fg_color="transparent")

        if title:
            # Title bar with bottom border
            self._title_frame = ctk.CTkFrame(
                self, fg_color="transparent", corner_radius=0
            )
            self._title_label = ctk.CTkLabel(
                self._title_frame,
                text=title,
                font=theme.ctk_font("subhead"),
                text_color=theme.color("text"),
                anchor="w",
            )
            self._title_label.grid(row=0, column=0, padx=_pad, pady=_pad, sticky="w")

            # Bottom border line in title bar area
            self._title_line = ctk.CTkFrame(
                self._title_frame,
                height=1,
                fg_color=theme.color("border"),
                corner_radius=0,
            )
            self._title_line.grid(row=1, column=0, sticky="ew", padx=_pad)

            # Pack title frame at top of card
            self._title_frame.pack(fill="x")
            self.body_frame.pack(fill="both", expand=True, padx=_pad, pady=(0, _pad))
        else:
            self.body_frame.pack(fill="both", expand=True, padx=_pad, pady=_pad)

    def set_title(self, title: str):
        """Update the card's title text."""
        if hasattr(self, '_title_label'):
            self._title_label.configure(text=title)

    def add_action_button(self, text, command=None, icon_name=None):
        """Add a small action button to the right of the title."""
        if not hasattr(self, '_actions'):
            self._actions = ctk.CTkFrame(self._title_frame, fg_color="transparent")
            self._actions.grid(row=0, column=1, padx=_pad, pady=_pad, sticky="e")
        btn = ctk.CTkButton(
            self._actions,
            text=text,
            font=theme.ctk_font("small"),
            fg_color=theme.color("surface_hover"),
            hover_color=theme.color("border"),
            corner_radius=theme.radius("sm"),
            height=24,
            width=60,
            command=command,
        )
        btn.pack(side="right", padx=4)
        return btn
