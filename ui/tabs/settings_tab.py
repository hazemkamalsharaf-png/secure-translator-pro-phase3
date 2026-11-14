import json
import os
import threading
import urllib.request
import customtkinter as ctk
from tkinter import filedialog

from data.config import ConfigManager
from ui.theme import ThemeManager, token_pair, entry_style, combo_style, radio_style
from ui.components.button import PrimaryButton, SecondaryButton
from ui.components.toast import Toast
from ui.components.card import Card
from ui.strings import t
from ui.asset_path import data_dir, data_path

theme = ThemeManager.get_instance()

LANGUAGES = {
    "en": "English",
    "ar": "Arabic",
    "fr": "French",
    "de": "German",
    "es": "Spanish",
}

DEFAULT_LOCAL = {
    "base_url": "http://localhost:1234/v1/chat/completions",
    "model_name": "local-model",
    "timeout": 120,
    "max_retries": 2,
}
CLOUD_PROVIDERS = ["gemini"]
CLOUD_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2.0-flash",
]


def _tr(key, default):
    """Use the strings file when the key exists, otherwise the default text."""
    try:
        v = t(key)
    except Exception:
        return default
    return default if (not v or v == key) else v


def _lang_display(code):
    name = LANGUAGES.get(code)
    return f"{name} ({code})" if name else (code or "")


def _lang_code(display):
    display = (display or "").strip()
    if display.endswith(")") and "(" in display:
        return display.rsplit("(", 1)[1].rstrip(")").strip()
    return display


def _models_url(base_url):
    """Derive the /models endpoint from the chat-completions URL."""
    base = (base_url or "").strip().rstrip("/")
    suffix = "/chat/completions"
    if base.endswith(suffix):
        base = base[: -len(suffix)]
    return base + "/models"


