
import customtkinter as ctk
from ui.sidebar import Sidebar
from ui.tabs.translation_tab import TranslationTab
from ui.tabs.glossary_tab import GlossaryTab
from ui.tabs.settings_tab import SettingsTab
from ui.theme import ThemeManager
from ui.strings import APP_NAME, APP_VERSION, t

theme = ThemeManager.get_instance()


class MainWindow(ctk.CTk):
    """
    Main application window with:
    - Sidebar (left, fixed width)
    - Content area (expands to fill remaining space)
      - Top bar (page title)
      - Body (tab content fills entire area)

    Constructor contract: MainWindow(config_manager=...)
    Attributes: config_manager, sidebar, body_frame, tabs (dict)
    Method: select_tab(name)
    """

    SIDEBAR_WIDTH = 240

    def __init__(self, config_manager):
        super().__init__()

        self.config_manager = config_manager
        self.title(APP_NAME)
        self.geometry("1280x780")
        self.minsize(1000, 650)

        # Grid layout: sidebar (fixed) + content (stretch)
        self.grid_columnconfigure(0, weight=0, minsize=self.SIDEBAR_WIDTH)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        self.sidebar = Sidebar(self, self.select_tab)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        # --- Content area (full height, no dead space) ---
        self.content_frame = ctk.CTkFrame(
            self,
            corner_radius=0,
            fg_color=theme.color("bg"),
        )
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=(4, 0), pady=0)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=0)  # top bar
        self.content_frame.grid_rowconfigure(1, weight=1)  # body

        # --- Top bar ---
        self._create_top_bar()

        # --- Tabs ---
        self.tabs = {}
        self._init_tabs()
        self.select_tab("translation")

        # Keyboard shortcuts
        self.bind("<Control-t>", lambda e: self.select_tab("translation"))
        self.bind("<Control-T>", lambda e: self.select_tab("translation"))
        self.bind("<Control-g>", lambda e: self.select_tab("glossary"))
        self.bind("<Control-G>", lambda e: self.select_tab("glossary"))
        self.bind("<Control-s>", lambda e: self._save_settings_from_current_tab())
        self.bind("<Control-S>", lambda e: self._save_settings_from_current_tab())

    def _create_top_bar(self):
        """Create the top bar with page title."""
        self.top_bar = ctk.CTkFrame(
            self.content_frame,
            height=48,
            fg_color=theme.color("surface"),
            border_width=0,
            corner_radius=0,
        )
        self.top_bar.grid(row=0, column=0, sticky="ew")
        self.top_bar.grid_columnconfigure(0, weight=1)

        self.top_bar_title = ctk.CTkLabel(
            self.top_bar,
            text=t("tab_translation"),
            font=theme.ctk_font("subhead"),
            text_color=theme.color("text"),
            anchor="w",
        )
        self.top_bar_title.grid(row=0, column=0, padx=24, pady=0, sticky="w")

        # Bottom border line (full-width separator)
        self.top_bar_line = ctk.CTkFrame(
            self.top_bar,
            height=1,
            fg_color=theme.color("border"),
            corner_radius=0,
        )
        self.top_bar_line.grid(row=1, column=0, sticky="ew", pady=(0, 0))

        # Body area (below top bar — fills remaining space)
        self.body_frame = ctk.CTkFrame(
            self.content_frame,
            fg_color=theme.color("bg"),
            corner_radius=0,
        )
        self.body_frame.grid(row=1, column=0, sticky="nsew")
        self.body_frame.grid_columnconfigure(0, weight=1)
        self.body_frame.grid_rowconfigure(0, weight=1)

    def _init_tabs(self):
        """Initialize all tab pages."""
        self.tabs["translation"] = TranslationTab(self.body_frame, self.config_manager)
        self.tabs["translation"].grid(row=0, column=0, sticky="nsew")

        self.tabs["glossary"] = GlossaryTab(self.body_frame)
        self.tabs["glossary"].grid(row=0, column=0, sticky="nsew")

        self.tabs["settings"] = SettingsTab(self.body_frame, config_manager=self.config_manager)
        self.tabs["settings"].grid(row=0, column=0, sticky="nsew")

    def select_tab(self, name):
        """Hide all tabs, show the requested one, update top bar title."""
        for tab in self.tabs.values():
            tab.grid_remove()
        if name in self.tabs:
            self.tabs[name].grid()
            # Update top bar title
            titles = {
                "translation": t("tab_translation"),
                "glossary": t("tab_glossary"),
                "settings": t("tab_settings"),
            }
            self.top_bar_title.configure(text=titles.get(name, name.title()))

    # ---------------------------------------------------------------
    # Theme integration
    # ---------------------------------------------------------------
    def on_theme_change(self, mode):
        """Called by Sidebar when theme is toggled."""
        theme.set_mode(mode)
        dark = mode == "dark"

        self.configure(fg_color=theme.color("bg"))
        self.content_frame.configure(fg_color=theme.color("bg"))
        self.top_bar.configure(fg_color=theme.color("surface"))
        self.top_bar_line.configure(fg_color=theme.color("border"))
        self.body_frame.configure(fg_color=theme.color("bg"))
        self.top_bar_title.configure(text_color=theme.color("text"))

        for tab in self.tabs.values():
            self._retheme_frame(tab)

        self.sidebar._apply_theme(self.sidebar, mode)

    def _save_settings_from_current_tab(self):
        """Save settings by triggering the Settings tab's save method."""
        settings_tab = self.tabs.get("settings")
        if settings_tab and hasattr(settings_tab, "_save_settings"):
            settings_tab._save_settings()

    def _retheme_frame(self, frame):
        """Recursively re-theme all widgets in a frame."""
        for child in frame.winfo_children():
            # Only retheme widgets that are frames (not Labels, Buttons, etc.)
            if isinstance(child, ctk.CTkFrame):
                try:
                    fg = child.cget("fg_color")
                    if fg and fg != "transparent":
                        child.configure(fg_color=theme.color("surface"))
                except Exception:
                    pass
            self._retheme_frame(child)
