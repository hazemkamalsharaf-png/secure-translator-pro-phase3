import customtkinter as ctk
from ui.sidebar import Sidebar
from ui.tabs.translation_tab import TranslationTab
from ui.tabs.glossary_tab import GlossaryTab
from ui.tabs.settings_tab import SettingsTab
from ui.theme import ThemeManager, token_pair, sync_appearance
from ui.strings import APP_NAME, APP_VERSION, t

theme = ThemeManager.get_instance()


class MainWindow(ctk.CTk):
    """
    Layout:
      column 0: Sidebar (fixed width)
      column 1: content_frame
          row 0: top bar (page title + version)
          row 1: 1px divider
          row 2: body (tabs live here and fill everything)

    Constructor contract: MainWindow(config_manager=...)
    Attributes: config_manager, sidebar, body_frame, tabs (dict)
    Method: select_tab(name)
    """

    SIDEBAR_WIDTH = 240
    TOPBAR_HEIGHT = 60
    TAB_TITLE_KEYS = {
        "translation": "tab_translation",
        "glossary": "tab_glossary",
        "settings": "tab_settings",
    }

    def __init__(self, config_manager):
        super().__init__()

        self.config_manager = config_manager
        self.current_tab = None
        self._selecting = False

        self.title(APP_NAME)
        self.geometry("1280x780")
        self.minsize(1000, 650)
        self.configure(fg_color=token_pair("bg"))

        self.grid_columnconfigure(0, weight=0, minsize=self.SIDEBAR_WIDTH)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = Sidebar(self, self.select_tab)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        self._build_content_area()

        self.tabs = {}
        self._init_tabs()
        self.select_tab("translation")

        self._bind_shortcuts()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    def _build_content_area(self):
        self.content_frame = ctk.CTkFrame(
            self, corner_radius=0, fg_color=token_pair("bg")
        )
        self.content_frame.grid(row=0, column=1, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=0)  # top bar
        self.content_frame.grid_rowconfigure(1, weight=0)  # divider
        self.content_frame.grid_rowconfigure(2, weight=1)  # body

        self._create_top_bar()

        self.top_bar_line = ctk.CTkFrame(
            self.content_frame,
            height=1,
            fg_color=token_pair("border"),
            corner_radius=0,
        )
        self.top_bar_line.grid(row=1, column=0, sticky="ew")

        self.body_frame = ctk.CTkFrame(
            self.content_frame, fg_color=token_pair("bg"), corner_radius=0
        )
        self.body_frame.grid(row=2, column=0, sticky="nsew")
        self.body_frame.grid_columnconfigure(0, weight=1)
        self.body_frame.grid_rowconfigure(0, weight=1)

    def _create_top_bar(self):
        self.top_bar = ctk.CTkFrame(
            self.content_frame,
            height=self.TOPBAR_HEIGHT,
            fg_color=token_pair("surface"),
            border_width=0,
            corner_radius=0,
        )
        self.top_bar.grid(row=0, column=0, sticky="ew")
        self.top_bar.grid_propagate(False)
        self.top_bar.grid_columnconfigure(0, weight=1)
        self.top_bar.grid_rowconfigure(0, weight=1)

        self.top_bar_title = ctk.CTkLabel(
            self.top_bar,
            text=t("tab_translation"),
            font=theme.ctk_font("subhead"),
            text_color=token_pair("text"),
            anchor="w",
        )
        self.top_bar_title.grid(row=0, column=0, padx=28, sticky="w")

        self.top_bar_meta = ctk.CTkLabel(
            self.top_bar,
            text=APP_VERSION,
            font=theme.ctk_font("small"),
            text_color=token_pair("text_muted"),
            anchor="e",
        )
        self.top_bar_meta.grid(row=0, column=1, padx=(0, 28), sticky="e")

    def _init_tabs(self):
        self.tabs["translation"] = TranslationTab(self.body_frame, self.config_manager)
        self.tabs["glossary"] = GlossaryTab(self.body_frame)
        self.tabs["settings"] = SettingsTab(
            self.body_frame, config_manager=self.config_manager
        )
        for tab in self.tabs.values():
            tab.grid(row=0, column=0, sticky="nsew")

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------
    def select_tab(self, name):
        """Show the requested tab, update the title and the sidebar highlight."""
        if name not in self.tabs or self._selecting:
            return
        self._selecting = True  # guards against Sidebar <-> MainWindow loops
        try:
            for tab in self.tabs.values():
                tab.grid_remove()
            self.tabs[name].grid()
            self.current_tab = name

            title_key = self.TAB_TITLE_KEYS.get(name)
            self.top_bar_title.configure(text=t(title_key) if title_key else name.title())

            set_active = getattr(self.sidebar, "set_active", None)
            if callable(set_active):
                set_active(name)
        finally:
            self._selecting = False

    def _bind_shortcuts(self):
        shortcuts = {
            "t": lambda: self.select_tab("translation"),
            "g": lambda: self.select_tab("glossary"),
            "comma": lambda: self.select_tab("settings"),
            "s": self._save_settings_from_current_tab,
        }
        for key, action in shortcuts.items():
            # إذا كان المفتاح عبارة عن حرف واحد (مثل t, g, s)، قم بإنشاء نسخة كبيرة وصغيرة
            # أما إذا كان كلمة (مثل comma)، اتركه كما هو
            if len(key) == 1 and key.isalpha():
                keys_to_bind = {key, key.upper()}
            else:
                keys_to_bind = {key}
                
            for k in keys_to_bind:
                self.bind(f"<Control-{k}>", lambda e, a=action: a())

        self.bind("<Control-Key-1>", lambda e: self.select_tab("translation"))
        self.bind("<Control-Key-2>", lambda e: self.select_tab("glossary"))
        self.bind("<Control-Key-3>", lambda e: self.select_tab("settings"))
    # ------------------------------------------------------------------
    # Theme integration
    # ------------------------------------------------------------------
    def on_theme_change(self, mode):
        """Called by Sidebar when theme is toggled (colour pairs follow appearance mode)."""
        theme.set_mode(mode)
        sync_appearance(mode)

    def _save_settings_from_current_tab(self):
        settings_tab = self.tabs.get("settings")
        if settings_tab and hasattr(settings_tab, "_save_settings"):
            settings_tab._save_settings()

    def _retheme_frame(self, frame):
        """Kept for callers; colour pairs update through appearance mode."""
        return None