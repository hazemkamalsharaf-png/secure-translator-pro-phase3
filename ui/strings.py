"""
Central UI strings for SecureTranslatorPro.

All visible text passes through here so Arabic/localization can be added later.
Current language: English (en). Add a 'strings_ar' dict and a switch function
when you're ready to support Arabic.
"""


# App branding constants
APP_NAME = "SecureTranslator"
APP_VERSION = "v2.0"

STRINGS = {
    # Window / branding
    "app_title": "SecureTranslator",
    "app_version": "v2.0",
    "window_title": "SecureTranslator",

    # Sidebar
    "tab_translation": "Translation",
    "tab_glossary": "Glossary",
    "tab_settings": "Settings",

    # Translation tab
    "trans_title": "Translation Workspace",
    "trans_source_label": "Source File",
    "trans_no_file": "No file selected",
    "trans_browse": "Browse File",
    "trans_persona_label": "System Persona / Instructions",
    "trans_persona_help": "Define the translator's role, tone, and rules. Leave blank for the default.",
    "trans_persona_default": "You are an elite, award-winning literary translator.",
    "trans_persona_reset": "Reset",
    "trans_start": "Start Translation",
    "trans_status_ready": "Ready to begin.",
    "trans_status_running": "Processing…",
    "trans_status_success": "Translation complete!",
    "trans_status_error": "An error occurred.",
    "trans_progress": "Progress",
    "trans_success_title": "Translation Complete",
    "trans_success_msg": "Translation completed successfully!",
    "trans_open_file": "Open File",
    "trans_open_folder": "Open Folder",
    "trans_file_info": "Size",
    "trans_select_file_hint": "Select a .txt file to translate",
    "trans_invalid_file": "Invalid File Type",
    "trans_file_too_large": "File too large (max 10 MB)",
    "trans_cannot_read_file": "Cannot read file — please check permissions.",
    "trans_cancel": "Cancel",
    "trans_cancelled": "Translation cancelled by user.",

    # Glossary tab
    "glossary_title": "Glossary Manager",
    "glossary_add_term": "Add New Term",
    "glossary_search_placeholder": "Search terms...",
    "glossary_term_label": "Term",
    "glossary_translation_label": "Translation",
    "glossary_empty_title": "Your glossary is empty",
    "glossary_empty_hint": "Add key terms so the translator uses them consistently.",
    "glossary_term_placeholder": "Enter source term...",
    "glossary_translation_placeholder": "Enter translation...",
    "glossary_add": "Add",
    "glossary_fill_all_fields": "Source and Target terms are required.",
    "glossary_added_success": "Term added successfully!",
    "glossary_deleted_success": "Term deleted.",
    "glossary_confirm_delete": "Are you sure you want to remove this term?",
    "glossary_delete": "Delete",
    "glossary_remove": "Remove",

    # Settings tab
    "settings_title": "Application Settings",
    "settings_translation": "Translation Settings",
    "settings_engine_label": "Translation Engine Mode",
    "settings_local_title": "Local Model Settings",
    "settings_cloud_title": "Cloud API Settings",
    "settings_source_lang": "Source Language",
    "settings_target_lang": "Target Language",
    "settings_output_and_archive": "Output & Archive",
    "settings_output_dir": "Output Directory",
    "settings_archive_dir": "Archive Directory",
    "settings_browse": "Browse",
    "settings_browse_title": "Select Directory",
    "settings_engine": "Engine Mode",
    "settings_engine_local": "Local (LM Studio / Ollama)",
    "settings_engine_cloud": "Cloud (Google Gemini)",
    "settings_base_url": "Base URL",
    "settings_base_url_help": "e.g. http://localhost:1234/v1 (Open Web UI, LM Studio)",
    "settings_model_name": "Model Name",
    "settings_model_help": "e.g. llama3, mistral",
    "settings_timeout": "Request Timeout (s)",
    "settings_timeout_help": "Maximum seconds to wait for an LLM response",
    "settings_max_retries": "Max Retries",
    "settings_max_retries_help": "Number of retry attempts on timeout/connection failure",
    "settings_provider": "Provider",
    "settings_api_key": "API Key",
    "settings_api_key_placeholder": "Enter your Gemini API key...",
    "settings_api_key_help": "Your Gemini API key (kept private)",
    "settings_save": "Save Settings",
    "settings_saved": "Settings saved successfully!",
    "settings_save_error": "Failed to save settings.",
    "settings_show_key": "Show",
    "settings_hide_key": "Hide",

    # Toasts
    "toast_success": "Success",
    "toast_error": "Error",
    "toast_warning": "Warning",
    "toast_info": "Info",

    # Shared
    "btn_cancel": "Cancel",
    "btn_ok": "OK",
    "btn_confirm": "Confirm",
    "btn_delete": "Delete",
}


# --- Arabic strings (add later) ---
# STRINGS_AR = {
#     "app_title": "المترجم الآمن",
#     "tab_translation": "الترجمة",
#     ...
# }


def t(key: str, lang: str = "en") -> str:
    """Look up a string by key."""
    if lang == "ar":
        return STRINGS.get(key, key)
    return STRINGS.get(key, key)
