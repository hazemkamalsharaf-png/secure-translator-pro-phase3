import os
import customtkinter as ctk
from data.config import ConfigManager
from ui.theme import ThemeManager
from ui.strings import t
from ui.asset_path import data_dir, data_path
from ui.components.card import Card

theme = ThemeManager.get_instance()


class SettingsTab(ctk.CTkFrame):
    """
    Redesigned settings tab with grouped sections and styled controls.

    Constructor contract: SettingsTab(parent, config_manager=...)
    Public method: _save_settings(self)
    """

    def __init__(self, master, config_manager=None):
        super().__init__(master, fg_color=theme.color("bg"))

        # Use the config manager passed from MainWindow if available
        if config_manager is not None:
            self.config_manager = config_manager
        else:
            self.config_manager = ConfigManager(os.path.join(data_dir(), "config.json"))

        self._toast = None  # initialized lazily below

        # Full-page scrollable area with centered content
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color=theme.color("bg"))
        self.scroll_frame.pack(fill="both", expand=True)

        wrapper = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        wrapper.pack(fill="x", padx=(24, 24), pady=(20, 32))
        wrapper.grid_columnconfigure(0, weight=1)

        # --- Card: Translation Settings ---
        self._create_translation_card(wrapper)

        # --- Card: Output & Archive ---
        self._create_output_archive_card(wrapper)

        # --- Card: Engine Mode ---
        self._create_engine_mode_card(wrapper)

    def _make_row(self, parent_frame, label_text, control):
        """Helper to create a label-left / control-right row inside a card body."""
        row = ctk.CTkFrame(parent_frame.body_frame, fg_color="transparent")
        row.pack(fill="x", pady=(0, 12))

        lbl = ctk.CTkLabel(
            row,
            text=label_text,
            font=theme.ctk_font("label"),
            text_color=theme.color("text"),
            anchor="w",
            width=160,
        )
        lbl.pack(side="left", padx=(0, 8), pady=4)

        control.pack(side="left", fill="x", expand=True, pady=4)

    def _create_translation_card(self, parent):
        """Translation settings card."""
        card = Card(parent, title=t("settings_translation"), padding="md")
        card.grid(row=0, column=0, sticky="ew", pady=(0, 12))

        # Source language selector
        self.lang_src_var = ctk.StringVar(value=self.config_manager.get("source_lang") or "en")
        src_combo = ctk.CTkComboBox(
            card.body_frame,
            values=["en", "ar", "fr", "de", "es"],
            variable=self.lang_src_var,
            font=theme.ctk_font("body"),
            height=36,
            corner_radius=theme.radius("sm"),
        )
        self._make_row(card, t("settings_source_lang") + ":", src_combo)

        # Target language selector
        self.lang_tgt_var = ctk.StringVar(value=self.config_manager.get("target_lang") or "ar")
        tgt_combo = ctk.CTkComboBox(
            card.body_frame,
            values=["en", "ar", "fr", "de", "es"],
            variable=self.lang_tgt_var,
            font=theme.ctk_font("body"),
            height=36,
            corner_radius=theme.radius("sm"),
        )
        self._make_row(card, t("settings_target_lang") + ":", tgt_combo)

    def _create_output_archive_card(self, parent):
        """Output & archive directories card."""
        card = Card(parent, title=t("settings_output_and_archive"), padding="md")
        card.grid(row=1, column=0, sticky="ew", pady=(0, 12))

        # Output directory
        self.out_dir_var = ctk.StringVar(value=self.config_manager.get("output_dir") or data_path("translated"))
        out_btn = ctk.CTkButton(
            card.body_frame,
            text=t("settings_browse"),
            command=lambda: self._browse_dir(self.out_dir_var),
            height=36,
            width=100,
            corner_radius=theme.radius("sm"),
        )
        self._make_row(card, t("settings_output_dir") + ":", out_btn)

        out_lbl = ctk.CTkLabel(
            card.body_frame,
            textvariable=self.out_dir_var,
            font=theme.ctk_font("small"),
            text_color=theme.color("text_muted"),
            anchor="w",
        )
        out_lbl.pack(fill="x", padx=(168, 0), pady=(0, 12))

        # Archive directory
        self.archive_dir_var = ctk.StringVar(value=self.config_manager.get("archive_dir") or data_path("archived"))
        arc_btn = ctk.CTkButton(
            card.body_frame,
            text=t("settings_browse"),
            command=lambda: self._browse_dir(self.archive_dir_var),
            height=36,
            width=100,
            corner_radius=theme.radius("sm"),
        )
        self._make_row(card, t("settings_archive_dir") + ":", arc_btn)

        arc_lbl = ctk.CTkLabel(
            card.body_frame,
            textvariable=self.archive_dir_var,
            font=theme.ctk_font("small"),
            text_color=theme.color("text_muted"),
            anchor="w",
        )
        arc_lbl.pack(fill="x", padx=(168, 0), pady=(0, 12))

    def _create_engine_mode_card(self, parent):
        """Engine mode card (local / cloud) + API settings."""
        card = Card(parent, title=t("settings_engine"), padding="md")
        card.grid(row=2, column=0, sticky="ew", pady=(0, 12))

        # Engine mode radio buttons
        self.engine_mode_var = ctk.StringVar(value=self.config_manager.get("engine_mode") or "local")
        mode_frame = ctk.CTkFrame(card.body_frame, fg_color="transparent")
        mode_frame.pack(fill="x", pady=(0, 12))

        def set_mode(mode):
            self.engine_mode_var.set(mode)

        radio_local = ctk.CTkRadioButton(
            mode_frame,
            text=t("settings_engine_local"),
            variable=self.engine_mode_var,
            value="local",
            command=lambda: set_mode("local"),
            font=theme.ctk_font("body"),
        )
        radio_local.pack(side="left", padx=(0, 16), pady=4)

        radio_cloud = ctk.CTkRadioButton(
            mode_frame,
            text=t("settings_engine_cloud"),
            variable=self.engine_mode_var,
            value="cloud",
            command=lambda: set_mode("cloud"),
            font=theme.ctk_font("body"),
        )
        radio_cloud.pack(side="left", padx=(0, 16), pady=4)

        # API key (for cloud mode)
        self.api_key_var = ctk.StringVar(value=self.config_manager.get("cloud_settings", "api_key") or "")
        api_entry = ctk.CTkEntry(
            card.body_frame,
            textvariable=self.api_key_var,
            placeholder_text=t("settings_api_key_placeholder"),
            font=theme.ctk_font("body"),
            height=36,
            corner_radius=theme.radius("sm"),
        )
        self._make_row(card, t("settings_api_key") + ":", api_entry)

    def _browse_dir(self, var):
        """Open a directory browser and update the given variable."""
        from tkinter import filedialog
        path = filedialog.askdirectory(title=t("settings_browse_title"))
        if path:
            var.set(path)

    def _save_settings(self):
        """Save all current settings to config manager."""
        # Build settings payload, merging into existing nested config
        cfg = self.config_manager.get_config()  # get full merged config
        cfg["source_lang"] = self.lang_src_var.get()
        cfg["target_lang"] = self.lang_tgt_var.get()
        cfg["engine_mode"] = self.engine_mode_var.get()

        # api_key lives under cloud_settings
        if "cloud_settings" not in cfg:
            cfg["cloud_settings"] = {}
        cfg["cloud_settings"]["api_key"] = self.api_key_var.get()

        try:
            self.config_manager.save(cfg)
        except Exception as e:
            pass  # silent fallback — settings are best-effort

    def load_settings(self):
        """Load current config values into UI controls."""
        cfg = self.config_manager.get_config()
        if "source_lang" in cfg:
            self.lang_src_var.set(cfg["source_lang"])
        if "target_lang" in cfg:
            self.lang_tgt_var.set(cfg["target_lang"])
        if "engine_mode" in cfg:
            self.engine_mode_var.set(cfg["engine_mode"])
        api_key = ""
        if isinstance(cfg.get("cloud_settings"), dict):
            api_key = cfg["cloud_settings"].get("api_key", "")
        self.api_key_var.set(api_key)
