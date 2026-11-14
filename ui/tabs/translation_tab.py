import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import threading

from core.engine import TranslationEngine
from ui.theme import ThemeManager, token_pair, entry_style
from ui.strings import t
from ui.asset_path import data_path
from ui.components.card import Card
from ui.components.toast import Toast, ToastBanner
from ui.components.button import PrimaryButton, GhostButton

theme = ThemeManager.get_instance()


class TranslationTab(ctk.CTkFrame):
    """
    Redesigned translation workspace with full-height card layout.

    Constructor contract: TranslationTab(parent, config_manager)
    Internal callbacks passed to TranslationEngine keep the same signatures.
    """

    def __init__(self, master, config_manager):
        super().__init__(master, fg_color=token_pair("bg"))

        self.config_manager = config_manager
        self._engine = None
        self._toast = Toast(self)
        self._is_running = False

        # One scrollable frame fills the entire body area
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=token_pair("bg"),
        )
        self.scroll_frame.pack(fill="both", expand=True)

        # Content wrapper — centers cards with max width
        self._content = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self._content.pack(fill="x", padx=24, pady=(20, 32))
        self._content.grid_columnconfigure(0, weight=1)

        # --- Card 1: Source File ---
        self._create_source_card()

        # --- Card 2: Translator Persona ---
        self._create_persona_card()

        # --- Card 3: Progress & Start ---
        self._create_progress_card()

    def _create_source_card(self):
        """Card 1: Source file selection."""
        card = Card(self._content, title=t("trans_source_label"), padding="md")
        card.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        card.body_frame.grid_columnconfigure(1, weight=1)

        # File path entry + Browse button
        fp_row = ctk.CTkFrame(card.body_frame, fg_color="transparent")
        fp_row.pack(fill="x", pady=(0, 4))

        self.file_path_var = ctk.StringVar(value=t("trans_no_file"))
        self.entry_file = ctk.CTkEntry(
            fp_row,
            textvariable=self.file_path_var,
            state="disabled",
            font=theme.ctk_font("body"),
            height=36,
            corner_radius=theme.radius("sm"),
            border_width=1,
            **entry_style(),
        )
        self.entry_file.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.btn_browse = PrimaryButton(
            fp_row,
            text=t("trans_browse"),
            command=self._browse_file,
            width=110,
            height=36,
        )
        self.btn_browse.pack(side="right")

        # File info line (size + name)
        self.file_info_label = ctk.CTkLabel(
            card.body_frame,
            text="",
            font=theme.ctk_font("muted"),
            text_color=token_pair("text_muted"),
            anchor="w",
        )
        self.file_info_label.pack(fill="x", pady=(4, 0))

    def _create_persona_card(self):
        """Card 2: Translator persona / instructions."""
        card = Card(self._content, title=t("trans_persona_label"), padding="md")
        card.grid(row=1, column=0, sticky="nsew", pady=(0, 12))
        card.body_frame.grid_rowconfigure(1, weight=1)

        # Header row (label + reset button)
        header = ctk.CTkFrame(card.body_frame, fg_color="transparent")
        header.pack(fill="x", pady=(0, 8))

        self.btn_reset_persona = GhostButton(
            header,
            text=t("trans_persona_reset"),
            command=self._reset_persona,
            height=32,
            width=80,
        )
        self.btn_reset_persona.pack(side="right")

        # Persona textarea (scrollable)
        self.txt_persona = ctk.CTkTextbox(
            card.body_frame,
            font=theme.ctk_font("body"),
            corner_radius=theme.radius("sm"),
            border_width=1,
            border_color=token_pair("border"),
            fg_color=token_pair("surface"),
            text_color=token_pair("text"),
            height=160,
        )
        self.txt_persona.pack(fill="both", expand=True, pady=(0, 8))
        self.txt_persona.insert("0.0", t("trans_persona_default"))

        # Helper text
        p_helper = ctk.CTkLabel(
            card.body_frame,
            text=t("trans_persona_help"),
            font=theme.ctk_font("muted"),
            text_color=token_pair("text_muted"),
            anchor="w",
        )
        p_helper.pack(fill="x")

    def _create_progress_card(self):
        """Card 3: Progress bar + Start button."""
        card = Card(self._content, title=t("trans_status_ready"), padding="md")
        self.progress_card = card
        card.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        card.body_frame.grid_columnconfigure(0, weight=1)

        # Progress bar (always visible, animated fill)
        self.progress_bar = ctk.CTkProgressBar(
            card.body_frame,
            progress_color=token_pair("primary"),
            fg_color=token_pair("border"),
            height=8,
            corner_radius=4,
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", pady=(0, 6))

        # Status line: counter | buttons
        status_row = ctk.CTkFrame(card.body_frame, fg_color="transparent")
        status_row.pack(fill="x")
        status_row.grid_columnconfigure(1, weight=1)

        self.progress_text = ctk.CTkLabel(
            status_row,
            text="0 / 0",
            font=theme.ctk_font("small"),
            text_color=token_pair("text_muted"),
        )
        self.progress_text.grid(row=0, column=0, padx=0, pady=4, sticky="w")

        self.btn_cancel = GhostButton(
            status_row,
            text=t("trans_cancel"),
            command=self._cancel_translation,
            height=38,
            width=90,
            state="disabled",
        )
        self.btn_cancel.grid(row=0, column=1, padx=4, pady=4, sticky="e")

        self.btn_start = PrimaryButton(
            status_row,
            text=t("trans_start"),
            command=self._start_translation,
            height=38,
            width=150,
        )
        self.btn_start.grid(row=0, column=2, padx=4, pady=4, sticky="e")

    def _browse_file(self):
        path = filedialog.askopenfilename(
            title=t("trans_source_label"),
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if path:
            # Validate file type and size
            if not path.lower().endswith(".txt"):
                self._toast.show(t("toast_warning"), t("trans_invalid_file"), "warning")
                return

            try:
                size = os.path.getsize(path)
                max_size = 10 * 1024 * 1024  # 10 MB
                if size > max_size:
                    self._toast.show(t("toast_warning"), t("trans_file_too_large"), "warning")
                    return
            except OSError:
                self._toast.show(t("toast_error"), t("trans_cannot_read_file"), "error")
                return

            self.file_path_var.set(path)
            self._update_file_info(path)
            self.btn_start.set_variant("primary")

    def _update_file_info(self, path):
        try:
            size = os.path.getsize(path)
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1024 * 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size / (1024 * 1024):.1f} MB"
            name = os.path.basename(path)
            self.file_info_label.configure(text=f"{t('trans_file_info')}: {size_str}  |  {name}")
        except Exception:
            self.file_info_label.configure(text="")

    def _reset_persona(self):
        self.txt_persona.delete("0.0", "end")
        self.txt_persona.insert("0.0", t("trans_persona_default"))

    def _start_translation(self):
        input_file = self.file_path_var.get()
        if not input_file or input_file == t("trans_no_file") or not os.path.exists(input_file):
            self._toast.show(t("toast_warning"), t("trans_select_file_hint"), "warning")
            return

        # Respect user-configured output & archive directories from Settings, fallback to data_path
        output_dir = (self.config_manager.get("output_dir") or "").strip() or data_path("translated")
        archive_dir = (self.config_manager.get("archive_dir") or "").strip() or data_path("archived")

        self._is_running = True
        self.btn_start.configure(state="disabled", text=t("trans_status_running"))
        self.btn_cancel.configure(state="normal")
        self.progress_bar.set(0)
        self.progress_text.configure(text="0 / 0")

        self._engine = TranslationEngine(
            input_file=input_file,
            output_dir=output_dir,
            archive_dir=archive_dir,
            config_manager=self.config_manager,
            progress_callback=self._update_ui_progress,
            error_callback=self._handle_engine_error,
            completion_callback=self._on_translation_complete,
            persona=self.txt_persona.get("0.0", "end").strip(),
        )
        self._engine.start()

    def _on_translation_complete(self, file_path):
        self.after(0, lambda: self._apply_completion(file_path))

    def _cancel_translation(self):
        """Cancel the running translation."""
        if self._engine and self._engine.is_alive():
            self._engine.stop()
            self._toast.show(t("toast_info"), t("trans_cancelled"), "info")
            self._is_running = False
            self.btn_start.configure(state="normal", text=t("trans_start"))
            self.btn_start.set_variant("primary")
            self.btn_cancel.configure(state="disabled")
            self.progress_text.configure(text=t("trans_cancelled"))
            self.progress_card.set_title(t("trans_status_ready"))

    def _apply_completion(self, file_path):
        self._is_running = False
        self.btn_start.configure(state="normal", text=t("trans_start"))
        self.btn_start.set_variant("primary")
        self.btn_cancel.configure(state="disabled")
        self.progress_bar.set(1)
        self.progress_text.configure(text=t("trans_status_success"))
        self.progress_card.set_title(t("trans_status_success"))
        if file_path:
            self.file_info_label.configure(text=f"Saved: {file_path}")

        # Show success toast
        self._toast.show(t("toast_success"), t("trans_success_msg"), "success")

    def _update_ui_progress(self, current, total, status):
        self.after(0, lambda: self._apply_ui_updates(current, total, status))

    def _apply_ui_updates(self, current, total, status):
        progress = current / total if total > 0 else 0
        self.progress_bar.set(progress)
        self.progress_text.configure(text=f"{current} / {total}")
        if status:
            self.progress_card.set_title(status)

    def _handle_engine_error(self, error_msg):
        self.after(0, lambda: self._apply_error_ui(error_msg))

    def _apply_error_ui(self, error_msg):
        self._is_running = False
        self.btn_start.configure(state="normal", text=t("trans_start"))
        self.btn_start.set_variant("primary")
        self.btn_cancel.configure(state="disabled")
        self.progress_text.configure(text=error_msg)
        self.progress_card.set_title(t("trans_status_error"))
        self._toast.show(t("toast_error"), error_msg, "error")