
import customtkinter as ctk
from ui.components.nav_item import NavItem
from ui.theme import ThemeManager
from ui.strings import APP_NAME, APP_VERSION

theme = ThemeManager.get_instance()


class Sidebar(ctk.CTkFrame):
    """
    Sidebar with:
    - Brand block (logo + name) at top
    - Navigation items with icon + label + active/hover states
    - Footer with theme toggle button + version

    Constructor contract: Sidebar(master, select_tab_callback)
    Public method: select_tab(name)
    """

    NAV_ITEMS = [
        ("translation", "book", "Translation"),
        ("glossary", "glossary", "Glossary"),
        ("settings", "settings", "Settings"),
    ]

    def __init__(self, master, select_tab_callback):
        super().__init__(
            master,
            width=240,
            corner_radius=0,
            fg_color=theme.color("sidebar_bg"),
        )
        self.select_tab_callback = select_tab_callback
        self._active_tab = None

        # Do NOT set grid_propagate(False) — let content determine natural size
        # within the fixed width we set above.
        self._min_width = 240

        # Row weights: brand, nav items (stretch), spacer, footer
        self.grid_rowconfigure(0, weight=0)   # Brand
        self.grid_rowconfigure(1, weight=3)   # Navigation (takes most space)
        self.grid_rowconfigure(2, weight=1)   # Spacer (pushes footer down)
        self.grid_rowconfigure(3, weight=0)   # Footer

        # --- Brand block ---
        brand_frame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        brand_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(20, 8))
        brand_frame.grid_columnconfigure(1, weight=1)

        # Logo circle with initials
        logo_frame = ctk.CTkFrame(brand_frame, width=38, height=38, corner_radius=12,
                                   fg_color=theme.color("primary"))
        logo_frame.grid(row=0, column=0, padx=(0, 12), pady=0)

        logo_text = ctk.CTkLabel(
            logo_frame,
            text="ST",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#ffffff",
        )
        logo_text.place(relx=0.5, rely=0.5, anchor="center")

        # App name (right of logo)
        brand_text = ctk.CTkLabel(
            brand_frame,
            text=APP_NAME,
            font=theme.ctk_font("subhead"),
            text_color=theme.color("sidebar_fg"),
            anchor="w",
        )
        brand_text.grid(row=0, column=1, padx=(0, 4), pady=2, sticky="w")

        # --- Navigation items ---
        nav_frame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        nav_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=(4, 0))

        self.nav_items = {}
        for tab_name, icon_name, label in self.NAV_ITEMS:
            item = NavItem(
                nav_frame,
                icon_name=icon_name,
                label=label,
                command=lambda t=tab_name: self.select_tab(t),
            )
            item.pack(fill="x", padx=4, pady=3)
            self.nav_items[tab_name] = item

        # --- Footer (theme toggle + version) ---
        footer_frame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        footer_frame.grid(row=3, column=0, sticky="ew", padx=16, pady=(8, 20))

        # Theme toggle button
        self._theme_btn = ctk.CTkButton(
            footer_frame,
            text="",
            font=ctk.CTkFont(size=14),
            fg_color="transparent",
            hover_color=theme.color("sidebar_active"),
            text_color=theme.color("sidebar_icon"),
            height=32,
            corner_radius=8,
            command=self._toggle_theme,
        )
        self._theme_btn.pack(fill="x")

        # Version label (below theme toggle)
        ver_label = ctk.CTkLabel(
            footer_frame,
            text=APP_VERSION,
            font=ctk.CTkFont(size=10),
            text_color=theme.color("sidebar_icon"),
        )
        ver_label.pack(pady=(4, 0))

        # Initialize theme icon
        self._update_theme_icons(theme.mode)

    def select_tab(self, name):
        """Switch to the given tab and update active state."""
        self._active_tab = name
        for tab_name, item in self.nav_items.items():
            if tab_name == name:
                item.activate()
            else:
                item.deactivate()
        if self.select_tab_callback:
            self.select_tab_callback(name)

    def _toggle_theme(self):
        """Toggle between light and dark modes."""
        new_mode = "dark" if theme.mode == "light" else "light"
        theme.set_mode(new_mode)
        self._update_theme_icons(new_mode)
        self._apply_theme(self, new_mode)
        # Persist theme mode to config
        try:
            cfg = self.master.config_manager.config
            cfg["theme_mode"] = new_mode
            self.master.config_manager.save(cfg)
        except Exception:
            pass
        if hasattr(self.master, "on_theme_change"):
            self.master.on_theme_change(new_mode)

    def _update_theme_icons(self, mode):
        """Update the theme toggle button icon."""
        icon = "\u2600\ufe0f" if mode == "light" else "\u263d\ufe0f"
        self._theme_btn.configure(text=icon)

    def _apply_theme(self, widget, mode):
        """Recursively apply theme colors to a widget tree."""
        dark = mode == "dark"
        fg = theme.color("sidebar_bg") if not dark else theme.color("sidebar_bg")
        if hasattr(widget, "configure"):
            try:
                cval = widget.cget("fg_color")
                if cval and cval != "transparent":
                    widget.configure(fg_color=fg)
            except Exception:
                pass
        for child in widget.winfo_children():
            self._apply_theme(child, mode)