class SettingsTab(ctk.CTkFrame):
    """
    Settings tab: language, folders, engine mode, local model, cloud API.

    Constructor contract: SettingsTab(parent, config_manager=...)
    Public methods: _save_settings(self), load_settings(self)
    """

    MAX_CONTENT_WIDTH = 860
    LABEL_WIDTH = 160
    MIN_SIDE_PAD = 24

    def __init__(self, master, config_manager=None):
        super().__init__(master, fg_color=token_pair("bg"))

        if config_manager is not None:
            self.config_manager = config_manager
        else:
            self.config_manager = ConfigManager(os.path.join(data_dir(), "config.json"))

        self._toast = Toast(self)
        self._status_job = None
        self._api_visible = False
        self._fetch_result = None

        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color=token_pair("bg"))
        self.scroll_frame.pack(fill="both", expand=True)

        self.wrapper = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.wrapper.pack(fill="x", anchor="n", padx=self.MIN_SIDE_PAD, pady=(20, 32))
        self.wrapper.grid_columnconfigure(0, weight=1)

        self._create_translation_card(self.wrapper)      # row 0
        self._create_output_archive_card(self.wrapper)   # row 1
        self._create_engine_mode_card(self.wrapper)      # row 2
        self._create_local_card(self.wrapper)            # row 3
        self._create_cloud_card(self.wrapper)            # row 4
        self._create_save_bar(self.wrapper)              # row 5

        self._update_engine_state()
        self.bind("<Configure>", self._on_resize, add="+")

    # ------------------------------------------------------------------
    # Layout helpers
    # ------------------------------------------------------------------
    def _on_resize(self, event):
        side = max(self.MIN_SIDE_PAD, (event.width - self.MAX_CONTENT_WIDTH) // 2)
        self.wrapper.pack_configure(padx=side)

    def _label(self, parent, text):
        return ctk.CTkLabel(
            parent,
            text=text,
            font=theme.ctk_font("label"),
            text_color=token_pair("text"),
            anchor="w",
            width=self.LABEL_WIDTH,
        )

    def _make_row(self, card, label_text, control):
        row = ctk.CTkFrame(card.body_frame, fg_color="transparent")
        row.pack(fill="x", pady=(0, 12))
        self._label(row, label_text).pack(side="left", padx=(0, 8), pady=4)
        control.pack(side="left", fill="x", expand=True, pady=4)
        return row

    def _make_entry(self, parent, var, placeholder="", width=None, show=None):
        kwargs = dict(
            textvariable=var,
            placeholder_text=placeholder,
            font=theme.ctk_font("body"),
            height=36,
            corner_radius=theme.radius("sm"),
            border_width=1,
            **entry_style(),
        )
        if width:
            kwargs["width"] = width
        if show:
            kwargs["show"] = show
        return ctk.CTkEntry(parent, **kwargs)

    def _make_lang_combo(self, card, var):
        return ctk.CTkComboBox(
            card.body_frame,
            values=[_lang_display(c) for c in LANGUAGES],
            variable=var,
            font=theme.ctk_font("body"),
            height=36,
            corner_radius=theme.radius("sm"),
            border_width=1,
            **combo_style(),
        )

    def _make_path_row(self, card, label_text, var):
        row = ctk.CTkFrame(card.body_frame, fg_color="transparent")
        row.pack(fill="x", pady=(0, 12))
        self._label(row, label_text).pack(side="left", padx=(0, 8), pady=4)
        SecondaryButton(
            row,
            text=t("settings_browse"),
            command=lambda: self._browse_dir(var),
            height=36,
            width=110,
        ).pack(side="right", pady=4)
        ctk.CTkLabel(
            row,
            textvariable=var,
            font=theme.ctk_font("small"),
            text_color=token_pair("text_muted"),
            anchor="w",
        ).pack(side="left", fill="x", expand=True, padx=(0, 12), pady=4)

    # ------------------------------------------------------------------
    # Cards
    # ------------------------------------------------------------------
    def _create_translation_card(self, parent):
        card = Card(parent, title=t("settings_translation"), padding="md")
        card.grid(row=0, column=0, sticky="ew", pady=(0, 12))

        self.lang_src_var = ctk.StringVar(
            value=_lang_display(self.config_manager.get("source_lang") or "en")
        )
        self._make_row(card, t("settings_source_lang") + ":",
                       self._make_lang_combo(card, self.lang_src_var))

        self.lang_tgt_var = ctk.StringVar(
            value=_lang_display(self.config_manager.get("target_lang") or "ar")
        )
        self._make_row(card, t("settings_target_lang") + ":",
                       self._make_lang_combo(card, self.lang_tgt_var))

    def _create_output_archive_card(self, parent):
        card = Card(parent, title=t("settings_output_and_archive"), padding="md")
        card.grid(row=1, column=0, sticky="ew", pady=(0, 12))

        self.out_dir_var = ctk.StringVar(
            value=self.config_manager.get("output_dir") or data_path("translated")
        )
        self._make_path_row(card, t("settings_output_dir") + ":", self.out_dir_var)

        self.archive_dir_var = ctk.StringVar(
            value=self.config_manager.get("archive_dir") or data_path("archived")
        )
        self._make_path_row(card, t("settings_archive_dir") + ":", self.archive_dir_var)

    def _create_engine_mode_card(self, parent):
        card = Card(parent, title=t("settings_engine"), padding="md")
        card.grid(row=2, column=0, sticky="ew", pady=(0, 12))

        self.engine_mode_var = ctk.StringVar(
            value=self.config_manager.get("engine_mode") or "local"
        )
        mode_frame = ctk.CTkFrame(card.body_frame, fg_color="transparent")
        mode_frame.pack(fill="x")

        for text_key, value in (("settings_engine_local", "local"),
                                ("settings_engine_cloud", "cloud")):
            ctk.CTkRadioButton(
                mode_frame,
                text=t(text_key),
                variable=self.engine_mode_var,
                value=value,
                command=self._update_engine_state,
                font=theme.ctk_font("body"),
                **radio_style(),
            ).pack(side="left", padx=(0, 20), pady=4)

    def _create_local_card(self, parent):
        self.local_card = Card(parent, title=_tr("settings_local_model", "Local Model Settings"),
                               padding="md")
        self.local_card.grid(row=3, column=0, sticky="ew", pady=(0, 12))
        card = self.local_card

        local = self.config_manager.get("local_settings") or {}
        if not isinstance(local, dict):
            local = {}

        # Model name: editable dropdown (type your own or fetch from the server)
        model = local.get("model_name") or DEFAULT_LOCAL["model_name"]
        self.model_name_var = ctk.StringVar(value=model)
        model_box = ctk.CTkFrame(card.body_frame, fg_color="transparent")
        self.model_combo = ctk.CTkComboBox(
            model_box,
            values=[model],
            variable=self.model_name_var,
            font=theme.ctk_font("body"),
            height=36,
            corner_radius=theme.radius("sm"),
            border_width=1,
            **combo_style(),
        )
        self.model_combo.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.fetch_btn = SecondaryButton(
            model_box,
            text=_tr("settings_fetch_models", "Fetch"),
            command=self._fetch_models,
            height=36,
            width=80,
        )
        self.fetch_btn.pack(side="right")
        self._make_row(card, _tr("settings_model_name", "Model name") + ":", model_box)

        self.base_url_var = ctk.StringVar(value=local.get("base_url") or DEFAULT_LOCAL["base_url"])
        self._make_row(card, _tr("settings_base_url", "Server URL") + ":",
                       self._make_entry(card.body_frame, self.base_url_var,
                                        "http://localhost:1234/v1/chat/completions"))

        self.timeout_var = ctk.StringVar(value=str(local.get("timeout", DEFAULT_LOCAL["timeout"])))
        self._make_row(card, _tr("settings_timeout", "Timeout (seconds)") + ":",
                       self._make_entry(card.body_frame, self.timeout_var, width=120))

        self.retries_var = ctk.StringVar(
            value=str(local.get("max_retries", DEFAULT_LOCAL["max_retries"]))
        )
        self._make_row(card, _tr("settings_max_retries", "Max retries") + ":",
                       self._make_entry(card.body_frame, self.retries_var, width=120))

        self._fetch_status = ctk.CTkLabel(
            card.body_frame,
            text="",
            font=theme.ctk_font("small"),
            text_color=token_pair("text_muted"),
            anchor="w",
        )
        self._fetch_status.pack(fill="x", pady=(0, 4))

    def _create_cloud_card(self, parent):
        self.cloud_card = Card(parent, title=_tr("settings_cloud_api", "Cloud API Settings"),
                               padding="md")
        self.cloud_card.grid(row=4, column=0, sticky="ew", pady=(0, 12))
        card = self.cloud_card

        cloud = self.config_manager.get("cloud_settings") or {}
        if not isinstance(cloud, dict):
            cloud = {}

        self.provider_var = ctk.StringVar(value=cloud.get("provider") or CLOUD_PROVIDERS[0])
        providers = list(CLOUD_PROVIDERS)
        if self.provider_var.get() not in providers:
            providers.append(self.provider_var.get())
        provider_combo = ctk.CTkComboBox(
            card.body_frame,
            values=providers,
            variable=self.provider_var,
            font=theme.ctk_font("body"),
            height=36,
            corner_radius=theme.radius("sm"),
            border_width=1,
            **combo_style(),
        )
        self._make_row(card, _tr("settings_provider", "Provider") + ":", provider_combo)

        cloud_model = cloud.get("model_name") or CLOUD_MODELS[0]
        self.cloud_model_var = ctk.StringVar(value=cloud_model)
        cloud_models = list(CLOUD_MODELS)
        if cloud_model not in cloud_models:
            cloud_models.insert(0, cloud_model)
        self.cloud_model_combo = ctk.CTkComboBox(
            card.body_frame,
            values=cloud_models,
            variable=self.cloud_model_var,
            font=theme.ctk_font("body"),
            height=36,
            corner_radius=theme.radius("sm"),
            border_width=1,
            **combo_style(),
        )
        self._make_row(card, _tr("settings_model_name", "Model name") + ":", self.cloud_model_combo)

        self.api_key_var = ctk.StringVar(value=cloud.get("api_key") or "")
        api_box = ctk.CTkFrame(card.body_frame, fg_color="transparent")
        self.api_entry = self._make_entry(
            api_box, self.api_key_var, t("settings_api_key_placeholder"), show="•"
        )
        self.api_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.api_toggle = SecondaryButton(
            api_box, text=_tr("settings_show", "Show"),
            command=self._toggle_api_visibility, height=36, width=70,
        )
        self.api_toggle.pack(side="right")
        self._make_row(card, t("settings_api_key") + ":", api_box)

    def _create_save_bar(self, parent):
        save_row = ctk.CTkFrame(parent, fg_color="transparent")
        save_row.grid(row=5, column=0, sticky="ew", pady=(4, 0))
        self._save_status = ctk.CTkLabel(
            save_row,
            text="",
            font=theme.ctk_font("small"),
            text_color=token_pair("success"),
            anchor="w",
        )
        self._save_status.pack(side="left", fill="x", expand=True)
        PrimaryButton(
            save_row,
            text=t("settings_save"),
            command=self._save_settings,
            height=38,
            width=160,
        ).pack(side="right")

    # ------------------------------------------------------------------
    # Behavior
    # ------------------------------------------------------------------
    def _update_engine_state(self):
        """Show the local card in local mode, the cloud card in cloud mode."""
        if self.engine_mode_var.get() == "cloud":
            self.local_card.grid_remove()
            self.cloud_card.grid()
        else:
            self.cloud_card.grid_remove()
            self.local_card.grid()

    def _toggle_api_visibility(self):
        self._api_visible = not self._api_visible
        self.api_entry.configure(show="" if self._api_visible else "•")
        self.api_toggle.configure(
            text=_tr("settings_hide", "Hide") if self._api_visible
            else _tr("settings_show", "Show")
        )

    def _browse_dir(self, var):
        path = filedialog.askdirectory(title=t("settings_browse_title"))
        if path:
            var.set(path)

    # -- fetch models from the local server ---------------------------
    def _fetch_models(self):
        url = _models_url(self.base_url_var.get())
        self.fetch_btn.configure(state="disabled")
        self._fetch_status.configure(text=f"Contacting {url} ...",
                                     text_color=token_pair("text_muted"))
        self._fetch_result = None

        def worker():
            try:
                with urllib.request.urlopen(url, timeout=5) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                ids = [m.get("id") for m in data.get("data", []) if m.get("id")]
                self._fetch_result = ("ok", ids)
            except Exception as exc:
                self._fetch_result = ("error", str(exc))

        threading.Thread(target=worker, daemon=True).start()
        self.after(150, self._poll_fetch)

    def _poll_fetch(self):
        if self._fetch_result is None:
            self.after(150, self._poll_fetch)
            return
        kind, payload = self._fetch_result
        self.fetch_btn.configure(state="normal")
        if kind == "ok" and payload:
            self.model_combo.configure(values=payload)
            if self.model_name_var.get() not in payload:
                self.model_name_var.set(payload[0])
            self._fetch_status.configure(
                text=f"Found {len(payload)} model(s).", text_color=token_pair("success"))
        elif kind == "ok":
            self._fetch_status.configure(
                text="Server answered but no models are loaded.",
                text_color=token_pair("warning"))
        else:
            self._fetch_status.configure(
                text=f"Could not reach the server: {payload}",
                text_color=token_pair("danger"))

    # -- saving --------------------------------------------------------
    def _set_status(self, text, color_key):
        self._save_status.configure(text=text, text_color=token_pair(color_key))
        if self._status_job is not None:
            self.after_cancel(self._status_job)
        self._status_job = self.after(4000, lambda: self._save_status.configure(text=""))

    @staticmethod
    def _to_int(value, fallback, minimum=0):
        try:
            return max(minimum, int(str(value).strip()))
        except (TypeError, ValueError):
            return fallback

    def _save_settings(self):
        """Save all settings, merging into the existing nested config."""
        cfg = self.config_manager.get_config()
        cfg["source_lang"] = _lang_code(self.lang_src_var.get())
        cfg["target_lang"] = _lang_code(self.lang_tgt_var.get())
        cfg["engine_mode"] = self.engine_mode_var.get()
        cfg["output_dir"] = self.out_dir_var.get()
        cfg["archive_dir"] = self.archive_dir_var.get()

        local = cfg.get("local_settings")
        if not isinstance(local, dict):
            local = {}
        local["base_url"] = self.base_url_var.get().strip() or DEFAULT_LOCAL["base_url"]
        local["model_name"] = self.model_name_var.get().strip() or DEFAULT_LOCAL["model_name"]
        local["timeout"] = self._to_int(
            self.timeout_var.get(), local.get("timeout", DEFAULT_LOCAL["timeout"]), minimum=1)
        local["max_retries"] = self._to_int(
            self.retries_var.get(), local.get("max_retries", DEFAULT_LOCAL["max_retries"]))
        cfg["local_settings"] = local

        cloud = cfg.get("cloud_settings")
        if not isinstance(cloud, dict):
            cloud = {}
        cloud["provider"] = self.provider_var.get().strip() or CLOUD_PROVIDERS[0]
        cloud["model_name"] = self.cloud_model_var.get().strip() or CLOUD_MODELS[0]
        cloud["api_key"] = self.api_key_var.get()
        cfg["cloud_settings"] = cloud

        try:
            saved = self.config_manager.save(cfg)
        except Exception:
            saved = False

        if saved:
            # Reflect any corrected numbers back in the fields
            self.timeout_var.set(str(local["timeout"]))
            self.retries_var.set(str(local["max_retries"]))
            self._set_status(t("settings_saved"), "success")
            self._toast.show(t("toast_success"), t("settings_saved"), "success")
        else:
            self._set_status(t("settings_save_error"), "danger")
            self._toast.show(t("toast_error"), t("settings_save_error"), "error")

    def load_settings(self):
        """Load current config values into UI controls."""
        cfg = self.config_manager.get_config()
        if "source_lang" in cfg:
            self.lang_src_var.set(_lang_display(cfg["source_lang"]))
        if "target_lang" in cfg:
            self.lang_tgt_var.set(_lang_display(cfg["target_lang"]))
        if "engine_mode" in cfg:
            self.engine_mode_var.set(cfg["engine_mode"])

        self.out_dir_var.set(cfg.get("output_dir") or data_path("translated"))
        self.archive_dir_var.set(cfg.get("archive_dir") or data_path("archived"))

        local = cfg.get("local_settings") if isinstance(cfg.get("local_settings"), dict) else {}
        self.model_name_var.set(local.get("model_name", DEFAULT_LOCAL["model_name"]))
        self.base_url_var.set(local.get("base_url", DEFAULT_LOCAL["base_url"]))
        self.timeout_var.set(str(local.get("timeout", DEFAULT_LOCAL["timeout"])))
        self.retries_var.set(str(local.get("max_retries", DEFAULT_LOCAL["max_retries"])))

        cloud = cfg.get("cloud_settings") if isinstance(cfg.get("cloud_settings"), dict) else {}
        self.provider_var.set(cloud.get("provider") or CLOUD_PROVIDERS[0])
        self.cloud_model_var.set(cloud.get("model_name") or CLOUD_MODELS[0])
        self.api_key_var.set(cloud.get("api_key", ""))
        self._update_engine_state()