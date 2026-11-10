
import json
import os
import copy


class ConfigManager:
    def __init__(self, config_path):
        self.config_path = config_path
        self.defaults = {
            "engine_mode": "local",  # 'local' or 'cloud'
            "theme_mode": "dark",    # 'light' or 'dark'
            "local_settings": {
                "base_url": "http://localhost:1234/v1",
                "model_name": "llama3",
                "timeout": 120,
                "max_retries": 2
            },
            "cloud_settings": {
                "provider": "gemini",
                "api_key": ""
            },
            "source_lang": "en",
            "target_lang": "ar",
            "output_dir": "",
            "archive_dir": ""
        }
        self.config = self.load()

    def load(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    # Merge user config with defaults — use deep copy to avoid mutating self.defaults
                    base = copy.deepcopy(self.defaults)
                    return self._deep_merge(base, user_config)
            except Exception:
                return copy.deepcopy(self.defaults)
        return copy.deepcopy(self.defaults)

    def save(self, new_config):
        try:
            with open(self.config_path, 'w') as f:
                json.dump(new_config, f, indent=4)
            self.config = new_config
            return True
        except Exception:
            return False

    def _deep_merge(self, base, update):
        for key, value in update.items():
            if isinstance(value, dict) and key in base:
                base[key] = self._deep_merge(base[key], value)
            else:
                base[key] = value
        return base

    def get(self, key, subkey=None):
        if subkey:
            return self.config.get(key, {}).get(subkey)
        return self.config.get(key)

    def get_config(self):
        """Return the full merged config dict."""
        return self.config
