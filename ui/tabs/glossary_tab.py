import os
import customtkinter as ctk
from tkinter import messagebox as _tk_msgbox
from data.database import GlossaryManager
from ui.theme import ThemeManager, token_pair, entry_style
from ui.strings import t
from ui.asset_path import data_dir
from ui.components.card import Card
from ui.components.toast import Toast
from ui.components.button import PrimaryButton, DangerGhostButton

theme = ThemeManager.get_instance()


class GlossaryTab(ctk.CTkFrame):
    """
    Redesigned glossary tab with card layout, search, and clean table.

    Constructor contract: GlossaryTab(parent)
    """

    def __init__(self, master):
        super().__init__(master, fg_color=token_pair("bg"))

        # Unified path resolution via asset_path module
        self.db_path = os.path.join(data_dir(), "glossary.db")
        self.manager = GlossaryManager(self.db_path)

        self._toast = Toast(self)

        self.toolbar = ctk.CTkFrame(self, fg_color="transparent")
        self.toolbar.pack(fill="x", side="top", padx=24, pady=(16, 0))
        self.toolbar.grid_columnconfigure(0, weight=1)

        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(
            self.toolbar,
            textvariable=self.search_var,
            placeholder_text=t("glossary_search_placeholder"),
            font=theme.ctk_font("body"),
            height=36,
            corner_radius=theme.radius("sm"),
            border_width=1,
            **entry_style(),
        )
        self.search_entry.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        self.search_var.trace_add("write", lambda *args: self._refresh_table())

        self.btn_add = PrimaryButton(
            self.toolbar,
            text=t("glossary_add_term"),
            command=self._toggle_add_form,
            height=36,
            width=140,
        )
        self.btn_add.grid(row=0, column=1, sticky="e")

        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color=token_pair("bg"))
        self.scroll_frame.pack(fill="both", expand=True)

        # Add term form (initially hidden)
        self.add_form_frame = ctk.CTkFrame(
            self.scroll_frame,
            fg_color=token_pair("surface"),
            corner_radius=theme.radius("md"),
            border_width=1,
            border_color=token_pair("border"),
        )

        self.table_shell = ctk.CTkFrame(
            self.scroll_frame,
            fg_color=token_pair("surface"),
            corner_radius=theme.radius("lg"),
            border_width=1,
            border_color=token_pair("border"),
        )
        self.table_shell.pack(fill="both", expand=True, padx=24, pady=(12, 24), side="top")

        self.table_header = ctk.CTkFrame(
            self.table_shell,
            fg_color="transparent",
            corner_radius=0,
        )
        self.table_header.pack(fill="x", side="top")

        header_source_lbl = ctk.CTkLabel(
            self.table_header,
            text=t("glossary_term_label"),
            font=theme.ctk_font("small", weight="bold"),
            text_color=token_pair("text_muted"),
            anchor="w",
        )
        header_source_lbl.pack(side="left", fill="x", padx=16, pady=(12, 8), expand=True)

        header_target_lbl = ctk.CTkLabel(
            self.table_header,
            text=t("glossary_translation_label"),
            font=theme.ctk_font("small", weight="bold"),
            text_color=token_pair("text_muted"),
            anchor="w",
        )
        header_target_lbl.pack(side="left", fill="x", padx=(0, 16), pady=(12, 8), expand=True)

        header_action_lbl = ctk.CTkLabel(
            self.table_header,
            text="",
            width=70,
            anchor="e",
        )
        header_action_lbl.pack(side="right", padx=16, pady=(8, 8))

        # --- Glossary entries container ---
        ctk.CTkFrame(
            self.table_shell, height=1, fg_color=token_pair("border_light"), corner_radius=0,
        ).pack(fill="x", side="top")

        self.entries_frame = ctk.CTkFrame(self.table_shell, fg_color="transparent")
        self.entries_frame.pack(fill="both", expand=True, side="top")

        # --- Empty state (shown when no entries) ---
        self.empty_label = ctk.CTkLabel(
            self.entries_frame,
            text=f"{t('glossary_empty_title')}\n{t('glossary_empty_hint')}",
            font=theme.ctk_font("body"),
            text_color=token_pair("text_muted"),
            anchor="center",
            justify="center",
        )

        self._entry_rows = []
        self._refresh_table()

    def _toggle_add_form(self):
        """Show or hide the one-row add-term form."""
        if self.add_form_frame.winfo_ismapped():
            self.add_form_frame.pack_forget()
            return

        # Clear and rebuild the add form
        for child in self.add_form_frame.winfo_children():
            child.destroy()

        self.add_form_frame.grid_columnconfigure(1, weight=1)
        self.add_form_frame.grid_columnconfigure(3, weight=1)

        term_lbl = ctk.CTkLabel(
            self.add_form_frame,
            text=t("glossary_term_label"),
            font=theme.ctk_font("label"),
            text_color=token_pair("text"),
        )
        term_lbl.grid(row=0, column=0, padx=(16, 8), pady=12, sticky="w")

        self.add_term_var = ctk.StringVar()
        add_entry = ctk.CTkEntry(
            self.add_form_frame,
            textvariable=self.add_term_var,
            placeholder_text=t("glossary_term_placeholder"),
            font=theme.ctk_font("body"),
            height=36,
            corner_radius=theme.radius("sm"),
            border_width=1,
            **entry_style(),
        )
        add_entry.grid(row=0, column=1, padx=(0, 8), pady=12, sticky="ew")

        trans_lbl = ctk.CTkLabel(
            self.add_form_frame,
            text=t("glossary_translation_label"),
            font=theme.ctk_font("label"),
            text_color=token_pair("text"),
        )
        trans_lbl.grid(row=0, column=2, padx=(8, 8), pady=12, sticky="w")

        self.add_trans_var = ctk.StringVar()
        add_trans_entry = ctk.CTkEntry(
            self.add_form_frame,
            textvariable=self.add_trans_var,
            placeholder_text=t("glossary_translation_placeholder"),
            font=theme.ctk_font("body"),
            height=36,
            corner_radius=theme.radius("sm"),
            border_width=1,
            **entry_style(),
        )
        add_trans_entry.grid(row=0, column=3, padx=(0, 8), pady=12, sticky="ew")

        def do_add():
            self._add_term()

        btn = PrimaryButton(
            self.add_form_frame,
            text=t("glossary_add"),
            command=do_add,
            height=36,
            width=90,
        )
        btn.grid(row=0, column=4, padx=(0, 16), pady=12)

        self.add_form_frame.pack(fill="x", padx=24, pady=(16, 0), side="top", before=self.table_shell)
        add_entry.focus_set()

    def _add_term(self):
        """Add a new term from the form fields."""
        term = self.add_term_var.get().strip()
        trans = self.add_trans_var.get().strip()

        if not term or not trans:
            self._toast.show(t("toast_warning"), t("glossary_fill_all_fields"), "warning")
            return

        try:
            self.manager.add_entry(term, trans)
            self._toast.show(t("toast_success"), t("glossary_added_success"), "success")
            self.add_term_var.set("")
            self.add_trans_var.set("")
            self._refresh_table()
        except Exception as e:
            self._toast.show(t("toast_error"), str(e), "error")

    def _refresh_table(self):
        """Rebuild the glossary table from DB, applying search filter."""
        query = self.search_var.get().strip().lower()

        # Remove existing entry rows
        for row in self._entry_rows:
            row.destroy()
        self._entry_rows.clear()

        entries = self.manager.get_all_entries()
        filtered = [e for e in entries if not query or query in e["source"].lower() or query in e["target"].lower()]

        # Show/hide empty state
        if filtered:
            self.empty_label.pack_forget()
        else:
            self.empty_label.pack(fill="x", padx=16, pady=36)

        for idx, item in enumerate(filtered):
            bg = token_pair("surface_hover") if idx % 2 == 0 else token_pair("surface")
            row_frame = ctk.CTkFrame(
                self.entries_frame,
                fg_color=bg,
                corner_radius=0,
                height=44,
            )
            row_frame.pack(fill="x", side="top")

            term_lbl = ctk.CTkLabel(
                row_frame,
                text=item["source"],
                font=theme.ctk_font("body"),
                text_color=token_pair("text"),
                anchor="w",
            )
            term_lbl.pack(side="left", fill="x", padx=(16, 8), pady=(0, 0), expand=True)

            trans_lbl = ctk.CTkLabel(
                row_frame,
                text=item["target"],
                font=theme.ctk_font("body"),
                text_color=token_pair("text_muted"),
                anchor="w",
            )
            trans_lbl.pack(side="left", fill="x", padx=(0, 8), pady=(0, 0), expand=True)

            # Delete button (right-aligned) — uses entry id, not source_term
            del_btn = DangerGhostButton(
                row_frame,
                text=t("glossary_delete"),
                command=lambda tid=item["id"]: self._delete_term(tid),
                height=28,
                width=72,
            )
            del_btn.pack(side="right", padx=(0, 16))

            # Separator line below row (except last)
            if idx < len(filtered) - 1:
                line = ctk.CTkFrame(
                    self.entries_frame,
                    height=1,
                    fg_color=token_pair("border_light"),
                    corner_radius=0,
                )
                line.pack(fill="x")
                self._entry_rows.append(line)

            self._entry_rows.append(row_frame)

    def _delete_term(self, term_id):
        """Delete a term from the glossary by id."""
        try:
            entry = [e for e in self.manager.get_all_entries() if e["id"] == term_id]
            display_name = entry[0]["source"] if entry else f"#{term_id}"
        except Exception:
            display_name = f"#{term_id}"
        if _tk_msgbox.askyesno(t("glossary_confirm_delete"), f"{t('glossary_remove')} '{display_name}'?"):
            try:
                self.manager.delete_entry(term_id)
                self._toast.show(t("toast_success"), t("glossary_deleted_success"), "success")
                self._refresh_table()
            except Exception as e:
                self._toast.show(t("toast_error"), str(e), "error")

    def load_entries(self):
        """Load glossary entries into the table view."""
        self.search_var.set("")
        self._refresh_table()
