import customtkinter as ctk
from ui.components.nav_item import NavItem
from ui.theme import ThemeManager, token_pair, sync_appearance
from ui.strings import APP_NAME, APP_VERSION, t

theme = ThemeManager.get_instance()


class Sidebar(ctk.CTkFrame):
    """
    Sidebar with:
    - Brand block (logo + name + PRO badge)
    - Navigation items with icon + label + active/hover states
    - Footer with theme toggle + version

    Constructor contract: Sidebar(master, select_tab_callback)
    Public methods: select_tab(name), set_active(name)
    """

    WIDTH = 240

    # (tab name, icon name, strings key)
    NAV_ITEMS = [
        ("translation", "book", "tab_translation"),
        ("glossary", "glossary", "tab_glossary"),
        ("settings", "settings", "tab_settings"),
    ]

    def __init__(self, master, select_tab_callback):
        super().__init__(
            master,
            width=self.WIDTH,
            corner_radius=0,
            fg_color=token_pair("sidebar_bg"),
        )
        self.select_tab_callback = select_tab_callback
        self._active_tab = None

        # Fixed width: long labels must never widen the sidebar
        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # brand
        self.grid_rowconfigure(1, weight=0)  # navigation
        self.grid_rowconfigure(2, weight=1)  # spacer
        self.grid_rowconfigure(3, weight=0)  # footer

        self._build_brand()
        self._build_nav()
        self._build_footer()
        self._update_theme_icons(theme.mode)

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------
    def _build_brand(self):
        brand = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        brand.grid(row=0, column=0, sticky="ew", padx=16, pady=(24, 18))
        brand.grid_columnconfigure(1, weight=1)

        logo = ctk.CTkFrame(
            brand, width=38, height=38, corner_radius=11,
            fg_color=token_pair("primary"),
        )
        logo.grid(row=0, column=0, rowspan=2, padx=(0, 10))
        logo.grid_propagate(False)
        ctk.CTkLabel(
            logo, text="ST",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#ffffff",
        ).place(relx=0.5, rely=0.5, anchor="center")

        # "SecureTranslatorPro" -> "SecureTranslator" + [PRO] badge
        has_badge = APP_NAME.endswith("Pro") and len(APP_NAME) > 3 and " " not in APP_NAME
        base_name = APP_NAME[:-3] if has_badge else APP_NAME

        name_row = ctk.CTkFrame(brand, fg_color="transparent")
        name_row.grid(row=0, column=1, sticky="sw")
        ctk.CTkLabel(
            name_row, text=base_name,
            font=theme.ctk_font("label", weight="bold"),
            text_color=token_pair("sidebar_fg"),
            anchor="w",
        ).pack(side="left")
        if has_badge:
            ctk.CTkLabel(
                name_row, text="PRO", height=16, corner_radius=5,
                fg_color=token_pair("primary"),
                text_color="#ffffff",
                font=ctk.CTkFont(size=9, weight="bold"),
                width=30,
            ).pack(side="left", padx=(6, 0))

        ctk.CTkLabel(
            brand, text=t("sidebar_tagline"),
            font=theme.ctk_font("small"),
            text_color=token_pair("sidebar_icon"),
            anchor="w",
        ).grid(row=1, column=1, sticky="nw")

    def _build_nav(self):
        nav = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        nav.grid(row=1, column=0, sticky="ew", padx=10, pady=(4, 0))

        self.nav_items = {}
        for tab_name, icon_name, label_key in self.NAV_ITEMS:
            item = NavItem(
                nav,
                icon_name=icon_name,
                label=t(label_key),
                command=lambda name=tab_name: self.select_tab(name),
            )
            item.pack(fill="x", padx=2, pady=3)
            self.nav_items[tab_name] = item

    def _build_footer(self):
        footer = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        footer.grid(row=3, column=0, sticky="ew", padx=16, pady=(8, 20))

        ctk.CTkFrame(
            footer, height=1, corner_radius=0,
            fg_color=token_pair("sidebar_active"),
        ).pack(fill="x", pady=(0, 12))

        self._theme_btn = ctk.CTkButton(
            footer,
            text="",
            font=theme.ctk_font("small"),
            fg_color=token_pair("sidebar_active"),
            hover_color=token_pair("primary"),
            text_color=token_pair("sidebar_fg"),
            height=36,
            corner_radius=8,
            anchor="w",
            command=self._toggle_theme,
        )
        self._theme_btn.pack(fill="x")

        ctk.CTkLabel(
            footer, text=APP_VERSION,
            font=ctk.CTkFont(size=11),
            text_color=token_pair("sidebar_icon"),
        ).pack(pady=(10, 0), anchor="w")

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------
    def set_active(self, name):
        """Update the highlight only (does NOT fire the callback)."""
        self._active_tab = name
        for tab_name, item in self.nav_items.items():
            if tab_name == name:
                item.activate()
            else:
                item.deactivate()

    def select_tab(self, name):
        """Highlight the tab and tell MainWindow to show it."""
        self.set_active(name)
        if self.select_tab_callback:
            self.select_tab_callback(name)

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------
    def _toggle_theme(self):
        new_mode = "dark" if theme.mode == "light" else "light"
        theme.set_mode(new_mode)
        sync_appearance(new_mode)
        self._update_theme_icons(new_mode)

        # Persist theme mode (same API the Settings tab uses)
        try:
            cm = self.master.config_manager
            cfg = cm.get_config()
            cfg["theme_mode"] = new_mode
            cm.save(cfg)
        except Exception:
            pass

        if hasattr(self.master, "on_theme_change"):
            self.master.on_theme_change(new_mode)

    def _update_theme_icons(self, mode):
        label = t("theme_switch_dark") if mode == "light" else t("theme_switch_light")
        glyph = "☾" if mode == "light" else "☀"
        self._theme_btn.configure(text=f"  {glyph}   {label}")