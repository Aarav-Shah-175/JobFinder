import os
import yaml
from typing import Dict, Any

class ConfigLoader:
    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.profile = self._load_yaml("profile.yaml")
        self.resume_profile = self._load_yaml("resume_profile.yaml")
        self.scoring = self._load_yaml("scoring.yaml")
        self.sources = self._load_yaml("sources.yaml")
        self.companies = self._load_yaml("companies.yaml")

    def _load_yaml(self, filename: str) -> Dict[str, Any]:
        filepath = os.path.join(self.config_dir, filename)
        if not os.path.exists(filepath):
            return {}
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            return {}

_config_instance = None

def get_config(config_dir: str = "config") -> ConfigLoader:
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigLoader(config_dir)
    return _config_instance
