"""
Section header — decorative divider with a title label.

Usage:
    header = SectionHeader(frame, "Local Model Settings")
    header.pack(fill="x", pady=(16, 4))
"""

import customtkinter as ctk
from ui.theme import ThemeManager

theme = ThemeManager.get_instance()


class SectionHeader(ctk.CTkFrame):
    """A section divider with a title and subtle bottom border."""

    def __init__(self, master, title: str):
        super().__init__(master, fg_color="transparent", height=36)
        self.grid_columnconfigure(0, weight=1)

        # Title label
        lbl = ctk.CTkLabel(
            self,
            text=title,
            font=theme.ctk_font("label"),
            text_color=theme.color("text"),
            anchor="w",
        )
        lbl.grid(row=0, column=0, padx=0, pady=8, sticky="w")

        # Bottom line
        line = ctk.CTkFrame(self, fg_color=theme.color("border"), height=1, corner_radius=0)
        line.grid(row=1, column=0, sticky="ew", pady=(0, 0))
        self.grid_rowconfigure(1, weight=0)
